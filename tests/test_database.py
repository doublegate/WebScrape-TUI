#!/usr/bin/env python3
"""Database operation tests for WebScrape-TUI."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

# Import from monolithic scrapetui.py using importlib.util
import importlib.util

_scrapetui_path = Path(__file__).parent.parent / 'scrapetui.py'
_spec = importlib.util.spec_from_file_location("scrapetui_monolith", _scrapetui_path)
_scrapetui_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scrapetui_module)


@pytest.fixture
def temp_db_path():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def initialized_db(temp_db_path, monkeypatch):
    """Create and initialize a test database."""
    # Use monkeypatch to override DB_PATH in monolithic module
    monkeypatch.setattr(_scrapetui_module, 'DB_PATH', temp_db_path)

    # Initialize database with the patched path
    _scrapetui_module.init_db()

    yield temp_db_path


class TestDatabaseInitialization:
    """Test database initialization and schema creation."""

    def test_database_file_created(self, temp_db_path, monkeypatch):
        """Test that database file is created."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import scrapetui

        # Use monkeypatch to override DB_PATH
        monkeypatch.setattr(scrapetui, 'DB_PATH', temp_db_path)

        from scrapetui import init_db
        assert init_db() is True
        assert temp_db_path.exists()

    def test_scraped_data_table_exists(self, initialized_db):
        """Test that scraped_data table is created."""
        with sqlite3.connect(initialized_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name='scraped_data'"
            )
            result = cursor.fetchone()
            assert result is not None

    def test_tags_table_exists(self, initialized_db):
        """Test that tags table is created."""
        with sqlite3.connect(initialized_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name='tags'"
            )
            result = cursor.fetchone()
            assert result is not None

    def test_article_tags_table_exists(self, initialized_db):
        """Test that article_tags junction table is created."""
        with sqlite3.connect(initialized_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name='article_tags'"
            )
            result = cursor.fetchone()
            assert result is not None

    def test_saved_scrapers_table_exists(self, initialized_db):
        """Test that saved_scrapers table is created."""
        with sqlite3.connect(initialized_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name='saved_scrapers'"
            )
            result = cursor.fetchone()
            assert result is not None

    def test_indexes_created(self, initialized_db):
        """Test that indexes are created for performance."""
        with sqlite3.connect(initialized_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            indexes = [row[0] for row in cursor.fetchall()]
            # SQLite creates automatic indexes for PRIMARY KEY and UNIQUE
            assert len(indexes) > 0


class TestArticleOperations:
    """Test article CRUD operations."""

    def test_insert_article(self, initialized_db):
        """Test inserting an article into the database."""
        with sqlite3.connect(initialized_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                INSERT INTO scraped_data (url, title, link)
                VALUES (?, ?, ?)
                """,
                ('https://example.com', 'Test Article', 'https://example.com/test')
            )
            conn.commit()
            article_id = cursor.lastrowid

            # Verify insertion
            cursor = conn.execute(
                "SELECT * FROM scraped_data WHERE id = ?",
                (article_id,)
            )
            article = cursor.fetchone()
            assert article is not None
            assert article['title'] == 'Test Article'
            assert article['url'] == 'https://example.com'
            assert article['link'] == 'https://example.com/test'

    def test_duplicate_url_constraint(self, initialized_db):
        """Test that duplicate link URLs are prevented by UNIQUE constraint."""
        with sqlite3.connect(initialized_db) as conn:
            conn.execute(
                """
                INSERT INTO scraped_data (url, title, link)
                VALUES (?, ?, ?)
                """,
                ('https://example.com', 'Test 1', 'https://example.com/test')
            )
            conn.commit()

            # Attempt to insert duplicate link - should fail
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO scraped_data (url, title, link)
                    VALUES (?, ?, ?)
                    """,
                    ('https://example.com', 'Test 2', 'https://example.com/test')
                )
                conn.commit()

    def test_update_article_summary(self, initialized_db):
        """Test updating article with AI-generated summary."""
        with sqlite3.connect(initialized_db) as conn:
            conn.row_factory = sqlite3.Row

            # Insert article
            cursor = conn.execute(
                """
                INSERT INTO scraped_data (url, title, link)
                VALUES (?, ?, ?)
                """,
                ('https://example.com', 'Test Article', 'https://example.com/test')
            )
            conn.commit()
            article_id = cursor.lastrowid

            # Update with summary and sentiment
            conn.execute(
                """
                UPDATE scraped_data
                SET summary = ?, sentiment = ?
                WHERE id = ?
                """,
                ('Test summary', 'Positive', article_id)
            )
            conn.commit()

            # Verify update
            cursor = conn.execute(
                "SELECT * FROM scraped_data WHERE id = ?",
                (article_id,)
            )
            article = cursor.fetchone()
            assert article['summary'] == 'Test summary'
            assert article['sentiment'] == 'Positive'


class TestTagOperations:
    """Test tag management operations."""

    def test_insert_tag(self, initialized_db):
        """Test inserting a tag."""
        with sqlite3.connect(initialized_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "INSERT INTO tags (name) VALUES (?)",
                ('python',)
            )
            conn.commit()
            tag_id = cursor.lastrowid

            # Verify insertion
            cursor = conn.execute(
                "SELECT * FROM tags WHERE id = ?",
                (tag_id,)
            )
            tag = cursor.fetchone()
            assert tag is not None
            assert tag['name'] == 'python'

    def test_article_tag_association(self, initialized_db):
        """Test associating tags with articles."""
        with sqlite3.connect(initialized_db) as conn:
            conn.row_factory = sqlite3.Row

            # Create article
            cursor = conn.execute(
                """
                INSERT INTO scraped_data (url, title, link)
                VALUES (?, ?, ?)
                """,
                ('https://example.com', 'Test', 'https://example.com/test')
            )
            article_id = cursor.lastrowid

            # Create tag
            cursor = conn.execute(
                "INSERT INTO tags (name) VALUES (?)",
                ('python',)
            )
            tag_id = cursor.lastrowid
            conn.commit()

            # Associate tag with article
            conn.execute(
                """
                INSERT INTO article_tags (article_id, tag_id)
                VALUES (?, ?)
                """,
                (article_id, tag_id)
            )
            conn.commit()

            # Verify association
            cursor = conn.execute(
                """
                SELECT t.name FROM tags t
                JOIN article_tags at ON t.id = at.tag_id
                WHERE at.article_id = ?
                """,
                (article_id,)
            )
            tags = [row['name'] for row in cursor.fetchall()]
            assert 'python' in tags

    def test_get_articles_by_tag(self, initialized_db):
        """Test retrieving articles by tag."""
        with sqlite3.connect(initialized_db) as conn:
            conn.row_factory = sqlite3.Row

            # Create articles
            cursor = conn.execute(
                """
                INSERT INTO scraped_data (url, title, link)
                VALUES (?, ?, ?)
                """,
                ('https://example.com', 'Python Article', 'https://example.com/python1')
            )
            python_article_id = cursor.lastrowid

            cursor = conn.execute(
                """
                INSERT INTO scraped_data (url, title, link)
                VALUES (?, ?, ?)
                """,
                ('https://example.com', 'Rust Article', 'https://example.com/rust1')
            )
            rust_article_id = cursor.lastrowid

            # Create tags
            cursor = conn.execute(
                "INSERT INTO tags (name) VALUES (?)",
                ('python',)
            )
            python_tag_id = cursor.lastrowid

            cursor = conn.execute(
                "INSERT INTO tags (name) VALUES (?)",
                ('rust',)
            )
            rust_tag_id = cursor.lastrowid
            conn.commit()

            # Associate tags
            conn.execute(
                """
                INSERT INTO article_tags (article_id, tag_id)
                VALUES (?, ?)
                """,
                (python_article_id, python_tag_id)
            )
            conn.execute(
                """
                INSERT INTO article_tags (article_id, tag_id)
                VALUES (?, ?)
                """,
                (rust_article_id, rust_tag_id)
            )
            conn.commit()

            # Query articles by tag
            cursor = conn.execute(
                """
                SELECT a.* FROM scraped_data a
                JOIN article_tags at ON a.id = at.article_id
                JOIN tags t ON at.tag_id = t.id
                WHERE t.name = ?
                """,
                ('python',)
            )
            articles = cursor.fetchall()
            assert len(articles) == 1
            assert articles[0]['title'] == 'Python Article'


class TestScraperProfiles:
    """Test scraper profile management."""

    def test_insert_scraper_profile(self, initialized_db):
        """Test inserting a scraper profile."""
        with sqlite3.connect(initialized_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                INSERT INTO saved_scrapers
                (name, url, selector, default_limit, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    'Test Scraper',
                    'https://example.com',
                    'article',
                    10,
                    'Test description'
                )
            )
            conn.commit()
            scraper_id = cursor.lastrowid

            # Verify insertion
            cursor = conn.execute(
                "SELECT * FROM saved_scrapers WHERE id = ?",
                (scraper_id,)
            )
            scraper = cursor.fetchone()
            assert scraper is not None
            assert scraper['name'] == 'Test Scraper'
            assert scraper['url'] == 'https://example.com'
            assert scraper['selector'] == 'article'

    def test_list_all_scrapers(self, initialized_db):
        """Test retrieving all scraper profiles."""
        with sqlite3.connect(initialized_db) as conn:
            conn.row_factory = sqlite3.Row

            # Insert multiple scrapers
            for i in range(3):
                conn.execute(
                    """
                    INSERT INTO saved_scrapers
                    (name, url, selector, default_limit)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        f'Scraper {i}',
                        f'https://example{i}.com',
                        'article',
                        10
                    )
                )
            conn.commit()

            # Retrieve only our test scrapers (not pre-installed ones)
            cursor = conn.execute(
                "SELECT * FROM saved_scrapers WHERE is_preinstalled = 0 ORDER BY name"
            )
            scrapers = cursor.fetchall()
            assert len(scrapers) == 3
            assert scrapers[0]['name'] == 'Scraper 0'
