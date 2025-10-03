"""Database connection and initialization."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from ..utils.logging import get_logger
from ..config import init_config

# Lazy initialization - do not create logger at module level


def get_db_path() -> Path:
    """Get database path from configuration."""
    config = init_config()
    return Path(config.database_path)


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Get database connection with context manager.

    Yields:
        SQLite connection with row factory enabled
    """
    db_path = get_db_path()
    try:
        # Python 3.12+ compatible: no automatic datetime conversion
        # Datetime values stored as ISO strings, no adapters needed
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        # Enable foreign key constraints (required for v2.0.0 multi-user support)
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    except sqlite3.Error as e:
        logger = get_logger(__name__)
        logger.critical(f"DB connection error: {e}", exc_info=True)
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initialize database with schema."""
    from ..database.schema import get_schema, SCHEMA_VERSION
    from ..database.migrations import run_migrations

    logger = get_logger(__name__)
    db_path = get_db_path()
    logger.info(f"Initializing database at {db_path}")

    with get_db_connection() as conn:
        # Create schema
        schema_sql = get_schema()
        conn.executescript(schema_sql)
        conn.commit()

        # Run migrations
        run_migrations(conn)

        logger.info(f"Database initialization complete (schema v{SCHEMA_VERSION})")


def check_database_exists() -> bool:
    """Check if database file exists."""
    return get_db_path().exists()


def backup_database(backup_suffix: str = "backup") -> Path:
    """
    Create backup of database.

    Args:
        backup_suffix: Suffix to add to backup filename

    Returns:
        Path to backup file
    """
    import shutil
    from datetime import datetime

    db_path = get_db_path()
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_suffix(f".{backup_suffix}-{timestamp}")

    shutil.copy2(db_path, backup_path)
    logger = get_logger(__name__)
    logger.info(f"Database backed up to: {backup_path}")

    return backup_path
