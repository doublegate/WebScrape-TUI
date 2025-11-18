"""
Unit tests for v2.2.0 database migration.

Tests migration from v2.1.0 to v2.2.0 schema.
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, timezone

from scrapetui.database.migrations.v2_2_0 import (
    get_current_schema_version,
    check_prerequisites,
    add_login_attempts_table,
    add_password_reset_table,
    add_audit_log_table,
    add_user_security_columns,
    add_user_quota_columns,
    set_admin_unlimited_quotas,
    initialize_password_timestamps,
    migrate,
    rollback
)


@pytest.fixture
def v2_1_0_database():
    """Create a v2.1.0 database for testing migration."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    conn = sqlite3.connect(path)

    # Create v2.1.0 schema
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            last_login TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE user_sessions (
            id INTEGER PRIMARY KEY,
            session_token TEXT UNIQUE,
            user_id INTEGER,
            created_at TEXT,
            expires_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE scraped_data (
            id INTEGER PRIMARY KEY,
            title TEXT,
            content TEXT,
            url TEXT,
            user_id INTEGER,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE saved_scrapers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            url_pattern TEXT,
            user_id INTEGER,
            is_shared INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE schema_version (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
    """)

    # Insert v2.1.0 version
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT INTO schema_version (version, applied_at)
        VALUES ('2.1.0', ?)
    """, (now,))

    # Insert test users
    conn.execute("""
        INSERT INTO users (id, username, password_hash, role, is_active, created_at)
        VALUES (1, 'admin', 'hash123', 'admin', 1, ?)
    """, (now,))

    conn.execute("""
        INSERT INTO users (id, username, password_hash, role, is_active, created_at)
        VALUES (2, 'testuser', 'hash456', 'user', 1, ?)
    """, (now,))

    conn.commit()
    conn.close()

    yield path

    if os.path.exists(path):
        os.unlink(path)


class TestSchemaVersion:
    """Test schema version utilities."""

    def test_get_current_schema_version(self, v2_1_0_database):
        """Test getting current schema version."""
        conn = sqlite3.connect(v2_1_0_database)
        version = get_current_schema_version(conn)
        conn.close()

        assert version == "2.1.0"

    def test_get_version_no_table(self):
        """Test getting version when table doesn't exist."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        conn = sqlite3.connect(path)
        version = get_current_schema_version(conn)
        conn.close()

        os.unlink(path)

        assert version is None


class TestPrerequisites:
    """Test migration prerequisites checking."""

    def test_check_prerequisites_success(self, v2_1_0_database):
        """Test prerequisites check passes for v2.1.0 database."""
        conn = sqlite3.connect(v2_1_0_database)
        can_migrate, message = check_prerequisites(conn)
        conn.close()

        assert can_migrate is True
        assert "Ready to migrate" in message

    def test_check_prerequisites_already_migrated(self, v2_1_0_database):
        """Test prerequisites fail if already at v2.2.0."""
        conn = sqlite3.connect(v2_1_0_database)

        # Update to v2.2.0
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("""
            INSERT INTO schema_version (version, applied_at)
            VALUES ('2.2.0', ?)
        """, (now,))
        conn.commit()

        can_migrate, message = check_prerequisites(conn)
        conn.close()

        assert can_migrate is False
        assert "already at version 2.2.0" in message


class TestTableCreation:
    """Test new table creation."""

    def test_add_login_attempts_table(self, v2_1_0_database):
        """Test creating login_attempts table."""
        conn = sqlite3.connect(v2_1_0_database)
        add_login_attempts_table(conn)
        conn.commit()

        # Verify table exists
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='login_attempts'
        """)
        result = cursor.fetchone()
        conn.close()

        assert result is not None

    def test_add_password_reset_table(self, v2_1_0_database):
        """Test creating password_reset_tokens table."""
        conn = sqlite3.connect(v2_1_0_database)
        add_password_reset_table(conn)
        conn.commit()

        # Verify table exists
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='password_reset_tokens'
        """)
        result = cursor.fetchone()
        conn.close()

        assert result is not None

    def test_add_audit_log_table(self, v2_1_0_database):
        """Test creating audit_log table."""
        conn = sqlite3.connect(v2_1_0_database)
        add_audit_log_table(conn)
        conn.commit()

        # Verify table exists
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='audit_log'
        """)
        result = cursor.fetchone()
        conn.close()

        assert result is not None


class TestColumnAddition:
    """Test adding new columns to users table."""

    def test_add_user_security_columns(self, v2_1_0_database):
        """Test adding security columns."""
        conn = sqlite3.connect(v2_1_0_database)
        add_user_security_columns(conn)
        conn.commit()

        # Verify columns exist
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        assert "account_locked" in columns
        assert "locked_until" in columns
        assert "failed_login_attempts" in columns
        assert "last_failed_login" in columns
        assert "password_changed_at" in columns
        assert "force_password_change" in columns

    def test_add_user_quota_columns(self, v2_1_0_database):
        """Test adding quota columns."""
        conn = sqlite3.connect(v2_1_0_database)
        add_user_quota_columns(conn)
        conn.commit()

        # Verify columns exist
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        assert "article_quota" in columns
        assert "scraper_quota" in columns
        assert "quota_reset_at" in columns


class TestDataMigration:
    """Test data migration functions."""

    def test_set_admin_unlimited_quotas(self, v2_1_0_database):
        """Test setting unlimited quotas for admins."""
        conn = sqlite3.connect(v2_1_0_database)

        # Add quota columns first
        add_user_quota_columns(conn)
        conn.commit()

        # Set admin quotas
        set_admin_unlimited_quotas(conn)
        conn.commit()

        # Verify admin has unlimited quotas
        cursor = conn.execute("""
            SELECT article_quota, scraper_quota
            FROM users
            WHERE role = 'admin'
        """)
        result = cursor.fetchone()
        conn.close()

        assert result[0] == -1  # article_quota
        assert result[1] == -1  # scraper_quota

    def test_initialize_password_timestamps(self, v2_1_0_database):
        """Test initializing password timestamps."""
        conn = sqlite3.connect(v2_1_0_database)

        # Add security columns first
        add_user_security_columns(conn)
        conn.commit()

        # Initialize timestamps
        initialize_password_timestamps(conn)
        conn.commit()

        # Verify all users have password_changed_at
        cursor = conn.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE password_changed_at IS NOT NULL
        """)
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2  # Both test users


class TestFullMigration:
    """Test complete migration process."""

    def test_migrate_success(self, v2_1_0_database):
        """Test successful migration from v2.1.0 to v2.2.0."""
        success = migrate(v2_1_0_database, skip_backup=True)

        assert success is True

        # Verify migration completed
        conn = sqlite3.connect(v2_1_0_database)

        # Check schema version
        version = get_current_schema_version(conn)
        assert version == "2.2.0"

        # Check new tables exist
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN (
                'login_attempts', 'password_reset_tokens', 'audit_log'
            )
        """)
        tables = {row[0] for row in cursor.fetchall()}
        assert len(tables) == 3

        # Check new columns exist
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = {row[1] for row in cursor.fetchall()}

        expected_columns = {
            'account_locked', 'locked_until', 'failed_login_attempts',
            'last_failed_login', 'password_changed_at', 'force_password_change',
            'article_quota', 'scraper_quota', 'quota_reset_at'
        }

        for col in expected_columns:
            assert col in columns

        conn.close()

    def test_migrate_already_migrated(self, v2_1_0_database):
        """Test migration fails if already at v2.2.0."""
        # First migration
        migrate(v2_1_0_database, skip_backup=True)

        # Second migration should fail
        success = migrate(v2_1_0_database, skip_backup=True)

        assert success is False


class TestRollback:
    """Test migration rollback."""

    def test_rollback_drops_tables(self, v2_1_0_database):
        """Test rollback removes new tables."""
        # Migrate first
        migrate(v2_1_0_database, skip_backup=True)

        # Rollback
        success = rollback(v2_1_0_database)

        assert success is True

        # Verify new tables removed
        conn = sqlite3.connect(v2_1_0_database)
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN (
                'login_attempts', 'password_reset_tokens', 'audit_log'
            )
        """)
        tables = cursor.fetchall()
        conn.close()

        assert len(tables) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
