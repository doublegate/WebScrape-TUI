"""
Comprehensive test suite for Advanced AI Features (v1.8.0).

This module tests the new AI-powered features including:
- AI-powered auto-tagging
- Named entity recognition
- Content similarity matching
- Keyword extraction
- Multi-level summarization

Total: 28 tests across 5 test classes
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from scrapetui import (
    AITaggingManager,
    EntityRecognitionManager,
    ContentSimilarityManager,
    KeywordExtractionManager,
    MultiLevelSummarizationManager
)


# ==================== AITaggingManager Tests (6 tests) ====================

class TestAITagging:
    """Test suite for AI-powered tagging functionality."""

    def test_generate_tags_basic(self):
        """Test basic tag generation from title and content."""
        with patch('scrapetui.AITaggingManager._ai_provider') as mock_provider:
            mock_provider.generate_summary.return_value = "technology, python, programming, web development, AI"

            tags = AITaggingManager.generate_tags(
                "Introduction to Python Programming",
                "Python is a versatile programming language used for web development and AI."
            )

            assert isinstance(tags, list)
            assert len(tags) > 0
            assert 'python' in [t.lower() for t in tags]

    def test_generate_tags_empty_content(self):
        """Test tag generation with empty content."""
        tags = AITaggingManager.generate_tags("", "")
        assert tags == []

    def test_generate_tags_limit(self):
        """Test that tag generation respects the max_tags limit."""
        with patch('scrapetui.AITaggingManager._ai_provider') as mock_provider:
            mock_provider.generate_summary.return_value = "tag1, tag2, tag3, tag4, tag5, tag6, tag7, tag8"

            tags = AITaggingManager.generate_tags(
                "Test Article",
                "Test content",
                max_tags=5
            )

            assert len(tags) <= 5

    def test_generate_tags_deduplication(self):
        """Test that duplicate tags are removed."""
        with patch('scrapetui.AITaggingManager._ai_provider') as mock_provider:
            mock_provider.generate_summary.return_value = "python, Python, PYTHON, web, Web"

            tags = AITaggingManager.generate_tags(
                "Python Programming",
                "Learn Python programming"
            )

            # Count occurrences of 'python' (case-insensitive)
            python_count = sum(1 for t in tags if t.lower() == 'python')
            assert python_count == 1

    def test_generate_tags_with_provider_failure(self):
        """Test tag generation when AI provider fails."""
        with patch('scrapetui.AITaggingManager._ai_provider') as mock_provider:
            mock_provider.generate_summary.side_effect = Exception("API Error")

            tags = AITaggingManager.generate_tags(
                "Test Article",
                "Test content"
            )

            assert tags == []

    def test_generate_tags_cleaning(self):
        """Test that generated tags are properly cleaned."""
        with patch('scrapetui.AITaggingManager._ai_provider') as mock_provider:
            mock_provider.generate_summary.return_value = " tag1 , tag2  , , tag3 "

            tags = AITaggingManager.generate_tags(
                "Test Article",
                "Test content"
            )

            # Check that tags are stripped and empty ones removed
            assert all(tag.strip() == tag for tag in tags)
            assert '' not in tags


# ==================== EntityRecognitionManager Tests (6 tests) ====================

class TestEntityRecognition:
    """Test suite for named entity recognition functionality."""

    @patch('scrapetui.spacy.load')
    def test_extract_entities_basic(self, mock_spacy_load):
        """Test basic entity extraction."""
        mock_nlp = Mock()
        mock_doc = Mock()

        # Create mock entities
        person_ent = Mock(text="John Doe", label_="PERSON")
        org_ent = Mock(text="Microsoft", label_="ORG")
        location_ent = Mock(text="New York", label_="GPE")

        mock_doc.ents = [person_ent, org_ent, location_ent]
        mock_nlp.return_value = mock_doc
        mock_spacy_load.return_value = mock_nlp

        entities = EntityRecognitionManager.extract_entities(
            "John Doe works at Microsoft in New York."
        )

        assert 'PERSON' in entities
        assert 'ORG' in entities
        assert 'GPE' in entities
        assert 'John Doe' in entities['PERSON']
        assert 'Microsoft' in entities['ORG']

    @patch('scrapetui.spacy.load')
    def test_extract_entities_empty_content(self, mock_spacy_load):
        """Test entity extraction with empty content."""
        entities = EntityRecognitionManager.extract_entities("")

        assert entities == {}

    @patch('scrapetui.spacy.load')
    def test_extract_entities_no_entities(self, mock_spacy_load):
        """Test entity extraction when no entities found."""
        mock_nlp = Mock()
        mock_doc = Mock()
        mock_doc.ents = []
        mock_nlp.return_value = mock_doc
        mock_spacy_load.return_value = mock_nlp

        entities = EntityRecognitionManager.extract_entities(
            "This text has no named entities."
        )

        assert entities == {}

    @patch('scrapetui.spacy.load')
    def test_extract_entities_deduplication(self, mock_spacy_load):
        """Test that duplicate entities are removed."""
        mock_nlp = Mock()
        mock_doc = Mock()

        # Create duplicate entities
        person_ent1 = Mock(text="John Doe", label_="PERSON")
        person_ent2 = Mock(text="John Doe", label_="PERSON")

        mock_doc.ents = [person_ent1, person_ent2]
        mock_nlp.return_value = mock_doc
        mock_spacy_load.return_value = mock_nlp

        entities = EntityRecognitionManager.extract_entities(
            "John Doe and John Doe are mentioned."
        )

        assert len(entities['PERSON']) == 1

    @patch('scrapetui.spacy.load')
    def test_extract_entities_multiple_types(self, mock_spacy_load):
        """Test extraction of multiple entity types."""
        mock_nlp = Mock()
        mock_doc = Mock()

        # Create various entity types
        person_ent = Mock(text="Alice", label_="PERSON")
        org_ent = Mock(text="Google", label_="ORG")
        location_ent = Mock(text="Paris", label_="GPE")
        date_ent = Mock(text="2024", label_="DATE")

        mock_doc.ents = [person_ent, org_ent, location_ent, date_ent]
        mock_nlp.return_value = mock_doc
        mock_spacy_load.return_value = mock_nlp

        entities = EntityRecognitionManager.extract_entities(
            "Alice works at Google in Paris since 2024."
        )

        assert len(entities) == 4

    @patch('scrapetui.spacy.load')
    def test_extract_entities_with_spacy_error(self, mock_spacy_load):
        """Test entity extraction when spaCy fails."""
        mock_spacy_load.side_effect = Exception("spaCy error")

        entities = EntityRecognitionManager.extract_entities(
            "Test content with entities."
        )

        assert entities == {}


# ==================== ContentSimilarityManager Tests (6 tests) ====================

class TestContentSimilarity:
    """Test suite for content similarity matching."""

    @patch('scrapetui.SentenceTransformer')
    def test_find_similar_articles_basic(self, mock_transformer):
        """Test basic similar article finding."""
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3], [0.15, 0.25, 0.35], [0.9, 0.8, 0.7]]
        mock_transformer.return_value = mock_model

        articles = [
            (1, "Python Programming", "Learn Python basics"),
            (2, "Python Tutorial", "Python programming guide"),
            (3, "JavaScript Guide", "Learn JavaScript")
        ]

        similar_ids = ContentSimilarityManager.find_similar_articles(1, articles)

        assert isinstance(similar_ids, list)
        assert 1 not in similar_ids  # Original article excluded

    @patch('scrapetui.SentenceTransformer')
    def test_find_similar_articles_threshold(self, mock_transformer):
        """Test similarity threshold filtering."""
        mock_model = Mock()
        # First encoding is target, rest are articles
        mock_model.encode.return_value = [
            [0.1, 0.2, 0.3],  # Target
            [0.1, 0.2, 0.3],  # Very similar (cosine distance ~0)
            [0.9, 0.8, 0.7]   # Very different (cosine distance ~1)
        ]
        mock_transformer.return_value = mock_model

        articles = [
            (1, "Article 1", "Content 1"),
            (2, "Article 2", "Content 2")
        ]

        similar_ids = ContentSimilarityManager.find_similar_articles(
            1,
            [(1, "Target", "Target content")] + articles,
            threshold=0.5
        )

        # Only very similar article should be returned
        assert len(similar_ids) <= 1

    @patch('scrapetui.SentenceTransformer')
    def test_find_similar_articles_top_k(self, mock_transformer):
        """Test that only top_k similar articles are returned."""
        mock_model = Mock()
        mock_model.encode.return_value = [
            [0.1, 0.2, 0.3],
            [0.11, 0.21, 0.31],
            [0.12, 0.22, 0.32],
            [0.13, 0.23, 0.33],
            [0.14, 0.24, 0.34]
        ]
        mock_transformer.return_value = mock_model

        articles = [
            (1, "Article 1", "Content 1"),
            (2, "Article 2", "Content 2"),
            (3, "Article 3", "Content 3"),
            (4, "Article 4", "Content 4")
        ]

        similar_ids = ContentSimilarityManager.find_similar_articles(
            1,
            [(1, "Target", "Target content")] + articles,
            top_k=2
        )

        assert len(similar_ids) <= 2

    @patch('scrapetui.SentenceTransformer')
    def test_find_similar_articles_empty_database(self, mock_transformer):
        """Test similar articles with empty article list."""
        similar_ids = ContentSimilarityManager.find_similar_articles(1, [])

        assert similar_ids == []

    @patch('scrapetui.SentenceTransformer')
    def test_find_similar_articles_single_article(self, mock_transformer):
        """Test similar articles when only target article exists."""
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer.return_value = mock_model

        articles = [(1, "Only Article", "Only content")]

        similar_ids = ContentSimilarityManager.find_similar_articles(1, articles)

        assert similar_ids == []

    @patch('scrapetui.SentenceTransformer')
    def test_find_similar_articles_with_model_error(self, mock_transformer):
        """Test similar articles when model fails."""
        mock_transformer.side_effect = Exception("Model error")

        articles = [
            (1, "Article 1", "Content 1"),
            (2, "Article 2", "Content 2")
        ]

        similar_ids = ContentSimilarityManager.find_similar_articles(1, articles)

        assert similar_ids == []


# ==================== KeywordExtractionManager Tests (6 tests) ====================

class TestKeywordExtraction:
    """Test suite for keyword extraction functionality."""

    @patch('scrapetui.nltk.corpus.stopwords.words')
    def test_extract_keywords_basic(self, mock_stopwords):
        """Test basic keyword extraction."""
        mock_stopwords.return_value = ['the', 'is', 'a', 'an', 'and', 'or', 'for', 'to', 'of', 'in']

        keywords = KeywordExtractionManager.extract_keywords(
            "Python programming is popular for web development and data science.",
            "Python Programming Guide"
        )

        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert 'python' in [k.lower() for k in keywords]

    @patch('scrapetui.nltk.corpus.stopwords.words')
    def test_extract_keywords_empty_content(self, mock_stopwords):
        """Test keyword extraction with empty content."""
        mock_stopwords.return_value = []

        keywords = KeywordExtractionManager.extract_keywords("", "")

        assert keywords == []

    @patch('scrapetui.nltk.corpus.stopwords.words')
    def test_extract_keywords_top_n(self, mock_stopwords):
        """Test that only top_n keywords are returned."""
        mock_stopwords.return_value = ['the', 'is', 'a']

        long_text = " ".join([f"keyword{i}" for i in range(20)] * 3)

        keywords = KeywordExtractionManager.extract_keywords(
            long_text,
            "Test Title",
            top_n=5
        )

        assert len(keywords) <= 5

    @patch('scrapetui.nltk.corpus.stopwords.words')
    def test_extract_keywords_frequency_scoring(self, mock_stopwords):
        """Test that keywords are scored by frequency."""
        mock_stopwords.return_value = ['the', 'is', 'a']

        # 'python' appears 3 times, 'java' appears 1 time
        text = "python python python java programming"

        keywords = KeywordExtractionManager.extract_keywords(
            text,
            "Programming",
            top_n=3
        )

        # 'python' should be ranked higher due to frequency
        assert 'python' in [k.lower() for k in keywords]

    @patch('scrapetui.nltk.corpus.stopwords.words')
    def test_extract_keywords_title_boost(self, mock_stopwords):
        """Test that keywords in title get boosted scores."""
        mock_stopwords.return_value = ['the', 'is', 'a', 'to']

        keywords = KeywordExtractionManager.extract_keywords(
            "This article discusses various topics including machine learning.",
            "Python Machine Learning Guide",  # 'machine' and 'learning' in title
            top_n=5
        )

        # Words from title should be included
        keyword_lower = [k.lower() for k in keywords]
        assert 'machine' in keyword_lower or 'learning' in keyword_lower

    @patch('scrapetui.nltk.corpus.stopwords.words')
    def test_extract_keywords_with_nltk_error(self, mock_stopwords):
        """Test keyword extraction when NLTK fails."""
        mock_stopwords.side_effect = Exception("NLTK error")

        keywords = KeywordExtractionManager.extract_keywords(
            "Test content",
            "Test Title"
        )

        assert keywords == []


# ==================== MultiLevelSummarizationManager Tests (4 tests) ====================

class TestMultiLevelSummarization:
    """Test suite for multi-level summarization functionality."""

    def test_generate_summary_levels(self):
        """Test generation of summary at different levels."""
        with patch('scrapetui.MultiLevelSummarizationManager._ai_provider') as mock_provider:
            mock_provider.generate_summary.return_value = "Brief summary"

            brief = MultiLevelSummarizationManager.generate_summary(
                "Long article content here...",
                "Article Title",
                level="brief"
            )

            assert isinstance(brief, str)
            assert len(brief) > 0

    def test_generate_summary_all_levels(self):
        """Test generation of summaries at all three levels."""
        with patch('scrapetui.MultiLevelSummarizationManager._ai_provider') as mock_provider:
            mock_provider.generate_summary.side_effect = [
                "Brief summary",
                "Detailed summary with more information",
                "Comprehensive summary with full analysis"
            ]

            summaries = MultiLevelSummarizationManager.generate_all_levels(
                "Article content",
                "Article Title"
            )

            assert 'brief' in summaries
            assert 'detailed' in summaries
            assert 'comprehensive' in summaries
            assert len(summaries['brief']) < len(summaries['detailed'])
            assert len(summaries['detailed']) < len(summaries['comprehensive'])

    def test_generate_summary_empty_content(self):
        """Test summary generation with empty content."""
        summary = MultiLevelSummarizationManager.generate_summary("", "")

        assert summary == ""

    def test_generate_summary_with_provider_error(self):
        """Test summary generation when AI provider fails."""
        with patch('scrapetui.MultiLevelSummarizationManager._ai_provider') as mock_provider:
            mock_provider.generate_summary.side_effect = Exception("API Error")

            summary = MultiLevelSummarizationManager.generate_summary(
                "Content",
                "Title",
                level="brief"
            )

            assert summary == ""


# ==================== Integration Tests ====================

class TestAdvancedAIIntegration:
    """Integration tests for advanced AI features working together."""

    @patch('scrapetui.AITaggingManager._ai_provider')
    @patch('scrapetui.spacy.load')
    def test_tag_and_entity_extraction_workflow(self, mock_spacy, mock_ai_provider):
        """Test combined workflow of tagging and entity extraction."""
        # Setup mocks
        mock_ai_provider.generate_summary.return_value = "python, programming, technology"

        mock_nlp = Mock()
        mock_doc = Mock()
        person_ent = Mock(text="John Doe", label_="PERSON")
        mock_doc.ents = [person_ent]
        mock_nlp.return_value = mock_doc
        mock_spacy.return_value = mock_nlp

        content = "John Doe writes about Python programming."
        title = "Python Guide"

        # Generate tags
        tags = AITaggingManager.generate_tags(title, content)

        # Extract entities
        entities = EntityRecognitionManager.extract_entities(content)

        # Verify both operations succeeded
        assert len(tags) > 0
        assert 'PERSON' in entities
        assert 'John Doe' in entities['PERSON']

    @patch('scrapetui.KeywordExtractionManager.extract_keywords')
    @patch('scrapetui.SentenceTransformer')
    def test_keyword_and_similarity_workflow(self, mock_transformer, mock_keywords):
        """Test combined workflow of keyword extraction and similarity matching."""
        # Setup mocks
        mock_keywords.return_value = ['python', 'programming', 'tutorial']

        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2], [0.15, 0.25]]
        mock_transformer.return_value = mock_model

        articles = [
            (1, "Python Tutorial", "Learn Python"),
            (2, "Python Guide", "Python programming")
        ]

        # Extract keywords from first article
        keywords = KeywordExtractionManager.extract_keywords(
            articles[0][2],
            articles[0][1]
        )

        # Find similar articles
        similar = ContentSimilarityManager.find_similar_articles(1, articles)

        # Verify both operations succeeded
        assert len(keywords) > 0
        assert isinstance(similar, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
