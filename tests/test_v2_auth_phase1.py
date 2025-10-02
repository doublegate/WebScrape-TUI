"""
Phase 1 Tests: v2.0.0 Authentication & User Management

This test suite covers Phase 1 of the v2.0.0 multi-user foundation:
- Password hashing and verification
- Session token generation
- User authentication
- Session management
- Admin user initialization
- Database migration from v1.x to v2.0

Total Tests: 20 tests covering all Phase 1 functionality
"""

import pytest
import sqlite3
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch

# Import functions from scrapetui
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapetui import (
    hash_password,
    verify_password,
    create_session_token,
    create_user_session,
    validate_session,
    logout_session,
    authenticate_user,
    initialize_admin_user,
    migrate_database_to_v2,
    get_db_connection,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create temporary database file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
    temp_db_path = Path(temp_file.name)
    temp_file.close()

    # Patch DB_PATH in scrapetui module
    import scrapetui
    original_db_path = scrapetui.DB_PATH
    scrapetui.DB_PATH = temp_db_path

    yield temp_db_path

    # Cleanup
    scrapetui.DB_PATH = original_db_path
    if temp_db_path.exists():
        temp_db_path.unlink()


@pytest.fixture
def v2_db(temp_db):
    """Create a v2.0 database with schema."""
    # Run migration to create v2.0 schema
    result = migrate_database_to_v2()
    assert result is True, "Migration should succeed"
    return temp_db


@pytest.fixture
def v1_db(temp_db):
    """Create a v1.x database with legacy schema."""
    with get_db_connection() as conn:
        # Create v1.x schema (no users, user_sessions, schema_version tables)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scraped_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                summary TEXT,
                sentiment TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_scrapers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                url TEXT NOT NULL,
                selector TEXT NOT NULL,
                default_limit INTEGER DEFAULT 0,
                default_tags_csv TEXT,
                description TEXT,
                is_preinstalled INTEGER DEFAULT 0
            )
        """)
        # Add some test data
        conn.execute("""
            INSERT INTO scraped_data (url, title, link)
            VALUES ('https://example.com', 'Test Article', 'https://example.com/article')
        """)
        conn.execute("""
            INSERT INTO saved_scrapers (name, url, selector)
            VALUES ('Test Scraper', 'https://test.com', 'h1')
        """)
        conn.commit()
    return temp_db


# --- Password Hashing Tests ---

def test_hash_password():
    """Test password hashing with bcrypt."""
    password = "Ch4ng3M3"
    hashed = hash_password(password)

    # Verify hash format
    assert hashed is not None
    assert len(hashed) > 0
    assert hashed.startswith('$2b$')  # bcrypt format
    assert hashed != password  # Should not be plaintext


def test_hash_password_uniqueness():
    """Test that hashing same password twice produces different hashes."""
    password = "TestPassword123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    # Different salts should produce different hashes
    assert hash1 != hash2


def test_verify_password_correct():
    """Test password verification with correct password."""
    password = "Ch4ng3M3"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    """Test password verification with incorrect password."""
    password = "Ch4ng3M3"
    hashed = hash_password(password)

    assert verify_password("WrongPassword", hashed) is False


def test_verify_password_empty():
    """Test password verification with empty password."""
    hashed = hash_password("ValidPassword")

    assert verify_password("", hashed) is False


# --- Session Token Tests ---

def test_create_session_token():
    """Test session token generation."""
    token = create_session_token()

    assert token is not None
    assert len(token) >= 32  # 32 bytes base64 encoded
    assert isinstance(token, str)


def test_session_token_uniqueness():
    """Test that session tokens are unique."""
    token1 = create_session_token()
    token2 = create_session_token()

    assert token1 != token2


# --- User Authentication Tests ---

def test_authenticate_user_valid(v2_db):
    """Test user authentication with valid credentials."""
    # Admin user should be created automatically
    user_id = authenticate_user('admin', 'Ch4ng3M3')

    assert user_id is not None
    assert user_id == 1  # First user


def test_authenticate_user_invalid_password(v2_db):
    """Test user authentication with invalid password."""
    user_id = authenticate_user('admin', 'WrongPassword')

    assert user_id is None


def test_authenticate_user_nonexistent(v2_db):
    """Test user authentication with non-existent user."""
    user_id = authenticate_user('nonexistent', 'password')

    assert user_id is None


def test_authenticate_user_updates_last_login(v2_db):
    """Test that authentication updates last_login timestamp."""
    # First login
    user_id = authenticate_user('admin', 'Ch4ng3M3')
    assert user_id is not None

    # Check last_login was updated
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT last_login FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        assert row['last_login'] is not None


# --- Session Management Tests ---

def test_create_user_session(v2_db):
    """Test creating a user session."""
    # Create admin user first
    user_id = authenticate_user('admin', 'Ch4ng3M3')

    # Create session
    token = create_user_session(user_id)

    assert token is not None
    assert len(token) >= 32


def test_validate_session_valid(v2_db):
    """Test validating a valid session."""
    # Create admin user and session
    user_id = authenticate_user('admin', 'Ch4ng3M3')
    token = create_user_session(user_id)

    # Validate session
    validated_user_id = validate_session(token)

    assert validated_user_id == user_id


def test_validate_session_invalid_token(v2_db):
    """Test validating an invalid session token."""
    validated_user_id = validate_session("invalid_token_123")

    assert validated_user_id is None


def test_validate_session_empty_token(v2_db):
    """Test validating empty session token."""
    validated_user_id = validate_session("")

    assert validated_user_id is None


def test_validate_session_expired(v2_db):
    """Test validating an expired session."""
    # Create admin user
    user_id = authenticate_user('admin', 'Ch4ng3M3')

    # Create session with very short duration
    with get_db_connection() as conn:
        token = create_session_token()
        # Set expiration to 1 second ago (use ISO format for Python 3.12+ compatibility)
        expires_at = (datetime.now() - timedelta(seconds=1)).isoformat()
        conn.execute("""
            INSERT INTO user_sessions (user_id, session_token, expires_at)
            VALUES (?, ?, ?)
        """, (user_id, token, expires_at))
        conn.commit()

    # Validate should fail
    validated_user_id = validate_session(token)
    assert validated_user_id is None


def test_logout_session(v2_db):
    """Test logging out a session."""
    # Create admin user and session
    user_id = authenticate_user('admin', 'Ch4ng3M3')
    token = create_user_session(user_id)

    # Verify session is valid
    assert validate_session(token) == user_id

    # Logout
    logout_session(token)

    # Verify session is no longer valid
    assert validate_session(token) is None


# --- Admin User Initialization Tests ---

def test_initialize_admin_user(v2_db):
    """Test admin user initialization on first run."""
    # Admin user should already be created by migration
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = 'admin'"
        ).fetchone()

        assert row is not None
        assert row['username'] == 'admin'
        assert row['email'] == 'admin@localhost'
        assert row['role'] == 'admin'
        assert row['is_active'] == 1


def test_initialize_admin_user_idempotent(v2_db):
    """Test that initializing admin user multiple times doesn't create duplicates."""
    # Run initialization again
    initialize_admin_user()

    # Should still only have one admin user
    with get_db_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) as cnt FROM users WHERE username = 'admin'"
        ).fetchone()['cnt']

        assert count == 1


# --- Database Migration Tests ---

def test_migrate_v1_to_v2_schema_creation(v1_db):
    """Test that v1 to v2 migration creates new tables."""
    # Run migration
    result = migrate_database_to_v2()
    assert result is True

    # Verify new tables exist
    with get_db_connection() as conn:
        # Check users table
        users = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        assert users is not None

        # Check user_sessions table
        sessions = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user_sessions'"
        ).fetchone()
        assert sessions is not None

        # Check schema_version table
        version = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        ).fetchone()
        assert version is not None


def test_migrate_v1_to_v2_data_preservation(v1_db):
    """Test that v1 to v2 migration preserves existing data."""
    # Run migration
    result = migrate_database_to_v2()
    assert result is True

    # Verify old data still exists
    with get_db_connection() as conn:
        # Check scraped_data
        articles = conn.execute(
            "SELECT COUNT(*) as cnt FROM scraped_data"
        ).fetchone()['cnt']
        assert articles == 1

        # Check saved_scrapers
        scrapers = conn.execute(
            "SELECT COUNT(*) as cnt FROM saved_scrapers"
        ).fetchone()['cnt']
        assert scrapers == 1


def test_migrate_v1_to_v2_user_id_assignment(v1_db):
    """Test that v1 to v2 migration assigns user_id to existing data."""
    # Run migration
    result = migrate_database_to_v2()
    assert result is True

    # Verify user_id columns were added and populated
    with get_db_connection() as conn:
        # Get admin user ID
        admin = conn.execute(
            "SELECT id FROM users WHERE username = 'admin'"
        ).fetchone()
        admin_id = admin['id']

        # Check scraped_data has user_id
        article = conn.execute(
            "SELECT user_id FROM scraped_data LIMIT 1"
        ).fetchone()
        assert article['user_id'] == admin_id

        # Check saved_scrapers has user_id
        scraper = conn.execute(
            "SELECT user_id FROM saved_scrapers LIMIT 1"
        ).fetchone()
        assert scraper['user_id'] == admin_id


def test_migrate_v1_to_v2_creates_backup(v1_db):
    """Test that migration creates a backup file."""
    import scrapetui
    backup_path = scrapetui.DB_PATH.with_suffix('.db.backup-v1')

    # Ensure no existing backup
    if backup_path.exists():
        backup_path.unlink()

    # Run migration
    result = migrate_database_to_v2()
    assert result is True

    # Verify backup was created
    assert backup_path.exists()

    # Cleanup
    if backup_path.exists():
        backup_path.unlink()


def test_migrate_v2_to_v2_idempotent(v2_db):
    """Test that migrating v2 to v2 is idempotent (no-op)."""
    # Run migration on already-migrated database
    result = migrate_database_to_v2()
    assert result is True

    # Verify schema version is still 2.0.0
    with get_db_connection() as conn:
        version = conn.execute(
            "SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1"
        ).fetchone()['version']
        assert version == '2.0.0'


def test_migrate_records_version(v1_db):
    """Test that migration records schema version in database."""
    # Run migration
    result = migrate_database_to_v2()
    assert result is True

    # Verify version was recorded
    with get_db_connection() as conn:
        version_row = conn.execute(
            "SELECT version, description FROM schema_version WHERE version = '2.0.0'"
        ).fetchone()

        assert version_row is not None
        assert version_row['version'] == '2.0.0'
        assert 'Multi-user' in version_row['description']


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
