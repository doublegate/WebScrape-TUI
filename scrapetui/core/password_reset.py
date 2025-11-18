"""
Password Reset System

Provides secure token-based password reset functionality.
Supports both admin-initiated and self-service password resets.

Part of v2.2.0 Security Enhancements.
"""

import secrets
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from dataclasses import dataclass

from .audit import log_audit_event, AuditEventType


@dataclass
class PasswordResetConfig:
    """Password reset configuration."""
    token_expiration_hours: int = 24
    token_length: int = 32  # bytes (64 hex characters)


@dataclass
class ResetTokenInfo:
    """Information about a reset token."""
    valid: bool
    user_id: Optional[int]
    username: Optional[str]
    expires_at: Optional[str]
    message: str


class PasswordResetManager:
    """Manages password reset tokens and operations."""

    def __init__(
        self,
        db_path: str = "scraped_data_tui_v1.0.db",
        config: PasswordResetConfig = None
    ):
        """
        Initialize password reset manager.

        Args:
            db_path: Path to SQLite database
            config: Reset configuration
        """
        self.db_path = db_path
        self.config = config or PasswordResetConfig()
        self._ensure_tables()

    def _ensure_tables(self):
        """Ensure password_reset_tokens table exists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    used_at TEXT,
                    created_by INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_reset_token
                ON password_reset_tokens(token)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_reset_user_created
                ON password_reset_tokens(user_id, created_at)
            """)

            # Add password-related columns to users table if they don't exist
            try:
                conn.execute("""
                    ALTER TABLE users ADD COLUMN password_changed_at TEXT
                """)
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                conn.execute("""
                    ALTER TABLE users ADD COLUMN force_password_change
                    INTEGER NOT NULL DEFAULT 0
                """)
            except sqlite3.OperationalError:
                pass  # Column already exists

            conn.commit()

    def generate_reset_token(
        self,
        user_id: int,
        created_by: Optional[int] = None
    ) -> Tuple[str, str]:
        """
        Generate a password reset token for a user.

        Args:
            user_id: User ID to generate token for
            created_by: Admin user ID who created the token (if applicable)

        Returns:
            Tuple of (token, expires_at)

        Example:
            >>> mgr = PasswordResetManager()
            >>> token, expires = mgr.generate_reset_token(user_id=5)
            >>> print(f"Reset token: {token}")
            >>> print(f"Expires: {expires}")
        """
        # Generate cryptographically secure token
        token = secrets.token_hex(self.config.token_length)

        now = datetime.now(timezone.utc)
        created_at = now.isoformat()
        expires_at = (
            now + timedelta(hours=self.config.token_expiration_hours)
        ).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get username for audit log
            user = conn.execute("""
                SELECT username FROM users WHERE id = ?
            """, (user_id,)).fetchone()

            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            username = user['username']

            # Invalidate any existing unused tokens for this user
            conn.execute("""
                UPDATE password_reset_tokens
                SET used_at = ?
                WHERE user_id = ?
                AND used_at IS NULL
            """, (created_at, user_id))

            # Create new token
            conn.execute("""
                INSERT INTO password_reset_tokens
                (user_id, token, created_at, expires_at, created_by)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, token, created_at, expires_at, created_by))

            conn.commit()

            # Log audit event
            log_audit_event(
                AuditEventType.PASSWORD_RESET_REQUESTED,
                user_id=user_id,
                username=username,
                event_data={
                    'created_by': created_by,
                    'expires_at': expires_at
                }
            )

        return token, expires_at

    def validate_token(self, token: str) -> ResetTokenInfo:
        """
        Validate a password reset token.

        Args:
            token: Token to validate

        Returns:
            ResetTokenInfo with validation result
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            token_record = conn.execute("""
                SELECT rt.*, u.username
                FROM password_reset_tokens rt
                JOIN users u ON rt.user_id = u.id
                WHERE rt.token = ?
            """, (token,)).fetchone()

            if not token_record:
                return ResetTokenInfo(
                    valid=False,
                    user_id=None,
                    username=None,
                    expires_at=None,
                    message="Invalid token"
                )

            # Check if already used
            if token_record['used_at']:
                return ResetTokenInfo(
                    valid=False,
                    user_id=token_record['user_id'],
                    username=token_record['username'],
                    expires_at=token_record['expires_at'],
                    message="Token has already been used"
                )

            # Check if expired
            expires_at = datetime.fromisoformat(token_record['expires_at'])
            now = datetime.now(timezone.utc)

            if now > expires_at:
                return ResetTokenInfo(
                    valid=False,
                    user_id=token_record['user_id'],
                    username=token_record['username'],
                    expires_at=token_record['expires_at'],
                    message="Token has expired"
                )

            # Token is valid
            return ResetTokenInfo(
                valid=True,
                user_id=token_record['user_id'],
                username=token_record['username'],
                expires_at=token_record['expires_at'],
                message="Token is valid"
            )

    def use_token(self, token: str, new_password_hash: str) -> bool:
        """
        Use a reset token to change password.

        Args:
            token: Reset token
            new_password_hash: Bcrypt hash of new password

        Returns:
            True if successful, False otherwise
        """
        # Validate token first
        token_info = self.validate_token(token)

        if not token_info.valid:
            return False

        now = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            # Update password
            conn.execute("""
                UPDATE users
                SET password_hash = ?,
                    password_changed_at = ?,
                    force_password_change = 0
                WHERE id = ?
            """, (new_password_hash, now, token_info.user_id))

            # Mark token as used
            conn.execute("""
                UPDATE password_reset_tokens
                SET used_at = ?
                WHERE token = ?
            """, (now, token))

            # Invalidate all sessions for this user (force re-login)
            conn.execute("""
                DELETE FROM user_sessions
                WHERE user_id = ?
            """, (token_info.user_id,))

            conn.commit()

            # Log audit event
            log_audit_event(
                AuditEventType.PASSWORD_RESET_COMPLETED,
                user_id=token_info.user_id,
                username=token_info.username
            )

        return True

    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired reset tokens.

        Returns:
            Number of tokens deleted
        """
        now = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM password_reset_tokens
                WHERE expires_at < ?
                OR used_at IS NOT NULL
            """, (now,))
            conn.commit()
            return cursor.rowcount

    def get_user_tokens(
        self,
        user_id: int,
        include_used: bool = False
    ) -> list:
        """
        Get all reset tokens for a user.

        Args:
            user_id: User ID
            include_used: Include used/expired tokens

        Returns:
            List of token records
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            query = """
                SELECT * FROM password_reset_tokens
                WHERE user_id = ?
            """
            params = [user_id]

            if not include_used:
                query += " AND used_at IS NULL"

            query += " ORDER BY created_at DESC"

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]


# Global password reset manager instance
_reset_manager: Optional[PasswordResetManager] = None


def get_password_reset_manager(
    db_path: str = "scraped_data_tui_v1.0.db",
    config: PasswordResetConfig = None
) -> PasswordResetManager:
    """
    Get or create global password reset manager instance.

    Args:
        db_path: Path to database
        config: Reset configuration

    Returns:
        PasswordResetManager instance
    """
    global _reset_manager
    if _reset_manager is None:
        _reset_manager = PasswordResetManager(db_path, config)
    return _reset_manager
