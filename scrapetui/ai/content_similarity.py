#!/usr/bin/env python3
"""Content similarity matching using embeddings.

This module provides content similarity search using sentence embeddings
and cosine similarity to find related articles.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np

try:
    from ..utils.logging import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Import SentenceTransformer at module level for mocking
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    # If sentence-transformers not installed, create a dummy class
    class SentenceTransformer:
        def __init__(self, *args, **kwargs):
            pass

        def encode(self, texts):
            raise ImportError("sentence-transformers library not installed")


# Lazy loading of heavy dependencies
_sentence_transformer_model = None


def _get_sentence_transformer():
    """Lazy load SentenceTransformer model."""
    global _sentence_transformer_model

    if _sentence_transformer_model is None:
        try:
            _sentence_transformer_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded SentenceTransformer model: all-MiniLM-L6-v2")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer: {e}")
            raise

    return _sentence_transformer_model


class ContentSimilarityManager:
    """Manager for content similarity analysis."""

    @staticmethod
    def load_model():
        """
        Load the SentenceTransformer model.

        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            _get_sentence_transformer()
            return True
        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            return False

    @staticmethod
    def find_similar_articles(
        target_text: str,
        articles: List[Dict[str, Any]],
        min_similarity: float = 0.0,
        top_k: int = 10
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Find articles similar to target text using embeddings.

        Args:
            target_text: Text to find similar articles for
            articles: List of article dicts with 'id', 'title', 'full_text' keys
            min_similarity: Minimum cosine similarity threshold (0.0 to 1.0)
            top_k: Maximum number of results to return

        Returns:
            List of (article, similarity_score) tuples, sorted by similarity (descending)
        """
        if not target_text or not articles:
            return []

        # Check if model can be loaded
        if not ContentSimilarityManager.load_model():
            return []

        try:
            model = _get_sentence_transformer()

            # Extract text from articles (prefer full_text, fallback to title)
            article_texts = [
                a.get('full_text') or a.get('title', '')
                for a in articles
            ]

            # Encode all texts (target + articles)
            all_texts = [target_text] + article_texts
            embeddings = model.encode(all_texts)

            # Separate target embedding from article embeddings
            target_embedding = embeddings[0]
            article_embeddings = embeddings[1:]

            # Calculate cosine similarity
            similarities = ContentSimilarityManager._cosine_similarity_batch(
                target_embedding,
                article_embeddings
            )

            # Create (article, score) tuples
            results = [
                (articles[i], float(similarities[i]))
                for i in range(len(articles))
                if similarities[i] >= min_similarity
            ]

            # Sort by similarity (descending) and take top_k
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"Content similarity error: {e}", exc_info=True)
            return []

    @staticmethod
    def _cosine_similarity_batch(vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        """
        Calculate cosine similarity between a vector and a matrix of vectors.

        Args:
            vec: Single embedding vector (shape: (dim,))
            matrix: Matrix of embedding vectors (shape: (n, dim))

        Returns:
            Array of cosine similarities (shape: (n,))
        """
        # Normalize vectors
        vec_norm = vec / (np.linalg.norm(vec) + 1e-10)
        matrix_norms = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10)

        # Compute cosine similarity
        similarities = np.dot(matrix_norms, vec_norm)

        return similarities

    @staticmethod
    def cluster_articles(
        articles: List[Dict[str, Any]],
        n_clusters: int = 5
    ) -> Dict[str, Any]:
        """
        Cluster articles by content similarity.

        Args:
            articles: List of article dicts
            n_clusters: Number of clusters to create

        Returns:
            Dict with 'clusters' (list of article ID lists) and 'cluster_labels'
        """
        if not articles or len(articles) < n_clusters:
            return {'clusters': [[a['id'] for a in articles]], 'cluster_labels': [0] * len(articles)}

        try:
            from sklearn.cluster import KMeans

            model = _get_sentence_transformer()

            # Extract text and encode
            article_texts = [a.get('full_text') or a.get('title', '') for a in articles]
            embeddings = model.encode(article_texts)

            # Perform K-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings)

            # Group articles by cluster
            clusters = [[] for _ in range(n_clusters)]
            for i, label in enumerate(cluster_labels):
                clusters[label].append(articles[i]['id'])

            return {
                'clusters': clusters,
                'cluster_labels': cluster_labels.tolist()
            }

        except Exception as e:
            logger.error(f"Article clustering error: {e}", exc_info=True)
            return {'clusters': [[a['id'] for a in articles]], 'cluster_labels': [0] * len(articles)}
