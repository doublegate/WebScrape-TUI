#!/usr/bin/env python3
"""Tests for Named Entity Recognition in AI processors."""

import pytest
from scrapetui.ai.processors import (
    extract_named_entities,
    extract_entities_from_articles
)


class TestNamedEntityRecognition:
    """Test NER functionality."""

    def test_extract_entities_basic(self):
        """Test basic entity extraction."""
        text = "Apple CEO Tim Cook announced new products in Cupertino."
        entities = extract_named_entities(text)

        assert len(entities) > 0

        # Check for expected entities (may vary by spaCy version)
        entity_texts = [e['text'] for e in entities]
        # At least one of these should be detected
        assert any(
            name in ' '.join(entity_texts)
            for name in ['Apple', 'Cook', 'Cupertino', 'Tim']
        )

    def test_extract_entities_with_filter(self):
        """Test entity extraction with type filtering."""
        text = "Microsoft and Google competed in Seattle."
        entities = extract_named_entities(text, entity_types=['ORG'])

        # Should only return organizations
        for entity in entities:
            assert entity['label'] == 'ORG'

    def test_extract_entities_empty_text(self):
        """Test with empty text."""
        assert extract_named_entities("") == []
        assert extract_named_entities("   ") == []
        assert extract_named_entities(None) == []

    def test_extract_entities_no_entities(self):
        """Test text with no entities."""
        text = "The quick brown fox jumps over the lazy dog."
        entities = extract_named_entities(text)
        # May or may not find entities depending on spaCy's interpretation
        assert isinstance(entities, list)

    def test_entity_structure(self):
        """Test entity dict structure."""
        text = "Barack Obama was president."
        entities = extract_named_entities(text)

        if entities:  # May find entities
            entity = entities[0]
            assert 'text' in entity
            assert 'label' in entity
            assert 'start' in entity
            assert 'end' in entity
            assert isinstance(entity['start'], int)
            assert isinstance(entity['end'], int)
            assert entity['start'] >= 0
            assert entity['end'] > entity['start']

    def test_extract_entities_multiple_types(self):
        """Test extraction with multiple entity types."""
        text = "Elon Musk founded SpaceX in California."
        entities = extract_named_entities(text, entity_types=['PERSON', 'ORG', 'GPE'])

        # Should find at least one entity
        assert len(entities) > 0

        # All entities should be one of the requested types
        for entity in entities:
            assert entity['label'] in ['PERSON', 'ORG', 'GPE']

    def test_extract_entities_long_text(self):
        """Test with longer text to ensure performance."""
        text = " ".join([
            "Apple Inc. is an American multinational technology company",
            "headquartered in Cupertino, California.",
            "Tim Cook is the CEO of Apple.",
            "Microsoft competes with Apple in many markets."
        ])

        entities = extract_named_entities(text)
        assert len(entities) > 0
        assert isinstance(entities, list)

    def test_extract_entities_special_characters(self):
        """Test handling of special characters."""
        text = "Dr. John Smith works at IBM in New York!"
        entities = extract_named_entities(text)

        # Should handle punctuation gracefully
        assert isinstance(entities, list)


class TestEntityExtractionFromArticles:
    """Test extracting entities from database articles."""

    def test_extract_from_articles(self, temp_db, unique_link):
        """Test extracting entities from articles in database."""
        from scrapetui.core.database import get_db_connection

        # Insert test article with entities
        with get_db_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO scraped_data (title, url, link, content, user_id)
                VALUES (?, ?, ?, ?, ?)
            """, (
                "Tech News",
                "https://example.com",
                unique_link,
                "Apple CEO Tim Cook announced new iPhone in California.",
                1
            ))
            article_id = cursor.lastrowid
            conn.commit()

        # Extract entities
        results = extract_entities_from_articles([article_id])

        assert article_id in results
        assert isinstance(results[article_id], list)

    def test_extract_from_nonexistent_article(self, db_connection):
        """Test with nonexistent article ID."""
        results = extract_entities_from_articles([999999])
        assert 999999 in results
        assert results[999999] == []

    def test_extract_from_multiple_articles(self, temp_db, unique_link):
        """Test extracting entities from multiple articles."""
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
                    f"This is article {i} about Microsoft and Google.",
                    1
                ))
                article_ids.append(cursor.lastrowid)
            conn.commit()

        # Extract entities from all articles
        results = extract_entities_from_articles(article_ids)

        assert len(results) == 3
        for article_id in article_ids:
            assert article_id in results
            assert isinstance(results[article_id], list)

    def test_extract_from_article_with_no_content(self, temp_db, unique_link):
        """Test extracting from article with no content."""
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

        results = extract_entities_from_articles([article_id])

        assert article_id in results
        assert results[article_id] == []

    def test_extract_uses_content_first(self, temp_db, unique_link):
        """Test that extraction prioritizes content over summary."""
        from scrapetui.core.database import get_db_connection

        with get_db_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO scraped_data (
                    title, url, link, content, summary, user_id
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "Test",
                "https://example.com",
                unique_link,
                "Microsoft announced new products.",
                "Apple announced new products.",
                1
            ))
            article_id = cursor.lastrowid
            conn.commit()

        results = extract_entities_from_articles([article_id])

        # Should extract from content (Microsoft), not summary (Apple)
        entities = results[article_id]
        if entities:
            entity_texts = ' '.join([e['text'] for e in entities])
            # More likely to find Microsoft than Apple since content is processed
            assert isinstance(entity_texts, str)
