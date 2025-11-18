"""
Unit tests for user quotas module.

Tests quota checking, enforcement, and management.
"""

import pytest
import sqlite3
import tempfile
import os

from scrapetui.core.quotas import (
    QuotaManager,
    QuotaConfig,
    QuotaType,
    QuotaStatus,
    get_quota_manager
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # Create tables
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            role TEXT DEFAULT 'user',
            article_quota INTEGER DEFAULT 10000,
            scraper_quota INTEGER DEFAULT 100
        )
    """)
    conn.execute("""
        CREATE TABLE scraped_data (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            title TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.execute("""
        CREATE TABLE saved_scrapers (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            name TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Insert test users
    conn.execute("""
        INSERT INTO users (id, username, role, article_quota, scraper_quota)
        VALUES (1, 'testuser', 'user', 100, 10)
    """)
    conn.execute("""
        INSERT INTO users (id, username, role, article_quota, scraper_quota)
        VALUES (2, 'admin', 'admin', 10000, 100)
    """)
    conn.commit()
    conn.close()

    yield path

    os.unlink(path)


class TestQuotaManager:
    """Test QuotaManager class."""

    def test_initialization(self, temp_db):
        """Test quota manager initialization."""
        mgr = QuotaManager(temp_db)
        assert mgr.db_path == temp_db
        assert mgr.config.default_article_quota == 10000
        assert mgr.config.default_scraper_quota == 100

    def test_custom_config(self, temp_db):
        """Test quota manager with custom config."""
        config = QuotaConfig(
            default_article_quota=5000,
            default_scraper_quota=50
        )
        mgr = QuotaManager(temp_db, config)
        assert mgr.config.default_article_quota == 5000

    def test_get_quota_status_articles(self, temp_db):
        """Test getting article quota status."""
        mgr = QuotaManager(temp_db)

        # Add some articles for user 1
        conn = sqlite3.connect(temp_db)
        for i in range(30):
            conn.execute("""
                INSERT INTO scraped_data (user_id, title)
                VALUES (1, ?)
            """, (f'Article {i}',))
        conn.commit()
        conn.close()

        status = mgr.get_quota_status(1, QuotaType.ARTICLES)

        assert status.quota_type == 'articles'
        assert status.current_usage == 30
        assert status.quota_limit == 100
        assert status.remaining == 70
        assert status.percentage_used == 30.0
        assert status.exceeded is False

    def test_get_quota_status_scrapers(self, temp_db):
        """Test getting scraper quota status."""
        mgr = QuotaManager(temp_db)

        # Add scrapers for user 1
        conn = sqlite3.connect(temp_db)
        for i in range(5):
            conn.execute("""
                INSERT INTO saved_scrapers (user_id, name)
                VALUES (1, ?)
            """, (f'Scraper {i}',))
        conn.commit()
        conn.close()

        status = mgr.get_quota_status(1, QuotaType.SCRAPERS)

        assert status.current_usage == 5
        assert status.quota_limit == 10
        assert status.remaining == 5
        assert status.percentage_used == 50.0

    def test_quota_exceeded(self, temp_db):
        """Test quota exceeded detection."""
        mgr = QuotaManager(temp_db)

        # Add articles up to quota limit
        conn = sqlite3.connect(temp_db)
        for i in range(100):
            conn.execute("""
                INSERT INTO scraped_data (user_id, title)
                VALUES (1, ?)
            """, (f'Article {i}',))
        conn.commit()
        conn.close()

        status = mgr.get_quota_status(1, QuotaType.ARTICLES)

        assert status.current_usage == 100
        assert status.quota_limit == 100
        assert status.remaining == 0
        assert status.exceeded is True

    def test_check_quota_available(self, temp_db):
        """Test checking if quota is available."""
        mgr = QuotaManager(temp_db)

        # User has quota available
        available = mgr.check_quota(1, QuotaType.ARTICLES)
        assert available is True

    def test_check_quota_exceeded(self, temp_db):
        """Test checking quota when exceeded."""
        mgr = QuotaManager(temp_db)

        # Fill quota
        conn = sqlite3.connect(temp_db)
        for i in range(100):
            conn.execute("""
                INSERT INTO scraped_data (user_id, title)
                VALUES (1, ?)
            """, (f'Article {i}',))
        conn.commit()
        conn.close()

        # Quota should be exceeded
        available = mgr.check_quota(1, QuotaType.ARTICLES)
        assert available is False

    def test_admin_unlimited_quota(self, temp_db):
        """Test that admin users have unlimited quota."""
        mgr = QuotaManager(temp_db)

        # Admin should have unlimited
        status = mgr.get_quota_status(2, QuotaType.ARTICLES)
        assert status.quota_limit == -1  # -1 indicates unlimited
        assert status.exceeded is False

        # Check should always pass for admin
        available = mgr.check_quota(2, QuotaType.ARTICLES)
        assert available is True

    def test_set_user_quota(self, temp_db):
        """Test setting user quota limits."""
        mgr = QuotaManager(temp_db)

        # Set new quotas
        mgr.set_user_quota(
            user_id=1,
            article_quota=200,
            scraper_quota=20
        )

        # Verify quotas were updated
        conn = sqlite3.connect(temp_db)
        user = conn.execute("""
            SELECT article_quota, scraper_quota
            FROM users WHERE id = 1
        """).fetchone()
        conn.close()

        assert user[0] == 200
        assert user[1] == 20

    def test_set_partial_quota(self, temp_db):
        """Test setting only one quota type."""
        mgr = QuotaManager(temp_db)

        # Set only article quota
        mgr.set_user_quota(user_id=1, article_quota=500)

        conn = sqlite3.connect(temp_db)
        user = conn.execute("""
            SELECT article_quota, scraper_quota
            FROM users WHERE id = 1
        """).fetchone()
        conn.close()

        assert user[0] == 500
        assert user[1] == 10  # Unchanged

    def test_get_all_quotas(self, temp_db):
        """Test getting all quota statuses for user."""
        mgr = QuotaManager(temp_db)

        quotas = mgr.get_all_quotas(user_id=1)

        assert 'articles' in quotas
        assert 'scrapers' in quotas
        assert isinstance(quotas['articles'], QuotaStatus)
        assert isinstance(quotas['scrapers'], QuotaStatus)

    def test_quota_summary(self, temp_db):
        """Test getting system-wide quota summary."""
        mgr = QuotaManager(temp_db)

        # Add articles to user 1 (80% of quota)
        conn = sqlite3.connect(temp_db)
        for i in range(80):
            conn.execute("""
                INSERT INTO scraped_data (user_id, title)
                VALUES (1, ?)
            """, (f'Article {i}',))
        conn.commit()
        conn.close()

        summary = mgr.get_quota_summary()

        assert 'articles' in summary
        assert 'scrapers' in summary
        assert 'near_limit' in summary['articles']
        assert 'exceeded' in summary['articles']

        # User 1 should be in near_limit (>80%)
        near_limit_users = summary['articles']['near_limit']
        assert len(near_limit_users) > 0

    def test_nonexistent_user(self, temp_db):
        """Test quota check for nonexistent user."""
        mgr = QuotaManager(temp_db)

        with pytest.raises(ValueError, match="not found"):
            mgr.get_quota_status(999, QuotaType.ARTICLES)

    def test_zero_quota(self, temp_db):
        """Test behavior with zero quota."""
        mgr = QuotaManager(temp_db)

        # Set quota to 0
        conn = sqlite3.connect(temp_db)
        conn.execute("""
            UPDATE users SET article_quota = 0 WHERE id = 1
        """)
        conn.commit()
        conn.close()

        status = mgr.get_quota_status(1, QuotaType.ARTICLES)
        assert status.quota_limit == 0
        assert status.remaining == 0
        assert status.exceeded is True  # 0 usage >= 0 limit


class TestQuotaType:
    """Test QuotaType enum."""

    def test_quota_types(self):
        """Test quota type enum values."""
        assert QuotaType.ARTICLES.value == 'articles'
        assert QuotaType.SCRAPERS.value == 'scrapers'


class TestQuotaStatus:
    """Test QuotaStatus dataclass."""

    def test_quota_status_structure(self):
        """Test QuotaStatus data structure."""
        status = QuotaStatus(
            quota_type='articles',
            current_usage=50,
            quota_limit=100,
            remaining=50,
            percentage_used=50.0,
            exceeded=False
        )

        assert status.quota_type == 'articles'
        assert status.current_usage == 50
        assert status.quota_limit == 100
        assert status.remaining == 50
        assert status.percentage_used == 50.0
        assert status.exceeded is False


class TestQuotaConfig:
    """Test QuotaConfig dataclass."""

    def test_default_config(self):
        """Test default quota configuration."""
        config = QuotaConfig()
        assert config.default_article_quota == 10000
        assert config.default_scraper_quota == 100
        assert config.admin_unlimited is True

    def test_custom_config(self):
        """Test custom quota configuration."""
        config = QuotaConfig(
            default_article_quota=5000,
            default_scraper_quota=50,
            admin_unlimited=False
        )
        assert config.default_article_quota == 5000
        assert config.default_scraper_quota == 50
        assert config.admin_unlimited is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
