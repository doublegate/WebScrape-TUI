"""
Unit tests for rate limiting and account lockout module.

Tests login rate limiting, account lockout, and automatic unlock functionality.
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, timezone, timedelta

from scrapetui.core.rate_limit import (
    RateLimiter,
    RateLimitConfig,
    LoginAttemptResult
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # Create tables
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            account_locked INTEGER DEFAULT 0,
            locked_until TEXT,
            failed_login_attempts INTEGER DEFAULT 0,
            last_failed_login TEXT
        )
    """)
    conn.execute("""
        INSERT INTO users (username, password_hash)
        VALUES ('testuser', 'hash123')
    """)
    conn.commit()
    conn.close()

    yield path

    os.unlink(path)


class TestRateLimiter:
    """Test RateLimiter class."""

    def test_initialization(self, temp_db):
        """Test rate limiter initialization."""
        limiter = RateLimiter(temp_db)
        assert limiter.db_path == temp_db
        assert limiter.config.max_attempts == 5
        assert limiter.config.lockout_duration_minutes == 15

    def test_custom_config(self, temp_db):
        """Test rate limiter with custom config."""
        config = RateLimitConfig(
            max_attempts=3,
            lockout_duration_minutes=10
        )
        limiter = RateLimiter(temp_db, config)
        assert limiter.config.max_attempts == 3
        assert limiter.config.lockout_duration_minutes == 10

    def test_record_successful_attempt(self, temp_db):
        """Test recording successful login attempt."""
        limiter = RateLimiter(temp_db)
        limiter.record_login_attempt(
            'testuser',
            success=True,
            ip_address='127.0.0.1'
        )

        # Check attempt was recorded
        conn = sqlite3.connect(temp_db)
        attempts = conn.execute("""
            SELECT * FROM login_attempts
            WHERE username = 'testuser' AND success = 1
        """).fetchall()
        conn.close()

        assert len(attempts) == 1

    def test_record_failed_attempt(self, temp_db):
        """Test recording failed login attempt."""
        limiter = RateLimiter(temp_db)
        limiter.record_login_attempt(
            'testuser',
            success=False,
            ip_address='127.0.0.1'
        )

        # Check attempt was recorded and counter incremented
        conn = sqlite3.connect(temp_db)
        user = conn.execute("""
            SELECT failed_login_attempts FROM users
            WHERE username = 'testuser'
        """).fetchone()
        conn.close()

        assert user[0] == 1

    def test_rate_limit_not_exceeded(self, temp_db):
        """Test rate limit check when not exceeded."""
        limiter = RateLimiter(temp_db)

        # Record 2 failed attempts
        for _ in range(2):
            limiter.record_login_attempt('testuser', success=False)

        result = limiter.check_rate_limit('testuser')
        assert result.allowed is True
        assert result.attempts_remaining == 3  # 5 - 2 = 3

    def test_rate_limit_exceeded(self, temp_db):
        """Test rate limit check when exceeded."""
        limiter = RateLimiter(temp_db)

        # Record 5 failed attempts
        for _ in range(5):
            limiter.record_login_attempt('testuser', success=False)

        result = limiter.check_rate_limit('testuser')
        assert result.allowed is False
        assert result.attempts_remaining == 0
        assert "locked" in result.message.lower()

    def test_account_lockout(self, temp_db):
        """Test account lockout after max attempts."""
        config = RateLimitConfig(max_attempts=3)
        limiter = RateLimiter(temp_db, config)

        # Exceed limit
        for _ in range(3):
            limiter.record_login_attempt('testuser', success=False)

        # Check lockout
        result = limiter.check_rate_limit('testuser')
        assert result.allowed is False

        # Verify account is locked in database
        conn = sqlite3.connect(temp_db)
        user = conn.execute("""
            SELECT account_locked, locked_until FROM users
            WHERE username = 'testuser'
        """).fetchone()
        conn.close()

        assert user[0] == 1  # account_locked
        assert user[1] is not None  # locked_until set

    def test_auto_unlock(self, temp_db):
        """Test automatic unlock after duration."""
        limiter = RateLimiter(temp_db)

        # Lock account manually with past expiration
        past_time = (
            datetime.now(timezone.utc) - timedelta(minutes=1)
        ).isoformat()

        conn = sqlite3.connect(temp_db)
        conn.execute("""
            UPDATE users
            SET account_locked = 1, locked_until = ?
            WHERE username = 'testuser'
        """, (past_time,))
        conn.commit()
        conn.close()

        # Check rate limit should auto-unlock
        result = limiter.check_rate_limit('testuser')
        assert result.allowed is True
        assert "auto-unlocked" in result.message.lower()

    def test_manual_unlock(self, temp_db):
        """Test manual account unlock."""
        limiter = RateLimiter(temp_db)

        # Lock account
        limiter.lock_account('testuser')

        # Unlock
        limiter.unlock_account('testuser')

        # Verify unlocked
        conn = sqlite3.connect(temp_db)
        user = conn.execute("""
            SELECT account_locked, failed_login_attempts FROM users
            WHERE username = 'testuser'
        """).fetchone()
        conn.close()

        assert user[0] == 0  # Not locked
        assert user[1] == 0  # Failed attempts reset

    def test_admin_lock(self, temp_db):
        """Test admin-initiated lock (no auto-unlock)."""
        limiter = RateLimiter(temp_db)

        # Admin lock
        limiter.lock_account('testuser', admin_lock=True)

        # Check locked with no expiration
        conn = sqlite3.connect(temp_db)
        user = conn.execute("""
            SELECT account_locked, locked_until FROM users
            WHERE username = 'testuser'
        """).fetchone()
        conn.close()

        assert user[0] == 1  # Locked
        assert user[1] is None  # No auto-unlock time

    def test_failed_attempts_count(self, temp_db):
        """Test getting failed attempts count."""
        limiter = RateLimiter(temp_db)

        # Record 3 failed attempts
        for _ in range(3):
            limiter.record_login_attempt('testuser', success=False)

        count = limiter.get_failed_attempts_count('testuser')
        assert count == 3

    def test_cleanup_old_attempts(self, temp_db):
        """Test cleanup of old login attempts."""
        limiter = RateLimiter(temp_db)

        # Record attempt
        limiter.record_login_attempt('testuser', success=False)

        # Manually set old timestamp
        old_time = (
            datetime.now(timezone.utc) - timedelta(days=60)
        ).isoformat()

        conn = sqlite3.connect(temp_db)
        conn.execute("""
            UPDATE login_attempts
            SET attempted_at = ?
        """, (old_time,))
        conn.commit()
        conn.close()

        # Cleanup attempts older than 30 days
        deleted = limiter.cleanup_old_attempts(days=30)
        assert deleted == 1

    def test_successful_login_resets_counter(self, temp_db):
        """Test that successful login resets failed attempts."""
        limiter = RateLimiter(temp_db)

        # Record failed attempts
        for _ in range(3):
            limiter.record_login_attempt('testuser', success=False)

        # Successful login
        limiter.record_login_attempt('testuser', success=True)

        # Check counter reset
        conn = sqlite3.connect(temp_db)
        user = conn.execute("""
            SELECT failed_login_attempts FROM users
            WHERE username = 'testuser'
        """).fetchone()
        conn.close()

        assert user[0] == 0

    def test_nonexistent_user(self, temp_db):
        """Test rate limit check for nonexistent user."""
        limiter = RateLimiter(temp_db)

        result = limiter.check_rate_limit('nonexistent')
        assert result.allowed is True  # Allow attempt (will fail anyway)


class TestLoginAttemptResult:
    """Test LoginAttemptResult dataclass."""

    def test_result_structure(self):
        """Test LoginAttemptResult data structure."""
        result = LoginAttemptResult(
            allowed=True,
            attempts_remaining=3,
            locked_until=None,
            message="Login allowed"
        )

        assert result.allowed is True
        assert result.attempts_remaining == 3
        assert result.locked_until is None
        assert result.message == "Login allowed"


class TestRateLimitConfig:
    """Test RateLimitConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RateLimitConfig()
        assert config.max_attempts == 5
        assert config.lockout_duration_minutes == 15
        assert config.attempt_window_minutes == 30

    def test_custom_config(self):
        """Test custom configuration values."""
        config = RateLimitConfig(
            max_attempts=10,
            lockout_duration_minutes=30,
            attempt_window_minutes=60
        )
        assert config.max_attempts == 10
        assert config.lockout_duration_minutes == 30
        assert config.attempt_window_minutes == 60


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
