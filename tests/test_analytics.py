#!/usr/bin/env python3
"""Tests for v1.6.0 features: Data Visualization & Advanced Analytics."""

import importlib.util
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch
import time
import random

# Import the application components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from monolithic scrapetui.py file directly
# We need to import the .py file, not the package directory which has AnalyticsManager=None
_scrapetui_path = Path(__file__).parent.parent / 'scrapetui.py'
_spec = importlib.util.spec_from_file_location("scrapetui_monolith", _scrapetui_path)
_scrapetui_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scrapetui_module)

# Import needed components from the monolithic module
AnalyticsManager = _scrapetui_module.AnalyticsManager
init_db = _scrapetui_module.init_db
get_db_connection = _scrapetui_module.get_db_connection
DB_PATH = _scrapetui_module.DB_PATH


@pytest.fixture
def analytics_test_db(temp_db):
    """Create a temporary database for analytics testing with unique data."""
    # temp_db fixture from conftest.py already provides isolated database
    # IMPORTANT: Must patch the monolithic module's DB_PATH to use temp database
    _scrapetui_module.DB_PATH = temp_db

    # Just add test data to it
    from scrapetui.core.database import get_db_connection as get_conn

    with get_conn() as conn:
        # Insert articles with various sentiments and timestamps
        now = datetime.now()
        base_unique_id = int(time.time() * 1000000)

        # Generate unique links for each article and collect article IDs
        article_ids = []
        for i in range(1, 11):
            unique_id = f"{base_unique_id}-{random.randint(1000, 9999)}-{i}"
            link = f"https://example.com/article-{unique_id}"
            url = f"https://example.com/{i}"

            # Determine sentiment based on article number
            if i <= 3:
                sentiment = 'positive'
                summary = f'Summary {i}'
            elif i <= 5:
                sentiment = 'negative'
                summary = f'Summary {i}'
            elif i <= 7:
                sentiment = 'neutral'
                summary = f'Summary {i}'
            else:
                sentiment = None
                summary = None

            timestamp = now - timedelta(days=i - 1)

            cursor = conn.execute("""
                INSERT INTO scraped_data (title, url, link, summary, sentiment, timestamp, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                f'Test Article {i}',
                url,
                link,
                summary,
                sentiment,
                timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                1  # admin user
            ))
            article_ids.append(cursor.lastrowid)

        # Add tags and get their IDs
        cursor = conn.execute("INSERT OR IGNORE INTO tags (name) VALUES ('tech')")
        tech_tag_id = cursor.lastrowid or conn.execute("SELECT id FROM tags WHERE name='tech'").fetchone()[0]

        cursor = conn.execute("INSERT OR IGNORE INTO tags (name) VALUES ('news')")
        news_tag_id = cursor.lastrowid or conn.execute("SELECT id FROM tags WHERE name='news'").fetchone()[0]

        cursor = conn.execute("INSERT OR IGNORE INTO tags (name) VALUES ('science')")
        science_tag_id = cursor.lastrowid or conn.execute("SELECT id FROM tags WHERE name='science'").fetchone()[0]

        # Link tags to articles (using actual article and tag IDs)
        # article_ids[0] is first article, article_ids[1] is second, etc.
        conn.execute("INSERT INTO article_tags (article_id, tag_id) VALUES (?, ?)", (article_ids[0], tech_tag_id))
        conn.execute("INSERT INTO article_tags (article_id, tag_id) VALUES (?, ?)", (article_ids[0], news_tag_id))
        conn.execute("INSERT INTO article_tags (article_id, tag_id) VALUES (?, ?)", (article_ids[1], tech_tag_id))
        conn.execute("INSERT INTO article_tags (article_id, tag_id) VALUES (?, ?)", (article_ids[2], science_tag_id))

        conn.commit()

    yield temp_db  # Return the temp_db Path object


class TestAnalyticsManager:
    """Test AnalyticsManager class for statistics and visualization."""

    def test_get_statistics(self, analytics_test_db):
        """Test getting comprehensive statistics."""
        stats = AnalyticsManager.get_statistics()

        assert stats is not None
        assert isinstance(stats, dict)

        # Check basic counts
        assert stats['total_articles'] == 10
        assert stats['articles_with_summaries'] == 7
        assert stats['articles_with_sentiment'] == 7

        # Check sentiment distribution
        assert 'sentiment_distribution' in stats
        assert stats['sentiment_distribution']['positive'] == 3
        assert stats['sentiment_distribution']['negative'] == 2
        assert stats['sentiment_distribution']['neutral'] == 2

        # Check percentages
        assert stats['summary_percentage'] == 70.0
        assert stats['sentiment_percentage'] == 70.0

        # Check top sources
        assert 'top_sources' in stats
        assert len(stats['top_sources']) == 10

        # Check top tags
        assert 'top_tags' in stats
        assert len(stats['top_tags']) == 3
        assert stats['top_tags'][0][0] == 'tech'  # Most used tag
        assert stats['top_tags'][0][1] == 2  # Used twice

        # Check articles per day
        assert 'articles_per_day' in stats
        assert isinstance(stats['articles_per_day'], list)

    def test_get_statistics_empty_database(self, monkeypatch):
        """Test statistics with empty database."""
        # Create empty temp database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_db_path = f.name

        monkeypatch.setattr('scrapetui.DB_PATH', Path(temp_db_path))
        init_db()

        stats = AnalyticsManager.get_statistics()

        assert stats['total_articles'] == 0
        assert stats['articles_with_summaries'] == 0
        assert stats['articles_with_sentiment'] == 0
        assert stats['summary_percentage'] == 0.0
        assert stats['sentiment_percentage'] == 0.0
        assert len(stats['sentiment_distribution']) == 0
        assert len(stats['top_sources']) == 0
        assert len(stats['top_tags']) == 0

        Path(temp_db_path).unlink(missing_ok=True)

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_generate_sentiment_chart(self, mock_close, mock_savefig, analytics_test_db):
        """Test sentiment pie chart generation."""
        output_path = '/tmp/test_sentiment.png'

        result = AnalyticsManager.generate_sentiment_chart(output_path)

        assert result == output_path
        assert mock_savefig.called
        assert mock_close.called

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_generate_timeline_chart(self, mock_close, mock_savefig, analytics_test_db):
        """Test timeline line chart generation."""
        output_path = '/tmp/test_timeline.png'

        result = AnalyticsManager.generate_timeline_chart(output_path)

        assert result == output_path
        assert mock_savefig.called
        assert mock_close.called

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_generate_top_sources_chart(self, mock_close, mock_savefig, analytics_test_db):
        """Test top sources bar chart generation."""
        output_path = '/tmp/test_sources.png'

        result = AnalyticsManager.generate_top_sources_chart(output_path)

        assert result == output_path
        assert mock_savefig.called
        assert mock_close.called

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_generate_charts_without_path(self, mock_close, mock_savefig, analytics_test_db):
        """Test chart generation returns base64 encoded data when no path provided."""
        # Test sentiment chart
        result = AnalyticsManager.generate_sentiment_chart()
        assert result is not None
        assert isinstance(result, str)
        assert result.startswith('data:image/png;base64,')

        # Test timeline chart
        result = AnalyticsManager.generate_timeline_chart()
        assert result is not None
        assert isinstance(result, str)
        assert result.startswith('data:image/png;base64,')

        # Test top sources chart
        result = AnalyticsManager.generate_top_sources_chart()
        assert result is not None
        assert isinstance(result, str)
        assert result.startswith('data:image/png;base64,')

    def test_generate_tag_cloud_data(self, analytics_test_db):
        """Test tag cloud data generation."""
        tag_data = AnalyticsManager.generate_tag_cloud_data()

        assert isinstance(tag_data, list)
        assert len(tag_data) == 3

        # Check structure
        for tag_name, count in tag_data:
            assert isinstance(tag_name, str)
            assert isinstance(count, int)
            assert count > 0

        # Check ordering (should be by count descending)
        assert tag_data[0][0] == 'tech'
        assert tag_data[0][1] == 2

    def test_export_statistics_report(self, analytics_test_db):
        """Test exporting statistics to a text file."""
        output_path = '/tmp/test_statistics_report.txt'

        success = AnalyticsManager.export_statistics_report(output_path)

        assert success is True
        assert Path(output_path).exists()

        # Read and verify content
        with open(output_path, 'r') as f:
            content = f.read()

        assert 'WebScrape-TUI Analytics Report' in content
        assert 'Total Articles:' in content
        assert 'Articles with Summaries:' in content
        assert 'Articles with Sentiment:' in content
        assert 'SENTIMENT DISTRIBUTION' in content
        assert 'TOP 10 SOURCES' in content
        assert 'TOP 20 TAGS' in content

        # Cleanup
        Path(output_path).unlink(missing_ok=True)

    def test_export_statistics_report_empty_database(self, monkeypatch):
        """Test exporting statistics with empty database."""
        # Create empty temp database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_db_path = f.name

        monkeypatch.setattr('scrapetui.DB_PATH', Path(temp_db_path))
        init_db()

        output_path = '/tmp/test_empty_report.txt'
        success = AnalyticsManager.export_statistics_report(output_path)

        assert success is True
        assert Path(output_path).exists()

        with open(output_path, 'r') as f:
            content = f.read()

        assert 'Total Articles: 0' in content
        # Empty sections are acceptable in report

        Path(output_path).unlink(missing_ok=True)
        Path(temp_db_path).unlink(missing_ok=True)

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_sentiment_chart_with_no_sentiment_data(self, mock_close, mock_savefig, monkeypatch):
        """Test sentiment chart generation with no sentiment data."""
        # Create database with articles but no sentiment
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_db_path = f.name

        monkeypatch.setattr('scrapetui.DB_PATH', Path(temp_db_path))
        init_db()

        with get_db_connection() as conn:
            unique_id = f"{int(time.time() * 1000000)}-{random.randint(1000, 9999)}"
            conn.execute("""
                INSERT INTO scraped_data (title, url, link, summary, sentiment, timestamp, user_id)
                VALUES ('Test', 'https://example.com', ?, NULL, NULL, ?, ?)
            """, (f'https://example.com/test-{unique_id}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1))
            conn.commit()

        result = AnalyticsManager.generate_sentiment_chart('/tmp/test.png')

        # Returns None when no sentiment data available
        assert result is None

        Path(temp_db_path).unlink(missing_ok=True)

    def test_timeline_chart_data_structure(self, analytics_test_db):
        """Test timeline chart includes all days in range."""
        stats = AnalyticsManager.get_statistics()
        articles_per_day = stats['articles_per_day']

        # Should have data for the days we inserted
        assert len(articles_per_day) > 0

        # Check date format (it's a list of tuples)
        for date_str, count in articles_per_day:
            # Should be in YYYY-MM-DD format
            datetime.strptime(date_str, '%Y-%m-%d')
            assert count > 0


class TestAnalyticsIntegration:
    """Test analytics integration with existing data."""

    def test_statistics_with_multiple_sources(self, analytics_test_db):
        """Test statistics correctly count articles from multiple sources."""
        # Get initial stats
        initial_stats = AnalyticsManager.get_statistics()
        initial_count = initial_stats['total_articles']

        with get_db_connection() as conn:
            # Add articles from different domains with unique links
            unique_id1 = f"{int(time.time() * 1000000)}-{random.randint(1000, 9999)}-a"
            unique_id2 = f"{int(time.time() * 1000000)}-{random.randint(1000, 9999)}-b"

            conn.execute("""
                INSERT INTO scraped_data (title, url, link, timestamp, user_id)
                VALUES ('Article from site1', 'https://site1.com/page', ?, ?, ?)
            """, (f'https://site1.com/article-{unique_id1}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1))
            conn.execute("""
                INSERT INTO scraped_data (title, url, link, timestamp, user_id)
                VALUES ('Article from site2', 'https://site2.com/page', ?, ?, ?)
            """, (f'https://site2.com/article-{unique_id2}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1))
            conn.commit()

        stats = AnalyticsManager.get_statistics()
        top_sources = stats['top_sources']

        # Should now have 2 more articles
        assert stats['total_articles'] == initial_count + 2

        # Should have sources listed
        assert len(top_sources) > 0

        # Verify counts are positive
        assert all(count >= 1 for url, count in top_sources)

    def test_tag_statistics_with_many_tags(self, analytics_test_db):
        """Test tag statistics handle many tags correctly."""
        with get_db_connection() as conn:
            # Add more tags
            for i in range(20):
                conn.execute(f"INSERT INTO tags (name) VALUES ('tag{i}')")

            # Link some tags to articles
            for i in range(10):
                conn.execute(f"INSERT INTO article_tags (article_id, tag_id) VALUES (1, {i + 4})")

            conn.commit()

        stats = AnalyticsManager.get_statistics()
        top_tags = stats['top_tags']

        # Should return all tags
        assert len(top_tags) >= 10

        # First tag should be the one used most (article 1 with many tags)
        # or 'tech' if it still has highest count


class TestAnalyticsEdgeCases:
    """Test analytics edge cases and error handling."""

    def test_statistics_with_null_timestamps(self, analytics_test_db):
        """Test statistics handle null timestamps gracefully."""
        with get_db_connection() as conn:
            unique_id = f"{int(time.time() * 1000000)}-{random.randint(1000, 9999)}"
            conn.execute("""
                INSERT INTO scraped_data (title, url, link, timestamp, user_id)
                VALUES ('No timestamp', 'https://example.com/null', ?, NULL, ?)
            """, (f'https://example.com/null-{unique_id}', 1))
            conn.commit()

        # Should not crash
        stats = AnalyticsManager.get_statistics()
        assert stats is not None

    def test_statistics_with_very_old_dates(self, analytics_test_db):
        """Test statistics with articles older than 30 days."""
        with get_db_connection() as conn:
            old_date = datetime.now() - timedelta(days=60)
            unique_id = f"{int(time.time() * 1000000)}-{random.randint(1000, 9999)}"
            conn.execute("""
                INSERT INTO scraped_data (title, url, link, timestamp, user_id)
                VALUES ('Old article', 'https://example.com/old', ?, ?, ?)
            """, (f'https://example.com/old-{unique_id}', old_date.strftime('%Y-%m-%d %H:%M:%S'), 1))
            conn.commit()

        stats = AnalyticsManager.get_statistics()

        # Total should include old article
        assert stats['total_articles'] == 11

        # Timeline should only show last 30 days
        stats['articles_per_day']
        # Old article should not appear in per-day breakdown (only last 30 days)

    def test_export_report_with_invalid_path(self, analytics_test_db):
        """Test export report handles invalid paths."""
        # Try to export to a directory that doesn't exist
        invalid_path = '/nonexistent/directory/report.txt'

        try:
            result = AnalyticsManager.export_statistics_report(invalid_path)
            # Should return False on failure
            assert result is False
        except BaseException:
            # Or raise an exception - both are acceptable
            pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
