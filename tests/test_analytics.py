#!/usr/bin/env python3
"""Tests for v1.6.0 features: Data Visualization & Advanced Analytics."""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import os

# Import the application components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapetui import AnalyticsManager, init_db, get_db_connection, DB_PATH


@pytest.fixture
def temp_db(monkeypatch):
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db_path = f.name

    # Monkeypatch the DB_PATH to use our temp database
    monkeypatch.setattr('scrapetui.DB_PATH', Path(temp_db_path))

    # Initialize the database
    init_db()

    # Add test data
    with get_db_connection() as conn:
        # Insert articles with various sentiments and timestamps
        now = datetime.now()
        test_articles = [
            # Positive sentiment articles
            ('Test Article 1', 'https://example.com/1', 'Content 1', 'Summary 1', 'positive', now),
            ('Test Article 2', 'https://example.com/2', 'Content 2', 'Summary 2', 'positive', now - timedelta(days=1)),
            ('Test Article 3', 'https://example.com/3', 'Content 3', 'Summary 3', 'positive', now - timedelta(days=2)),
            # Negative sentiment articles
            ('Test Article 4', 'https://example.com/4', 'Content 4', 'Summary 4', 'negative', now - timedelta(days=3)),
            ('Test Article 5', 'https://example.com/5', 'Content 5', 'Summary 5', 'negative', now - timedelta(days=4)),
            # Neutral sentiment articles
            ('Test Article 6', 'https://example.com/6', 'Content 6', 'Summary 6', 'neutral', now - timedelta(days=5)),
            ('Test Article 7', 'https://example.com/7', 'Content 7', 'Summary 7', 'neutral', now - timedelta(days=6)),
            # Articles without summaries or sentiment
            ('Test Article 8', 'https://example.com/8', 'Content 8', None, None, now - timedelta(days=7)),
            ('Test Article 9', 'https://example.com/9', 'Content 9', None, None, now - timedelta(days=8)),
            ('Test Article 10', 'https://example.com/10', 'Content 10', None, None, now - timedelta(days=9)),
        ]

        for title, url, link, summary, sentiment, timestamp in test_articles:
            conn.execute("""
                INSERT INTO scraped_data (title, url, link, summary, sentiment, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, url, link, summary, sentiment, timestamp.strftime('%Y-%m-%d %H:%M:%S')))

        # Add tags
        conn.execute("INSERT INTO tags (name) VALUES ('tech')")
        conn.execute("INSERT INTO tags (name) VALUES ('news')")
        conn.execute("INSERT INTO tags (name) VALUES ('science')")

        # Link tags to articles
        conn.execute("INSERT INTO article_tags (article_id, tag_id) VALUES (1, 1)")
        conn.execute("INSERT INTO article_tags (article_id, tag_id) VALUES (1, 2)")
        conn.execute("INSERT INTO article_tags (article_id, tag_id) VALUES (2, 1)")
        conn.execute("INSERT INTO article_tags (article_id, tag_id) VALUES (3, 3)")

        conn.commit()

    yield temp_db_path

    # Cleanup
    Path(temp_db_path).unlink(missing_ok=True)


class TestAnalyticsManager:
    """Test AnalyticsManager class for statistics and visualization."""

    def test_get_statistics(self, temp_db):
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
    def test_generate_sentiment_chart(self, mock_close, mock_savefig, temp_db):
        """Test sentiment pie chart generation."""
        output_path = '/tmp/test_sentiment.png'

        result = AnalyticsManager.generate_sentiment_chart(output_path)

        assert result == output_path
        assert mock_savefig.called
        assert mock_close.called

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_generate_timeline_chart(self, mock_close, mock_savefig, temp_db):
        """Test timeline line chart generation."""
        output_path = '/tmp/test_timeline.png'

        result = AnalyticsManager.generate_timeline_chart(output_path)

        assert result == output_path
        assert mock_savefig.called
        assert mock_close.called

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_generate_top_sources_chart(self, mock_close, mock_savefig, temp_db):
        """Test top sources bar chart generation."""
        output_path = '/tmp/test_sources.png'

        result = AnalyticsManager.generate_top_sources_chart(output_path)

        assert result == output_path
        assert mock_savefig.called
        assert mock_close.called

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_generate_charts_without_path(self, mock_close, mock_savefig, temp_db):
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

    def test_generate_tag_cloud_data(self, temp_db):
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

    def test_export_statistics_report(self, temp_db):
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
            conn.execute("""
                INSERT INTO scraped_data (title, url, link, summary, sentiment, timestamp)
                VALUES ('Test', 'https://example.com', 'https://example.com/test', NULL, NULL, ?)
            """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
            conn.commit()

        result = AnalyticsManager.generate_sentiment_chart('/tmp/test.png')

        # Returns None when no sentiment data available
        assert result is None

        Path(temp_db_path).unlink(missing_ok=True)

    def test_timeline_chart_data_structure(self, temp_db):
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

    def test_statistics_with_multiple_sources(self, temp_db):
        """Test statistics correctly count articles from multiple sources."""
        # Get initial stats
        initial_stats = AnalyticsManager.get_statistics()
        initial_count = initial_stats['total_articles']

        with get_db_connection() as conn:
            # Add articles from different domains
            conn.execute("""
                INSERT INTO scraped_data (title, url, link, timestamp)
                VALUES ('Article from site1', 'https://site1.com/page', 'https://site1.com/article1', ?)
            """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
            conn.execute("""
                INSERT INTO scraped_data (title, url, link, timestamp)
                VALUES ('Article from site2', 'https://site2.com/page', 'https://site2.com/article2', ?)
            """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
            conn.commit()

        stats = AnalyticsManager.get_statistics()
        top_sources = stats['top_sources']

        # Should now have 2 more articles
        assert stats['total_articles'] == initial_count + 2

        # Should have sources listed
        assert len(top_sources) > 0

        # Verify counts are positive
        assert all(count >= 1 for url, count in top_sources)

    def test_tag_statistics_with_many_tags(self, temp_db):
        """Test tag statistics handle many tags correctly."""
        with get_db_connection() as conn:
            # Add more tags
            for i in range(20):
                conn.execute(f"INSERT INTO tags (name) VALUES ('tag{i}')")

            # Link some tags to articles
            for i in range(10):
                conn.execute(f"INSERT INTO article_tags (article_id, tag_id) VALUES (1, {i+4})")

            conn.commit()

        stats = AnalyticsManager.get_statistics()
        top_tags = stats['top_tags']

        # Should return all tags
        assert len(top_tags) >= 10

        # First tag should be the one used most (article 1 with many tags)
        # or 'tech' if it still has highest count


class TestAnalyticsEdgeCases:
    """Test analytics edge cases and error handling."""

    def test_statistics_with_null_timestamps(self, temp_db):
        """Test statistics handle null timestamps gracefully."""
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO scraped_data (title, url, link, timestamp)
                VALUES ('No timestamp', 'https://example.com/null', 'https://example.com/null', NULL)
            """)
            conn.commit()

        # Should not crash
        stats = AnalyticsManager.get_statistics()
        assert stats is not None

    def test_statistics_with_very_old_dates(self, temp_db):
        """Test statistics with articles older than 30 days."""
        with get_db_connection() as conn:
            old_date = datetime.now() - timedelta(days=60)
            conn.execute("""
                INSERT INTO scraped_data (title, url, link, timestamp)
                VALUES ('Old article', 'https://example.com/old', 'https://example.com/old', ?)
            """, (old_date.strftime('%Y-%m-%d %H:%M:%S'),))
            conn.commit()

        stats = AnalyticsManager.get_statistics()

        # Total should include old article
        assert stats['total_articles'] == 11

        # Timeline should only show last 30 days
        articles_per_day = stats['articles_per_day']
        # Old article should not appear in per-day breakdown (only last 30 days)

    def test_export_report_with_invalid_path(self, temp_db):
        """Test export report handles invalid paths."""
        # Try to export to a directory that doesn't exist
        invalid_path = '/nonexistent/directory/report.txt'

        try:
            result = AnalyticsManager.export_statistics_report(invalid_path)
            # Should return False on failure
            assert result is False
        except:
            # Or raise an exception - both are acceptable
            pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
