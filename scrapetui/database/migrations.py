"""Database migration management for WebScrape-TUI."""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from ..utils.logging import get_logger
from ..core.auth import hash_password

logger = get_logger(__name__)


def get_current_version(conn: sqlite3.Connection) -> Optional[str]:
    """
    Get current database schema version.

    Args:
        conn: SQLite database connection

    Returns:
        Version string or None if not found
    """
    try:
        result = conn.execute("""
            SELECT version FROM schema_version
            ORDER BY applied_at DESC LIMIT 1
        """).fetchone()
        return result[0] if result else None
    except sqlite3.OperationalError:
        # schema_version table doesn't exist - this is v1.x or earlier
        return None


def create_backup(db_path: Path, version_label: str = "backup") -> Path:
    """
    Create database backup before migration.

    Args:
        db_path: Path to database file
        version_label: Label to include in backup filename

    Returns:
        Path to backup file
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = db_path.parent / f"{db_path.name}.{version_label}-{timestamp}"

    logger.info(f"Creating backup: {backup_path}")
    shutil.copy2(db_path, backup_path)

    return backup_path


def migrate_v1_to_v2_0_0(conn: sqlite3.Connection) -> bool:
    """
    Migrate database from v1.x to v2.0.0.

    This migration:
    - Creates users and user_sessions tables
    - Creates schema_version table
    - Adds user_id columns to existing tables
    - Creates default admin user
    - Assigns all existing data to admin user

    Args:
        conn: SQLite database connection

    Returns:
        True if migration successful, False otherwise
    """
    try:
        logger.info("Migrating from v1.x to v2.0.0...")

        # Check if users table exists
        tables = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='users'
        """).fetchone()

        if tables:
            logger.info("Users table already exists, skipping v2.0.0 migration")
            return True

        # Create users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                email TEXT,
                role TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('admin', 'user', 'viewer')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)

        # Create user_sessions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_token TEXT NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                ip_address TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Create schema_version table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)

        # Create indexes for performance
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id)"
        )

        # Add user_id column to scraped_data if it doesn't exist
        try:
            conn.execute("SELECT user_id FROM scraped_data LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Adding user_id column to scraped_data")
            conn.execute("ALTER TABLE scraped_data ADD COLUMN user_id INTEGER DEFAULT 1")
            conn.execute("""
                UPDATE scraped_data SET user_id = 1 WHERE user_id IS NULL
            """)

        # Add user_id and is_shared columns to saved_scrapers
        try:
            conn.execute("SELECT user_id, is_shared FROM saved_scrapers LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Adding user_id and is_shared columns to saved_scrapers")
            conn.execute("ALTER TABLE saved_scrapers ADD COLUMN user_id INTEGER DEFAULT 1")
            conn.execute("ALTER TABLE saved_scrapers ADD COLUMN is_shared INTEGER DEFAULT 0")
            conn.execute("""
                UPDATE saved_scrapers SET user_id = 1, is_shared = 1
                WHERE is_preinstalled = 1
            """)

        # Create default admin user
        count_row = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()

        if count_row['cnt'] == 0:
            password_hash = hash_password('Ch4ng3M3')
            conn.execute("""
                INSERT INTO users (username, password_hash, email, role, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, ('admin', password_hash, 'admin@localhost', 'admin', 1))
            logger.info(
                "Default admin user created: username='admin', "
                "password='Ch4ng3M3' (please change after first login)"
            )

        # Get admin user ID
        admin_row = conn.execute(
            "SELECT id FROM users WHERE username = 'admin'"
        ).fetchone()

        if not admin_row:
            logger.error("Failed to create or find admin user during migration")
            return False

        admin_id = admin_row['id']

        # Assign all existing data to admin user (only if tables exist)
        # Check if saved_scrapers table exists
        scrapers_table = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='saved_scrapers'
        """).fetchone()
        if scrapers_table:
            conn.execute(
                "UPDATE saved_scrapers SET user_id = ? WHERE user_id IS NULL",
                (admin_id,)
            )

        # Check if scraped_data table exists
        data_table = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='scraped_data'
        """).fetchone()
        if data_table:
            conn.execute(
                "UPDATE scraped_data SET user_id = ? WHERE user_id IS NULL",
                (admin_id,)
            )

        # Create indexes for user_id columns
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scraped_data_user_id ON scraped_data(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_saved_scrapers_user ON saved_scrapers(user_id)")

        # Record migration
        conn.execute("""
            INSERT OR REPLACE INTO schema_version (version, description)
            VALUES (?, ?)
        """, (
            '2.0.0',
            'Multi-user foundation: users, sessions, ownership tracking'
        ))

        conn.commit()
        logger.info("Migration to v2.0.0 complete")
        return True

    except sqlite3.Error as e:
        logger.error(f"Migration to v2.0.0 failed: {e}", exc_info=True)
        conn.rollback()
        return False


def migrate_v2_0_0_add_content_column(conn: sqlite3.Connection) -> bool:
    """
    Migrate v2.0.0 schema to add missing 'content' column to scraped_data table.

    This migration:
    - Checks if content column exists in scraped_data table
    - Adds content column if missing (TEXT, nullable)
    - Updates schema_version to mark this migration as applied

    Args:
        conn: SQLite database connection

    Returns:
        True if migration successful, False otherwise
    """
    try:
        logger.info("Checking for content column in scraped_data table...")

        # Check if content column exists
        cursor = conn.execute("PRAGMA table_info(scraped_data)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'content' in columns:
            logger.info("Content column already exists, skipping migration")
            return True

        logger.info("Adding content column to scraped_data table...")

        # Add content column (nullable, no default needed)
        conn.execute("ALTER TABLE scraped_data ADD COLUMN content TEXT")

        # Record migration in schema_version
        conn.execute("""
            INSERT OR REPLACE INTO schema_version (version, description)
            VALUES (?, ?)
        """, (
            '2.0.1',
            'Add content column to scraped_data table'
        ))

        conn.commit()
        logger.info("Content column migration complete")
        return True

    except sqlite3.Error as e:
        logger.error(f"Failed to add content column: {e}", exc_info=True)
        conn.rollback()
        return False


def run_migrations(conn: sqlite3.Connection) -> bool:
    """
    Run all necessary database migrations.

    Args:
        conn: SQLite database connection

    Returns:
        True if all migrations successful, False otherwise
    """
    current_version = get_current_version(conn)

    logger.info(f"Current database version: {current_version or 'v1.x or earlier'}")

    if current_version is None:
        # v1.x or earlier - migrate to v2.0.0
        if not migrate_v1_to_v2_0_0(conn):
            logger.error("Failed to migrate to v2.0.0")
            return False
        current_version = '2.0.0'

    # Apply v2.0.1 migration if on v2.0.0
    if current_version == '2.0.0':
        logger.info("Applying v2.0.1 migration (add content column)...")
        if not migrate_v2_0_0_add_content_column(conn):
            logger.error("Failed to migrate to v2.0.1")
            return False
    elif current_version == '2.0.1':
        logger.info("Database already at v2.0.1")
    else:
        logger.warning(f"Unknown database version: {current_version}")
        # Don't fail - might be a newer version

    return True


def verify_schema(conn: sqlite3.Connection) -> bool:
    """
    Verify database schema is complete and correct.

    Args:
        conn: SQLite database connection

    Returns:
        True if schema is valid, False otherwise
    """
    from .schema import get_table_names

    expected_tables = set(get_table_names())

    # Get actual tables
    actual_tables = set()
    for row in conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
    """):
        actual_tables.add(row[0])

    missing_tables = expected_tables - actual_tables
    extra_tables = actual_tables - expected_tables

    if missing_tables:
        logger.error(f"Missing tables: {missing_tables}")
        return False

    if extra_tables:
        logger.warning(f"Extra tables (not in schema): {extra_tables}")

    logger.info("Schema verification passed")
    return True
