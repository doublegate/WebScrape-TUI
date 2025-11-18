"""
Unit tests for password reset module.

Tests token generation, validation, and password reset functionality.
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, timezone, timedelta

from scrapetui.core.password_reset import (
    PasswordResetManager,
    PasswordResetConfig,
    ResetTokenInfo,
    get_password_reset_manager
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
            password_changed_at TEXT,
            force_password_change INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE user_sessions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            session_token TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Insert test users
    conn.execute("""
        INSERT INTO users (id, username, password_hash)
        VALUES (1, 'testuser', 'oldhash123')
    """)
    conn.execute("""
        INSERT INTO users (id, username, password_hash)
        VALUES (2, 'admin', 'adminhash')
    """)
    conn.commit()
    conn.close()

    yield path

    os.unlink(path)


class TestPasswordResetManager:
    """Test PasswordResetManager class."""

    def test_initialization(self, temp_db):
        """Test password reset manager initialization."""
        mgr = PasswordResetManager(temp_db)
        assert mgr.db_path == temp_db
        assert mgr.config.token_expiration_hours == 24

        # Verify table was created
        conn = sqlite3.connect(temp_db)
        tables = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='password_reset_tokens'
        """).fetchone()
        conn.close()

        assert tables is not None

    def test_custom_config(self, temp_db):
        """Test password reset with custom config."""
        config = PasswordResetConfig(
            token_expiration_hours=48,
            token_length=64
        )
        mgr = PasswordResetManager(temp_db, config)
        assert mgr.config.token_expiration_hours == 48
        assert mgr.config.token_length == 64

    def test_generate_reset_token(self, temp_db):
        """Test generating password reset token."""
        mgr = PasswordResetManager(temp_db)

        token, expires_at = mgr.generate_reset_token(user_id=1)

        # Token should be non-empty string
        assert isinstance(token, str)
        assert len(token) == 64  # 32 bytes = 64 hex chars

        # Expires should be ISO format timestamp
        assert isinstance(expires_at, str)
        expires_dt = datetime.fromisoformat(expires_at)
        now = datetime.now(timezone.utc)
        assert expires_dt > now

    def test_token_uniqueness(self, temp_db):
        """Test that generated tokens are unique."""
        mgr = PasswordResetManager(temp_db)

        token1, _ = mgr.generate_reset_token(user_id=1)
        token2, _ = mgr.generate_reset_token(user_id=1)

        assert token1 != token2

    def test_generate_token_invalidates_old(self, temp_db):
        """Test that generating new token invalidates old ones."""
        mgr = PasswordResetManager(temp_db)

        # Generate first token
        token1, _ = mgr.generate_reset_token(user_id=1)

        # Generate second token (should invalidate first)
        token2, _ = mgr.generate_reset_token(user_id=1)

        # First token should be marked as used
        conn = sqlite3.connect(temp_db)
        old_token = conn.execute("""
            SELECT used_at FROM password_reset_tokens
            WHERE token = ?
        """, (token1,)).fetchone()
        conn.close()

        assert old_token[0] is not None  # used_at is set

    def test_validate_valid_token(self, temp_db):
        """Test validating a valid token."""
        mgr = PasswordResetManager(temp_db)

        token, _ = mgr.generate_reset_token(user_id=1)

        result = mgr.validate_token(token)

        assert result.valid is True
        assert result.user_id == 1
        assert result.username == 'testuser'
        assert result.message == 'Token is valid'

    def test_validate_invalid_token(self, temp_db):
        """Test validating an invalid token."""
        mgr = PasswordResetManager(temp_db)

        result = mgr.validate_token('invalid_token_12345')

        assert result.valid is False
        assert result.user_id is None
        assert 'Invalid token' in result.message

    def test_validate_expired_token(self, temp_db):
        """Test validating an expired token."""
        mgr = PasswordResetManager(temp_db)

        token, _ = mgr.generate_reset_token(user_id=1)

        # Manually expire the token
        past_time = (
            datetime.now(timezone.utc) - timedelta(hours=2)
        ).isoformat()

        conn = sqlite3.connect(temp_db)
        conn.execute("""
            UPDATE password_reset_tokens
            SET expires_at = ?
            WHERE token = ?
        """, (past_time, token))
        conn.commit()
        conn.close()

        result = mgr.validate_token(token)

        assert result.valid is False
        assert 'expired' in result.message.lower()

    def test_validate_used_token(self, temp_db):
        """Test validating a used token."""
        mgr = PasswordResetManager(temp_db)

        token, _ = mgr.generate_reset_token(user_id=1)

        # Mark token as used
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(temp_db)
        conn.execute("""
            UPDATE password_reset_tokens
            SET used_at = ?
            WHERE token = ?
        """, (now, token))
        conn.commit()
        conn.close()

        result = mgr.validate_token(token)

        assert result.valid is False
        assert 'already been used' in result.message

    def test_use_token(self, temp_db):
        """Test using a token to reset password."""
        mgr = PasswordResetManager(temp_db)

        token, _ = mgr.generate_reset_token(user_id=1)

        # Use token to change password
        success = mgr.use_token(token, 'newhash456')

        assert success is True

        # Verify password was changed
        conn = sqlite3.connect(temp_db)
        user = conn.execute("""
            SELECT password_hash, password_changed_at, force_password_change
            FROM users WHERE id = 1
        """).fetchone()
        conn.close()

        assert user[0] == 'newhash456'
        assert user[1] is not None  # password_changed_at set
        assert user[2] == 0  # force_password_change cleared

    def test_use_token_invalidates_sessions(self, temp_db):
        """Test that using token invalidates all user sessions."""
        mgr = PasswordResetManager(temp_db)

        # Create some sessions
        conn = sqlite3.connect(temp_db)
        conn.execute("""
            INSERT INTO user_sessions (user_id, session_token)
            VALUES (1, 'session1'), (1, 'session2')
        """)
        conn.commit()
        conn.close()

        token, _ = mgr.generate_reset_token(user_id=1)
        mgr.use_token(token, 'newhash')

        # Verify sessions were deleted
        conn = sqlite3.connect(temp_db)
        sessions = conn.execute("""
            SELECT * FROM user_sessions WHERE user_id = 1
        """).fetchall()
        conn.close()

        assert len(sessions) == 0

    def test_use_invalid_token(self, temp_db):
        """Test using an invalid token."""
        mgr = PasswordResetManager(temp_db)

        success = mgr.use_token('invalid_token', 'newhash')

        assert success is False

    def test_cleanup_expired_tokens(self, temp_db):
        """Test cleaning up expired tokens."""
        mgr = PasswordResetManager(temp_db)

        # Generate token
        token, _ = mgr.generate_reset_token(user_id=1)

        # Expire it
        past_time = (
            datetime.now(timezone.utc) - timedelta(hours=2)
        ).isoformat()

        conn = sqlite3.connect(temp_db)
        conn.execute("""
            UPDATE password_reset_tokens
            SET expires_at = ?
        """, (past_time,))
        conn.commit()
        conn.close()

        # Cleanup
        deleted = mgr.cleanup_expired_tokens()

        assert deleted == 1

    def test_cleanup_used_tokens(self, temp_db):
        """Test cleaning up used tokens."""
        mgr = PasswordResetManager(temp_db)

        token, _ = mgr.generate_reset_token(user_id=1)
        mgr.use_token(token, 'newhash')

        # Cleanup should remove used tokens
        deleted = mgr.cleanup_expired_tokens()

        assert deleted == 1

    def test_get_user_tokens(self, temp_db):
        """Test getting all tokens for a user."""
        mgr = PasswordResetManager(temp_db)

        # Generate multiple tokens
        token1, _ = mgr.generate_reset_token(user_id=1)
        # First token is invalidated when second is created
        token2, _ = mgr.generate_reset_token(user_id=1)

        tokens = mgr.get_user_tokens(user_id=1, include_used=True)

        assert len(tokens) == 2

    def test_get_user_tokens_active_only(self, temp_db):
        """Test getting only active tokens."""
        mgr = PasswordResetManager(temp_db)

        token1, _ = mgr.generate_reset_token(user_id=1)
        token2, _ = mgr.generate_reset_token(user_id=1)

        # Only second token should be active (first was invalidated)
        tokens = mgr.get_user_tokens(user_id=1, include_used=False)

        assert len(tokens) == 1
        assert tokens[0]['token'] == token2

    def test_admin_created_token(self, temp_db):
        """Test token created by admin."""
        mgr = PasswordResetManager(temp_db)

        token, _ = mgr.generate_reset_token(
            user_id=1,
            created_by=2  # Admin user
        )

        # Verify created_by is stored
        conn = sqlite3.connect(temp_db)
        reset = conn.execute("""
            SELECT created_by FROM password_reset_tokens
            WHERE token = ?
        """, (token,)).fetchone()
        conn.close()

        assert reset[0] == 2

    def test_token_expiration_calculation(self, temp_db):
        """Test that token expiration is calculated correctly."""
        config = PasswordResetConfig(token_expiration_hours=48)
        mgr = PasswordResetManager(temp_db, config)

        token, expires_at = mgr.generate_reset_token(user_id=1)

        expires_dt = datetime.fromisoformat(expires_at)
        now = datetime.now(timezone.utc)
        diff = (expires_dt - now).total_seconds() / 3600  # Hours

        # Should be approximately 48 hours (allow small variance)
        assert 47.9 < diff < 48.1

    def test_nonexistent_user(self, temp_db):
        """Test generating token for nonexistent user."""
        mgr = PasswordResetManager(temp_db)

        with pytest.raises(ValueError, match="not found"):
            mgr.generate_reset_token(user_id=999)


class TestResetTokenInfo:
    """Test ResetTokenInfo dataclass."""

    def test_token_info_structure(self):
        """Test ResetTokenInfo data structure."""
        info = ResetTokenInfo(
            valid=True,
            user_id=1,
            username='testuser',
            expires_at='2025-12-01T00:00:00',
            message='Token is valid'
        )

        assert info.valid is True
        assert info.user_id == 1
        assert info.username == 'testuser'
        assert info.message == 'Token is valid'


class TestPasswordResetConfig:
    """Test PasswordResetConfig dataclass."""

    def test_default_config(self):
        """Test default configuration."""
        config = PasswordResetConfig()
        assert config.token_expiration_hours == 24
        assert config.token_length == 32

    def test_custom_config(self):
        """Test custom configuration."""
        config = PasswordResetConfig(
            token_expiration_hours=12,
            token_length=64
        )
        assert config.token_expiration_hours == 12
        assert config.token_length == 64


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
