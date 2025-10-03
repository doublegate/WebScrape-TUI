"""Unit tests for database module."""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import patch

from scrapetui.database.schema import (
    get_schema,
    get_schema_v2_0_0,
    get_indexes,
    get_builtin_data,
    get_table_names,
    SCHEMA_VERSION
)
from scrapetui.database.migrations import (
    get_current_version,
    migrate_v1_to_v2_0_0,
    run_migrations,
    verify_schema,
    create_backup
)
from scrapetui.database.queries import (
    QueryBuilder,
    build_insert,
    build_update,
    build_delete
)


class TestSchema:
    """Test database schema functions."""

    def test_schema_version(self):
        """Test schema version constant."""
        assert SCHEMA_VERSION == "2.0.0"

    def test_get_schema_v2_0_0(self):
        """Test v2.0.0 schema generation."""
        schema = get_schema_v2_0_0()
        assert "CREATE TABLE" in schema
        assert "users" in schema
        assert "scraped_data" in schema
        assert "schema_version" in schema

    def test_get_indexes(self):
        """Test index creation SQL."""
        indexes = get_indexes()
        assert "CREATE INDEX" in indexes or "CREATE UNIQUE INDEX" in indexes
        assert "idx_users_username" in indexes
        assert "idx_scraped_data_user_id" in indexes

    def test_get_builtin_data(self):
        """Test built-in data generation."""
        data = get_builtin_data()
        assert "INSERT" in data
        assert "admin" in data
        assert "TechCrunch" in data

    def test_get_complete_schema(self):
        """Test complete schema includes all parts."""
        schema = get_schema()
        assert "CREATE TABLE" in schema
        assert "CREATE INDEX" in schema
        assert "INSERT" in schema

    def test_get_table_names(self):
        """Test table name listing."""
        tables = get_table_names()
        assert isinstance(tables, list)
        assert 'users' in tables
        assert 'scraped_data' in tables
        assert 'schema_version' in tables
        assert 'token_blacklist' in tables  # v2.1.0 API tables
        assert 'refresh_tokens' in tables   # v2.1.0 API tables
        assert len(tables) == 21  # Total tables in schema (v2.1.0)


class TestMigrations:
    """Test database migrations."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_path = Path(temp_file.name)
        temp_file.close()

        yield temp_path

        if temp_path.exists():
            temp_path.unlink()

    def test_get_current_version_v2_0_0(self, temp_db):
        """Test version detection for v2.0.0 database."""
        conn = sqlite3.connect(str(temp_db))
        conn.executescript(get_schema())
        conn.commit()

        version = get_current_version(conn)
        assert version == '2.0.0'

        conn.close()

    def test_get_current_version_v1(self, temp_db):
        """Test version detection for v1.x database."""
        conn = sqlite3.connect(str(temp_db))

        # Create v1.x database (no schema_version table)
        conn.execute("""
            CREATE TABLE scraped_data (
                id INTEGER PRIMARY KEY,
                url TEXT,
                title TEXT,
                content TEXT,
                link TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()

        version = get_current_version(conn)
        assert version is None

        conn.close()

    def test_migrate_v1_to_v2_0_0(self, temp_db):
        """Test migration from v1.x to v2.0.0."""
        conn = sqlite3.connect(str(temp_db))
        conn.row_factory = sqlite3.Row

        # Create v1.x database
        conn.execute("""
            CREATE TABLE scraped_data (
                id INTEGER PRIMARY KEY,
                url TEXT,
                title TEXT,
                content TEXT,
                link TEXT,
                timestamp TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE tags (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE
            )
        """)
        conn.execute("""
            CREATE TABLE saved_scrapers (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                url TEXT,
                selector TEXT,
                is_preinstalled INTEGER DEFAULT 0
            )
        """)
        conn.commit()

        # Run migration
        success = migrate_v1_to_v2_0_0(conn)
        assert success is True

        # Verify users table exists
        cursor = conn.execute("SELECT * FROM users WHERE id = 1")
        admin = cursor.fetchone()
        assert admin is not None
        assert admin['username'] == 'admin'
        assert admin['role'] == 'admin'

        # Verify user_id column added to scraped_data
        cursor = conn.execute("PRAGMA table_info(scraped_data)")
        columns = {row[1] for row in cursor}
        assert 'user_id' in columns

        # Verify schema version recorded
        version = get_current_version(conn)
        assert version == '2.0.0'

        conn.close()

    def test_run_migrations_from_v1(self, temp_db):
        """Test run_migrations on v1.x database."""
        conn = sqlite3.connect(str(temp_db))
        conn.row_factory = sqlite3.Row

        # Create v1.x database (minimal schema that existed in v1.x)
        conn.execute("""
            CREATE TABLE scraped_data (
                id INTEGER PRIMARY KEY,
                url TEXT,
                title TEXT,
                link TEXT,
                timestamp TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE tags (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE
            )
        """)
        conn.execute("""
            CREATE TABLE article_tags (
                article_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (article_id, tag_id)
            )
        """)
        conn.execute("""
            CREATE TABLE saved_scrapers (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                url TEXT,
                selector TEXT,
                default_limit INTEGER DEFAULT 0,
                is_preinstalled INTEGER DEFAULT 0
            )
        """)
        conn.commit()

        # Run migrations
        success = run_migrations(conn)
        assert success is True

        # Verify migration complete
        version = get_current_version(conn)
        assert version == '2.0.0'

        conn.close()

    def test_verify_schema(self, temp_db):
        """Test schema verification."""
        conn = sqlite3.connect(str(temp_db))
        conn.executescript(get_schema())
        conn.commit()

        # Verify schema
        is_valid = verify_schema(conn)
        assert is_valid is True

        conn.close()

    def test_verify_schema_missing_tables(self, temp_db):
        """Test schema verification with missing tables."""
        conn = sqlite3.connect(str(temp_db))

        # Create incomplete schema
        conn.execute("""
            CREATE TABLE users (id INTEGER PRIMARY KEY)
        """)
        conn.commit()

        # Verify schema should fail
        is_valid = verify_schema(conn)
        assert is_valid is False

        conn.close()

    def test_create_backup(self, temp_db):
        """Test database backup creation."""
        # Create a database file
        conn = sqlite3.connect(str(temp_db))
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.commit()
        conn.close()

        # Create backup
        backup_path = create_backup(temp_db, "test")

        # Verify backup exists
        assert backup_path.exists()
        assert "test" in str(backup_path)

        # Cleanup backup
        if backup_path.exists():
            backup_path.unlink()


class TestQueryBuilder:
    """Test query builder utilities."""

    def test_simple_select(self):
        """Test simple SELECT query."""
        builder = QueryBuilder('users')
        query, params = builder.select('id', 'username').build()

        assert 'SELECT id, username FROM users' in query
        assert params == []

    def test_select_with_where(self):
        """Test SELECT with WHERE clause."""
        builder = QueryBuilder('users')
        query, params = builder.select('*').where('role = ?', 'admin').build()

        assert 'SELECT * FROM users' in query
        assert 'WHERE role = ?' in query
        assert params == ['admin']

    def test_select_with_multiple_where(self):
        """Test SELECT with multiple WHERE conditions."""
        builder = QueryBuilder('users')
        query, params = (
            builder
            .select('*')
            .where('role = ?', 'admin')
            .where('is_active = ?', 1)
            .build()
        )

        assert 'WHERE role = ? AND is_active = ?' in query
        assert params == ['admin', 1]

    def test_select_with_join(self):
        """Test SELECT with JOIN."""
        builder = QueryBuilder('scraped_data')
        query, params = (
            builder
            .select('scraped_data.id', 'users.username')
            .join('users', 'users.id = scraped_data.user_id')
            .where('scraped_data.id = ?', 123)
            .build()
        )

        assert 'JOIN users ON users.id = scraped_data.user_id' in query
        assert 'WHERE scraped_data.id = ?' in query
        assert params == [123]

    def test_select_with_left_join(self):
        """Test SELECT with LEFT JOIN."""
        builder = QueryBuilder('articles')
        query, params = (
            builder
            .left_join('tags', 'tags.article_id = articles.id')
            .build()
        )

        assert 'LEFT JOIN tags ON tags.article_id = articles.id' in query

    def test_select_with_order_by(self):
        """Test SELECT with ORDER BY."""
        builder = QueryBuilder('articles')
        query, params = (
            builder
            .order_by('timestamp', 'DESC')
            .build()
        )

        assert 'ORDER BY timestamp DESC' in query

    def test_select_with_limit_offset(self):
        """Test SELECT with LIMIT and OFFSET."""
        builder = QueryBuilder('articles')
        query, params = (
            builder
            .limit(50)
            .offset(100)
            .build()
        )

        assert 'LIMIT 50' in query
        assert 'OFFSET 100' in query

    def test_build_insert(self):
        """Test INSERT query builder."""
        data = {'username': 'testuser', 'email': 'test@example.com', 'role': 'user'}
        query, params = build_insert('users', data)

        assert 'INSERT INTO users' in query
        assert 'username, email, role' in query
        assert '?, ?, ?' in query
        assert params == ['testuser', 'test@example.com', 'user']

    def test_build_update(self):
        """Test UPDATE query builder."""
        data = {'email': 'newemail@example.com'}
        query, params = build_update('users', data, 'id = ?', [123])

        assert 'UPDATE users SET email = ?' in query
        assert 'WHERE id = ?' in query
        assert params == ['newemail@example.com', 123]

    def test_build_delete(self):
        """Test DELETE query builder."""
        query, params = build_delete('articles', 'id = ?', [456])

        assert 'DELETE FROM articles WHERE id = ?' in query
        assert params == [456]


class TestDatabaseIntegration:
    """Integration tests for database module."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_path = Path(temp_file.name)
        temp_file.close()

        yield temp_path

        if temp_path.exists():
            temp_path.unlink()

    def test_full_schema_initialization(self, temp_db):
        """Test full schema initialization."""
        conn = sqlite3.connect(str(temp_db))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        # Initialize schema
        conn.executescript(get_schema())
        conn.commit()

        # Verify all tables exist
        expected_tables = set(get_table_names())
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        actual_tables = {row[0] for row in cursor}

        assert actual_tables == expected_tables

        # Verify admin user exists
        cursor = conn.execute("SELECT * FROM users WHERE username = 'admin'")
        admin = cursor.fetchone()
        assert admin is not None
        assert admin['role'] == 'admin'

        # Verify preinstalled scrapers exist
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM saved_scrapers WHERE is_preinstalled = 1")
        count = cursor.fetchone()['cnt']
        assert count == 10  # 10 preinstalled scrapers

        conn.close()

    def test_foreign_key_constraints(self, temp_db):
        """Test foreign key constraints are enforced."""
        conn = sqlite3.connect(str(temp_db))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        # Initialize schema
        conn.executescript(get_schema())
        conn.commit()

        # Try to insert article with invalid user_id
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO scraped_data (url, link, timestamp, user_id)
                VALUES (?, ?, datetime('now'), ?)
            """, ('https://example.com', 'https://example.com/1', 999))
            conn.commit()

        conn.close()
