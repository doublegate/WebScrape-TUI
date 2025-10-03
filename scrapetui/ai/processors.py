#!/usr/bin/env python3
"""AI processing functions for article analysis."""

import spacy
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Load spaCy model (lazy loading)
_nlp_model = None


def _get_nlp_model():
    """Get or load spaCy NLP model."""
    global _nlp_model
    if _nlp_model is None:
        try:
            _nlp_model = spacy.load('en_core_web_sm')
        except OSError:
            logger.error(
                "spaCy model 'en_core_web_sm' not found. "
                "Run: python -m spacy download en_core_web_sm"
            )
            raise
    return _nlp_model


def extract_named_entities(
    text: str,
    entity_types: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Extract named entities from text using spaCy.

    Args:
        text: Input text to analyze
        entity_types: Optional list of entity types to filter (PERSON, ORG, GPE, etc.)
                     If None, returns all entity types

    Returns:
        List of dicts with 'text', 'label', 'start', 'end' keys

    Example:
        >>> entities = extract_named_entities("Apple CEO Tim Cook announced...")
        >>> entities[0]
        {'text': 'Apple', 'label': 'ORG', 'start': 0, 'end': 5}
    """
    if not text or not text.strip():
        return []

    try:
        nlp = _get_nlp_model()
        # Limit to 1M chars for performance
        doc = nlp(text[:1000000])

        entities = []
        for ent in doc.ents:
            if entity_types is None or ent.label_ in entity_types:
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char
                })

        return entities
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        return []


def extract_entities_from_articles(
    article_ids: List[int]
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Extract named entities from multiple articles.

    Args:
        article_ids: List of article IDs to process

    Returns:
        Dict mapping article_id -> list of entities
    """
    from ..core.database import get_db_connection

    results = {}

    with get_db_connection() as conn:
        for article_id in article_ids:
            # Get article content
            row = conn.execute(
                "SELECT content, summary, title FROM scraped_data WHERE id = ?",
                (article_id,)
            ).fetchone()

            if not row:
                results[article_id] = []
                continue

            # Try content first, fall back to summary, then title
            text = row[0] or row[1] or row[2] or ""

            # Extract entities
            entities = extract_named_entities(text)
            results[article_id] = entities

    return results


def extract_keywords(
    text: str,
    top_n: int = 10,
    ngram_range: tuple = (1, 2)
) -> List[Dict[str, float]]:
    """
    Extract keywords using TF-IDF.

    Args:
        text: Input text
        top_n: Number of top keywords to return
        ngram_range: Range of n-grams (default: unigrams and bigrams)

    Returns:
        List of dicts with 'keyword' and 'score' keys, sorted by score descending

    Example:
        >>> keywords = extract_keywords("Machine learning is a subset of AI...")
        >>> keywords[0]
        {'keyword': 'machine learning', 'score': 0.85}
    """
    if not text or not text.strip():
        return []

    try:
        vectorizer = TfidfVectorizer(
            max_features=top_n * 2,
            ngram_range=ngram_range,
            stop_words='english'
        )

        tfidf_matrix = vectorizer.fit_transform([text])
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]

        # Get top N keywords
        top_indices = scores.argsort()[-top_n:][::-1]

        keywords = []
        for idx in top_indices:
            if scores[idx] > 0:
                keywords.append({
                    'keyword': feature_names[idx],
                    'score': float(scores[idx])
                })

        return keywords
    except Exception as e:
        logger.error(f"Keyword extraction failed: {e}")
        return []


def extract_keywords_from_articles(
    article_ids: List[int],
    top_n: int = 10
) -> Dict[int, List[Dict[str, float]]]:
    """
    Extract keywords from multiple articles.

    Args:
        article_ids: List of article IDs to process
        top_n: Number of top keywords per article

    Returns:
        Dict mapping article_id -> list of keywords
    """
    from ..core.database import get_db_connection

    results = {}

    with get_db_connection() as conn:
        for article_id in article_ids:
            # Get article content
            row = conn.execute(
                "SELECT content, summary, title FROM scraped_data WHERE id = ?",
                (article_id,)
            ).fetchone()

            if not row:
                results[article_id] = []
                continue

            # Try content first, fall back to summary, then title
            text = row[0] or row[1] or row[2] or ""

            # Extract keywords
            keywords = extract_keywords(text, top_n=top_n)
            results[article_id] = keywords

    return results
