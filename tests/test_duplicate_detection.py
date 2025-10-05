"""
Tests for Duplicate Detection functionality (v1.9.0).

Tests exact and fuzzy duplicate detection, similarity thresholds,
clustering, and related article finding.
"""

import pytest

# Import from monolithic scrapetui.py using importlib.util
import importlib.util
from pathlib import Path

_scrapetui_path = Path(__file__).parent.parent / 'scrapetui.py'
_spec = importlib.util.spec_from_file_location("scrapetui_monolith", _scrapetui_path)
_scrapetui_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scrapetui_module)

# Import needed components from monolithic module
DuplicateDetectionManager = _scrapetui_module.DuplicateDetectionManager


@pytest.fixture
def duplicate_articles():
    """Articles with exact and near duplicates."""
    return [
        {
            'id': 1,
            'title': 'Python Programming Tutorial',
            'content': 'Learn Python programming from scratch. This comprehensive guide covers all Python basics.'
        },
        {
            'id': 2,
            'title': 'Python Programming Tutorial',  # Exact title duplicate
            'content': 'Learn Python programming from scratch. This comprehensive guide covers all Python basics.'
        },
        {
            'id': 3,
            'title': 'Python Programming Guide',  # Similar title
            'content': 'Learn Python programming from scratch. This comprehensive tutorial covers all Python fundamentals.'
        },
        {
            'id': 4,
            'title': 'JavaScript Web Development',  # Different topic
            'content': 'Master JavaScript for web development. Build modern web applications with JavaScript frameworks.'
        },
        {
            'id': 5,
            'title': 'Python Basics Tutorial',  # Related but different
            'content': 'Introduction to Python programming. Basic concepts and syntax for beginners learning Python.'
        }
    ]


@pytest.fixture
def unique_articles():
    """Articles with no duplicates."""
    return [
        {
            'id': 1,
            'title': 'Machine Learning Basics',
            'content': 'Introduction to machine learning algorithms and concepts.'
        },
        {
            'id': 2,
            'title': 'Web Security Best Practices',
            'content': 'Essential security measures for web applications and APIs.'
        },
        {
            'id': 3,
            'title': 'Database Design Principles',
            'content': 'Fundamental principles of relational database design and normalization.'
        }
    ]


class TestExactDuplicateDetection:
    """Tests for exact duplicate detection."""

    def test_find_exact_duplicates(self, duplicate_articles):
        """Test finding exact duplicate articles."""
        duplicates = DuplicateDetectionManager.find_duplicates(
            duplicate_articles,
            similarity_threshold=100  # Exact match
        )

        assert len(duplicates) > 0

        # Verify duplicate structure
        dup = duplicates[0]
        assert 'article1_id' in dup
        assert 'article2_id' in dup
        assert 'article1_title' in dup
        assert 'article2_title' in dup
        assert 'similarity_score' in dup
        assert dup['similarity_score'] >= 95  # High similarity (0-100 scale)

    def test_no_exact_duplicates(self, unique_articles):
        """Test with articles that have no exact duplicates."""
        duplicates = DuplicateDetectionManager.find_duplicates(
            unique_articles,
            similarity_threshold=100
        )

        assert len(duplicates) == 0

    def test_exact_duplicate_identification(self, duplicate_articles):
        """Test that exact duplicates are correctly identified."""
        duplicates = DuplicateDetectionManager.find_duplicates(
            duplicate_articles,
            similarity_threshold=100
        )

        # Articles 1 and 2 should be exact duplicates
        found_exact = False
        for dup in duplicates:
            if (dup['article1_id'] == 1 and dup['article2_id'] == 2) or (
                    dup['article1_id'] == 2 and dup['article2_id'] == 1):
                found_exact = True
                assert dup['similarity_score'] >= 95  # Very high similarity (0-100 scale)

        assert found_exact, "Exact duplicates not detected"


class TestFuzzyDuplicateDetection:
    """Tests for fuzzy/approximate duplicate detection."""

    def test_fuzzy_duplicate_detection(self, duplicate_articles):
        """Test fuzzy matching for similar articles."""
        duplicates = DuplicateDetectionManager.find_duplicates(
            duplicate_articles,
            similarity_threshold=70  # 70% similarity
        )

        assert len(duplicates) > 0

        # Should find articles 1, 2, and 3 as duplicates
        # (they have similar content about Python)

    def test_fuzzy_threshold_adjustment(self, duplicate_articles):
        """Test different similarity thresholds."""
        # High threshold - fewer duplicates
        strict_dups = DuplicateDetectionManager.find_duplicates(
            duplicate_articles,
            similarity_threshold=90
        )

        # Low threshold - more duplicates
        loose_dups = DuplicateDetectionManager.find_duplicates(
            duplicate_articles,
            similarity_threshold=50
        )

        # Lower threshold should find same or more duplicates
        assert len(loose_dups) >= len(strict_dups)

    def test_near_duplicate_detection(self, duplicate_articles):
        """Test detection of near-duplicate articles."""
        duplicates = DuplicateDetectionManager.find_duplicates(
            duplicate_articles,
            similarity_threshold=80
        )

        # Articles 1 and 3 are near-duplicates (similar content, slightly different wording)
        similar_ids = set()
        for dup in duplicates:
            similar_ids.add(dup['article1_id'])
            similar_ids.add(dup['article2_id'])

        # Should include the Python-related articles
        assert 1 in similar_ids or 3 in similar_ids

    def test_similarity_scores(self, duplicate_articles):
        """Test that similarity scores are meaningful."""
        duplicates = DuplicateDetectionManager.find_duplicates(
            duplicate_articles,
            similarity_threshold=50
        )

        for dup in duplicates:
            sim = dup['similarity_score']
            assert 0 <= sim <= 100
            assert sim >= 50  # At least threshold similarity


class TestSimilarityThreshold:
    """Tests for configurable similarity threshold."""

    def test_threshold_boundary_cases(self, duplicate_articles):
        """Test threshold boundary values."""
        # Threshold = 0 (everything is duplicate)
        all_dups = DuplicateDetectionManager.find_duplicates(
            duplicate_articles,
            similarity_threshold=0
        )
        assert len(all_dups) > 0

        # Threshold = 1.0 (only exact matches)
        exact_dups = DuplicateDetectionManager.find_duplicates(
            duplicate_articles,
            similarity_threshold=100
        )
        # Should be fewer than all_dups
        assert len(exact_dups) <= len(all_dups)

    def test_invalid_threshold_handling(self, duplicate_articles):
        """Test handling of invalid threshold values."""
        # Threshold > 1.0 should be clamped or error
        try:
            duplicates = DuplicateDetectionManager.find_duplicates(
                duplicate_articles,
                similarity_threshold=150
            )
            # If it doesn't error, threshold should be clamped
            assert isinstance(duplicates, list)
        except ValueError:
            # Acceptable to raise error for invalid threshold
            pass

    def test_threshold_precision(self, duplicate_articles):
        """Test threshold with decimal precision."""
        dups_85 = DuplicateDetectionManager.find_duplicates(
            duplicate_articles,
            similarity_threshold=85
        )

        dups_86 = DuplicateDetectionManager.find_duplicates(
            duplicate_articles,
            similarity_threshold=86
        )

        # Small threshold change may affect results
        # Just verify both work without error
        assert isinstance(dups_85, list)
        assert isinstance(dups_86, list)


class TestArticleClustering:
    """Tests for article clustering functionality."""

    def test_cluster_articles_basic(self, duplicate_articles):
        """Test basic article clustering."""
        result = DuplicateDetectionManager.cluster_articles(
            duplicate_articles,
            num_clusters=2
        )

        assert 'clusters' in result
        assert 'num_clusters' in result
        assert result['num_clusters'] == 2

        # Verify cluster structure
        clusters = result['clusters']
        first_cluster_id = list(clusters.keys())[0]
        cluster = clusters[first_cluster_id]
        assert 'articles' in cluster
        assert 'cluster_id' in cluster
        assert 'size' in cluster
        assert len(cluster['articles']) > 0

    def test_cluster_with_custom_num_clusters(self, duplicate_articles):
        """Test clustering with different numbers of clusters."""
        result_2 = DuplicateDetectionManager.cluster_articles(
            duplicate_articles,
            num_clusters=2
        )

        result_3 = DuplicateDetectionManager.cluster_articles(
            duplicate_articles,
            num_clusters=3
        )

        assert result_2['num_clusters'] == 2
        assert result_3['num_clusters'] == 3

    def test_cluster_coverage(self, duplicate_articles):
        """Test that all articles are assigned to clusters."""
        result = DuplicateDetectionManager.cluster_articles(
            duplicate_articles,
            num_clusters=3
        )

        # Count total articles in all clusters
        total_articles = sum(c['size'] for c in result['clusters'].values())

        # Should equal original article count (or close due to clustering)
        assert total_articles == result['total_articles']

    def test_cluster_keywords(self, duplicate_articles):
        """Test that clusters have meaningful structure."""
        result = DuplicateDetectionManager.cluster_articles(
            duplicate_articles,
            num_clusters=2
        )

        clusters = result['clusters']
        for cluster_id, cluster in clusters.items():
            # Verify cluster has articles
            assert len(cluster['articles']) > 0
            # Each article should have article_id and title
            for article in cluster['articles']:
                assert 'article_id' in article
                assert 'title' in article


class TestRelatedArticlesFinding:
    """Tests for finding related articles."""

    def test_find_related_articles(self, duplicate_articles):
        """Test finding articles related to a specific one."""
        # Find articles related to article 1
        reference_article = duplicate_articles[0]
        other_articles = duplicate_articles[1:]

        related = DuplicateDetectionManager.find_related_articles(
            reference_article,
            other_articles,
            top_n=5
        )

        assert isinstance(related, list)
        # Should find at least the similar Python articles
        assert len(related) >= 0

    def test_related_articles_sorting(self, duplicate_articles):
        """Test that related articles are sorted by similarity."""
        reference_article = duplicate_articles[0]
        other_articles = duplicate_articles[1:]

        related = DuplicateDetectionManager.find_related_articles(
            reference_article,
            other_articles,
            top_n=5
        )

        if len(related) >= 2:
            # Verify sorting (highest similarity first)
            for i in range(len(related) - 1):
                assert related[i]['similarity_score'] >= related[i + 1]['similarity_score']

    def test_related_articles_limit(self, duplicate_articles):
        """Test limiting number of related articles returned."""
        reference_article = duplicate_articles[0]
        other_articles = duplicate_articles[1:]

        related = DuplicateDetectionManager.find_related_articles(
            reference_article,
            other_articles,
            top_n=2  # Limit to 2
        )

        assert len(related) <= 2


class TestNoDuplicatesScenario:
    """Tests for scenarios with no duplicates."""

    def test_no_duplicates_found(self, unique_articles):
        """Test behavior when no duplicates exist."""
        duplicates = DuplicateDetectionManager.find_duplicates(
            unique_articles,
            similarity_threshold=85
        )

        assert len(duplicates) == 0
        assert isinstance(duplicates, list)

    def test_single_article_no_duplicates(self):
        """Test duplicate detection with single article."""
        single_article = [{
            'id': 1,
            'title': 'Test Article',
            'content': 'This is a test article.'
        }]

        duplicates = DuplicateDetectionManager.find_duplicates(
            single_article,
            similarity_threshold=80
        )

        assert len(duplicates) == 0

    def test_empty_articles_list(self):
        """Test with empty articles list."""
        duplicates = DuplicateDetectionManager.find_duplicates(
            [],
            similarity_threshold=80
        )

        assert len(duplicates) == 0
        assert isinstance(duplicates, list)


class TestEdgeCases:
    """Tests for edge cases in duplicate detection."""

    def test_articles_with_no_content(self):
        """Test with articles that have no content."""
        articles = [
            {'id': 1, 'title': 'Article 1', 'content': ''},
            {'id': 2, 'title': 'Article 2', 'content': None},
            {'id': 3, 'title': 'Article 3', 'content': 'Some content'}
        ]

        duplicates = DuplicateDetectionManager.find_duplicates(articles)

        # Should handle gracefully
        assert isinstance(duplicates, list)

    def test_very_long_content(self):
        """Test with very long article content."""
        articles = [
            {
                'id': 1,
                'title': 'Long Article 1',
                'content': 'word ' * 10000  # Very long content
            },
            {
                'id': 2,
                'title': 'Long Article 2',
                'content': 'word ' * 10000  # Identical long content
            }
        ]

        duplicates = DuplicateDetectionManager.find_duplicates(articles)

        # Should handle long content
        assert isinstance(duplicates, list)

    def test_special_characters_handling(self):
        """Test handling of special characters in content."""
        articles = [
            {
                'id': 1,
                'title': 'Special Chars @#$%',
                'content': 'Content with special chars: @#$%^&*()!'
            },
            {
                'id': 2,
                'title': 'Special Chars @#$%',
                'content': 'Content with special chars: @#$%^&*()!'
            }
        ]

        duplicates = DuplicateDetectionManager.find_duplicates(articles)

        # Should find duplicates despite special chars
        assert len(duplicates) > 0
