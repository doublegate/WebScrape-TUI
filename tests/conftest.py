#!/usr/bin/env python3
"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path
import sqlite3
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def db_connection():
    """
    Create an in-memory SQLite database connection for testing.

    This fixture provides a fresh database connection for each test,
    automatically cleaned up after the test completes.
    """
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row

    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")

    yield conn

    conn.close()
