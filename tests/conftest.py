#!/usr/bin/env python3
"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path
import sqlite3
import pytest
import tempfile
from unittest.mock import patch
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import after path is set
import scrapetui


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Reset all global singleton instances before each test.

    This ensures test isolation by clearing cached config, loggers, and cache instances.
    """
    # Reset cache singleton
    import scrapetui.core.cache
    scrapetui.core.cache._cache_instance = None

    # Reset config singleton
    from scrapetui.config import reset_config
    reset_config()

    # Reset logging singleton
    from scrapetui.utils.logging import reset_logging
    reset_logging()

    # Reset auth lazy loggers
    import scrapetui.core.auth
    scrapetui.core.auth._logger = None

    # Reset manager lazy loggers/config
    import scrapetui.scrapers.manager
    scrapetui.scrapers.manager._logger = None
    scrapetui.scrapers.manager._config = None

    yield

    # Cleanup after test (reset again for next test)
    scrapetui.core.cache._cache_instance = None


@pytest.fixture(autouse=True)
def test_env_vars():
    """
    Set safe test environment variables.

    Ensures tests use isolated configuration without affecting system.
    """
    original_env = os.environ.copy()

    # Set test-specific environment variables
    os.environ['CACHE_ENABLED'] = 'false'  # Disable caching in tests
    os.environ['LOG_LEVEL'] = 'ERROR'  # Reduce log noise in tests

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def db_connection():
    """
    Create an in-memory SQLite database connection for testing.

    This fixture provides a fresh database connection with full schema
    initialized, automatically cleaned up after the test completes.
    """
    # Create temporary database file for proper init_db() execution
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
    temp_db_path = Path(temp_file.name)
    temp_file.close()

    # Set DATABASE_PATH environment variable and reset config
    original_db_path = os.environ.get('DATABASE_PATH')
    os.environ['DATABASE_PATH'] = str(temp_db_path)
    scrapetui.reset_config()  # Force config reload with new DATABASE_PATH

    # Also patch the legacy scrapetui.DB_PATH for backward compatibility
    original_legacy_db = scrapetui.DB_PATH
    scrapetui.DB_PATH = temp_db_path

    # Initialize full database schema
    scrapetui.init_db()

    # Get connection to initialized database
    conn = scrapetui.get_db_connection()
    conn.__enter__()  # Enter context manager

    yield conn

    # Cleanup
    conn.__exit__(None, None, None)  # Exit context manager

    # Restore environment and config
    if original_db_path is not None:
        os.environ['DATABASE_PATH'] = original_db_path
    else:
        os.environ.pop('DATABASE_PATH', None)
    scrapetui.DB_PATH = original_legacy_db
    scrapetui.reset_config()  # Reset config back

    if temp_db_path.exists():
        temp_db_path.unlink()


@pytest.fixture
def temp_db():
    """
    Create temporary test database with proper isolation.

    This fixture provides a complete isolated database for each test,
    with automatic cleanup after the test completes.
    """
    from scrapetui.config import reset_config
    from scrapetui.database.schema import get_schema_v2_0_0, get_indexes, get_builtin_data

    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    # Override database path via environment variable
    original_db_path = os.environ.get('DATABASE_PATH')
    os.environ['DATABASE_PATH'] = str(db_path)

    # Reset config singleton to pick up new DATABASE_PATH
    reset_config()

    # Initialize database schema
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    # Create schema
    conn.executescript(get_schema_v2_0_0())

    # Add API tables (v2.1.0)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS token_blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT NOT NULL UNIQUE,
            blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_token_blacklist_token ON token_blacklist (token);
        CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens (token);
        CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens (user_id);
    """)

    conn.executescript(get_indexes())
    conn.executescript(get_builtin_data())

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup - restore original DATABASE_PATH and reset config singleton
    if original_db_path is None:
        os.environ.pop('DATABASE_PATH', None)
    else:
        os.environ['DATABASE_PATH'] = original_db_path
    reset_config()

    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def unique_link():
    """Generate unique article link to avoid UNIQUE constraint violations."""
    import time
    import random
    unique_id = f"{int(time.time() * 1000000)}-{random.randint(1000, 9999)}"
    return f"https://example.com/article-{unique_id}"


@pytest.fixture
def unique_scraper_name():
    """Generate unique scraper name to avoid UNIQUE constraint violations."""
    import time
    import random
    unique_id = f"{int(time.time() * 1000000)}-{random.randint(1000, 9999)}"
    return f"Test Scraper {unique_id}"
