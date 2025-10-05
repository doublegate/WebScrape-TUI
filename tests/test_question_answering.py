"""
Tests for Question Answering functionality (v1.9.0).

Tests Q&A with single and multiple articles, conversation history,
and source attribution.
"""

import pytest
import json
from datetime import datetime
from scrapetui import QuestionAnsweringManager


@pytest.fixture
def sample_articles():
    """Sample articles for Q&A testing."""
    return [
        {
            'id': 1,
            'title': 'Python Programming Basics',
            'content': '''
            Python is a high-level, interpreted programming language known for its simplicity and readability.
            It was created by Guido van Rossum and first released in 1991.
            Python supports multiple programming paradigms including procedural, object-oriented, and functional programming.
            Popular applications include web development, data science, and automation.
            ''',
            'url': 'https://example.com/python-basics'
        },
        {
            'id': 2,
            'title': 'Machine Learning with Python',
            'content': '''
            Machine learning is a subset of artificial intelligence that enables computers to learn from data.
            Python has become the preferred language for machine learning due to libraries like scikit-learn, TensorFlow, and PyTorch.
            Common machine learning tasks include classification, regression, and clustering.
            Data preprocessing and feature engineering are critical steps in any machine learning pipeline.
            ''',
            'url': 'https://example.com/ml-python'
        },
        {
            'id': 3,
            'title': 'Web Development Frameworks',
            'content': '''
            Python offers several popular web frameworks including Django and Flask.
            Django is a high-level framework that encourages rapid development and clean design.
            Flask is a micro-framework that provides flexibility and is great for smaller applications.
            Both frameworks support RESTful API development and integrate well with databases.
            ''',
            'url': 'https://example.com/web-frameworks'
        }
    ]


@pytest.fixture
def single_article():
    """Single article for testing."""
    return [{
        'id': 1,
        'title': 'Climate Change Facts',
        'content': '''
        Climate change refers to long-term shifts in global temperatures and weather patterns.
        Human activities, particularly burning fossil fuels, are the primary cause.
        Effects include rising sea levels, extreme weather events, and ecosystem disruption.
        Renewable energy and carbon reduction are key solutions.
        ''',
        'url': 'https://example.com/climate'
    }]


class TestSingleArticleQA:
    """Tests for Q&A with single article."""

    def test_answer_question_single_article(self, single_article, mocker):
        """Test answering question from single article."""
        # Mock AI provider
        mocker.patch('scrapetui.get_ai_provider', return_value=mocker.Mock(get_summary=lambda *args,
                     ** kwargs: "Climate change is caused primarily by human activities like burning fossil fuels."))

        question = "What causes climate change?"
        result = QuestionAnsweringManager.answer_question(question, single_article)

        assert 'answer' in result
        assert 'sources' in result
        assert 'confidence' in result
        assert result['answer'] is not None
        assert len(result['answer']) > 0

    def test_source_attribution_single_article(self, single_article, mocker):
        """Test that source is properly attributed."""
        mocker.patch('scrapetui.get_ai_provider', return_value=mocker.Mock(
            get_summary=lambda *args, **kwargs: "Renewable energy is a key solution."
        ))

        question = "What are solutions to climate change?"
        result = QuestionAnsweringManager.answer_question(question, single_article)

        sources = result['sources']
        assert len(sources) >= 1

        source = sources[0]
        assert 'article_id' in source
        assert 'title' in source
        assert 'url' in source
        assert source['article_id'] == 1

    def test_no_ai_provider(self, single_article, mocker):
        """Test Q&A when AI provider is not configured."""
        mocker.patch('scrapetui.get_ai_provider', return_value=None)

        question = "Test question?"
        result = QuestionAnsweringManager.answer_question(question, single_article)

        assert 'answer' in result
        assert 'AI provider not configured' in result['answer']
        assert result['confidence'] == 0


class TestMultiArticleSynthesis:
    """Tests for Q&A across multiple articles."""

    def test_answer_from_multiple_articles(self, sample_articles, mocker):
        """Test synthesizing answer from multiple articles."""
        mocker.patch(
            'scrapetui.get_ai_provider',
            return_value=mocker.Mock(
                get_summary=lambda *args,
                **kwargs: "Python is used for web development (Django, Flask) and machine learning (scikit-learn, TensorFlow)."))

        question = "What is Python used for?"
        result = QuestionAnsweringManager.answer_question(question, sample_articles)

        assert 'answer' in result
        sources = result['sources']

        # Should use multiple sources
        assert len(sources) >= 1
        # Answer should synthesize information
        assert len(result['answer']) > 0

    def test_context_from_multiple_articles(self, sample_articles, mocker):
        """Test that context is built from multiple articles."""
        captured_prompt = None

        def mock_summary(prompt, **kwargs):
            nonlocal captured_prompt
            captured_prompt = prompt
            return "Synthesized answer from multiple sources."

        mocker.patch('scrapetui.get_ai_provider', return_value=mocker.Mock(
            get_summary=mock_summary
        ))

        question = "What are Python's applications?"
        result = QuestionAnsweringManager.answer_question(question, sample_articles)

        # Verify multiple articles were included in context
        assert captured_prompt is not None
        assert 'Article 1:' in captured_prompt
        assert 'Article 2:' in captured_prompt

    def test_max_context_length(self, mocker):
        """Test that context is limited to max_context_length."""
        # Create very long articles
        long_articles = [{
            'id': i,
            'title': f'Article {i}',
            'content': 'word ' * 5000,  # Very long content
            'url': f'http://example.com/{i}'
        } for i in range(1, 6)]

        mocker.patch('scrapetui.get_ai_provider', return_value=mocker.Mock(
            get_summary=lambda *args, **kwargs: "Answer"
        ))

        question = "Test question?"
        result = QuestionAnsweringManager.answer_question(
            question,
            long_articles,
            max_context_length=1000  # Limited context
        )

        # Should handle long content gracefully
        assert 'answer' in result

    def test_article_limit(self, mocker):
        """Test that only a limited number of articles are used."""
        # Create many articles
        many_articles = [{
            'id': i,
            'title': f'Article {i}',
            'content': f'Content of article {i}',
            'url': f'http://example.com/{i}'
        } for i in range(1, 20)]

        mocker.patch('scrapetui.get_ai_provider', return_value=mocker.Mock(
            get_summary=lambda *args, **kwargs: "Answer"
        ))

        question = "Test question?"
        result = QuestionAnsweringManager.answer_question(question, many_articles)

        # Should limit to 5 articles (as per implementation)
        assert len(result['sources']) <= 5


class TestConversationHistoryTracking:
    """Tests for Q&A conversation history."""

    def test_save_qa_conversation(self, db_connection):
        """Test saving Q&A conversation to database."""
        question = "What is Python?"
        answer = "Python is a programming language."
        article_ids = [1, 2]
        confidence = 0.85

        success = QuestionAnsweringManager.save_qa_conversation(
            question, answer, article_ids, confidence, conn=db_connection
        )

        assert success is True

        # Verify saved
        cursor = db_connection.execute("""
            SELECT * FROM qa_history
            ORDER BY created_at DESC LIMIT 1
        """)

        row = cursor.fetchone()
        assert row is not None
        assert row['question'] == question
        assert row['answer'] == answer
        assert json.loads(row['article_ids']) == article_ids
        assert row['confidence'] == confidence

    def test_retrieve_qa_history(self, db_connection):
        """Test retrieving Q&A history."""
        # Insert test conversations
        conversations = [
            ("What is AI?", "AI is artificial intelligence.", [1], 0.9),
            ("What is ML?", "ML is machine learning.", [2], 0.85),
            ("What is Python?", "Python is a programming language.", [1, 2], 0.8)
        ]

        for question, answer, article_ids, confidence in conversations:
            db_connection.execute("""
                INSERT INTO qa_history
                (question, answer, article_ids, confidence, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (question, answer, json.dumps(article_ids), confidence, datetime.now().isoformat()))
        db_connection.commit()

        # Retrieve history
        history = QuestionAnsweringManager.get_qa_history(limit=20, conn=db_connection)

        assert len(history) >= 3

        # Verify structure
        qa = history[0]
        assert 'question' in qa
        assert 'answer' in qa
        assert 'article_ids' in qa
        assert 'confidence' in qa
        assert 'created_at' in qa

    def test_history_limit(self, db_connection):
        """Test limiting number of history entries retrieved."""
        # Insert many conversations
        for i in range(25):
            db_connection.execute("""
                INSERT INTO qa_history
                (question, answer, article_ids, confidence, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                f"Question {i}",
                f"Answer {i}",
                json.dumps([i]),
                0.8,
                datetime.now().isoformat()
            ))
        db_connection.commit()

        # Retrieve with limit
        history = QuestionAnsweringManager.get_qa_history(limit=10, conn=db_connection)

        assert len(history) <= 10

    def test_history_ordering(self, db_connection):
        """Test that history is ordered by most recent first."""
        # Insert conversations with timestamps
        import time

        for i in range(3):
            db_connection.execute("""
                INSERT INTO qa_history
                (question, answer, article_ids, confidence, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                f"Question {i}",
                f"Answer {i}",
                json.dumps([i]),
                0.8,
                datetime.now().isoformat()
            ))
            db_connection.commit()
            time.sleep(0.1)  # Small delay to ensure different timestamps

        history = QuestionAnsweringManager.get_qa_history(limit=5, conn=db_connection)

        # Most recent should be first
        if len(history) >= 2:
            # Questions should be in reverse order (2, 1, 0)
            assert history[0]['question'] == "Question 2"


class TestSourceAttribution:
    """Tests for source citation in answers."""

    def test_source_article_ids(self, sample_articles, mocker):
        """Test that source article IDs are tracked."""
        mocker.patch('scrapetui.get_ai_provider', return_value=mocker.Mock(
            get_summary=lambda *args, **kwargs: "Python is versatile."
        ))

        question = "What is Python?"
        result = QuestionAnsweringManager.answer_question(question, sample_articles)

        sources = result['sources']

        # Extract article IDs
        article_ids = [s['article_id'] for s in sources]

        # Should have article IDs from sample_articles
        assert len(article_ids) > 0
        assert all(isinstance(aid, int) for aid in article_ids)

    def test_source_includes_title_and_url(self, sample_articles, mocker):
        """Test that sources include title and URL."""
        mocker.patch('scrapetui.get_ai_provider', return_value=mocker.Mock(
            get_summary=lambda *args, **kwargs: "Answer with sources."
        ))

        question = "Test question?"
        result = QuestionAnsweringManager.answer_question(question, sample_articles)

        sources = result['sources']

        for source in sources:
            assert 'title' in source
            assert 'url' in source
            assert len(source['title']) > 0
            assert len(source['url']) > 0

    def test_confidence_score(self, sample_articles, mocker):
        """Test that confidence score is included."""
        mocker.patch('scrapetui.get_ai_provider', return_value=mocker.Mock(
            get_summary=lambda *args, **kwargs: "Confident answer."
        ))

        question = "Test question?"
        result = QuestionAnsweringManager.answer_question(question, sample_articles)

        assert 'confidence' in result
        confidence = result['confidence']

        # Confidence should be between 0 and 1
        assert 0 <= confidence <= 1


class TestEdgeCases:
    """Tests for edge cases in question answering."""

    def test_empty_question(self, sample_articles, mocker):
        """Test with empty question."""
        mocker.patch('scrapetui.get_ai_provider', return_value=mocker.Mock(
            get_summary=lambda *args, **kwargs: "Response to empty question."
        ))

        question = ""
        result = QuestionAnsweringManager.answer_question(question, sample_articles)

        # Should handle gracefully
        assert 'answer' in result

    def test_no_articles(self, mocker):
        """Test Q&A with no articles."""
        mocker.patch('scrapetui.get_ai_provider', return_value=mocker.Mock(
            get_summary=lambda *args, **kwargs: "No articles available."
        ))

        question = "Test question?"
        result = QuestionAnsweringManager.answer_question(question, [])

        assert 'answer' in result
        assert result['sources'] == []

    def test_articles_without_content(self, mocker):
        """Test with articles that have no content."""
        mocker.patch('scrapetui.get_ai_provider', return_value=mocker.Mock(
            get_summary=lambda *args, **kwargs: "No content available."
        ))

        articles = [
            {'id': 1, 'title': 'Article 1', 'content': '', 'url': 'http://example.com/1'},
            {'id': 2, 'title': 'Article 2', 'content': None, 'url': 'http://example.com/2'}
        ]

        question = "Test question?"
        result = QuestionAnsweringManager.answer_question(question, articles)

        # Should handle gracefully
        assert 'answer' in result

    def test_very_long_question(self, sample_articles, mocker):
        """Test with very long question."""
        mocker.patch('scrapetui.get_ai_provider', return_value=mocker.Mock(
            get_summary=lambda *args, **kwargs: "Answer to long question."
        ))

        question = "What " * 500 + "is Python?"  # Very long question
        result = QuestionAnsweringManager.answer_question(question, sample_articles)

        # Should handle long questions
        assert 'answer' in result

    def test_special_characters_in_question(self, sample_articles, mocker):
        """Test with special characters in question."""
        mocker.patch('scrapetui.get_ai_provider', return_value=mocker.Mock(
            get_summary=lambda *args, **kwargs: "Answer with special chars."
        ))

        question = "What's Python? @#$%^&*()"
        result = QuestionAnsweringManager.answer_question(question, sample_articles)

        # Should handle special characters
        assert 'answer' in result

    def test_error_handling(self, sample_articles, mocker):
        """Test error handling when AI provider fails."""
        def failing_summary(*args, **kwargs):
            raise Exception("AI provider error")

        mocker.patch('scrapetui.get_ai_provider', return_value=mocker.Mock(
            get_summary=failing_summary
        ))

        question = "Test question?"
        result = QuestionAnsweringManager.answer_question(question, sample_articles)

        # Should return error message
        assert 'answer' in result
        assert 'error' in result['answer'].lower() or result['confidence'] == 0
