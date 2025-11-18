"""
Unit tests for enhanced authentication module.

Tests integration of password policy, rate limiting, and audit logging
into authentication flows.
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, timezone

from scrapetui.core.auth_enhanced import (
    authenticate_user_enhanced,
    create_user_with_policy,
    change_password_with_policy,
    logout_user
)
from scrapetui.core.password_policy import PasswordPolicy
from scrapetui.core.rate_limit import get_rate_limiter
from scrapetui.core.audit import get_audit_logger, AuditEventType


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # Create all required tables
    conn = sqlite3.connect(path)

    # Users table
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            account_locked INTEGER DEFAULT 0,
            locked_until TEXT,
            failed_login_attempts INTEGER DEFAULT 0,
            last_failed_login TEXT,
            password_changed_at TEXT,
            force_password_change INTEGER DEFAULT 0,
            last_login TEXT,
            created_at TEXT
        )
    """)

    # Sessions table
    conn.execute("""
        CREATE TABLE user_sessions (
            id INTEGER PRIMARY KEY,
            session_token TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            created_at TEXT,
            expires_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Login attempts table
    conn.execute("""
        CREATE TABLE login_attempts (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            success INTEGER NOT NULL,
            ip_address TEXT,
            attempted_at TEXT NOT NULL
        )
    """)

    # Audit log table
    conn.execute("""
        CREATE TABLE audit_log (
            id INTEGER PRIMARY KEY,
            event_type TEXT NOT NULL,
            user_id INTEGER,
            username TEXT,
            ip_address TEXT,
            user_agent TEXT,
            event_data TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

    yield path

    os.unlink(path)


class TestAuthenticateUserEnhanced:
    """Test enhanced authentication function."""

    def test_successful_authentication(self, temp_db):
        """Test successful login creates session and logs audit event."""
        from scrapetui.core.auth import hash_password

        # Create test user
        conn = sqlite3.connect(temp_db)
        password_hash = hash_password("TestP@ssw0rd123")
        conn.execute("""
            INSERT INTO users (username, password_hash, is_active)
            VALUES (?, ?, 1)
        """, ("testuser", password_hash))
        conn.commit()
        conn.close()

        # Authenticate
        user_id, token, msg = authenticate_user_enhanced(
            "testuser",
            "TestP@ssw0rd123",
            ip_address="127.0.0.1",
            user_agent="TestAgent/1.0"
        )

        assert user_id is not None
        assert token is not None
        assert "successful" in msg.lower()

        # Verify session created
        conn = sqlite3.connect(temp_db)
        session = conn.execute(
            "SELECT * FROM user_sessions WHERE session_token = ?",
            (token,)
        ).fetchone()
        conn.close()

        assert session is not None

    def test_invalid_password(self, temp_db):
        """Test failed login with invalid password."""
        from scrapetui.core.auth import hash_password

        # Create test user
        conn = sqlite3.connect(temp_db)
        password_hash = hash_password("TestP@ssw0rd123")
        conn.execute("""
            INSERT INTO users (username, password_hash, is_active)
            VALUES (?, ?, 1)
        """, ("testuser", password_hash))
        conn.commit()
        conn.close()

        # Authenticate with wrong password
        user_id, token, msg = authenticate_user_enhanced(
            "testuser",
            "WrongPassword",
            ip_address="127.0.0.1"
        )

        assert user_id is None
        assert token is None
        assert "invalid" in msg.lower()

        # Verify failed attempt recorded
        conn = sqlite3.connect(temp_db)
        attempt = conn.execute(
            "SELECT * FROM login_attempts WHERE username = ? AND success = 0",
            ("testuser",)
        ).fetchone()
        conn.close()

        assert attempt is not None

    def test_nonexistent_user(self, temp_db):
        """Test login attempt for nonexistent user."""
        user_id, token, msg = authenticate_user_enhanced(
            "nonexistent",
            "AnyPassword",
            ip_address="127.0.0.1"
        )

        assert user_id is None
        assert token is None
        assert "invalid" in msg.lower()

    def test_locked_account(self, temp_db):
        """Test login blocked for locked account."""
        from scrapetui.core.auth import hash_password

        # Create locked user
        conn = sqlite3.connect(temp_db)
        password_hash = hash_password("TestP@ssw0rd123")
        conn.execute("""
            INSERT INTO users (username, password_hash, is_active, account_locked)
            VALUES (?, ?, 1, 1)
        """, ("testuser", password_hash))
        conn.commit()
        conn.close()

        # Authenticate
        user_id, token, msg = authenticate_user_enhanced(
            "testuser",
            "TestP@ssw0rd123",
            ip_address="127.0.0.1"
        )

        assert user_id is None
        assert token is None
        assert "locked" in msg.lower()

    def test_inactive_account(self, temp_db):
        """Test login blocked for inactive account."""
        from scrapetui.core.auth import hash_password

        # Create inactive user
        conn = sqlite3.connect(temp_db)
        password_hash = hash_password("TestP@ssw0rd123")
        conn.execute("""
            INSERT INTO users (username, password_hash, is_active)
            VALUES (?, ?, 0)
        """, ("testuser", password_hash))
        conn.commit()
        conn.close()

        # Authenticate
        user_id, token, msg = authenticate_user_enhanced(
            "testuser",
            "TestP@ssw0rd123",
            ip_address="127.0.0.1"
        )

        assert user_id is None
        assert token is None
        assert "inactive" in msg.lower()

    def test_rate_limit_exceeded(self, temp_db):
        """Test login blocked after rate limit exceeded."""
        from scrapetui.core.auth import hash_password
        from scrapetui.core.rate_limit import RateLimiter, RateLimitConfig

        # Create user
        conn = sqlite3.connect(temp_db)
        password_hash = hash_password("TestP@ssw0rd123")
        conn.execute("""
            INSERT INTO users (username, password_hash, is_active)
            VALUES (?, ?, 1)
        """, ("testuser", password_hash))
        conn.commit()
        conn.close()

        # Configure rate limiter with low threshold
        config = RateLimitConfig(max_attempts=3)
        limiter = RateLimiter(temp_db, config)

        # Exceed rate limit
        for _ in range(3):
            limiter.record_login_attempt("testuser", success=False)

        # Attempt login
        user_id, token, msg = authenticate_user_enhanced(
            "testuser",
            "TestP@ssw0rd123",
            ip_address="127.0.0.1"
        )

        assert user_id is None
        assert token is None
        assert "locked" in msg.lower() or "limit" in msg.lower()

    def test_audit_logging(self, temp_db):
        """Test that authentication events are logged."""
        from scrapetui.core.auth import hash_password

        # Create user
        conn = sqlite3.connect(temp_db)
        password_hash = hash_password("TestP@ssw0rd123")
        conn.execute("""
            INSERT INTO users (username, password_hash, is_active)
            VALUES (?, ?, 1)
        """, ("testuser", password_hash))
        conn.commit()
        conn.close()

        # Successful login
        authenticate_user_enhanced(
            "testuser",
            "TestP@ssw0rd123",
            ip_address="127.0.0.1",
            user_agent="TestAgent/1.0"
        )

        # Check audit log
        conn = sqlite3.connect(temp_db)
        audit = conn.execute(
            "SELECT * FROM audit_log WHERE event_type = ?",
            ("login_success",)
        ).fetchone()
        conn.close()

        assert audit is not None


class TestCreateUserWithPolicy:
    """Test user creation with password policy."""

    def test_create_user_valid_password(self, temp_db):
        """Test creating user with valid password."""
        user_id, msg = create_user_with_policy(
            "newuser",
            "Str0ng!P@ssw0rd",
            email="user@example.com",
            role="user"
        )

        assert user_id is not None
        assert "successful" in msg.lower()

        # Verify user created
        conn = sqlite3.connect(temp_db)
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            ("newuser",)
        ).fetchone()
        conn.close()

        assert user is not None

    def test_create_user_weak_password(self, temp_db):
        """Test creating user with weak password fails."""
        user_id, msg = create_user_with_policy(
            "newuser",
            "weak",
            email="user@example.com"
        )

        assert user_id is None
        assert "does not meet requirements" in msg.lower()

    def test_create_user_custom_policy(self, temp_db):
        """Test creating user with custom password policy."""
        policy = PasswordPolicy(
            min_length=8,
            require_special=False
        )

        user_id, msg = create_user_with_policy(
            "newuser",
            "Simple123",
            password_policy=policy
        )

        assert user_id is not None
        assert "successful" in msg.lower()

    def test_create_user_force_password_change(self, temp_db):
        """Test creating user with forced password change."""
        user_id, msg = create_user_with_policy(
            "newuser",
            "Str0ng!P@ssw0rd",
            force_password_change=True
        )

        assert user_id is not None

        # Verify force_password_change flag set
        conn = sqlite3.connect(temp_db)
        user = conn.execute(
            "SELECT force_password_change FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        conn.close()

        assert user[0] == 1

    def test_create_user_audit_log(self, temp_db):
        """Test user creation is logged."""
        create_user_with_policy(
            "newuser",
            "Str0ng!P@ssw0rd",
            created_by=1
        )

        # Check audit log
        conn = sqlite3.connect(temp_db)
        audit = conn.execute(
            "SELECT * FROM audit_log WHERE event_type = ?",
            ("account_created",)
        ).fetchone()
        conn.close()

        assert audit is not None


class TestChangePasswordWithPolicy:
    """Test password change with policy validation."""

    def test_change_password_success(self, temp_db):
        """Test successful password change."""
        from scrapetui.core.auth import hash_password

        # Create user
        conn = sqlite3.connect(temp_db)
        old_hash = hash_password("OldP@ss123456")
        conn.execute("""
            INSERT INTO users (id, username, password_hash)
            VALUES (1, 'testuser', ?)
        """, (old_hash,))
        conn.commit()
        conn.close()

        # Change password
        success, msg = change_password_with_policy(
            user_id=1,
            old_password="OldP@ss123456",
            new_password="N3wP@ssw0rd!!"
        )

        assert success is True
        assert "successful" in msg.lower()

        # Verify password changed
        from scrapetui.core.auth import verify_password
        conn = sqlite3.connect(temp_db)
        new_hash = conn.execute(
            "SELECT password_hash FROM users WHERE id = 1"
        ).fetchone()[0]
        conn.close()

        assert verify_password("N3wP@ssw0rd!!", new_hash)

    def test_change_password_wrong_old(self, temp_db):
        """Test password change fails with wrong old password."""
        from scrapetui.core.auth import hash_password

        # Create user
        conn = sqlite3.connect(temp_db)
        old_hash = hash_password("OldP@ss123456")
        conn.execute("""
            INSERT INTO users (id, username, password_hash)
            VALUES (1, 'testuser', ?)
        """, (old_hash,))
        conn.commit()
        conn.close()

        # Change password with wrong old password
        success, msg = change_password_with_policy(
            user_id=1,
            old_password="WrongPassword",
            new_password="N3wP@ssw0rd!!"
        )

        assert success is False
        assert "incorrect" in msg.lower()

    def test_change_password_weak_new(self, temp_db):
        """Test password change fails with weak new password."""
        from scrapetui.core.auth import hash_password

        # Create user
        conn = sqlite3.connect(temp_db)
        old_hash = hash_password("OldP@ss123456")
        conn.execute("""
            INSERT INTO users (id, username, password_hash)
            VALUES (1, 'testuser', ?)
        """, (old_hash,))
        conn.commit()
        conn.close()

        # Change to weak password
        success, msg = change_password_with_policy(
            user_id=1,
            old_password="OldP@ss123456",
            new_password="weak"
        )

        assert success is False
        assert "does not meet requirements" in msg.lower()

    def test_change_password_invalidates_sessions(self, temp_db):
        """Test password change invalidates all sessions."""
        from scrapetui.core.auth import hash_password

        # Create user with session
        conn = sqlite3.connect(temp_db)
        old_hash = hash_password("OldP@ss123456")
        conn.execute("""
            INSERT INTO users (id, username, password_hash)
            VALUES (1, 'testuser', ?)
        """, (old_hash,))
        conn.execute("""
            INSERT INTO user_sessions (session_token, user_id, created_at, expires_at)
            VALUES ('token123', 1, '2025-11-18T00:00:00', '2025-11-19T00:00:00')
        """)
        conn.commit()
        conn.close()

        # Change password
        change_password_with_policy(
            user_id=1,
            old_password="OldP@ss123456",
            new_password="N3wP@ssw0rd!!"
        )

        # Verify sessions deleted
        conn = sqlite3.connect(temp_db)
        sessions = conn.execute(
            "SELECT * FROM user_sessions WHERE user_id = 1"
        ).fetchall()
        conn.close()

        assert len(sessions) == 0


class TestLogoutUser:
    """Test user logout function."""

    def test_logout_success(self, temp_db):
        """Test successful logout."""
        # Create session
        conn = sqlite3.connect(temp_db)
        conn.execute("""
            INSERT INTO user_sessions (session_token, user_id, created_at, expires_at)
            VALUES ('token123', 1, '2025-11-18T00:00:00', '2025-11-19T00:00:00')
        """)
        conn.commit()
        conn.close()

        # Logout
        result = logout_user("token123", user_id=1, username="testuser")

        assert result is True

        # Verify session deleted
        conn = sqlite3.connect(temp_db)
        session = conn.execute(
            "SELECT * FROM user_sessions WHERE session_token = 'token123'"
        ).fetchone()
        conn.close()

        assert session is None

    def test_logout_audit_log(self, temp_db):
        """Test logout is logged to audit log."""
        # Create session
        conn = sqlite3.connect(temp_db)
        conn.execute("""
            INSERT INTO user_sessions (session_token, user_id, created_at, expires_at)
            VALUES ('token123', 1, '2025-11-18T00:00:00', '2025-11-19T00:00:00')
        """)
        conn.commit()
        conn.close()

        # Logout
        logout_user("token123", user_id=1, username="testuser")

        # Check audit log
        conn = sqlite3.connect(temp_db)
        audit = conn.execute(
            "SELECT * FROM audit_log WHERE event_type = ?",
            ("logout",)
        ).fetchone()
        conn.close()

        assert audit is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
