"""
Tests for async database layer.

Tests AsyncDatabaseManager functionality including:
- Connection management
- Article CRUD operations
- User CRUD operations
- Session management
- Context manager usage
- Filter operations
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta
import tempfile
import os

# Import from monolithic scrapetui.py
import importlib.util
_scrapetui_path = Path(__file__).parent.parent.parent / 'scrapetui.py'
_spec = importlib.util.spec_from_file_location("scrapetui_monolith", _scrapetui_path)
_scrapetui_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scrapetui_module)

hash_password = _scrapetui_module.hash_password

from scrapetui.core.database_async import (
    AsyncDatabaseManager,
    get_async_db_manager,
    reset_async_db_manager
)


@pytest.fixture
async def async_db():
    """Create temporary async database for testing."""
    # Create temp database file
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # Set env var for database path
    os.environ['DATABASE_PATH'] = db_path

    # Initialize database with schema
    import sqlite3
    conn = sqlite3.connect(db_path)

    # Create tables (same schema as main app)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT NOT NULL,
            last_login TEXT,
            is_active INTEGER NOT NULL DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS scraped_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT,
            content TEXT,
            timestamp TEXT,
            user_id INTEGER DEFAULT 1,
            summary TEXT,
            sentiment TEXT,
            keywords TEXT,
            topics TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS article_tags (
            article_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            FOREIGN KEY (article_id) REFERENCES scraped_data(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (article_id, tag_id)
        )
    """)

    conn.commit()
    conn.close()

    # Create async manager
    manager = AsyncDatabaseManager(db_path)

    yield manager

    # Cleanup
    await manager.close()
    await reset_async_db_manager()
    Path(db_path).unlink(missing_ok=True)
    if 'DATABASE_PATH' in os.environ:
        del os.environ['DATABASE_PATH']


@pytest.mark.asyncio
async def test_async_db_connect(async_db):
    """Test async database connection."""
    conn = await async_db.connect()
    assert conn is not None

    # Test that foreign keys are enabled
    async with conn.execute("PRAGMA foreign_keys") as cursor:
        result = await cursor.fetchone()
        assert result[0] == 1


@pytest.mark.asyncio
async def test_async_db_context_manager(async_db):
    """Test async database context manager."""
    async with async_db as conn:
        assert conn is not None
        async with conn.execute("SELECT 1") as cursor:
            result = await cursor.fetchone()
            assert result[0] == 1


@pytest.mark.asyncio
async def test_async_create_user(async_db):
    """Test creating user asynchronously."""
    user_data = {
        'username': 'testuser',
        'password_hash': hash_password('testpass'),
        'email': 'test@example.com',
        'role': 'user',
        'is_active': 1
    }

    user_id = await async_db.create_user(user_data)
    assert user_id > 0

    # Verify user exists
    user = await async_db.get_user_by_id(user_id)
    assert user is not None
    assert user['username'] == 'testuser'
    assert user['email'] == 'test@example.com'
    assert user['role'] == 'user'
    assert user['is_active'] == 1


@pytest.mark.asyncio
async def test_async_get_user_by_username(async_db):
    """Test getting user by username asynchronously."""
    # Create user first
    user_data = {
        'username': 'testuser2',
        'password_hash': hash_password('testpass'),
        'email': 'test2@example.com'
    }
    await async_db.create_user(user_data)

    # Fetch by username
    user = await async_db.get_user_by_username('testuser2')
    assert user is not None
    assert user['username'] == 'testuser2'
    assert user['email'] == 'test2@example.com'


@pytest.mark.asyncio
async def test_async_get_user_nonexistent(async_db):
    """Test getting nonexistent user returns None."""
    user = await async_db.get_user_by_username('nonexistent')
    assert user is None


@pytest.mark.asyncio
async def test_async_update_user(async_db):
    """Test updating user asynchronously."""
    # Create user
    user_data = {
        'username': 'updatetest',
        'password_hash': hash_password('testpass'),
        'email': 'old@example.com',
        'role': 'user'
    }
    user_id = await async_db.create_user(user_data)

    # Update user
    updates = {
        'email': 'new@example.com',
        'role': 'admin'
    }
    success = await async_db.update_user(user_id, updates)
    assert success is True

    # Verify update
    user = await async_db.get_user_by_id(user_id)
    assert user['email'] == 'new@example.com'
    assert user['role'] == 'admin'


@pytest.mark.asyncio
async def test_async_fetch_users_with_filters(async_db):
    """Test fetching users with role and active filters."""
    # Create multiple users
    for i in range(5):
        user_data = {
            'username': f'user{i}',
            'password_hash': hash_password('testpass'),
            'role': 'admin' if i % 2 == 0 else 'user',
            'is_active': 1 if i < 3 else 0
        }
        await async_db.create_user(user_data)

    # Fetch all users
    users = await async_db.fetch_users()
    assert len(users) == 5

    # Fetch admins only
    users = await async_db.fetch_users(role='admin')
    assert len(users) == 3

    # Fetch active users only
    users = await async_db.fetch_users(is_active=True)
    assert len(users) == 3

    # Fetch inactive users
    users = await async_db.fetch_users(is_active=False)
    assert len(users) == 2


@pytest.mark.asyncio
async def test_async_create_session(async_db):
    """Test creating session asynchronously."""
    # Create user first
    user_data = {
        'username': 'sessionuser',
        'password_hash': hash_password('testpass')
    }
    user_id = await async_db.create_user(user_data)

    # Create session
    session_token = 'test_token_123'
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

    session_id = await async_db.create_session(user_id, session_token, expires_at)
    assert session_id > 0


@pytest.mark.asyncio
async def test_async_validate_session(async_db):
    """Test validating session asynchronously."""
    # Create user
    user_data = {
        'username': 'sessionuser2',
        'password_hash': hash_password('testpass')
    }
    user_id = await async_db.create_user(user_data)

    # Create valid session
    session_token = 'valid_token_456'
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    await async_db.create_session(user_id, session_token, expires_at)

    # Validate
    validated_user_id = await async_db.validate_session(session_token)
    assert validated_user_id == user_id


@pytest.mark.asyncio
async def test_async_validate_expired_session(async_db):
    """Test that expired sessions are invalid."""
    # Create user
    user_data = {
        'username': 'expireduser',
        'password_hash': hash_password('testpass')
    }
    user_id = await async_db.create_user(user_data)

    # Create expired session
    session_token = 'expired_token_789'
    expires_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    await async_db.create_session(user_id, session_token, expires_at)

    # Validate should return None
    validated_user_id = await async_db.validate_session(session_token)
    assert validated_user_id is None


@pytest.mark.asyncio
async def test_async_delete_session(async_db):
    """Test deleting session (logout)."""
    # Create user
    user_data = {
        'username': 'logoutuser',
        'password_hash': hash_password('testpass')
    }
    user_id = await async_db.create_user(user_data)

    # Create session
    session_token = 'logout_token'
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    await async_db.create_session(user_id, session_token, expires_at)

    # Validate session exists
    validated_user_id = await async_db.validate_session(session_token)
    assert validated_user_id == user_id

    # Delete session
    success = await async_db.delete_session(session_token)
    assert success is True

    # Validate session is gone
    validated_user_id = await async_db.validate_session(session_token)
    assert validated_user_id is None


@pytest.mark.asyncio
async def test_async_cleanup_expired_sessions(async_db):
    """Test cleaning up expired sessions."""
    # Create user
    user_data = {
        'username': 'cleanupuser',
        'password_hash': hash_password('testpass')
    }
    user_id = await async_db.create_user(user_data)

    # Create mix of valid and expired sessions
    valid_token = 'valid_session'
    valid_expires = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    await async_db.create_session(user_id, valid_token, valid_expires)

    expired_token1 = 'expired_session1'
    expired_expires = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    await async_db.create_session(user_id, expired_token1, expired_expires)

    expired_token2 = 'expired_session2'
    await async_db.create_session(user_id, expired_token2, expired_expires)

    # Cleanup expired sessions
    deleted_count = await async_db.cleanup_expired_sessions()
    assert deleted_count == 2

    # Verify valid session still exists
    validated_user_id = await async_db.validate_session(valid_token)
    assert validated_user_id == user_id


@pytest.mark.asyncio
async def test_async_create_article(async_db):
    """Test creating article asynchronously."""
    # Create user first for foreign key constraint
    user_data = {
        'username': 'articleowner',
        'password_hash': hash_password('testpass')
    }
    user_id = await async_db.create_user(user_data)

    article_data = {
        'title': 'Test Article',
        'link': 'https://example.com/article',
        'content': 'Test content here',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'user_id': user_id
    }

    article_id = await async_db.create_article(article_data)
    assert article_id > 0

    # Verify article exists
    article = await async_db.get_article_by_id(article_id)
    assert article is not None
    assert article['title'] == 'Test Article'
    assert article['link'] == 'https://example.com/article'


@pytest.mark.asyncio
async def test_async_create_article_with_ai_fields(async_db):
    """Test creating article with AI-generated fields."""
    # Create user first for foreign key constraint
    user_data = {
        'username': 'aiuser',
        'password_hash': hash_password('testpass')
    }
    user_id = await async_db.create_user(user_data)

    article_data = {
        'title': 'AI Article',
        'link': 'https://example.com/ai',
        'content': 'AI-processed content',
        'summary': 'Test summary',
        'sentiment': 'positive',
        'keywords': 'test,keyword,ai',
        'topics': 'technology,ai',
        'user_id': user_id
    }

    article_id = await async_db.create_article(article_data)
    article = await async_db.get_article_by_id(article_id)

    assert article['summary'] == 'Test summary'
    assert article['sentiment'] == 'positive'
    assert article['keywords'] == 'test,keyword,ai'
    assert article['topics'] == 'technology,ai'


@pytest.mark.asyncio
async def test_async_get_article_nonexistent(async_db):
    """Test getting nonexistent article returns None."""
    article = await async_db.get_article_by_id(99999)
    assert article is None


@pytest.mark.asyncio
async def test_async_update_article(async_db):
    """Test updating article asynchronously."""
    # Create user first
    user_data = {'username': 'updateuser', 'password_hash': hash_password('pass')}
    user_id = await async_db.create_user(user_data)

    # Create article
    article_data = {
        'title': 'Original Title',
        'link': 'https://example.com/original',
        'content': 'Original content',
        'user_id': user_id
    }
    article_id = await async_db.create_article(article_data)

    # Update
    updates = {
        'title': 'Updated Title',
        'summary': 'Test summary'
    }
    success = await async_db.update_article(article_id, updates)
    assert success is True

    # Verify update
    article = await async_db.get_article_by_id(article_id)
    assert article['title'] == 'Updated Title'
    assert article['summary'] == 'Test summary'


@pytest.mark.asyncio
async def test_async_delete_article(async_db):
    """Test deleting article asynchronously."""
    # Create user first
    user_data = {'username': 'deleteuser', 'password_hash': hash_password('pass')}
    user_id = await async_db.create_user(user_data)

    # Create article
    article_data = {
        'title': 'To Delete',
        'link': 'https://example.com/delete',
        'user_id': user_id
    }
    article_id = await async_db.create_article(article_data)

    # Delete
    success = await async_db.delete_article(article_id)
    assert success is True

    # Verify deleted
    article = await async_db.get_article_by_id(article_id)
    assert article is None


@pytest.mark.asyncio
async def test_async_fetch_articles_basic(async_db):
    """Test fetching all articles."""
    # Create user first
    user_data = {'username': 'fetchuser', 'password_hash': hash_password('pass')}
    user_id = await async_db.create_user(user_data)

    # Create multiple articles
    for i in range(5):
        article_data = {
            'title': f'Article {i}',
            'link': f'https://example.com/article{i}',
            'content': f'Content {i}',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'user_id': user_id
        }
        await async_db.create_article(article_data)

    # Fetch all
    articles = await async_db.fetch_articles()
    assert len(articles) == 5


@pytest.mark.asyncio
async def test_async_fetch_articles_with_limit(async_db):
    """Test fetching articles with limit and offset."""
    # Create user first
    user_data = {'username': 'limituser', 'password_hash': hash_password('pass')}
    user_id = await async_db.create_user(user_data)

    # Create articles
    for i in range(10):
        article_data = {
            'title': f'Article {i}',
            'link': f'https://example.com/article{i}',
            'user_id': user_id
        }
        await async_db.create_article(article_data)

    # Fetch with limit
    articles = await async_db.fetch_articles(limit=3)
    assert len(articles) == 3

    # Fetch with limit and offset
    articles = await async_db.fetch_articles(limit=3, offset=3)
    assert len(articles) == 3


@pytest.mark.asyncio
async def test_async_fetch_articles_with_search(async_db):
    """Test fetching articles with search filter."""
    # Create user first
    user_data = {'username': 'searchuser', 'password_hash': hash_password('pass')}
    user_id = await async_db.create_user(user_data)

    # Create articles
    await async_db.create_article({
        'title': 'Python Programming',
        'content': 'Learn Python',
        'user_id': user_id
    })
    await async_db.create_article({
        'title': 'JavaScript Basics',
        'content': 'Learn JS',
        'user_id': user_id
    })
    await async_db.create_article({
        'title': 'Advanced Python',
        'content': 'Expert Python',
        'user_id': user_id
    })

    # Search for Python
    articles = await async_db.fetch_articles(search='Python')
    assert len(articles) == 2

    # Search for JavaScript
    articles = await async_db.fetch_articles(search='JavaScript')
    assert len(articles) == 1


@pytest.mark.asyncio
async def test_async_fetch_articles_with_user_filter(async_db):
    """Test fetching articles filtered by user."""
    # Create users
    user1_data = {'username': 'user1', 'password_hash': hash_password('pass')}
    user2_data = {'username': 'user2', 'password_hash': hash_password('pass')}
    user1_id = await async_db.create_user(user1_data)
    user2_id = await async_db.create_user(user2_data)

    # Create articles for different users
    await async_db.create_article({'title': 'Article 1', 'user_id': user1_id})
    await async_db.create_article({'title': 'Article 2', 'user_id': user1_id})
    await async_db.create_article({'title': 'Article 3', 'user_id': user2_id})

    # Fetch user1's articles
    articles = await async_db.fetch_articles(user_id=user1_id)
    assert len(articles) == 2

    # Fetch user2's articles
    articles = await async_db.fetch_articles(user_id=user2_id)
    assert len(articles) == 1


@pytest.mark.asyncio
async def test_async_fetch_articles_with_sentiment_filter(async_db):
    """Test fetching articles filtered by sentiment."""
    # Create user first
    user_data = {'username': 'sentimentuser', 'password_hash': hash_password('pass')}
    user_id = await async_db.create_user(user_data)

    # Create articles with different sentiments
    await async_db.create_article({
        'title': 'Happy News',
        'sentiment': 'positive',
        'user_id': user_id
    })
    await async_db.create_article({
        'title': 'Sad News',
        'sentiment': 'negative',
        'user_id': user_id
    })
    await async_db.create_article({
        'title': 'More Happy News',
        'sentiment': 'positive',
        'user_id': user_id
    })

    # Fetch positive articles
    articles = await async_db.fetch_articles(sentiment='positive')
    assert len(articles) == 2

    # Fetch negative articles
    articles = await async_db.fetch_articles(sentiment='negative')
    assert len(articles) == 1


@pytest.mark.asyncio
async def test_async_fetch_articles_with_date_filters(async_db):
    """Test fetching articles filtered by date range."""
    # Create user first
    user_data = {'username': 'dateuser', 'password_hash': hash_password('pass')}
    user_id = await async_db.create_user(user_data)

    # Create articles with different timestamps
    old_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    recent_date = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    new_date = datetime.now(timezone.utc).isoformat()

    await async_db.create_article({'title': 'Old Article', 'timestamp': old_date, 'user_id': user_id})
    await async_db.create_article({'title': 'Recent Article', 'timestamp': recent_date, 'user_id': user_id})
    await async_db.create_article({'title': 'New Article', 'timestamp': new_date, 'user_id': user_id})

    # Fetch articles from last 5 days
    date_from = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    articles = await async_db.fetch_articles(date_from=date_from)
    assert len(articles) == 2

    # Fetch articles up to 5 days ago
    date_to = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    articles = await async_db.fetch_articles(date_to=date_to)
    assert len(articles) == 1


@pytest.mark.asyncio
async def test_async_fetch_articles_combined_filters(async_db):
    """Test fetching articles with multiple filters combined."""
    # Create user
    user_data = {'username': 'testuser', 'password_hash': hash_password('pass')}
    user_id = await async_db.create_user(user_data)

    # Create articles
    await async_db.create_article({
        'title': 'Python Article',
        'content': 'Python content',
        'sentiment': 'positive',
        'user_id': user_id
    })
    await async_db.create_article({
        'title': 'JavaScript Article',
        'content': 'JS content',
        'sentiment': 'negative',
        'user_id': user_id
    })
    await async_db.create_article({
        'title': 'Python Tutorial',
        'content': 'Python guide',
        'sentiment': 'positive',
        'user_id': user_id
    })

    # Fetch Python articles with positive sentiment
    articles = await async_db.fetch_articles(
        search='Python',
        sentiment='positive',
        user_id=user_id
    )
    assert len(articles) == 2


@pytest.mark.asyncio
async def test_async_db_singleton_pattern():
    """Test get_async_db_manager singleton pattern."""
    # Create temp DB
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    os.environ['DATABASE_PATH'] = db_path

    try:
        # Reset singleton
        await reset_async_db_manager()

        # Get manager (should create new one)
        manager1 = get_async_db_manager(db_path)
        assert manager1 is not None

        # Get manager again (should return same instance)
        manager2 = get_async_db_manager(db_path)
        assert manager2 is manager1

    finally:
        # Cleanup
        await reset_async_db_manager()
        Path(db_path).unlink(missing_ok=True)
        if 'DATABASE_PATH' in os.environ:
            del os.environ['DATABASE_PATH']
