"""
Database migration from v2.1.0 to v2.2.0.

Adds security and administrative features:
- New tables: login_attempts, password_reset_tokens, audit_log
- New columns: account lockout, password management, user quotas
- Indexes for performance

Run with: python -m scrapetui.database.migrations.v2_2_0
"""

import sqlite3
import os
import shutil
from datetime import datetime, timezone
from typing import Optional, Tuple


MIGRATION_VERSION = "2.2.0"
PREVIOUS_VERSION = "2.1.0"  # Or 2.0.1/2.0.0


def get_current_schema_version(conn: sqlite3.Connection) -> Optional[str]:
    """
    Get current database schema version.

    Args:
        conn: Database connection

    Returns:
        Current version string or None if version table doesn't exist
    """
    try:
        cursor = conn.execute(
            "SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1"
        )
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.OperationalError:
        # schema_version table doesn't exist (pre-v2.0.0)
        return None


def create_backup(db_path: str) -> str:
    """
    Create backup of database before migration.

    Args:
        db_path: Path to database file

    Returns:
        Path to backup file
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup-v2.1.0-{timestamp}"

    if os.path.exists(db_path):
        shutil.copy2(db_path, backup_path)
        print(f"✓ Database backup created: {backup_path}")

    return backup_path


def check_prerequisites(conn: sqlite3.Connection) -> Tuple[bool, str]:
    """
    Check if database is ready for v2.2.0 migration.

    Args:
        conn: Database connection

    Returns:
        Tuple of (can_migrate, message)
    """
    # Check current version
    current_version = get_current_schema_version(conn)

    if current_version is None:
        return False, "Database schema version not found. Run v2.0.0 migration first."

    if current_version == MIGRATION_VERSION:
        return False, f"Database is already at version {MIGRATION_VERSION}"

    # Check if users table exists
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
    )
    if cursor.fetchone() is None:
        return False, "Users table not found. Database may be corrupted."

    return True, f"Ready to migrate from v{current_version} to v{MIGRATION_VERSION}"


def add_login_attempts_table(conn: sqlite3.Connection) -> None:
    """Create login_attempts table for rate limiting."""
    print("  → Creating login_attempts table...")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            success INTEGER NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            attempted_at TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
        )
    """)

    # Create indexes for performance
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_login_attempts_username
        ON login_attempts(username)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_login_attempts_attempted_at
        ON login_attempts(attempted_at)
    """)

    print("    ✓ login_attempts table created")


def add_password_reset_table(conn: sqlite3.Connection) -> None:
    """Create password_reset_tokens table."""
    print("  → Creating password_reset_tokens table...")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # Create indexes
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_password_reset_token
        ON password_reset_tokens(token)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_password_reset_user_id
        ON password_reset_tokens(user_id)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_password_reset_expires_at
        ON password_reset_tokens(expires_at)
    """)

    print("    ✓ password_reset_tokens table created")


def add_audit_log_table(conn: sqlite3.Connection) -> None:
    """Create audit_log table for security tracking."""
    print("  → Creating audit_log table...")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            user_id INTEGER,
            username TEXT,
            ip_address TEXT,
            user_agent TEXT,
            event_data TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # Create indexes
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_event_type
        ON audit_log(event_type)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_user_id
        ON audit_log(user_id)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_created_at
        ON audit_log(created_at)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_username
        ON audit_log(username)
    """)

    print("    ✓ audit_log table created")


def add_user_security_columns(conn: sqlite3.Connection) -> None:
    """Add security-related columns to users table."""
    print("  → Adding security columns to users table...")

    # Get existing columns
    cursor = conn.execute("PRAGMA table_info(users)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    # Add columns if they don't exist
    columns_to_add = [
        ("account_locked", "INTEGER DEFAULT 0"),
        ("locked_until", "TEXT"),
        ("failed_login_attempts", "INTEGER DEFAULT 0"),
        ("last_failed_login", "TEXT"),
        ("password_changed_at", "TEXT"),
        ("force_password_change", "INTEGER DEFAULT 0"),
    ]

    for column_name, column_def in columns_to_add:
        if column_name not in existing_columns:
            conn.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")
            print(f"    ✓ Added column: {column_name}")


def add_user_quota_columns(conn: sqlite3.Connection) -> None:
    """Add quota-related columns to users table."""
    print("  → Adding quota columns to users table...")

    # Get existing columns
    cursor = conn.execute("PRAGMA table_info(users)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    # Add quota columns
    quota_columns = [
        ("article_quota", "INTEGER DEFAULT 10000"),
        ("scraper_quota", "INTEGER DEFAULT 100"),
        ("quota_reset_at", "TEXT"),
    ]

    for column_name, column_def in quota_columns:
        if column_name not in existing_columns:
            conn.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")
            print(f"    ✓ Added column: {column_name}")


def set_admin_unlimited_quotas(conn: sqlite3.Connection) -> None:
    """Set unlimited quotas for admin users."""
    print("  → Setting unlimited quotas for admin users...")

    conn.execute("""
        UPDATE users
        SET article_quota = -1, scraper_quota = -1
        WHERE role = 'admin'
    """)

    admin_count = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'admin'"
    ).fetchone()[0]

    print(f"    ✓ Updated {admin_count} admin user(s) with unlimited quotas")


def initialize_password_timestamps(conn: sqlite3.Connection) -> None:
    """Initialize password_changed_at for existing users."""
    print("  → Initializing password timestamps...")

    now = datetime.now(timezone.utc).isoformat()

    conn.execute("""
        UPDATE users
        SET password_changed_at = ?
        WHERE password_changed_at IS NULL
    """, (now,))

    updated_count = conn.total_changes

    print(f"    ✓ Initialized password timestamps for {updated_count} user(s)")


def update_schema_version(conn: sqlite3.Connection) -> None:
    """Update schema version table."""
    print("  → Updating schema version...")

    now = datetime.now(timezone.utc).isoformat()

    conn.execute("""
        INSERT INTO schema_version (version, applied_at)
        VALUES (?, ?)
    """, (MIGRATION_VERSION, now))

    print(f"    ✓ Schema version updated to {MIGRATION_VERSION}")


def migrate(db_path: str, skip_backup: bool = False) -> bool:
    """
    Run migration from v2.1.0 to v2.2.0.

    Args:
        db_path: Path to database file
        skip_backup: Skip backup creation (for testing)

    Returns:
        True if migration successful, False otherwise
    """
    print(f"\n{'=' * 60}")
    print(f"WebScrape-TUI Database Migration to v{MIGRATION_VERSION}")
    print(f"{'=' * 60}\n")

    if not os.path.exists(db_path):
        print(f"✗ Database file not found: {db_path}")
        return False

    # Create backup
    if not skip_backup:
        backup_path = create_backup(db_path)
    else:
        backup_path = None

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)

        # Check prerequisites
        can_migrate, message = check_prerequisites(conn)
        print(f"Prerequisites: {message}")

        if not can_migrate:
            conn.close()
            return False

        print("\nStarting migration...\n")

        # Begin transaction
        conn.execute("BEGIN TRANSACTION")

        # Run migration steps
        add_login_attempts_table(conn)
        add_password_reset_table(conn)
        add_audit_log_table(conn)
        add_user_security_columns(conn)
        add_user_quota_columns(conn)
        set_admin_unlimited_quotas(conn)
        initialize_password_timestamps(conn)
        update_schema_version(conn)

        # Commit transaction
        conn.commit()
        conn.close()

        print(f"\n{'=' * 60}")
        print(f"✓ Migration to v{MIGRATION_VERSION} completed successfully!")
        print(f"{'=' * 60}\n")

        if backup_path:
            print(f"Backup saved: {backup_path}\n")

        return True

    except Exception as e:
        print(f"\n✗ Migration failed: {str(e)}\n")

        # Rollback
        try:
            conn.rollback()
            conn.close()
            print("✓ Transaction rolled back")
        except Exception:
            pass

        # Restore from backup if available
        if backup_path and os.path.exists(backup_path):
            print(f"\nRestoring from backup: {backup_path}")
            try:
                shutil.copy2(backup_path, db_path)
                print("✓ Database restored from backup")
            except Exception as restore_error:
                print(f"✗ Failed to restore backup: {str(restore_error)}")

        return False


def rollback(db_path: str, backup_path: Optional[str] = None) -> bool:
    """
    Rollback v2.2.0 migration.

    Args:
        db_path: Path to database file
        backup_path: Path to backup file (optional)

    Returns:
        True if rollback successful, False otherwise
    """
    print(f"\n{'=' * 60}")
    print(f"Rolling back v{MIGRATION_VERSION} migration")
    print(f"{'=' * 60}\n")

    if backup_path and os.path.exists(backup_path):
        # Restore from backup
        try:
            shutil.copy2(backup_path, db_path)
            print(f"✓ Database restored from: {backup_path}")
            return True
        except Exception as e:
            print(f"✗ Failed to restore backup: {str(e)}")
            return False
    else:
        # Manual rollback (drop new tables and columns)
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("BEGIN TRANSACTION")

            # Drop new tables
            conn.execute("DROP TABLE IF EXISTS login_attempts")
            conn.execute("DROP TABLE IF EXISTS password_reset_tokens")
            conn.execute("DROP TABLE IF EXISTS audit_log")

            # Note: SQLite doesn't support DROP COLUMN, so columns remain
            # but can be ignored by older application versions

            # Remove v2.2.0 from schema_version
            conn.execute(
                "DELETE FROM schema_version WHERE version = ?",
                (MIGRATION_VERSION,)
            )

            conn.commit()
            conn.close()

            print("✓ Migration rolled back (new tables removed)")
            print("⚠ Note: New columns in users table remain (SQLite limitation)")
            return True

        except Exception as e:
            print(f"✗ Rollback failed: {str(e)}")
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            return False


def main():
    """Main migration script entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description=f"Migrate database to v{MIGRATION_VERSION}"
    )
    parser.add_argument(
        "--db-path",
        default="scraped_data_tui_v1.0.db",
        help="Path to database file"
    )
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="Skip backup creation (for testing)"
    )
    parser.add_argument(
        "--rollback",
        metavar="BACKUP_PATH",
        help="Rollback migration using backup file"
    )

    args = parser.parse_args()

    if args.rollback:
        success = rollback(args.db_path, args.rollback)
    else:
        success = migrate(args.db_path, args.skip_backup)

    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
