"""
Tests for Topic Modeling functionality (v1.9.0).

Tests LDA and NMF topic modeling algorithms, category assignment,
and topic hierarchy creation.
"""

import pytest
from scrapetui import TopicModelingManager


@pytest.fixture
def sample_articles():
    """Sample articles for topic modeling tests."""
    return [{'id': 1,
             'title': 'Python Machine Learning Tutorial',
             'content': 'Python machine learning tutorial covers scikit-learn, tensorflow, and neural networks. Deep learning with Python is essential for modern AI development.'},
            {'id': 2,
             'title': 'Web Development with JavaScript',
             'content': 'JavaScript web development using React, Node.js, and Express. Frontend and backend JavaScript frameworks for building modern web applications.'},
            {'id': 3,
             'title': 'Data Science with Python',
             'content': 'Data science using Python pandas, numpy, and matplotlib. Statistical analysis and data visualization with Python libraries for data scientists.'},
            {'id': 4,
             'title': 'React Native Mobile Development',
             'content': 'Mobile app development with React Native. Building cross-platform mobile applications using JavaScript and React framework for iOS and Android.'},
            {'id': 5,
             'title': 'Deep Learning Fundamentals',
             'content': 'Deep learning fundamentals including neural networks, convolutional networks, and recurrent networks. TensorFlow and PyTorch for deep learning projects.'}]


@pytest.fixture
def single_article():
    """Single article for edge case testing."""
    return [{
        'id': 1,
        'title': 'Test Article',
        'content': 'This is a test article with minimal content.'
    }]


class TestLDATopicModeling:
    """Tests for LDA topic modeling."""

    def test_lda_topic_modeling_success(self, sample_articles):
        """Test LDA topic modeling with sample articles."""
        result = TopicModelingManager.perform_lda_topic_modeling(
            sample_articles,
            num_topics=2,
            passes=10
        )

        assert 'topics' in result
        assert 'assignments' in result
        assert len(result['topics']) == 2
        assert result['num_articles'] == 5

        # Check topic structure
        topic = result['topics'][0]
        assert 'id' in topic
        assert 'words' in topic
        assert 'weights' in topic
        assert 'label' in topic
        assert len(topic['words']) == 10  # Default top 10 words

    def test_lda_topic_modeling_empty_articles(self):
        """Test LDA topic modeling with empty article list."""
        result = TopicModelingManager.perform_lda_topic_modeling(
            [],
            num_topics=2
        )

        assert 'error' in result
        assert result['topics'] == []
        assert result['assignments'] == {}

    def test_lda_single_article(self, single_article):
        """Test LDA topic modeling with single article."""
        result = TopicModelingManager.perform_lda_topic_modeling(
            single_article,
            num_topics=2
        )

        assert 'error' in result
        assert 'at least 2 articles' in result['error'].lower()

    def test_lda_topic_assignments(self, sample_articles):
        """Test that articles are assigned to topics."""
        result = TopicModelingManager.perform_lda_topic_modeling(
            sample_articles,
            num_topics=2
        )

        assignments = result['assignments']
        assert len(assignments) > 0

        # Check assignment structure
        for article_id, assignment in assignments.items():
            assert 'topic_id' in assignment
            assert 'confidence' in assignment
            assert 'all_topics' in assignment
            assert 0 <= assignment['confidence'] <= 1
            assert 0 <= assignment['topic_id'] < 2

    def test_lda_with_custom_parameters(self, sample_articles):
        """Test LDA with custom number of topics and passes."""
        result = TopicModelingManager.perform_lda_topic_modeling(
            sample_articles,
            num_topics=3,
            passes=5
        )

        assert len(result['topics']) == 3
        assert result['num_articles'] == 5


class TestNMFTopicModeling:
    """Tests for NMF topic modeling."""

    def test_nmf_topic_modeling_success(self, sample_articles):
        """Test NMF topic modeling with sample articles."""
        result = TopicModelingManager.perform_nmf_topic_modeling(
            sample_articles,
            num_topics=2
        )

        assert 'topics' in result
        assert 'assignments' in result
        assert len(result['topics']) == 2
        assert result['num_articles'] == 5

    def test_nmf_topic_modeling_empty_articles(self):
        """Test NMF topic modeling with empty article list."""
        result = TopicModelingManager.perform_nmf_topic_modeling(
            [],
            num_topics=2
        )

        assert 'error' in result
        assert result['topics'] == []

    def test_nmf_single_article(self, single_article):
        """Test NMF topic modeling with single article."""
        result = TopicModelingManager.perform_nmf_topic_modeling(
            single_article,
            num_topics=2
        )

        assert 'error' in result

    def test_nmf_topic_structure(self, sample_articles):
        """Test NMF topic structure."""
        result = TopicModelingManager.perform_nmf_topic_modeling(
            sample_articles,
            num_topics=2
        )

        topic = result['topics'][0]
        assert 'id' in topic
        assert 'words' in topic
        assert 'weights' in topic
        assert 'label' in topic


class TestCategoryAssignment:
    """Tests for automatic category assignment."""

    def test_assign_categories_to_articles(self, sample_articles, db_connection):
        """Test automatic category assignment to articles."""
        # First, run topic modeling
        result = TopicModelingManager.perform_lda_topic_modeling(
            sample_articles,
            num_topics=2
        )

        assignments = result['assignments']

        # Assign categories based on topics
        categories = {}
        for article_id, assignment in assignments.items():
            topic_id = assignment['topic_id']
            topic_label = result['topics'][topic_id]['label']
            categories[article_id] = topic_label

        assert len(categories) == len(sample_articles)
        # Verify all articles got a category
        for article in sample_articles:
            assert article['id'] in categories

    def test_category_hierarchy(self, sample_articles):
        """Test creation of category hierarchies."""
        result = TopicModelingManager.perform_lda_topic_modeling(
            sample_articles,
            num_topics=3
        )

        # Build hierarchy based on topic relationships
        hierarchy = {}
        for topic in result['topics']:
            parent_category = topic['words'][0]  # Use top word as parent
            hierarchy[topic['id']] = {
                'parent': parent_category,
                'children': topic['words'][1:3]
            }

        assert len(hierarchy) == 3
        for topic_id, structure in hierarchy.items():
            assert 'parent' in structure
            assert 'children' in structure


class TestMultiLabelClassification:
    """Tests for multi-label topic classification."""

    def test_multi_label_topic_assignment(self, sample_articles):
        """Test that articles can belong to multiple topics."""
        result = TopicModelingManager.perform_lda_topic_modeling(
            sample_articles,
            num_topics=3
        )

        # Check that articles have distribution across topics
        for article_id, assignment in result['assignments'].items():
            all_topics = assignment['all_topics']
            assert len(all_topics) > 0
            # Sum of all topic probabilities should be close to 1
            total_prob = sum(prob for _, prob in all_topics)
            assert 0.9 <= total_prob <= 1.1

    def test_topic_threshold_filtering(self, sample_articles):
        """Test filtering topics by confidence threshold."""
        result = TopicModelingManager.perform_lda_topic_modeling(
            sample_articles,
            num_topics=3
        )

        threshold = 0.2
        filtered_assignments = {}

        for article_id, assignment in result['assignments'].items():
            relevant_topics = [
                (topic_id, prob)
                for topic_id, prob in assignment['all_topics']
                if prob >= threshold
            ]
            if relevant_topics:
                filtered_assignments[article_id] = relevant_topics

        # Verify filtering worked
        assert len(filtered_assignments) > 0
        for article_id, topics in filtered_assignments.items():
            for topic_id, prob in topics:
                assert prob >= threshold


class TestTopicModelingEdgeCases:
    """Tests for edge cases and error handling."""

    def test_articles_with_no_content(self):
        """Test topic modeling with articles that have no content."""
        articles = [
            {'id': 1, 'title': 'Article 1', 'content': ''},
            {'id': 2, 'title': 'Article 2', 'content': None},
        ]

        result = TopicModelingManager.perform_lda_topic_modeling(articles)
        assert 'error' in result

    def test_articles_with_short_content(self):
        """Test topic modeling with very short content."""
        articles = [
            {'id': 1, 'title': 'A', 'content': 'a b c'},
            {'id': 2, 'title': 'B', 'content': 'd e f'},
        ]

        result = TopicModelingManager.perform_lda_topic_modeling(articles, num_topics=2)
        # Should handle gracefully even with minimal content
        assert 'topics' in result or 'error' in result

    def test_large_num_topics(self, sample_articles):
        """Test requesting more topics than reasonable."""
        # Request more topics than articles
        result = TopicModelingManager.perform_lda_topic_modeling(
            sample_articles,
            num_topics=10  # More than 5 articles
        )

        # Should handle gracefully
        assert 'topics' in result or 'error' in result
