#!/usr/bin/env python3
"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path
import sqlite3
import pytest
import tempfile
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import after path is set
import scrapetui


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

    # Patch DB_PATH in scrapetui module
    original_db_path = scrapetui.DB_PATH
    scrapetui.DB_PATH = temp_db_path

    # Initialize full database schema
    scrapetui.init_db()

    # Get connection to initialized database
    conn = scrapetui.get_db_connection()
    conn.__enter__()  # Enter context manager

    yield conn

    # Cleanup
    conn.__exit__(None, None, None)  # Exit context manager
    scrapetui.DB_PATH = original_db_path
    if temp_db_path.exists():
        temp_db_path.unlink()
