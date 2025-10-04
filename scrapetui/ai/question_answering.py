#!/usr/bin/env python3
"""Question answering system for article content.

This module provides question answering capabilities using TF-IDF-based
relevance scoring and optional AI provider integration for generating answers.
"""

from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

try:
    from ..utils.logging import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class QuestionAnsweringManager:
    """Manager for question answering from article content."""

    def __init__(self):
        """Initialize the Question Answering Manager."""
        self._vectorizer = None

    @staticmethod
    def answer_question(
        question: str,
        articles: List[Dict[str, Any]],
        top_n: int = 5,
        max_context_length: int = 10000
    ) -> Dict[str, Any]:
        """
        Answer a question based on article content.

        Uses TF-IDF to find relevant articles, then uses AI provider if available
        to generate a natural language answer. Falls back to extractive answer
        if no AI provider is configured.

        Args:
            question: The question to answer
            articles: List of article dicts with 'content', 'title', 'id', 'url' keys
            top_n: Number of top relevant articles to use (default: 5)
            max_context_length: Maximum context length for AI provider (default: 10000)

        Returns:
            Dict with 'answer', 'sources', 'confidence' keys
        """
        if not question or not question.strip():
            # Empty question
            return {
                'answer': None,
                'sources': [],
                'confidence': 0.0
            }

        if not articles:
            # No articles available
            return {
                'answer': None,
                'sources': [],
                'confidence': 0.0
            }

        # Extract text from articles
        article_texts = []
        article_data = []

        for article in articles:
            text = article.get('content') or article.get('summary') or article.get('title', '')
            if text and text.strip():
                article_texts.append(text)
                article_data.append({
                    'id': article.get('id'),
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'content': text
                })

        if not article_texts:
            # No valid content found
            return {
                'answer': None,
                'sources': [],
                'confidence': 0.0
            }

        # Limit number of articles to process
        if len(article_texts) > top_n:
            article_texts = article_texts[:top_n]
            article_data = article_data[:top_n]

        try:
            # Use TF-IDF to find most relevant articles
            vectorizer = TfidfVectorizer(max_features=500, stop_words='english')

            # Add question to corpus for similarity calculation
            all_texts = article_texts + [question]
            tfidf_matrix = vectorizer.fit_transform(all_texts)

            # Calculate similarity between question and each article
            question_vec = tfidf_matrix[-1]
            article_vecs = tfidf_matrix[:-1]
            similarities = cosine_similarity(question_vec, article_vecs)[0]

            # Sort articles by relevance
            sorted_indices = similarities.argsort()[::-1]

            # Build sources list with relevance scores
            sources = []
            for idx in sorted_indices:
                if similarities[idx] > 0.01:  # Minimum relevance threshold (lowered from 0.05)
                    article = article_data[idx]
                    sources.append({
                        'article_id': article['id'],
                        'title': article['title'],
                        'url': article['url'],
                        'relevance': float(similarities[idx])
                    })

            # If no highly relevant sources, still use the best match if we have articles
            if not sources and len(article_data) > 0:
                # Use the top article even with low relevance
                idx = sorted_indices[0]
                article = article_data[idx]
                sources.append({
                    'article_id': article['id'],
                    'title': article['title'],
                    'url': article['url'],
                    'relevance': float(similarities[idx])
                })

            if not sources:
                # No articles at all
                return {
                    'answer': None,
                    'sources': [],
                    'confidence': 0.0
                }

            # Get top article for answer extraction
            top_idx = sorted_indices[0]
            top_article = article_data[top_idx]
            confidence = float(similarities[top_idx])

            # Try to get AI provider for natural language answer
            try:
                import scrapetui
                get_ai_prov_func = getattr(scrapetui, 'get_ai_provider', None)
                ai_provider = get_ai_prov_func() if callable(get_ai_prov_func) else None
            except (ImportError, AttributeError, TypeError):
                ai_provider = None

            if ai_provider is None:
                # No AI provider configured - return error message
                return {
                    'answer': 'AI provider not configured. Please set up an AI provider to use question answering.',
                    'sources': sources,
                    'confidence': 0.0
                }

            # Build context from top articles
            context_parts = []
            total_length = 0

            for i, idx in enumerate(sorted_indices[:top_n], 1):
                if similarities[idx] > 0.05:
                    article = article_data[idx]
                    content = article['content'][:2000]  # Limit per article

                    context_part = f"Article {i}: {article['title']}\n{content}\n"

                    if total_length + len(context_part) > max_context_length:
                        break

                    context_parts.append(context_part)
                    total_length += len(context_part)

            context = "\n".join(context_parts)

            # Create prompt for AI provider
            prompt = f"""Based on the following articles, answer this question: {question}

Articles:
{context}

Provide a concise, accurate answer based only on the information in the articles above."""

            # Generate answer using AI provider
            try:
                answer = ai_provider.get_summary(prompt, style='concise')

                return {
                    'answer': answer,
                    'sources': sources,
                    'confidence': confidence
                }

            except Exception as e:
                logger.error(f"AI provider error: {e}")
                # Return error in answer
                return {
                    'answer': f'Error generating answer: {str(e)}',
                    'sources': sources,
                    'confidence': 0.0
                }

        except Exception as e:
            logger.error(f"Question answering failed: {e}")
            return {
                'answer': f'Error: {str(e)}',
                'sources': [],
                'confidence': 0.0
            }

    @staticmethod
    def answer_from_database(question: str, limit: int = 10, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Answer question using articles from database.

        Args:
            question: The question to answer
            limit: Maximum number of articles to use (default: 10)
            user_id: Optional user ID for filtering articles

        Returns:
            Dict with 'answer', 'sources', 'confidence' keys
        """
        try:
            from ..core.database import get_db_connection
        except ImportError:
            import scrapetui
            get_db_connection = scrapetui.get_db_connection

        articles = []

        try:
            with get_db_connection() as conn:
                if user_id is not None:
                    rows = conn.execute(
                        "SELECT id, title, content, summary, url FROM scraped_data WHERE user_id = ? LIMIT ?",
                        (user_id, limit)
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT id, title, content, summary, url FROM scraped_data LIMIT ?",
                        (limit,)
                    ).fetchall()

                for row in rows:
                    articles.append({
                        'id': row[0],
                        'title': row[1],
                        'content': row[2],
                        'summary': row[3],
                        'url': row[4]
                    })
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return {
                'answer': None,
                'sources': [],
                'confidence': 0.0
            }

        return QuestionAnsweringManager.answer_question(question, articles)

    @staticmethod
    def save_qa_conversation(
        question: str,
        answer: str,
        article_ids: List[int],
        confidence: float,
        conn=None
    ) -> bool:
        """
        Save a Q&A conversation to the database.

        Args:
            question: The question asked
            answer: The answer generated
            article_ids: List of article IDs used as sources
            confidence: Confidence score (0.0 to 1.0)
            conn: Optional database connection (for testing)

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            from ..core.database import get_db_connection as _get_db_conn
        except ImportError:
            import scrapetui
            _get_db_conn = scrapetui.get_db_connection

        try:
            # If connection provided (from tests), use it directly
            if conn is not None:
                # Handle both actual connections and context managers
                if hasattr(conn, '__enter__') and not hasattr(conn, 'execute'):
                    # It's a context manager, enter it
                    conn = conn.__enter__()

                # Ensure qa_history table exists
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS qa_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        question TEXT NOT NULL,
                        answer TEXT NOT NULL,
                        article_ids TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        created_at TEXT NOT NULL
                    )
                """)

                # Insert conversation
                conn.execute("""
                    INSERT INTO qa_history
                    (question, answer, article_ids, confidence, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    question,
                    answer,
                    json.dumps(article_ids),
                    confidence,
                    datetime.now().isoformat()
                ))

                conn.commit()
                return True
            else:
                # Use context manager for production code
                with _get_db_conn() as conn:
                    # Ensure qa_history table exists
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS qa_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            question TEXT NOT NULL,
                            answer TEXT NOT NULL,
                            article_ids TEXT NOT NULL,
                            confidence REAL NOT NULL,
                            created_at TEXT NOT NULL
                        )
                    """)

                    # Insert conversation
                    conn.execute("""
                        INSERT INTO qa_history
                        (question, answer, article_ids, confidence, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        question,
                        answer,
                        json.dumps(article_ids),
                        confidence,
                        datetime.now().isoformat()
                    ))

                    conn.commit()
                    return True

        except Exception as e:
            logger.error(f"Failed to save Q&A conversation: {e}")
            return False

    @staticmethod
    def get_qa_history(limit: int = 20, conn=None) -> List[Dict[str, Any]]:
        """
        Retrieve Q&A conversation history.

        Args:
            limit: Maximum number of entries to retrieve (default: 20)
            conn: Optional database connection (for testing)

        Returns:
            List of conversation dicts with question, answer, article_ids, confidence, created_at
        """
        try:
            from ..core.database import get_db_connection as _get_db_conn
        except ImportError:
            import scrapetui
            _get_db_conn = scrapetui.get_db_connection

        try:
            # If connection provided (from tests), use it directly
            if conn is not None:
                # Handle both actual connections and context managers
                if hasattr(conn, '__enter__') and not hasattr(conn, 'execute'):
                    # It's a context manager, enter it
                    conn = conn.__enter__()

                # Ensure table exists
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS qa_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        question TEXT NOT NULL,
                        answer TEXT NOT NULL,
                        article_ids TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        created_at TEXT NOT NULL
                    )
                """)

                rows = conn.execute("""
                    SELECT question, answer, article_ids, confidence, created_at
                    FROM qa_history
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,)).fetchall()

                history = []
                for row in rows:
                    history.append({
                        'question': row[0],
                        'answer': row[1],
                        'article_ids': json.loads(row[2]),
                        'confidence': row[3],
                        'created_at': row[4]
                    })

                return history
            else:
                # Use context manager for production code
                with _get_db_conn() as conn:
                    # Ensure table exists
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS qa_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            question TEXT NOT NULL,
                            answer TEXT NOT NULL,
                            article_ids TEXT NOT NULL,
                            confidence REAL NOT NULL,
                            created_at TEXT NOT NULL
                        )
                    """)

                    rows = conn.execute("""
                        SELECT question, answer, article_ids, confidence, created_at
                        FROM qa_history
                        ORDER BY created_at DESC
                        LIMIT ?
                    """, (limit,)).fetchall()

                    history = []
                    for row in rows:
                        history.append({
                            'question': row[0],
                            'answer': row[1],
                            'article_ids': json.loads(row[2]),
                            'confidence': row[3],
                            'created_at': row[4]
                        })

                    return history

        except Exception as e:
            logger.error(f"Failed to retrieve Q&A history: {e}")
            return []
