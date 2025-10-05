"""Performance tests for multi-user scenarios.

This module contains performance tests to ensure WebScrape-TUI v2.0.0
performs well under multi-user workloads with realistic data volumes.

Test Categories:
- Article query performance with data isolation
- Scraper loading with mixed shared/private profiles
- Session validation performance
- Multi-user concurrent operations

Target Performance Metrics:
- Article queries: < 100ms for filtered results
- Scraper loading: < 50ms for 50+ profiles
- Session validation: < 10ms per check
- Database operations: < 200ms for complex queries
"""

from pathlib import Path
import importlib.util
import pytest
import time
from typing import List
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from monolithic scrapetui.py file directly
# We need to import the .py file, not the package directory

_scrapetui_path = Path(__file__).parent.parent / 'scrapetui.py'
_spec = importlib.util.spec_from_file_location("scrapetui_monolith", _scrapetui_path)
_scrapetui_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scrapetui_module)

# Import needed components from the monolithic module
get_db_connection = _scrapetui_module.get_db_connection
init_db = _scrapetui_module.init_db
hash_password = _scrapetui_module.hash_password
create_user_session = _scrapetui_module.create_user_session
validate_session = _scrapetui_module.validate_session
db_datetime_now = _scrapetui_module.db_datetime_now
db_datetime_future = _scrapetui_module.db_datetime_future


@pytest.fixture
def perf_test_db(tmp_path):
    """Create a temporary database for performance testing."""
    db_path = tmp_path / "perf_test.db"

    # Patch the monolithic module's DB_PATH to use temp database
    original_db = _scrapetui_module.DB_PATH
    _scrapetui_module.DB_PATH = Path(db_path)

    init_db()

    yield str(db_path)

    # Restore original
    _scrapetui_module.DB_PATH = original_db


def create_test_users(count: int = 10) -> List[int]:
    """Create multiple test users and return their IDs."""
    import random
    user_ids = []
    # Generate unique base ID for this test run
    base_unique_id = int(time.time() * 1000000)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        for i in range(count):
            # Make usernames and emails unique to avoid UNIQUE constraint failures
            unique_id = f"{base_unique_id}_{random.randint(1000, 9999)}_{i}"
            cursor.execute(
                """INSERT INTO users (username, password_hash, email, role, created_at, is_active)
                   VALUES (?, ?, ?, ?, ?, 1)""",
                (
                    f"testuser_{unique_id}",
                    hash_password(f"password{i}"),
                    f"user_{unique_id}@test.com",
                    "user",
                    db_datetime_now(),
                ),
            )
            user_ids.append(cursor.lastrowid)
        conn.commit()
    return user_ids


def create_test_articles(user_id: int, count: int = 100) -> List[int]:
    """Create multiple test articles for a user."""
    import random
    article_ids = []
    # Generate unique base ID for this test run
    base_unique_id = int(time.time() * 1000000)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        for i in range(count):
            # Make links unique to avoid UNIQUE constraint failures
            unique_id = f"{user_id}_{i}_{base_unique_id}_{random.randint(1000, 9999)}"
            cursor.execute(
                """INSERT INTO scraped_data
                   (url, title, link, timestamp, user_id)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    f"http://example.com/article_{unique_id}",
                    f"Test Article {i} by User {user_id}",
                    f"http://example.com/article_{unique_id}",
                    db_datetime_now(),
                    user_id,
                ),
            )
            article_ids.append(cursor.lastrowid)
        conn.commit()
    return article_ids


def create_test_scrapers(user_id: int, count: int = 10, shared: bool = False) -> List[int]:
    """Create test scraper profiles for a user."""
    import random
    import time
    scraper_ids = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for i in range(count):
            # Make unique names to avoid UNIQUE constraint failures
            # Include timestamp and random component for uniqueness
            unique_id = f"{user_id}_{i}_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
            cursor.execute(
                """INSERT INTO saved_scrapers
                   (name, url, selector, is_preinstalled, user_id, is_shared)
                   VALUES (?, ?, ?, 0, ?, ?)""",
                (
                    f"TestScraper_{unique_id}",
                    f"http://example{i}.com",
                    "article, div.content",
                    user_id,
                    1 if shared else 0,
                ),
            )
            scraper_ids.append(cursor.lastrowid)
        conn.commit()
    return scraper_ids


class TestArticleQueryPerformance:
    """Test article query performance with data isolation."""

    def test_article_query_with_1000_articles_multi_user(self, perf_test_db):
        """Test article query performance with 1000+ articles from 10 users."""
        # Create 10 users with 100 articles each (1000 total)
        user_ids = create_test_users(10)
        for user_id in user_ids:
            create_test_articles(user_id, 100)

        # Test query performance for a specific user (data isolation)
        test_user_id = user_ids[5]

        start_time = time.perf_counter()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, link, title, timestamp
                   FROM scraped_data
                   WHERE user_id = ?
                   ORDER BY timestamp DESC
                   LIMIT 50""",
                (test_user_id,),
            )
            results = cursor.fetchall()
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Verify results
        assert len(results) == 50  # Should get 50 most recent
        # Check that all articles belong to test_user_id (link format: article_{user_id}_{i}_{timestamp}_{random})
        assert all(row[1].startswith(f"http://example.com/article_{test_user_id}_") for row in results)

        # Performance assertion: < 100ms for filtered query
        assert elapsed_ms < 100, f"Query took {elapsed_ms:.2f}ms (target: <100ms)"
        print(f"✓ Article query with data isolation: {elapsed_ms:.2f}ms")

    def test_admin_query_all_articles(self, perf_test_db):
        """Test admin query performance (no user_id filter)."""
        # Create 10 users with 100 articles each
        user_ids = create_test_users(10)
        for user_id in user_ids:
            create_test_articles(user_id, 100)

        start_time = time.perf_counter()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, link, title, timestamp
                   FROM scraped_data
                   ORDER BY timestamp DESC
                   LIMIT 50"""
            )
            results = cursor.fetchall()
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Verify results
        assert len(results) == 50

        # Performance assertion: < 100ms even for admin queries
        assert elapsed_ms < 100, f"Admin query took {elapsed_ms:.2f}ms (target: <100ms)"
        print(f"✓ Admin query (all users): {elapsed_ms:.2f}ms")


class TestScraperLoadPerformance:
    """Test scraper loading performance with mixed visibility."""

    def test_scraper_load_50_profiles(self, perf_test_db):
        """Test scraper loading with 50+ profiles (shared + private)."""
        # Create 5 users with 10 scrapers each (25 private + 25 shared)
        user_ids = create_test_users(5)
        for i, user_id in enumerate(user_ids):
            # First user: 10 private scrapers
            # Other users: 5 private + 5 shared
            if i == 0:
                create_test_scrapers(user_id, 10, shared=False)
            else:
                create_test_scrapers(user_id, 5, shared=False)
                create_test_scrapers(user_id, 5, shared=True)

        # Test loading scrapers for first user (should see own + shared from others)
        test_user_id = user_ids[0]

        start_time = time.perf_counter()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, name, url, is_shared, is_preinstalled
                   FROM saved_scrapers
                   WHERE user_id = ? OR is_shared = 1
                   ORDER BY name""",
                (test_user_id,),
            )
            results = cursor.fetchall()
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Verify results: 10 own + 20 shared from others = 30
        assert len(results) == 30

        # Performance assertion: < 50ms for scraper loading
        assert elapsed_ms < 50, f"Scraper load took {elapsed_ms:.2f}ms (target: <50ms)"
        print(f"✓ Scraper loading (50+ profiles): {elapsed_ms:.2f}ms")


class TestSessionValidationPerformance:
    """Test session validation performance."""

    def test_session_validation_speed(self, perf_test_db):
        """Test session validation performance."""
        # Create user and session
        user_ids = create_test_users(1)
        user_id = user_ids[0]
        session_token = create_user_session(user_id)

        # Measure validation time (should be very fast)
        start_time = time.perf_counter()
        validated_user_id = validate_session(session_token)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Verify validation worked
        assert validated_user_id == user_id

        # Performance assertion: < 10ms per validation
        assert elapsed_ms < 10, f"Session validation took {elapsed_ms:.2f}ms (target: <10ms)"
        print(f"✓ Session validation: {elapsed_ms:.2f}ms")

    def test_session_validation_with_100_active_sessions(self, perf_test_db):
        """Test session validation performance with many active sessions."""
        # Create 100 users with active sessions
        user_ids = create_test_users(100)
        sessions = []
        for user_id in user_ids:
            token = create_user_session(user_id)
            sessions.append((user_id, token))

        # Validate middle session
        test_user_id, test_token = sessions[50]

        start_time = time.perf_counter()
        validated_user_id = validate_session(test_token)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert validated_user_id == test_user_id

        # Performance should still be fast even with many sessions
        assert elapsed_ms < 10, f"Validation took {elapsed_ms:.2f}ms with 100 sessions (target: <10ms)"
        print(f"✓ Session validation (100 active sessions): {elapsed_ms:.2f}ms")


class TestComplexQueryPerformance:
    """Test performance of complex multi-table queries."""

    def test_article_with_tags_query(self, perf_test_db):
        """Test performance of article queries with tag filtering."""
        # Create user and articles
        user_ids = create_test_users(1)
        user_id = user_ids[0]
        article_ids = create_test_articles(user_id, 100)

        # Add tags to articles
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Create the tag once (use INSERT OR IGNORE to handle if it already exists)
            cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", ("important",))
            # Get the tag_id
            cursor.execute("SELECT id FROM tags WHERE name = ?", ("important",))
            tag_id = cursor.fetchone()[0]

            # Add tag to first 50 articles
            for article_id in article_ids[:50]:
                cursor.execute(
                    "INSERT INTO article_tags (article_id, tag_id) VALUES (?, ?)",
                    (article_id, tag_id),
                )
            conn.commit()

        # Query articles with "important" tag
        start_time = time.perf_counter()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT DISTINCT sd.id, sd.link, sd.title
                   FROM scraped_data sd
                   JOIN article_tags at ON sd.id = at.article_id
                   JOIN tags t ON at.tag_id = t.id
                   WHERE t.name = ? AND sd.user_id = ?
                   ORDER BY sd.timestamp DESC""",
                ("important", user_id),
            )
            results = cursor.fetchall()
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Verify results
        assert len(results) == 50

        # Performance assertion: < 200ms for complex JOIN query
        assert elapsed_ms < 200, f"Complex query took {elapsed_ms:.2f}ms (target: <200ms)"
        print(f"✓ Complex query with JOINs: {elapsed_ms:.2f}ms")


# Performance summary
def pytest_sessionfinish(session, exitstatus):
    """Print performance summary after all tests."""
    if exitstatus == 0:
        print("\n" + "=" * 70)
        print("Performance Test Summary - All targets met ✓")
        print("=" * 70)
        print("Target Metrics:")
        print("  • Article queries: < 100ms ✓")
        print("  • Scraper loading: < 50ms ✓")
        print("  • Session validation: < 10ms ✓")
        print("  • Complex queries: < 200ms ✓")
        print("=" * 70)
