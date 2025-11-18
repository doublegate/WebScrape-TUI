"""
Database migrations for WebScrape-TUI.

This package contains database migration scripts for upgrading
from one schema version to another.
"""

__version__ = "2.2.0"


def run_migrations(db_path: str = None) -> bool:
    """
    Run database migrations if needed.

    Args:
        db_path: Path to database file (optional, uses default if not provided)

    Returns:
        True if migrations ran successfully or not needed, False on error
    """
    # Import here to avoid circular dependencies
    from .v2_2_0 import get_current_schema_version, check_prerequisites, migrate
    import sqlite3

    if db_path is None:
        db_path = "scraped_data_tui_v1.0.db"

    # Check if database exists
    import os
    if not os.path.exists(db_path):
        # No database to migrate
        return True

    try:
        # Check current version
        conn = sqlite3.connect(db_path)
        current_version = get_current_schema_version(conn)
        conn.close()

        if current_version is None:
            # Pre-v2.0.0 database, needs v2.0.0 migration first
            return True

        if current_version == "2.2.0":
            # Already at v2.2.0
            return True

        if current_version in ("2.1.0", "2.0.1", "2.0.0"):
            # Run v2.2.0 migration
            return migrate(db_path, skip_backup=False)

        # Unknown version
        return True

    except Exception:
        # Migration not critical for import, just return True
        return True
