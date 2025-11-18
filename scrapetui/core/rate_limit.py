"""
Rate Limiting and Account Lockout Protection

Implements login rate limiting and account lockout to prevent brute force attacks.

Part of v2.2.0 Security Enhancements.
"""

import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from dataclasses import dataclass

from .audit import log_audit_event, AuditEventType


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    max_attempts: int = 5
    lockout_duration_minutes: int = 15
    attempt_window_minutes: int = 30


@dataclass
class LoginAttemptResult:
    """Result of login attempt check."""
    allowed: bool
    attempts_remaining: int
    locked_until: Optional[str]
    message: str


class RateLimiter:
    """Manages login rate limiting and account lockout."""

    def __init__(
        self,
        db_path: str = "scraped_data_tui_v1.0.db",
        config: RateLimitConfig = None
    ):
        """
        Initialize rate limiter.

        Args:
            db_path: Path to SQLite database
            config: Rate limit configuration
        """
        self.db_path = db_path
        self.config = config or RateLimitConfig()
        self._ensure_tables()

    def _ensure_tables(self):
        """Ensure required database tables exist."""
        with sqlite3.connect(self.db_path) as conn:
            # Login attempts tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    ip_address TEXT,
                    success INTEGER NOT NULL DEFAULT 0,
                    attempted_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_login_attempts_username
                ON login_attempts(username, attempted_at)
            """)

            # Add lockout columns to users table if they don't exist
            try:
                conn.execute("""
                    ALTER TABLE users ADD COLUMN account_locked
                    INTEGER NOT NULL DEFAULT 0
                """)
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                conn.execute("""
                    ALTER TABLE users ADD COLUMN locked_until TEXT
                """)
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                conn.execute("""
                    ALTER TABLE users ADD COLUMN failed_login_attempts
                    INTEGER NOT NULL DEFAULT 0
                """)
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                conn.execute("""
                    ALTER TABLE users ADD COLUMN last_failed_login TEXT
                """)
            except sqlite3.OperationalError:
                pass  # Column already exists

            conn.commit()

    def record_login_attempt(
        self,
        username: str,
        success: bool,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Record a login attempt.

        Args:
            username: Username that attempted login
            success: Whether login was successful
            ip_address: IP address of the attempt
        """
        now = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            # Record attempt in login_attempts table
            conn.execute("""
                INSERT INTO login_attempts
                (username, ip_address, success, attempted_at)
                VALUES (?, ?, ?, ?)
            """, (username, ip_address, 1 if success else 0, now))

            if success:
                # Reset failed attempts counter on successful login
                conn.execute("""
                    UPDATE users
                    SET failed_login_attempts = 0,
                        last_failed_login = NULL
                    WHERE username = ?
                """, (username,))
            else:
                # Increment failed attempts counter
                conn.execute("""
                    UPDATE users
                    SET failed_login_attempts = failed_login_attempts + 1,
                        last_failed_login = ?
                    WHERE username = ?
                """, (now, username))

            conn.commit()

    def check_rate_limit(
        self,
        username: str
    ) -> LoginAttemptResult:
        """
        Check if login attempt is allowed for user.

        Args:
            username: Username to check

        Returns:
            LoginAttemptResult with status and details
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Check if account is locked
            user = conn.execute("""
                SELECT account_locked, locked_until, failed_login_attempts
                FROM users
                WHERE username = ?
            """, (username,)).fetchone()

            if not user:
                # User doesn't exist, allow attempt (will fail anyway)
                return LoginAttemptResult(
                    allowed=True,
                    attempts_remaining=self.config.max_attempts,
                    locked_until=None,
                    message="Login attempt allowed"
                )

            # Check if account is locked
            if user['account_locked']:
                locked_until_str = user['locked_until']
                if locked_until_str:
                    locked_until = datetime.fromisoformat(locked_until_str)
                    now = datetime.now(timezone.utc)

                    if now < locked_until:
                        # Still locked
                        minutes_left = int(
                            (locked_until - now).total_seconds() / 60
                        )
                        return LoginAttemptResult(
                            allowed=False,
                            attempts_remaining=0,
                            locked_until=locked_until_str,
                            message=f"Account locked for {minutes_left} more minutes"
                        )
                    else:
                        # Lock expired, unlock account
                        self.unlock_account(username, auto_unlock=True)
                        return LoginAttemptResult(
                            allowed=True,
                            attempts_remaining=self.config.max_attempts,
                            locked_until=None,
                            message="Account auto-unlocked, login attempt allowed"
                        )

            # Check recent failed attempts
            window_start = (
                datetime.now(timezone.utc) -
                timedelta(minutes=self.config.attempt_window_minutes)
            ).isoformat()

            failed_count = conn.execute("""
                SELECT COUNT(*) as count
                FROM login_attempts
                WHERE username = ?
                AND success = 0
                AND attempted_at >= ?
            """, (username, window_start)).fetchone()['count']

            attempts_remaining = max(
                0,
                self.config.max_attempts - failed_count
            )

            if failed_count >= self.config.max_attempts:
                # Lock the account
                self.lock_account(username)
                return LoginAttemptResult(
                    allowed=False,
                    attempts_remaining=0,
                    locked_until=self._get_lockout_time(),
                    message=f"Account locked due to {failed_count} failed login attempts"
                )

            return LoginAttemptResult(
                allowed=True,
                attempts_remaining=attempts_remaining,
                locked_until=None,
                message=f"Login attempt allowed ({attempts_remaining} attempts remaining)"
            )

    def lock_account(
        self,
        username: str,
        admin_lock: bool = False
    ) -> None:
        """
        Lock a user account.

        Args:
            username: Username to lock
            admin_lock: Whether lock is admin-initiated (no auto-unlock)
        """
        locked_until = None if admin_lock else self._get_lockout_time()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE users
                SET account_locked = 1,
                    locked_until = ?
                WHERE username = ?
            """, (locked_until, username))
            conn.commit()

            # Get user_id for audit log
            user = conn.execute("""
                SELECT id FROM users WHERE username = ?
            """, (username,)).fetchone()

            if user:
                log_audit_event(
                    AuditEventType.ACCOUNT_LOCKED,
                    user_id=user[0],
                    username=username,
                    event_data={
                        'locked_until': locked_until,
                        'admin_lock': admin_lock
                    }
                )

    def unlock_account(
        self,
        username: str,
        auto_unlock: bool = False
    ) -> None:
        """
        Unlock a user account.

        Args:
            username: Username to unlock
            auto_unlock: Whether this is an automatic unlock
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE users
                SET account_locked = 0,
                    locked_until = NULL,
                    failed_login_attempts = 0,
                    last_failed_login = NULL
                WHERE username = ?
            """, (username,))
            conn.commit()

            # Get user_id for audit log
            user = conn.execute("""
                SELECT id FROM users WHERE username = ?
            """, (username,)).fetchone()

            if user:
                log_audit_event(
                    AuditEventType.ACCOUNT_UNLOCKED,
                    user_id=user[0],
                    username=username,
                    event_data={'auto_unlock': auto_unlock}
                )

    def _get_lockout_time(self) -> str:
        """
        Calculate lockout expiration time.

        Returns:
            ISO format timestamp
        """
        unlock_time = (
            datetime.now(timezone.utc) +
            timedelta(minutes=self.config.lockout_duration_minutes)
        )
        return unlock_time.isoformat()

    def get_failed_attempts_count(
        self,
        username: str,
        since_minutes: int = 30
    ) -> int:
        """
        Get count of failed login attempts for user.

        Args:
            username: Username to check
            since_minutes: Time window in minutes

        Returns:
            Number of failed attempts
        """
        window_start = (
            datetime.now(timezone.utc) -
            timedelta(minutes=since_minutes)
        ).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute("""
                SELECT COUNT(*) as count
                FROM login_attempts
                WHERE username = ?
                AND success = 0
                AND attempted_at >= ?
            """, (username, window_start)).fetchone()

            return result[0] if result else 0

    def cleanup_old_attempts(self, days: int = 30) -> int:
        """
        Remove old login attempt records.

        Args:
            days: Number of days to retain

        Returns:
            Number of records deleted
        """
        cutoff = (
            datetime.now(timezone.utc) -
            timedelta(days=days)
        ).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM login_attempts
                WHERE attempted_at < ?
            """, (cutoff,))
            conn.commit()
            return cursor.rowcount


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(
    db_path: str = "scraped_data_tui_v1.0.db",
    config: RateLimitConfig = None
) -> RateLimiter:
    """
    Get or create global rate limiter instance.

    Args:
        db_path: Path to database
        config: Rate limit configuration

    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(db_path, config)
    return _rate_limiter
