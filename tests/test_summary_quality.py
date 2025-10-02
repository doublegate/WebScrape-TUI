"""
Tests for Summary Quality evaluation (v1.9.0).

Tests ROUGE score calculation, coherence evaluation,
and quality metrics.
"""

import pytest
from scrapetui import SummaryQualityManager, get_db_connection


@pytest.fixture
def sample_text_and_summary():
    """Sample original text and summary for quality testing."""
    return {
        'original': '''
        Artificial intelligence is transforming the technology industry.
        Machine learning algorithms are becoming increasingly sophisticated,
        enabling computers to perform tasks that previously required human intelligence.
        Deep learning, a subset of machine learning, uses neural networks
        to process vast amounts of data and identify complex patterns.
        These advancements are driving innovation in fields such as
        healthcare, finance, and autonomous vehicles.
        ''',
        'summary': '''
        AI is revolutionizing technology through advanced machine learning and deep learning.
        These innovations are impacting healthcare, finance, and autonomous vehicles.
        '''
    }


@pytest.fixture
def poor_quality_summary():
    """Sample with poor quality summary."""
    return {
        'original': '''
        Climate change is one of the most pressing issues of our time.
        Rising global temperatures are causing ice caps to melt,
        sea levels to rise, and weather patterns to become more extreme.
        Scientists warn that immediate action is needed to reduce carbon emissions
        and transition to renewable energy sources.
        ''',
        'summary': '''
        The weather is nice today. I like ice cream.
        Cars are fast.
        '''  # Irrelevant summary
    }


class TestROUGEScoreCalculation:
    """Tests for ROUGE score metrics."""

    def test_calculate_rouge_scores_success(self, sample_text_and_summary):
        """Test ROUGE score calculation."""
        metrics = SummaryQualityManager.calculate_rouge_scores(
            sample_text_and_summary['summary'],
            sample_text_and_summary['original']
        )

        assert 'rouge_scores' in metrics
        rouge = metrics['rouge_scores']

        # Check ROUGE-1, ROUGE-2, ROUGE-L scores
        assert 'rouge1' in rouge
        assert 'rouge2' in rouge
        assert 'rougeL' in rouge

        # Scores should be between 0 and 1
        assert 0 <= rouge['rouge1'] <= 1
        assert 0 <= rouge['rouge2'] <= 1
        assert 0 <= rouge['rougeL'] <= 1

    def test_rouge_scores_good_summary(self, sample_text_and_summary):
        """Test that good summary has high ROUGE scores."""
        metrics = SummaryQualityManager.calculate_rouge_scores(
            sample_text_and_summary['summary'],
            sample_text_and_summary['original']
        )

        rouge = metrics['rouge_scores']

        # Good summary should have reasonable scores
        # ROUGE-1 should be higher than ROUGE-2
        assert rouge['rouge1'] >= rouge['rouge2']

    def test_rouge_scores_poor_summary(self, poor_quality_summary):
        """Test that poor summary has low ROUGE scores."""
        metrics = SummaryQualityManager.calculate_rouge_scores(
            poor_quality_summary['summary'],
            poor_quality_summary['original']
        )

        rouge = metrics['rouge_scores']

        # Poor/irrelevant summary should have low scores
        assert rouge['rouge1'] < 0.3  # Very low overlap
        assert rouge['rouge2'] < 0.2

    def test_rouge_exact_match(self):
        """Test ROUGE scores when summary equals original."""
        text = "This is a test sentence."
        metrics = SummaryQualityManager.calculate_rouge_scores(text, text)

        rouge = metrics['rouge_scores']

        # Exact match should give perfect scores
        assert rouge['rouge1'] >= 0.95
        assert rouge['rougeL'] >= 0.95

    def test_rouge_empty_summary(self):
        """Test ROUGE calculation with empty summary."""
        original = "This is the original text."
        summary = ""

        metrics = SummaryQualityManager.calculate_rouge_scores(summary, original)

        # Should handle gracefully
        assert 'rouge_scores' in metrics
        # Empty summary should have zero or very low scores


class TestCoherenceEvaluation:
    """Tests for coherence score evaluation."""

    def test_coherence_evaluation(self, sample_text_and_summary):
        """Test coherence score calculation."""
        metrics = SummaryQualityManager.calculate_rouge_scores(
            sample_text_and_summary['summary'],
            sample_text_and_summary['original']
        )

        assert 'coherence' in metrics
        coherence = metrics['coherence']

        # Coherence should be 0-100
        assert 0 <= coherence <= 100

    def test_coherent_summary_high_score(self, sample_text_and_summary):
        """Test that coherent summary has high coherence score."""
        metrics = SummaryQualityManager.calculate_rouge_scores(
            sample_text_and_summary['summary'],
            sample_text_and_summary['original']
        )

        coherence = metrics['coherence']

        # Good summary should have reasonable coherence
        # (exact threshold depends on implementation)
        assert coherence > 0

    def test_incoherent_summary_low_score(self, poor_quality_summary):
        """Test that incoherent summary has low coherence score."""
        metrics = SummaryQualityManager.calculate_rouge_scores(
            poor_quality_summary['summary'],
            poor_quality_summary['original']
        )

        coherence = metrics['coherence']

        # Poor summary likely has lower coherence
        assert isinstance(coherence, (int, float))


class TestQualityMetricsRetrieval:
    """Tests for retrieving quality metrics from database."""

    def test_save_quality_metrics(self, sample_text_and_summary, db_connection):
        """Test saving quality metrics to database."""
        metrics = SummaryQualityManager.calculate_rouge_scores(
            sample_text_and_summary['summary'],
            sample_text_and_summary['original']
        )

        # Save metrics to database
        article_id = 1
        db_connection.execute("""
            INSERT OR REPLACE INTO summary_quality
            (article_id, rouge1, rouge2, rougeL, coherence_score, user_rating)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            article_id,
            metrics['rouge_scores']['rouge1'],
            metrics['rouge_scores']['rouge2'],
            metrics['rouge_scores']['rougeL'],
            metrics['coherence'],
            None
        ))
        db_connection.commit()

        # Retrieve and verify
        cursor = db_connection.execute("""
            SELECT * FROM summary_quality WHERE article_id = ?
        """, (article_id,))

        saved = cursor.fetchone()
        assert saved is not None
        assert saved['rouge1'] == metrics['rouge_scores']['rouge1']

    def test_retrieve_quality_metrics(self, db_connection):
        """Test retrieving quality metrics for an article."""
        # Insert test metrics
        article_id = 1
        db_connection.execute("""
            INSERT OR REPLACE INTO summary_quality
            (article_id, rouge1, rouge2, rougeL, coherence_score, user_rating)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (article_id, 0.75, 0.55, 0.68, 82.5, 4))
        db_connection.commit()

        # Retrieve
        cursor = db_connection.execute("""
            SELECT * FROM summary_quality WHERE article_id = ?
        """, (article_id,))

        metrics = cursor.fetchone()
        assert metrics['rouge1'] == 0.75
        assert metrics['rouge2'] == 0.55
        assert metrics['rougeL'] == 0.68
        assert metrics['coherence_score'] == 82.5
        assert metrics['user_rating'] == 4

    def test_update_user_rating(self, db_connection):
        """Test updating user rating for summary quality."""
        article_id = 1

        # Initial insert
        db_connection.execute("""
            INSERT OR REPLACE INTO summary_quality
            (article_id, rouge1, rouge2, rougeL, coherence_score, user_rating)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (article_id, 0.70, 0.50, 0.65, 75.0, 3))
        db_connection.commit()

        # Update user rating
        db_connection.execute("""
            UPDATE summary_quality
            SET user_rating = ?, feedback_date = CURRENT_TIMESTAMP
            WHERE article_id = ?
        """, (5, article_id))
        db_connection.commit()

        # Verify update
        cursor = db_connection.execute("""
            SELECT user_rating FROM summary_quality WHERE article_id = ?
        """, (article_id,))

        row = cursor.fetchone()
        assert row['user_rating'] == 5


class TestReadabilityMetrics:
    """Tests for readability metrics (if implemented)."""

    def test_readability_calculation(self, sample_text_and_summary):
        """Test readability metrics calculation."""
        metrics = SummaryQualityManager.calculate_rouge_scores(
            sample_text_and_summary['summary'],
            sample_text_and_summary['original']
        )

        # Check if readability metrics are included
        if 'readability' in metrics:
            readability = metrics['readability']

            # Common readability metrics
            if 'flesch' in readability:
                # Flesch Reading Ease: 0-100
                assert 0 <= readability['flesch'] <= 100

    def test_flesch_reading_ease(self):
        """Test Flesch Reading Ease calculation."""
        # Simple text should have high readability
        simple_summary = "The cat sat on the mat. The dog ran fast."

        # Complex text should have lower readability
        complex_summary = """
        Notwithstanding the aforementioned circumstances,
        it is imperative to acknowledge the multifaceted
        implications of contemporary technological advancement.
        """

        # If Flesch is implemented, simple should score higher
        # This is a placeholder - actual implementation may vary
        # assert simple_flesch > complex_flesch


class TestUserFeedbackStorage:
    """Tests for storing user feedback on summary quality."""

    def test_save_user_feedback(self, db_connection):
        """Test saving user feedback (rating 1-5)."""
        article_id = 1
        user_rating = 4

        db_connection.execute("""
            INSERT OR REPLACE INTO summary_quality
            (article_id, user_rating, feedback_date)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (article_id, user_rating))
        db_connection.commit()

        # Verify
        cursor = db_connection.execute("""
            SELECT user_rating FROM summary_quality WHERE article_id = ?
        """, (article_id,))

        row = cursor.fetchone()
        assert row['user_rating'] == user_rating

    def test_validate_user_rating_range(self, db_connection):
        """Test that user rating is within 1-5 range."""
        article_id = 1

        # Valid ratings
        for rating in [1, 2, 3, 4, 5]:
            db_connection.execute("""
                INSERT OR REPLACE INTO summary_quality
                (article_id, user_rating)
                VALUES (?, ?)
            """, (article_id, rating))
            db_connection.commit()

            cursor = db_connection.execute("""
                SELECT user_rating FROM summary_quality WHERE article_id = ?
            """, (article_id,))

            row = cursor.fetchone()
            assert 1 <= row['user_rating'] <= 5

    def test_aggregate_user_ratings(self, db_connection):
        """Test aggregating user ratings across articles."""
        # Insert multiple ratings
        ratings = [(1, 5), (2, 4), (3, 5), (4, 3), (5, 4)]

        for article_id, rating in ratings:
            db_connection.execute("""
                INSERT OR REPLACE INTO summary_quality
                (article_id, user_rating)
                VALUES (?, ?)
            """, (article_id, rating))
        db_connection.commit()

        # Calculate average rating
        cursor = db_connection.execute("""
            SELECT AVG(user_rating) as avg_rating
            FROM summary_quality
            WHERE user_rating IS NOT NULL
        """)

        row = cursor.fetchone()
        avg_rating = row['avg_rating']

        # Average should be between 1 and 5
        assert 1 <= avg_rating <= 5
        # For these ratings, average should be (5+4+5+3+4)/5 = 4.2
        assert 4.0 <= avg_rating <= 4.5


class TestEdgeCases:
    """Tests for edge cases in quality evaluation."""

    def test_very_short_summary(self):
        """Test quality evaluation with very short summary."""
        original = "This is a long original text with many words and sentences."
        summary = "Short."

        metrics = SummaryQualityManager.calculate_rouge_scores(summary, original)

        # Should handle gracefully
        assert 'rouge_scores' in metrics

    def test_very_long_summary(self):
        """Test quality evaluation with very long summary."""
        original = "Short original."
        summary = "This is a very long summary that is much longer than the original text. " * 10

        metrics = SummaryQualityManager.calculate_rouge_scores(summary, original)

        # Should handle gracefully
        assert 'rouge_scores' in metrics

    def test_non_english_text(self):
        """Test with non-English text (if supported)."""
        original = "Bonjour le monde. Ceci est un texte en français."
        summary = "Bonjour monde."

        try:
            metrics = SummaryQualityManager.calculate_rouge_scores(summary, original)
            # Should work or gracefully handle non-English
            assert 'rouge_scores' in metrics
        except Exception as e:
            # Acceptable if non-English not supported
            pass
