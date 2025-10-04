#!/usr/bin/env python3
"""Summary quality assessment using ROUGE scores and coherence metrics.

This module provides comprehensive summary quality evaluation including
ROUGE-N scores, coherence analysis, and overall quality scoring.
"""

from typing import Dict, Any, List, Optional
import re
from collections import Counter
import json

try:
    from ..utils.logging import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class SummaryQualityManager:
    """Manager for assessing summary quality."""

    @staticmethod
    def calculate_rouge_scores(summary: str, reference: str) -> Dict[str, float]:
        """
        Calculate ROUGE scores for summary quality.

        ROUGE (Recall-Oriented Understudy for Gisting Evaluation) measures
        n-gram overlap between summary and reference text.

        Args:
            summary: Generated summary text
            reference: Reference text (original content)

        Returns:
            Dict with 'rouge-1', 'rouge-2', 'rouge-l' scores (0.0 to 1.0)
        """
        if not summary or not reference:
            return {'rouge-1': 0.0, 'rouge-2': 0.0, 'rouge-l': 0.0}

        # Tokenize (simple word-based tokenization)
        summary_tokens = re.findall(r'\w+', summary.lower())
        reference_tokens = re.findall(r'\w+', reference.lower())

        if not summary_tokens or not reference_tokens:
            return {'rouge-1': 0.0, 'rouge-2': 0.0, 'rouge-l': 0.0}

        # ROUGE-1: Unigram overlap (F1 score)
        summary_unigrams = Counter(summary_tokens)
        reference_unigrams = Counter(reference_tokens)

        overlapping_unigrams = sum((summary_unigrams & reference_unigrams).values())

        if len(summary_tokens) > 0 and len(reference_tokens) > 0:
            rouge_1_precision = overlapping_unigrams / len(summary_tokens)
            rouge_1_recall = overlapping_unigrams / len(reference_tokens)

            if (rouge_1_precision + rouge_1_recall) > 0:
                rouge_1 = 2 * rouge_1_precision * rouge_1_recall / (rouge_1_precision + rouge_1_recall)
            else:
                rouge_1 = 0.0
        else:
            rouge_1 = 0.0

        # ROUGE-2: Bigram overlap
        summary_bigrams = [
            tuple(summary_tokens[i:i + 2])
            for i in range(len(summary_tokens) - 1)
        ]
        reference_bigrams = [
            tuple(reference_tokens[i:i + 2])
            for i in range(len(reference_tokens) - 1)
        ]

        if summary_bigrams and reference_bigrams:
            summary_bigrams_count = Counter(summary_bigrams)
            reference_bigrams_count = Counter(reference_bigrams)

            overlapping_bigrams = sum((summary_bigrams_count & reference_bigrams_count).values())

            rouge_2_precision = overlapping_bigrams / len(summary_bigrams)
            rouge_2_recall = overlapping_bigrams / len(reference_bigrams)

            if (rouge_2_precision + rouge_2_recall) > 0:
                rouge_2 = 2 * rouge_2_precision * rouge_2_recall / (rouge_2_precision + rouge_2_recall)
            else:
                rouge_2 = 0.0
        else:
            rouge_2 = 0.0

        # ROUGE-L: Longest Common Subsequence
        lcs_length = SummaryQualityManager._lcs_length(summary_tokens, reference_tokens)

        if len(summary_tokens) > 0 and len(reference_tokens) > 0:
            rouge_l_precision = lcs_length / len(summary_tokens)
            rouge_l_recall = lcs_length / len(reference_tokens)

            if (rouge_l_precision + rouge_l_recall) > 0:
                rouge_l = 2 * rouge_l_precision * rouge_l_recall / (rouge_l_precision + rouge_l_recall)
            else:
                rouge_l = 0.0
        else:
            rouge_l = 0.0

        return {
            'rouge-1': round(rouge_1, 4),
            'rouge-2': round(rouge_2, 4),
            'rouge-l': round(rouge_l, 4)
        }

    @staticmethod
    def _lcs_length(seq1: List[str], seq2: List[str]) -> int:
        """
        Calculate longest common subsequence length using dynamic programming.

        Args:
            seq1: First sequence (list of tokens)
            seq2: Second sequence (list of tokens)

        Returns:
            Length of LCS
        """
        m, n = len(seq1), len(seq2)

        # Create DP table
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        # Fill DP table
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i - 1] == seq2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        return dp[m][n]

    @staticmethod
    def assess_coherence(text: str) -> float:
        """
        Assess text coherence using simple heuristic metrics.

        Coherence measures how well sentences flow together. This implementation
        uses sentence length consistency as a proxy for coherence.

        Args:
            text: Input text to assess

        Returns:
            Coherence score (0.0 to 1.0), where higher is better
        """
        if not text or not text.strip():
            return 0.0

        # Split into sentences
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

        if len(sentences) < 2:
            return 0.5  # Single sentence has moderate coherence

        # Calculate sentence length consistency
        lengths = [len(s.split()) for s in sentences]

        if not lengths:
            return 0.0

        avg_length = sum(lengths) / len(lengths)

        if avg_length == 0:
            return 0.0

        # Calculate variance
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)

        # Convert variance to coherence score (lower variance = higher coherence)
        # Normalize using average length to make it scale-invariant
        normalized_variance = variance / (avg_length ** 2) if avg_length > 0 else 0

        coherence = 1.0 / (1.0 + normalized_variance)

        return round(min(1.0, max(0.0, coherence)), 4)

    @staticmethod
    def assess_summary_quality(summary: str, reference: str) -> Dict[str, Any]:
        """
        Comprehensive summary quality assessment.

        Combines ROUGE scores and coherence analysis into overall quality metric.

        Args:
            summary: Generated summary
            reference: Reference text (original content)

        Returns:
            Dict with rouge_scores, coherence, and overall_quality
        """
        rouge_scores = SummaryQualityManager.calculate_rouge_scores(summary, reference)
        coherence = SummaryQualityManager.assess_coherence(summary)

        # Overall quality: weighted average
        # ROUGE-1: 30%, ROUGE-2: 30%, ROUGE-L: 20%, Coherence: 20%
        overall = (
            rouge_scores['rouge-1'] * 0.3 +
            rouge_scores['rouge-2'] * 0.3 +
            rouge_scores['rouge-l'] * 0.2 +
            coherence * 0.2
        )

        return {
            'rouge_scores': rouge_scores,
            'coherence': round(coherence, 4),
            'overall_quality': round(overall, 4)
        }

    @staticmethod
    def calculate_readability(text: str) -> Dict[str, float]:
        """
        Calculate readability metrics (Flesch Reading Ease, etc.).

        Args:
            text: Input text

        Returns:
            Dict with readability metrics
        """
        if not text or not text.strip():
            return {'flesch_reading_ease': 0.0, 'avg_sentence_length': 0.0, 'avg_word_length': 0.0}

        # Count sentences
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        num_sentences = len(sentences)

        # Count words
        words = re.findall(r'\w+', text)
        num_words = len(words)

        # Count syllables (rough approximation)
        syllables = sum(SummaryQualityManager._count_syllables(word) for word in words)

        if num_sentences == 0 or num_words == 0:
            return {'flesch_reading_ease': 0.0, 'avg_sentence_length': 0.0, 'avg_word_length': 0.0}

        # Flesch Reading Ease: 206.835 - 1.015(total words/total sentences) - 84.6(total syllables/total words)
        avg_sentence_length = num_words / num_sentences
        avg_syllables_per_word = syllables / num_words

        flesch_score = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables_per_word
        flesch_score = max(0, min(100, flesch_score))  # Clamp to 0-100

        avg_word_length = sum(len(word) for word in words) / num_words if words else 0

        return {
            'flesch_reading_ease': round(flesch_score, 2),
            'avg_sentence_length': round(avg_sentence_length, 2),
            'avg_word_length': round(avg_word_length, 2)
        }

    @staticmethod
    def _count_syllables(word: str) -> int:
        """
        Count syllables in a word (approximation).

        Args:
            word: Input word

        Returns:
            Estimated syllable count
        """
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel

        # Handle silent 'e' at end
        if word.endswith('e'):
            syllable_count -= 1

        # Ensure at least 1 syllable
        return max(1, syllable_count)

    @staticmethod
    def save_quality_metrics(article_id: int, metrics: Dict[str, Any], conn=None) -> bool:
        """
        Save quality metrics to database.

        Args:
            article_id: ID of the article
            metrics: Quality metrics dict
            conn: Optional database connection

        Returns:
            True if successful
        """
        try:
            from ..core.database import get_db_connection as _get_db_conn
        except ImportError:
            import scrapetui
            _get_db_conn = scrapetui.get_db_connection

        try:
            # Handle context manager if needed
            if conn is not None:
                if hasattr(conn, '__enter__') and not hasattr(conn, 'execute'):
                    conn = conn.__enter__()
                db_conn = conn
                own_conn = False
            else:
                db_conn_mgr = _get_db_conn()
                db_conn = db_conn_mgr.__enter__()
                own_conn = True

            # Ensure table exists
            db_conn.execute("""
                CREATE TABLE IF NOT EXISTS summary_quality_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    rouge_1 REAL,
                    rouge_2 REAL,
                    rouge_l REAL,
                    coherence REAL,
                    overall_quality REAL,
                    user_rating INTEGER,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (article_id) REFERENCES scraped_data(id) ON DELETE CASCADE
                )
            """)

            # Extract metrics
            rouge = metrics.get('rouge_scores', {})
            rouge_1 = rouge.get('rouge-1', 0.0)
            rouge_2 = rouge.get('rouge-2', 0.0)
            rouge_l = rouge.get('rouge-l', 0.0)
            coherence = metrics.get('coherence', 0.0)
            overall = metrics.get('overall_quality', 0.0)

            # Insert metrics
            from datetime import datetime
            db_conn.execute("""
                INSERT INTO summary_quality_metrics
                (article_id, rouge_1, rouge_2, rouge_l, coherence, overall_quality, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (article_id, rouge_1, rouge_2, rouge_l, coherence, overall, datetime.now().isoformat()))

            db_conn.commit()

            if own_conn:
                db_conn_mgr.__exit__(None, None, None)

            return True

        except Exception as e:
            logger.error(f"Failed to save quality metrics: {e}")
            return False

    @staticmethod
    def get_quality_metrics(article_id: int, conn=None) -> Optional[Dict[str, Any]]:
        """
        Retrieve quality metrics from database.

        Args:
            article_id: ID of the article
            conn: Optional database connection

        Returns:
            Dict with quality metrics or None
        """
        try:
            from ..core.database import get_db_connection as _get_db_conn
        except ImportError:
            import scrapetui
            _get_db_conn = scrapetui.get_db_connection

        try:
            # Handle context manager if needed
            if conn is not None:
                if hasattr(conn, '__enter__') and not hasattr(conn, 'execute'):
                    conn = conn.__enter__()
                db_conn = conn
                own_conn = False
            else:
                db_conn_mgr = _get_db_conn()
                db_conn = db_conn_mgr.__enter__()
                own_conn = True

            # Ensure table exists
            db_conn.execute("""
                CREATE TABLE IF NOT EXISTS summary_quality_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    rouge_1 REAL,
                    rouge_2 REAL,
                    rouge_l REAL,
                    coherence REAL,
                    overall_quality REAL,
                    user_rating INTEGER,
                    created_at TEXT NOT NULL
                )
            """)

            row = db_conn.execute("""
                SELECT rouge_1, rouge_2, rouge_l, coherence, overall_quality, user_rating
                FROM summary_quality_metrics
                WHERE article_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (article_id,)).fetchone()

            if own_conn:
                db_conn_mgr.__exit__(None, None, None)

            if not row:
                return None

            return {
                'rouge_scores': {
                    'rouge-1': row[0],
                    'rouge-2': row[1],
                    'rouge-l': row[2]
                },
                'coherence': row[3],
                'overall_quality': row[4],
                'user_rating': row[5]
            }

        except Exception as e:
            logger.error(f"Failed to retrieve quality metrics: {e}")
            return None

    @staticmethod
    def update_user_rating(article_id: int, rating: int, conn=None) -> bool:
        """
        Update user rating for summary quality.

        Args:
            article_id: ID of the article
            rating: User rating (1-5)
            conn: Optional database connection

        Returns:
            True if successful
        """
        if not (1 <= rating <= 5):
            return False

        try:
            from ..core.database import get_db_connection as _get_db_conn
        except ImportError:
            import scrapetui
            _get_db_conn = scrapetui.get_db_connection

        try:
            # Handle context manager if needed
            if conn is not None:
                if hasattr(conn, '__enter__') and not hasattr(conn, 'execute'):
                    conn = conn.__enter__()
                db_conn = conn
                own_conn = False
            else:
                db_conn_mgr = _get_db_conn()
                db_conn = db_conn_mgr.__enter__()
                own_conn = True

            # Update rating
            db_conn.execute("""
                UPDATE summary_quality_metrics
                SET user_rating = ?
                WHERE article_id = ?
                AND id = (
                    SELECT id FROM summary_quality_metrics
                    WHERE article_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                )
            """, (rating, article_id, article_id))

            db_conn.commit()

            if own_conn:
                db_conn_mgr.__exit__(None, None, None)

            return True

        except Exception as e:
            logger.error(f"Failed to update user rating: {e}")
            return False
