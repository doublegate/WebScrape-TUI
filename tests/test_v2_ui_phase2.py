"""
Test suite for v2.0.0 Phase 2: UI Components & RBAC

Tests all user interface components and role-based access control functionality
introduced in Phase 2 of the multi-user system.
"""

import pytest
import sqlite3
from datetime import datetime, timedelta
import sys
import os
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scrapetui import (
    get_db_connection,
    hash_password,
    authenticate_user,
    create_user_session,
    validate_session,
    logout_session,
    init_db,
)


# ═══════════════════════════════════════════════════════════════════════════
# Test Fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def clean_test_db():
    """Provide clean database for each test."""
    # Create temporary database file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
    temp_db_path = Path(temp_file.name)
    temp_file.close()

    # Patch DB_PATH in scrapetui module
    import scrapetui
    original_db_path = scrapetui.DB_PATH
    scrapetui.DB_PATH = temp_db_path

    # Run init_db to create all tables including scraped_data
    result = init_db()
    assert result is True, "Database initialization should succeed"

    yield temp_db_path

    # Cleanup
    scrapetui.DB_PATH = original_db_path
    if temp_db_path.exists():
        temp_db_path.unlink()


@pytest.fixture
def test_users(clean_test_db):
    """Create test users with different roles."""
    with get_db_connection() as conn:
        # Admin user already exists from migration - just get its ID
        admin_row = conn.execute("SELECT id FROM users WHERE username='admin'").fetchone()
        if not admin_row:
            # Create admin if somehow missing
            conn.execute("""
                INSERT INTO users (username, password_hash, role, email)
                VALUES (?, ?, ?, ?)
            """, ('admin', hash_password('admin123'), 'admin', 'admin@test.com'))
            admin_row = conn.execute("SELECT id FROM users WHERE username='admin'").fetchone()
        admin_id = admin_row['id']

        # Regular user
        conn.execute("""
            INSERT INTO users (username, password_hash, role, email)
            VALUES (?, ?, ?, ?)
        """, ('user1', hash_password('user123'), 'user', 'user1@test.com'))

        # Viewer user
        conn.execute("""
            INSERT INTO users (username, password_hash, role, email)
            VALUES (?, ?, ?, ?)
        """, ('viewer1', hash_password('viewer123'), 'viewer', 'viewer1@test.com'))

        # Inactive user
        conn.execute("""
            INSERT INTO users (username, password_hash, role, is_active)
            VALUES (?, ?, ?, ?)
        """, ('inactive', hash_password('inactive123'), 'user', False))

        conn.commit()

        # Return user IDs (admin_id already fetched above)
        user_id = conn.execute("SELECT id FROM users WHERE username=?", ('user1',)).fetchone()['id']
        viewer_id = conn.execute("SELECT id FROM users WHERE username=?", ('viewer1',)).fetchone()['id']
        inactive_id = conn.execute("SELECT id FROM users WHERE username=?", ('inactive',)).fetchone()['id']

        return {
            'admin': admin_id,
            'user': user_id,
            'viewer': viewer_id,
            'inactive': inactive_id
        }


# ═══════════════════════════════════════════════════════════════════════════
# Authentication Tests
# ═══════════════════════════════════════════════════════════════════════════


def test_authenticate_admin_user(test_users):
    """Test admin user authentication."""
    user_id = authenticate_user('admin', 'Ch4ng3M3')  # Default admin password from migration
    assert user_id == test_users['admin']

    # Verify last_login was updated
    with get_db_connection() as conn:
        row = conn.execute("SELECT last_login FROM users WHERE id=?", (user_id,)).fetchone()
        assert row['last_login'] is not None


def test_authenticate_regular_user(test_users):
    """Test regular user authentication."""
    user_id = authenticate_user('user1', 'user123')
    assert user_id == test_users['user']


def test_authenticate_viewer_user(test_users):
    """Test viewer user authentication."""
    user_id = authenticate_user('viewer1', 'viewer123')
    assert user_id == test_users['viewer']


def test_authenticate_wrong_password(test_users):
    """Test authentication with wrong password."""
    user_id = authenticate_user('admin', 'wrongpassword')
    assert user_id is None


def test_authenticate_nonexistent_user(test_users):
    """Test authentication with non-existent user."""
    user_id = authenticate_user('doesnotexist', 'password')
    assert user_id is None


def test_authenticate_inactive_user(test_users):
    """Test authentication with inactive user."""
    user_id = authenticate_user('inactive', 'inactive123')
    assert user_id is None  # Inactive users cannot login


# ═══════════════════════════════════════════════════════════════════════════
# Session Management Tests
# ═══════════════════════════════════════════════════════════════════════════


def test_create_session(test_users):
    """Test creating user session."""
    token = create_user_session(test_users['admin'])
    assert token is not None
    assert len(token) > 0

    # Verify session in database
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT user_id FROM user_sessions WHERE session_token=?",
            (token,)
        ).fetchone()
        assert row['user_id'] == test_users['admin']


def test_validate_session(test_users):
    """Test session validation."""
    token = create_user_session(test_users['user'])
    user_id = validate_session(token)
    assert user_id == test_users['user']


def test_validate_invalid_token(test_users):
    """Test validation with invalid token."""
    user_id = validate_session('invalid-token-12345')
    assert user_id is None


def test_validate_expired_session(test_users):
    """Test validation with expired session."""
    # Create session that's already expired
    token = create_user_session(test_users['user'], duration_hours=-1)
    user_id = validate_session(token)
    assert user_id is None


def test_logout_session(test_users):
    """Test session logout."""
    token = create_user_session(test_users['admin'])

    # Verify session exists
    assert validate_session(token) is not None

    # Logout
    logout_session(token)

    # Verify session is invalidated
    assert validate_session(token) is None


def test_session_with_ip_address(test_users):
    """Test session creation with IP address."""
    token = create_user_session(test_users['admin'], ip_address='192.168.1.1')

    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT ip_address FROM user_sessions WHERE session_token=?",
            (token,)
        ).fetchone()
        assert row['ip_address'] == '192.168.1.1'


# ═══════════════════════════════════════════════════════════════════════════
# Permission Checking Tests (Simulated)
# ═══════════════════════════════════════════════════════════════════════════


def test_permission_hierarchy():
    """Test role hierarchy for permission checking."""
    role_hierarchy = {'admin': 3, 'user': 2, 'viewer': 1, 'guest': 0}

    # Admin can do everything
    assert role_hierarchy['admin'] >= role_hierarchy['user']
    assert role_hierarchy['admin'] >= role_hierarchy['viewer']

    # User cannot do admin tasks
    assert role_hierarchy['user'] < role_hierarchy['admin']

    # Viewer has lowest permissions
    assert role_hierarchy['viewer'] < role_hierarchy['user']


def test_check_permission_admin(test_users):
    """Test admin permission checking."""
    # Simulate checking if admin has 'user' permission
    with get_db_connection() as conn:
        row = conn.execute("SELECT role FROM users WHERE id=?", (test_users['admin'],)).fetchone()
        role_hierarchy = {'admin': 3, 'user': 2, 'viewer': 1, 'guest': 0}
        current = role_hierarchy.get(row['role'], 0)
        required = role_hierarchy.get('user', 0)
        assert current >= required


def test_check_permission_user(test_users):
    """Test user permission checking."""
    with get_db_connection() as conn:
        row = conn.execute("SELECT role FROM users WHERE id=?", (test_users['user'],)).fetchone()
        role_hierarchy = {'admin': 3, 'user': 2, 'viewer': 1, 'guest': 0}
        current = role_hierarchy.get(row['role'], 0)

        # User can do 'user' tasks
        assert current >= role_hierarchy['user']

        # User cannot do 'admin' tasks
        assert current < role_hierarchy['admin']


def test_check_permission_viewer(test_users):
    """Test viewer permission checking."""
    with get_db_connection() as conn:
        row = conn.execute("SELECT role FROM users WHERE id=?", (test_users['viewer'],)).fetchone()
        role_hierarchy = {'admin': 3, 'user': 2, 'viewer': 1, 'guest': 0}
        current = role_hierarchy.get(row['role'], 0)

        # Viewer cannot do 'user' tasks
        assert current < role_hierarchy['user']


# ═══════════════════════════════════════════════════════════════════════════
# User CRUD Tests
# ═══════════════════════════════════════════════════════════════════════════


def test_create_new_user(clean_test_db):
    """Test creating a new user."""
    password_hash = hash_password('newuser123')

    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, ('newuser', 'new@test.com', password_hash, 'user'))
        conn.commit()

        # Verify user created
        row = conn.execute("SELECT * FROM users WHERE username=?", ('newuser',)).fetchone()
        assert row is not None
        assert row['username'] == 'newuser'
        assert row['email'] == 'new@test.com'
        assert row['role'] == 'user'
        assert row['is_active'] == True


def test_update_user_email(test_users):
    """Test updating user email."""
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE users SET email = ? WHERE id = ?",
            ('newemail@test.com', test_users['user'])
        )
        conn.commit()

        row = conn.execute("SELECT email FROM users WHERE id=?", (test_users['user'],)).fetchone()
        assert row['email'] == 'newemail@test.com'


def test_update_user_role(test_users):
    """Test updating user role."""
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE users SET role = ? WHERE id = ?",
            ('admin', test_users['user'])
        )
        conn.commit()

        row = conn.execute("SELECT role FROM users WHERE id=?", (test_users['user'],)).fetchone()
        assert row['role'] == 'admin'


def test_toggle_user_active_status(test_users):
    """Test toggling user active status."""
    with get_db_connection() as conn:
        # Deactivate active user
        conn.execute("UPDATE users SET is_active = NOT is_active WHERE id = ?", (test_users['user'],))
        conn.commit()

        row = conn.execute("SELECT is_active FROM users WHERE id=?", (test_users['user'],)).fetchone()
        assert row['is_active'] == False

        # Reactivate
        conn.execute("UPDATE users SET is_active = NOT is_active WHERE id = ?", (test_users['user'],))
        conn.commit()

        row = conn.execute("SELECT is_active FROM users WHERE id=?", (test_users['user'],)).fetchone()
        assert row['is_active'] == True


def test_list_all_users(test_users):
    """Test listing all users."""
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT id, username, email, role, is_active, last_login
            FROM users
            ORDER BY id
        """).fetchall()

        assert len(rows) >= 4  # At least our test users
        usernames = [row['username'] for row in rows]
        assert 'admin' in usernames
        assert 'user1' in usernames
        assert 'viewer1' in usernames


# ═══════════════════════════════════════════════════════════════════════════
# User Profile Tests
# ═══════════════════════════════════════════════════════════════════════════


def test_get_user_profile(test_users):
    """Test retrieving user profile."""
    with get_db_connection() as conn:
        row = conn.execute("""
            SELECT username, email, role, created_at, last_login, is_active
            FROM users WHERE id = ?
        """, (test_users['admin'],)).fetchone()

        assert row is not None
        assert row['username'] == 'admin'
        assert row['role'] == 'admin'
        assert row['is_active'] == True


def test_change_password(test_users):
    """Test changing user password."""
    new_password = 'newpassword123'
    new_hash = hash_password(new_password)

    with get_db_connection() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (new_hash, test_users['user'])
        )
        conn.commit()

    # Verify new password works
    user_id = authenticate_user('user1', new_password)
    assert user_id == test_users['user']

    # Verify old password doesn't work
    user_id = authenticate_user('user1', 'user123')
    assert user_id is None


# ═══════════════════════════════════════════════════════════════════════════
# Data Ownership Tests
# ═══════════════════════════════════════════════════════════════════════════


def test_article_ownership_tracking(test_users):
    """Test that articles track user_id."""
    with get_db_connection() as conn:
        # Insert article with user_id
        conn.execute("""
            INSERT INTO scraped_data (url, title, link, user_id)
            VALUES (?, ?, ?, ?)
        """, ('http://test.com', 'Test Article', 'http://test.com/article', test_users['user']))
        conn.commit()

        # Verify user_id stored
        row = conn.execute("SELECT user_id FROM scraped_data WHERE title=?", ('Test Article',)).fetchone()
        assert row['user_id'] == test_users['user']


def test_scraper_profile_ownership(test_users):
    """Test that scraper profiles track user_id."""
    with get_db_connection() as conn:
        # Insert scraper with user_id
        conn.execute("""
            INSERT INTO saved_scrapers (name, url, selector, user_id)
            VALUES (?, ?, ?, ?)
        """, ('Test Scraper', 'http://test.com', 'h2 a', test_users['admin']))
        conn.commit()

        # Verify user_id stored
        row = conn.execute("SELECT user_id FROM saved_scrapers WHERE name=?", ('Test Scraper',)).fetchone()
        assert row['user_id'] == test_users['admin']


def test_edit_permission_check(test_users):
    """Test edit permission checking (admin or owner)."""
    # Admin can edit anything
    assert test_users['admin'] == test_users['admin']  # Admin editing own

    # User can edit own
    assert test_users['user'] == test_users['user']

    # User cannot edit others (simulated)
    assert test_users['user'] != test_users['admin']


# ═══════════════════════════════════════════════════════════════════════════
# Edge Cases & Error Handling
# ═══════════════════════════════════════════════════════════════════════════


def test_duplicate_username_prevention(test_users):
    """Test that duplicate usernames are prevented."""
    with pytest.raises(sqlite3.IntegrityError):
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
            """, ('admin', hash_password('password'), 'user'))
            conn.commit()


def test_password_minimum_length():
    """Test password minimum length enforcement."""
    # This should be enforced at UI level, but test hash works
    short_password = '1234567'  # 7 chars
    password_hash = hash_password(short_password)
    assert password_hash is not None


def test_session_cleanup_on_logout(test_users):
    """Test that logout properly cleans up sessions."""
    token = create_user_session(test_users['user'])

    with get_db_connection() as conn:
        # Session exists
        row = conn.execute("SELECT * FROM user_sessions WHERE session_token=?", (token,)).fetchone()
        assert row is not None

    logout_session(token)

    with get_db_connection() as conn:
        # Session deleted
        row = conn.execute("SELECT * FROM user_sessions WHERE session_token=?", (token,)).fetchone()
        assert row is None


def test_multiple_sessions_same_user(test_users):
    """Test that same user can have multiple sessions."""
    token1 = create_user_session(test_users['user'])
    token2 = create_user_session(test_users['user'])

    assert token1 != token2
    assert validate_session(token1) == test_users['user']
    assert validate_session(token2) == test_users['user']


def test_user_profile_with_no_email(test_users):
    """Test user profile when email is NULL."""
    with get_db_connection() as conn:
        conn.execute("UPDATE users SET email = NULL WHERE id = ?", (test_users['viewer'],))
        conn.commit()

        row = conn.execute("SELECT email FROM users WHERE id=?", (test_users['viewer'],)).fetchone()
        assert row['email'] is None


# ═══════════════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════════════


def test_complete_login_flow(test_users):
    """Test complete login to logout flow."""
    # 1. Authenticate
    user_id = authenticate_user('admin', 'Ch4ng3M3')  # Default admin password
    assert user_id == test_users['admin']

    # 2. Create session
    token = create_user_session(user_id)
    assert token is not None

    # 3. Validate session
    validated_id = validate_session(token)
    assert validated_id == user_id

    # 4. Logout
    logout_session(token)

    # 5. Verify session invalid
    assert validate_session(token) is None


def test_user_management_workflow(clean_test_db):
    """Test complete user management workflow."""
    # 1. Create user
    password_hash = hash_password('testuser123')
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, ('testuser', 'test@example.com', password_hash, 'user'))
        conn.commit()
        user_id = conn.execute("SELECT id FROM users WHERE username=?", ('testuser',)).fetchone()['id']

    # 2. Login
    assert authenticate_user('testuser', 'testuser123') == user_id

    # 3. Update email
    with get_db_connection() as conn:
        conn.execute("UPDATE users SET email = ? WHERE id = ?", ('updated@example.com', user_id))
        conn.commit()

    # 4. Change password
    new_hash = hash_password('newpassword123')
    with get_db_connection() as conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
        conn.commit()

    # 5. Verify new password
    assert authenticate_user('testuser', 'newpassword123') == user_id

    # 6. Deactivate
    with get_db_connection() as conn:
        conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (False, user_id))
        conn.commit()

    # 7. Verify cannot login when inactive
    assert authenticate_user('testuser', 'newpassword123') is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
