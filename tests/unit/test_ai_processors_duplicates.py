#!/usr/bin/env python3
"""Tests for Duplicate Detection in AI processors."""

from scrapetui.ai.processors import (
    detect_duplicates,
    detect_duplicates_from_db
)


class TestDuplicateDetection:
    """Test duplicate detection functionality."""

    def test_detect_exact_duplicates(self):
        """Test detection of exact duplicate articles."""
        articles = [
            {'id': 1, 'title': 'Same Title', 'content': 'Same content here.'},
            {'id': 2, 'title': 'Same Title', 'content': 'Same content here.'}
        ]

        duplicates = detect_duplicates(articles, threshold=0.95)

        assert len(duplicates) == 1
        assert duplicates[0]['article1_id'] == 1
        assert duplicates[0]['article2_id'] == 2
        assert duplicates[0]['similarity'] > 0.95

    def test_detect_similar_titles(self):
        """Test detection based on similar titles."""
        articles = [
            {'id': 1, 'title': 'Breaking News: Major Event', 'content': ''},
            {'id': 2, 'title': 'Breaking News: Major Event!', 'content': ''}
        ]

        duplicates = detect_duplicates(articles, threshold=0.85)

        assert len(duplicates) >= 1
        if duplicates:
            assert duplicates[0]['similarity'] > 0.85

    def test_no_duplicates(self):
        """Test with completely different articles."""
        articles = [
            {'id': 1, 'title': 'First Article', 'content': 'First content'},
            {'id': 2, 'title': 'Second Article', 'content': 'Second content'}
        ]

        duplicates = detect_duplicates(articles, threshold=0.9)

        # Should find no duplicates above 90% similarity
        assert len(duplicates) == 0

    def test_empty_articles_list(self):
        """Test with empty articles list."""
        duplicates = detect_duplicates([], threshold=0.85)
        assert duplicates == []

    def test_single_article(self):
        """Test with single article."""
        articles = [
            {'id': 1, 'title': 'Only Article', 'content': 'Only content'}
        ]

        duplicates = detect_duplicates(articles, threshold=0.85)
        assert duplicates == []

    def test_threshold_filtering(self):
        """Test that threshold properly filters results."""
        articles = [
            {'id': 1, 'title': 'News about technology', 'content': 'Tech content'},
            {'id': 2, 'title': 'News about tech', 'content': 'Technology content'}
        ]

        # High threshold - should find fewer/no duplicates
        high_threshold = detect_duplicates(articles, threshold=0.95)

        # Low threshold - should find more duplicates
        low_threshold = detect_duplicates(articles, threshold=0.5)

        # Lower threshold should find at least as many as higher threshold
        assert len(low_threshold) >= len(high_threshold)

    def test_weighted_similarity(self):
        """Test that titles are weighted more than content."""
        articles = [
            {'id': 1, 'title': 'Identical Title', 'content': 'Different content A'},
            {'id': 2, 'title': 'Identical Title', 'content': 'Different content B'}
        ]

        duplicates = detect_duplicates(articles, threshold=0.70)

        # Should find duplicate due to identical titles (weighted 60%)
        assert len(duplicates) >= 1

    def test_content_similarity(self):
        """Test detection based on content similarity."""
        articles = [
            {
                'id': 1,
                'title': 'Different A',
                'content': 'This is a long piece of content about artificial intelligence.'
            },
            {
                'id': 2,
                'title': 'Different B',
                'content': 'This is a long piece of content about artificial intelligence.'
            }
        ]

        duplicates = detect_duplicates(articles, threshold=0.60)

        # Should find duplicate due to identical content (weighted 40%)
        assert len(duplicates) >= 1

    def test_missing_content_fields(self):
        """Test handling of missing content fields."""
        articles = [
            {'id': 1, 'title': 'Title Only'},  # No content field
            {'id': 2, 'title': 'Title Only', 'content': None}  # None content
        ]

        duplicates = detect_duplicates(articles, threshold=0.90)

        # Should handle gracefully and compare titles
        assert isinstance(duplicates, list)

    def test_three_way_duplicates(self):
        """Test detection with three duplicate articles."""
        articles = [
            {'id': 1, 'title': 'Same Story', 'content': 'Same text'},
            {'id': 2, 'title': 'Same Story', 'content': 'Same text'},
            {'id': 3, 'title': 'Same Story', 'content': 'Same text'}
        ]

        duplicates = detect_duplicates(articles, threshold=0.95)

        # Should find 3 pairs: (1,2), (1,3), (2,3)
        assert len(duplicates) == 3

    def test_similarity_score_range(self):
        """Test that similarity scores are in valid range."""
        articles = [
            {'id': 1, 'title': 'Article A', 'content': 'Content A'},
            {'id': 2, 'title': 'Article B', 'content': 'Content B'}
        ]

        duplicates = detect_duplicates(articles, threshold=0.0)

        for dup in duplicates:
            assert 0.0 <= dup['similarity'] <= 1.0

    def test_duplicate_pair_structure(self):
        """Test structure of duplicate pair results."""
        articles = [
            {'id': 1, 'title': 'Same', 'content': 'Same'},
            {'id': 2, 'title': 'Same', 'content': 'Same'}
        ]

        duplicates = detect_duplicates(articles, threshold=0.85)

        if duplicates:
            dup = duplicates[0]
            assert 'article1_id' in dup
            assert 'article2_id' in dup
            assert 'similarity' in dup
            assert isinstance(dup['article1_id'], int)
            assert isinstance(dup['article2_id'], int)
            assert isinstance(dup['similarity'], float)


class TestDuplicateDetectionFromDB:
    """Test duplicate detection from database."""

    def test_detect_from_empty_db(self, temp_db):
        """Test with empty database."""
        # Delete default admin user's articles if any
        from scrapetui.core.database import get_db_connection
        with get_db_connection() as conn:
            conn.execute("DELETE FROM scraped_data")
            conn.commit()

        duplicates = detect_duplicates_from_db(threshold=0.85)
        assert duplicates == []

    def test_detect_from_db_with_duplicates(self, temp_db, unique_link):
        """Test detection from database with actual duplicates."""
        from scrapetui.core.database import get_db_connection
        import time
        import random

        # Insert duplicate articles
        with get_db_connection() as conn:
            for i in range(2):
                unique_id = f"{int(time.time() * 1000000)}-{random.randint(1000, 9999)}-{i}"
                link = f"https://example.com/article-{unique_id}"

                conn.execute("""
                    INSERT INTO scraped_data (title, url, link, content, user_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    "Duplicate Article",
                    "https://example.com",
                    link,
                    "This is duplicate content for testing.",
                    1
                ))
            conn.commit()

        duplicates = detect_duplicates_from_db(threshold=0.85)

        # Should find at least one duplicate pair
        assert len(duplicates) >= 1
        assert all('article1_id' in d and 'article2_id' in d for d in duplicates)

    def test_detect_from_db_with_limit(self, temp_db, unique_link):
        """Test database detection with limit parameter."""
        from scrapetui.core.database import get_db_connection
        import time
        import random

        # Insert multiple articles
        with get_db_connection() as conn:
            for i in range(5):
                unique_id = f"{int(time.time() * 1000000)}-{random.randint(1000, 9999)}-{i}"
                link = f"https://example.com/article-{unique_id}"

                conn.execute("""
                    INSERT INTO scraped_data (title, url, link, content, user_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    f"Article {i}",
                    "https://example.com",
                    link,
                    f"Different content {i}",
                    1
                ))
            conn.commit()

        # Detect with limit - should only check first 2 articles
        duplicates = detect_duplicates_from_db(threshold=0.85, limit=2)

        # Result should be a list (may or may not have duplicates)
        assert isinstance(duplicates, list)

    def test_detect_from_db_no_duplicates(self, temp_db, unique_link):
        """Test database detection with no duplicates."""
        from scrapetui.core.database import get_db_connection
        import time
        import random

        # Insert very distinct articles with different titles and content
        articles_data = [
            ("Python Programming Guide", "Learn Python programming from basics to advanced."),
            ("Climate Change Report", "Scientists discover new evidence of global warming effects."),
            ("Stock Market Analysis", "Technology stocks rise amid economic recovery signals.")
        ]

        with get_db_connection() as conn:
            for i, (title, content) in enumerate(articles_data):
                unique_id = f"{int(time.time() * 1000000)}-{random.randint(1000, 9999)}-{i}"
                link = f"https://example.com/article-{unique_id}"

                conn.execute("""
                    INSERT INTO scraped_data (title, url, link, content, user_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    title,
                    "https://example.com",
                    link,
                    content,
                    1
                ))
            conn.commit()

        duplicates = detect_duplicates_from_db(threshold=0.90)

        # Should find no duplicates
        assert len(duplicates) == 0
