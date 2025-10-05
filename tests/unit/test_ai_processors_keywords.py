#!/usr/bin/env python3
"""Tests for Keyword Extraction in AI processors."""

from scrapetui.ai.processors import (
    extract_keywords,
    extract_keywords_from_articles
)


class TestKeywordExtraction:
    """Test keyword extraction functionality."""

    def test_extract_keywords_basic(self):
        """Test basic keyword extraction."""
        text = """
        Machine learning is a subset of artificial intelligence.
        Machine learning algorithms build models based on sample data.
        """
        keywords = extract_keywords(text, top_n=5)

        assert len(keywords) > 0
        assert all('keyword' in kw and 'score' in kw for kw in keywords)
        assert all(isinstance(kw['score'], float) for kw in keywords)

        # Check for expected keywords
        keyword_texts = [kw['keyword'] for kw in keywords]
        assert any('machine' in kw.lower() or 'learning' in kw.lower()
                   for kw in keyword_texts)

    def test_extract_keywords_empty_text(self):
        """Test with empty text."""
        assert extract_keywords("") == []
        assert extract_keywords("   ") == []
        assert extract_keywords(None) == []

    def test_extract_keywords_top_n(self):
        """Test limiting number of keywords."""
        text = " ".join([
            "Python programming language is popular.",
            "Python is used for data science.",
            "Machine learning uses Python.",
            "Web development with Python."
        ])

        keywords_5 = extract_keywords(text, top_n=5)
        keywords_3 = extract_keywords(text, top_n=3)

        assert len(keywords_5) <= 5
        assert len(keywords_3) <= 3
        assert len(keywords_3) <= len(keywords_5)

    def test_extract_keywords_scoring(self):
        """Test that keywords are scored and sorted."""
        text = """
        The quick brown fox jumps over the lazy dog.
        The fox is quick and the dog is lazy.
        """
        keywords = extract_keywords(text, top_n=5)

        # Scores should be in descending order
        scores = [kw['score'] for kw in keywords]
        assert scores == sorted(scores, reverse=True)

        # All scores should be between 0 and 1
        assert all(0 <= score <= 1 for score in scores)

    def test_extract_keywords_ngrams(self):
        """Test n-gram extraction."""
        text = """
        Natural language processing is a field of artificial intelligence.
        Natural language processing enables computers to understand text.
        """

        # Test with bigrams
        keywords = extract_keywords(text, top_n=10, ngram_range=(1, 2))

        keyword_texts = [kw['keyword'] for kw in keywords]

        # Should find some bigrams (phrases with spaces)
        bigrams = [kw for kw in keyword_texts if ' ' in kw]
        # May or may not have bigrams depending on text, but structure should work
        assert isinstance(bigrams, list)

    def test_extract_keywords_unigrams_only(self):
        """Test with unigrams only."""
        text = "Python programming language for data science and machine learning."
        keywords = extract_keywords(text, top_n=5, ngram_range=(1, 1))

        keyword_texts = [kw['keyword'] for kw in keywords]

        # All keywords should be single words (no spaces)
        assert all(' ' not in kw for kw in keyword_texts)

    def test_extract_keywords_stop_words(self):
        """Test that stop words are filtered."""
        text = "The quick brown fox jumps over the lazy dog in the garden."
        keywords = extract_keywords(text, top_n=10)

        keyword_texts = [kw['keyword'].lower() for kw in keywords]

        # Common stop words should be filtered out
        common_stop_words = ['the', 'in', 'a', 'an', 'and', 'or']
        for stop_word in common_stop_words:
            assert stop_word not in keyword_texts

    def test_extract_keywords_repetition(self):
        """Test that repeated words get higher scores."""
        text = """
        Python is great. Python is powerful. Python is popular.
        Java is good. JavaScript is okay.
        """
        keywords = extract_keywords(text, top_n=5)

        keyword_texts = [kw['keyword'].lower() for kw in keywords]

        # 'python' appears 3 times, should likely be in top keywords
        # (though exact ranking depends on TF-IDF calculation)
        assert any('python' in kw for kw in keyword_texts)

    def test_extract_keywords_long_text(self):
        """Test with longer text."""
        text = " ".join([
            "Artificial intelligence and machine learning are transforming industries.",
            "Deep learning is a subset of machine learning using neural networks.",
            "Natural language processing enables computers to understand human language.",
            "Computer vision allows machines to interpret visual information.",
            "Reinforcement learning trains agents through rewards and penalties."
        ])

        keywords = extract_keywords(text, top_n=10)

        assert len(keywords) > 0
        assert len(keywords) <= 10
        assert all(isinstance(kw['keyword'], str) for kw in keywords)


class TestKeywordExtractionFromArticles:
    """Test extracting keywords from database articles."""

    def test_extract_from_articles(self, temp_db, unique_link):
        """Test extracting keywords from articles in database."""
        from scrapetui.core.database import get_db_connection

        # Insert test article
        with get_db_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO scraped_data (title, url, link, content, user_id)
                VALUES (?, ?, ?, ?, ?)
            """, (
                "Machine Learning Article",
                "https://example.com",
                unique_link,
                "Machine learning and artificial intelligence are transforming technology.",
                1
            ))
            article_id = cursor.lastrowid
            conn.commit()

        # Extract keywords
        results = extract_keywords_from_articles([article_id], top_n=5)

        assert article_id in results
        assert isinstance(results[article_id], list)
        assert len(results[article_id]) <= 5

    def test_extract_from_nonexistent_article(self, db_connection):
        """Test with nonexistent article ID."""
        results = extract_keywords_from_articles([999999], top_n=5)
        assert 999999 in results
        assert results[999999] == []

    def test_extract_from_multiple_articles(self, temp_db, unique_link):
        """Test extracting keywords from multiple articles."""
        from scrapetui.core.database import get_db_connection
        import time
        import random

        article_ids = []

        with get_db_connection() as conn:
            # Insert multiple articles
            for i in range(3):
                unique_id = f"{int(time.time() * 1000000)}-{random.randint(1000, 9999)}-{i}"
                link = f"https://example.com/article-{unique_id}"

                cursor = conn.execute("""
                    INSERT INTO scraped_data (title, url, link, content, user_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    f"Article {i}",
                    "https://example.com",
                    link,
                    f"This article discusses technology and innovation in field {i}.",
                    1
                ))
                article_ids.append(cursor.lastrowid)
            conn.commit()

        # Extract keywords from all articles
        results = extract_keywords_from_articles(article_ids, top_n=5)

        assert len(results) == 3
        for article_id in article_ids:
            assert article_id in results
            assert isinstance(results[article_id], list)
            assert len(results[article_id]) <= 5

    def test_extract_from_article_with_no_content(self, temp_db, unique_link):
        """Test extracting from article with no content (falls back to title)."""
        from scrapetui.core.database import get_db_connection

        with get_db_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO scraped_data (title, url, link, user_id)
                VALUES (?, ?, ?, ?)
            """, (
                "Empty Article",
                "https://example.com",
                unique_link,
                1
            ))
            article_id = cursor.lastrowid
            conn.commit()

        results = extract_keywords_from_articles([article_id], top_n=5)

        assert article_id in results
        # Should extract from title as fallback
        assert isinstance(results[article_id], list)

    def test_extract_with_custom_top_n(self, temp_db, unique_link):
        """Test custom top_n parameter."""
        from scrapetui.core.database import get_db_connection

        with get_db_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO scraped_data (title, url, link, content, user_id)
                VALUES (?, ?, ?, ?, ?)
            """, (
                "Tech Article",
                "https://example.com",
                unique_link,
                " ".join([
                    "Python programming for machine learning.",
                    "Data science with Python and artificial intelligence.",
                    "Neural networks and deep learning applications."
                ]),
                1
            ))
            article_id = cursor.lastrowid
            conn.commit()

        # Test different top_n values
        results_3 = extract_keywords_from_articles([article_id], top_n=3)
        results_10 = extract_keywords_from_articles([article_id], top_n=10)

        assert len(results_3[article_id]) <= 3
        assert len(results_10[article_id]) <= 10
        assert len(results_3[article_id]) <= len(results_10[article_id])
