#!/usr/bin/env python3
"""Topic modeling functionality for article analysis."""

from typing import List, Dict, Any, Optional
from sklearn.decomposition import LatentDirichletAllocation, NMF
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import numpy as np

from ..utils.logging import get_logger

logger = get_logger(__name__)


class TopicModelingManager:
    """Manager class for topic modeling operations."""

    @staticmethod
    def perform_lda_topic_modeling(
        articles: List[Dict[str, Any]],
        num_topics: int = 5,
        passes: int = 10,
        top_words: int = 10
    ) -> Dict[str, Any]:
        """
        Perform LDA topic modeling on articles.

        Args:
            articles: List of article dicts with 'id', 'title', 'content'
            num_topics: Number of topics to extract
            passes: Number of passes (iterations) for LDA
            top_words: Number of top words per topic

        Returns:
            Dict with 'topics', 'assignments', 'num_articles' keys
        """
        if not articles:
            return {
                'error': 'No articles provided',
                'topics': [],
                'assignments': {},
                'num_articles': 0
            }

        if len(articles) < 2:
            return {
                'error': 'Need at least 2 articles for topic modeling',
                'topics': [],
                'assignments': {},
                'num_articles': len(articles)
            }

        try:
            # Check if articles have content field
            has_content = []
            for article in articles:
                content = article.get('content', '')
                has_content.append(bool(content and content.strip()))

            # If no articles have content, return error
            if not any(has_content):
                return {
                    'error': 'Articles have no content',
                    'topics': [],
                    'assignments': {},
                    'num_articles': len(articles)
                }

            # Combine title and content for each article
            texts = []
            for article in articles:
                title = article.get('title', '') or ''
                content = article.get('content', '') or ''
                text = f"{title} {content}".strip()
                if not text:
                    text = "empty"
                texts.append(text)

            # Create document-term matrix
            vectorizer = CountVectorizer(
                max_features=1000,
                stop_words='english',
                min_df=1
            )
            doc_term_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()

            # Perform LDA
            lda = LatentDirichletAllocation(
                n_components=num_topics,
                max_iter=passes,
                random_state=42
            )
            doc_topics = lda.fit_transform(doc_term_matrix)

            # Extract topics with words and weights
            topics = []
            for topic_idx, topic in enumerate(lda.components_):
                top_indices = topic.argsort()[-top_words:][::-1]
                words = [feature_names[i] for i in top_indices]
                weights = [float(topic[i]) for i in top_indices]

                # Generate topic label from top 3 words
                label = ', '.join(words[:3])

                topics.append({
                    'id': topic_idx,
                    'words': words,
                    'weights': weights,
                    'label': label
                })

            # Assign articles to topics
            assignments = {}
            for i, article in enumerate(articles):
                article_id = article['id']
                topic_dist = doc_topics[i]
                primary_topic = int(np.argmax(topic_dist))
                confidence = float(topic_dist[primary_topic])

                # Create all_topics list with (topic_id, probability) pairs
                all_topics = [(idx, float(prob)) for idx, prob in enumerate(topic_dist)]
                all_topics.sort(key=lambda x: x[1], reverse=True)

                assignments[article_id] = {
                    'topic_id': primary_topic,
                    'confidence': confidence,
                    'distribution': topic_dist.tolist(),
                    'all_topics': all_topics
                }

            return {
                'topics': topics,
                'assignments': assignments,
                'num_articles': len(articles)
            }

        except Exception as e:
            logger.error(f"LDA topic modeling failed: {e}")
            return {
                'error': str(e),
                'topics': [],
                'assignments': {},
                'num_articles': len(articles)
            }

    @staticmethod
    def perform_nmf_topic_modeling(
        articles: List[Dict[str, Any]],
        num_topics: int = 5,
        max_iter: int = 200,
        top_words: int = 10
    ) -> Dict[str, Any]:
        """
        Perform NMF topic modeling on articles.

        Args:
            articles: List of article dicts with 'id', 'title', 'content'
            num_topics: Number of topics to extract
            max_iter: Maximum iterations for NMF
            top_words: Number of top words per topic

        Returns:
            Dict with 'topics', 'assignments', 'num_articles' keys
        """
        if not articles:
            return {
                'error': 'No articles provided',
                'topics': [],
                'assignments': {},
                'num_articles': 0
            }

        if len(articles) < 2:
            return {
                'error': 'Need at least 2 articles for topic modeling',
                'topics': [],
                'assignments': {},
                'num_articles': len(articles)
            }

        try:
            # Check if articles have content field
            has_content = []
            for article in articles:
                content = article.get('content', '')
                has_content.append(bool(content and content.strip()))

            # If no articles have content, return error
            if not any(has_content):
                return {
                    'error': 'Articles have no content',
                    'topics': [],
                    'assignments': {},
                    'num_articles': len(articles)
                }

            # Combine title and content for each article
            texts = []
            for article in articles:
                title = article.get('title', '') or ''
                content = article.get('content', '') or ''
                text = f"{title} {content}".strip()
                if not text:
                    text = "empty"
                texts.append(text)

            # Create TF-IDF matrix
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                min_df=1
            )
            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()

            # Perform NMF
            nmf = NMF(
                n_components=num_topics,
                max_iter=max_iter,
                random_state=42
            )
            doc_topics = nmf.fit_transform(tfidf_matrix)

            # Extract topics with words and weights
            topics = []
            for topic_idx, topic in enumerate(nmf.components_):
                top_indices = topic.argsort()[-top_words:][::-1]
                words = [feature_names[i] for i in top_indices]
                weights = [float(topic[i]) for i in top_indices]

                # Generate topic label from top 3 words
                label = ', '.join(words[:3])

                topics.append({
                    'id': topic_idx,
                    'words': words,
                    'weights': weights,
                    'label': label
                })

            # Assign articles to topics
            assignments = {}
            for i, article in enumerate(articles):
                article_id = article['id']
                topic_dist = doc_topics[i]
                primary_topic = int(np.argmax(topic_dist))
                confidence = float(topic_dist[primary_topic])

                # Create all_topics list with (topic_id, probability) pairs
                all_topics = [(idx, float(prob)) for idx, prob in enumerate(topic_dist)]
                all_topics.sort(key=lambda x: x[1], reverse=True)

                assignments[article_id] = {
                    'topic_id': primary_topic,
                    'confidence': confidence,
                    'distribution': topic_dist.tolist(),
                    'all_topics': all_topics
                }

            return {
                'topics': topics,
                'assignments': assignments,
                'num_articles': len(articles)
            }

        except Exception as e:
            logger.error(f"NMF topic modeling failed: {e}")
            return {
                'error': str(e),
                'topics': [],
                'assignments': {},
                'num_articles': len(articles)
            }

    @staticmethod
    def assign_categories(
        article_ids: List[int],
        num_categories: int = 5
    ) -> Dict[int, Dict[str, Any]]:
        """
        Assign articles to categories using topic modeling.

        Args:
            article_ids: List of article IDs from database
            num_categories: Number of categories to create

        Returns:
            Dict mapping article_id -> category info
        """
        from ..core.database import get_db_connection

        try:
            # Fetch articles from database
            with get_db_connection() as conn:
                placeholders = ','.join(['?'] * len(article_ids))
                query = f"""
                    SELECT id, title, content
                    FROM scraped_data
                    WHERE id IN ({placeholders})
                """
                rows = conn.execute(query, article_ids).fetchall()

            articles = [
                {
                    'id': row['id'],
                    'title': row['title'],
                    'content': row['content']
                }
                for row in rows
            ]

            # Perform topic modeling
            result = TopicModelingManager.perform_lda_topic_modeling(
                articles,
                num_topics=num_categories
            )

            if 'error' in result:
                return {}

            # Return assignments with category labels
            assignments = result['assignments']
            topics = result['topics']

            for article_id, assignment in assignments.items():
                topic_id = assignment['topic_id']
                assignment['category'] = topics[topic_id]['label']

            return assignments

        except Exception as e:
            logger.error(f"Category assignment failed: {e}")
            return {}

    @staticmethod
    def create_topic_hierarchy(
        articles: List[Dict[str, Any]],
        num_parent_topics: int = 3,
        num_child_topics: int = 5
    ) -> Dict[str, Any]:
        """
        Create hierarchical topic structure.

        Args:
            articles: List of article dicts
            num_parent_topics: Number of high-level topics
            num_child_topics: Number of subtopics per parent

        Returns:
            Dict with hierarchical topic structure
        """
        try:
            # First level: parent topics
            parent_result = TopicModelingManager.perform_lda_topic_modeling(
                articles,
                num_topics=num_parent_topics
            )

            if 'error' in parent_result:
                return parent_result

            # Build hierarchy structure
            hierarchy = {
                'parent_topics': parent_result['topics'],
                'children': {}
            }

            # For each parent topic, extract child topics from assigned articles
            for parent_idx in range(num_parent_topics):
                # Get articles assigned to this parent topic
                parent_articles = [
                    article for article in articles
                    if parent_result['assignments'].get(article['id'], {}).get('topic_id') == parent_idx
                ]

                if len(parent_articles) >= 2:
                    # Perform child topic modeling
                    child_result = TopicModelingManager.perform_lda_topic_modeling(
                        parent_articles,
                        num_topics=min(num_child_topics, len(parent_articles))
                    )

                    hierarchy['children'][parent_idx] = {
                        'topics': child_result.get('topics', []),
                        'num_articles': len(parent_articles)
                    }
                else:
                    hierarchy['children'][parent_idx] = {
                        'topics': [],
                        'num_articles': len(parent_articles)
                    }

            return hierarchy

        except Exception as e:
            logger.error(f"Topic hierarchy creation failed: {e}")
            return {'error': str(e)}
