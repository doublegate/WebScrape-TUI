"""Pytest fixtures for API tests."""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from typing import Generator

from fastapi.testclient import TestClient

from scrapetui.api.app import app
from scrapetui.core.database import get_db_connection
from scrapetui.core.auth import hash_password
from scrapetui.config import get_config


@pytest.fixture(scope="function")
def test_db() -> Generator[Path, None, None]:
    """Create temporary test database."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    # Override database path in config
    config = get_config()
    original_db_path = config.database_path
    config.database_path = str(db_path)

    # Initialize database schema
    from scrapetui.database.schema import get_schema_v2_0_0, get_indexes, get_builtin_data

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    # Create schema
    conn.executescript(get_schema_v2_0_0())

    # Add API tables (v2.1.0) - BEFORE builtin data
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

    # Cleanup
    config.database_path = original_db_path
    db_path.unlink()


@pytest.fixture(scope="function")
def client(test_db: Path) -> TestClient:
    """Create FastAPI test client with test database."""
    # Disable startup/shutdown events for testing
    app.router.lifespan_context = None
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture(scope="function")
def admin_token(client: TestClient) -> str:
    """Get JWT token for admin user."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Ch4ng3M3"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def user_token(client: TestClient, test_db: Path) -> str:
    """Create regular user and get JWT token."""
    # Create user (delete if exists first)
    with get_db_connection() as conn:
        conn.execute("DELETE FROM users WHERE username = ?", ("testuser",))
        conn.execute("""
            INSERT INTO users (username, password_hash, email, role, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, ("testuser", hash_password("testpass123"), "user@test.com", "user"))
        conn.commit()

    # Login
    response = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def viewer_token(client: TestClient, test_db: Path) -> str:
    """Create viewer user and get JWT token."""
    # Create viewer (delete if exists first)
    with get_db_connection() as conn:
        conn.execute("DELETE FROM users WHERE username = ?", ("viewer",))
        conn.execute("""
            INSERT INTO users (username, password_hash, email, role, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, ("viewer", hash_password("viewer123"), "viewer@test.com", "viewer"))
        conn.commit()

    # Login
    response = client.post(
        "/api/auth/login",
        json={"username": "viewer", "password": "viewer123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def sample_article(test_db: Path) -> int:
    """Create sample article and return its ID."""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO scraped_data
            (url, title, content, link, user_id, timestamp)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (
            "https://example.com/article",
            "Test Article",
            "This is test content for the article.",
            "https://example.com/article",
            1  # admin user
        ))
        article_id = cursor.lastrowid
        conn.commit()

    return article_id


@pytest.fixture(scope="function")
def auth_headers(admin_token: str) -> dict:
    """Get authorization headers with admin token."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def user_auth_headers(user_token: str) -> dict:
    """Get authorization headers with user token."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture(scope="function")
def viewer_auth_headers(viewer_token: str) -> dict:
    """Get authorization headers with viewer token."""
    return {"Authorization": f"Bearer {viewer_token}"}
