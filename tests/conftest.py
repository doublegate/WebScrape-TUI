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
