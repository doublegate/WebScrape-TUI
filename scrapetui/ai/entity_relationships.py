#!/usr/bin/env python3
"""Entity relationship extraction and knowledge graph construction.

This module provides entity recognition, relationship extraction, and
knowledge graph construction capabilities using spaCy NLP.
"""

from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
import json

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from ..utils.logging import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class EntityRelationshipManager:
    """Manager for entity relationships and knowledge graphs."""

    def __init__(self):
        """Initialize the Entity Relationship Manager."""
        self._nlp = None

    def _get_nlp(self):
        """Lazy load spaCy model."""
        if not SPACY_AVAILABLE:
            raise ImportError("spaCy is not installed. Install with: pip install spacy")

        if self._nlp is None:
            try:
                self._nlp = spacy.load('en_core_web_sm')
            except OSError:
                logger.error("spaCy model 'en_core_web_sm' not found. Download with: python -m spacy download en_core_web_sm")
                raise
        return self._nlp

    @staticmethod
    def extract_entity_relationships(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract entities and relationships from articles.

        Args:
            articles: List of article dicts with 'id', 'content', 'title' keys

        Returns:
            Dict with 'entities' (dict of entity text -> entity info) and 'relationships' keys
        """
        if not articles:
            return {'entities': {}, 'relationships': []}

        manager = EntityRelationshipManager()

        try:
            nlp = manager._get_nlp()
        except (ImportError, OSError) as e:
            logger.error(f"Failed to load spaCy: {e}")
            return {'entities': {}, 'relationships': []}

        # Extract entities across all articles
        entities_dict = defaultdict(lambda: {
            'text': '',
            'type': '',
            'count': 0,
            'articles': set()
        })

        relationships = []

        for article in articles:
            article_id = article.get('id', 0)
            text = article.get('content') or article.get('title', '')

            if not text or not text.strip():
                continue

            # Limit text length for performance
            text = text[:100000]

            try:
                doc = nlp(text)

                # Extract entities
                for ent in doc.ents:
                    entity_key = ent.text
                    if entity_key not in entities_dict:
                        entities_dict[entity_key] = {
                            'text': ent.text,
                            'type': ent.label_,
                            'count': 0,
                            'articles': set()
                        }

                    entities_dict[entity_key]['count'] += 1
                    entities_dict[entity_key]['articles'].add(article_id)

                # Extract simple subject-verb-object relationships
                for sent in doc.sents:
                    # Find subjects and objects
                    subjects = [token for token in sent if token.dep_ in ('nsubj', 'nsubjpass')]
                    objects = [token for token in sent if token.dep_ in ('dobj', 'pobj')]
                    verbs = [token for token in sent if token.pos_ == 'VERB']

                    for subj in subjects:
                        for verb in verbs:
                            for obj in objects:
                                # Check if they're connected in dependency tree
                                if (verb in subj.ancestors or verb in subj.descendants or
                                    verb in obj.ancestors or verb in obj.descendants):
                                    relationships.append({
                                        'subject': subj.text,
                                        'predicate': verb.text,
                                        'object': obj.text,
                                        'article_id': article_id
                                    })

            except Exception as e:
                logger.error(f"Error processing article {article_id}: {e}")
                continue

        # Convert sets to lists for JSON serialization
        for entity in entities_dict.values():
            entity['articles'] = list(entity['articles'])

        return {
            'entities': dict(entities_dict),
            'relationships': relationships
        }

    @staticmethod
    def build_knowledge_graph(entity_data: Dict[str, Any]):
        """
        Build a NetworkX knowledge graph from entity data.

        Args:
            entity_data: Dict with 'entities' and 'relationships' keys from extract_entity_relationships()

        Returns:
            NetworkX Graph object
        """
        try:
            import networkx as nx
        except ImportError:
            logger.error("NetworkX is not installed. Install with: pip install networkx")
            # Return empty graph-like object
            class EmptyGraph:
                def __init__(self):
                    self.nodes = []
                    self.edges = []
            return EmptyGraph()

        # Create directed graph
        graph = nx.Graph()

        # Add entity nodes
        entities = entity_data.get('entities', {})
        for entity_text, entity_info in entities.items():
            graph.add_node(
                entity_text,
                type=entity_info.get('type', 'UNKNOWN'),
                count=entity_info.get('count', 1),
                articles=entity_info.get('articles', [])
            )

        # Add relationship edges
        relationships = entity_data.get('relationships', [])
        for rel in relationships:
            subject = rel.get('subject')
            obj = rel.get('object')
            predicate = rel.get('predicate')

            if subject and obj:
                graph.add_edge(
                    subject,
                    obj,
                    relation=predicate,
                    article_id=rel.get('article_id')
                )

        return graph

    @staticmethod
    def get_entity_connections(entity: str, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get all entities connected to a given entity.

        Args:
            entity: Entity text to find connections for
            articles: List of articles to analyze

        Returns:
            List of connected entities with relationship info
        """
        result = EntityRelationshipManager.extract_entity_relationships(articles)
        relationships = result['relationships']

        connections = []
        entity_lower = entity.lower()

        for rel in relationships:
            if rel['subject'].lower() == entity_lower:
                connections.append({
                    'entity': rel['object'],
                    'relation': rel['predicate'],
                    'direction': 'outgoing'
                })
            elif rel['object'].lower() == entity_lower:
                connections.append({
                    'entity': rel['subject'],
                    'relation': rel['predicate'],
                    'direction': 'incoming'
                })

        return connections

    @staticmethod
    def store_entity_relationships(article_id: int, conn=None) -> bool:
        """
        Store entity relationships for an article in the database.

        Args:
            article_id: ID of the article to process
            conn: Optional database connection

        Returns:
            True if successful, False otherwise
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

            # Ensure tables exist
            db_conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_text TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    article_id INTEGER NOT NULL,
                    FOREIGN KEY (article_id) REFERENCES scraped_data(id) ON DELETE CASCADE
                )
            """)

            db_conn.execute("""
                CREATE TABLE IF NOT EXISTS entity_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    object TEXT NOT NULL,
                    article_id INTEGER NOT NULL,
                    FOREIGN KEY (article_id) REFERENCES scraped_data(id) ON DELETE CASCADE
                )
            """)

            # Get article content
            row = db_conn.execute(
                "SELECT content, title FROM scraped_data WHERE id = ?",
                (article_id,)
            ).fetchone()

            if not row:
                return False

            content = row[0] or row[1] or ''

            # Extract entities and relationships
            article = {'id': article_id, 'content': content}
            result = EntityRelationshipManager.extract_entity_relationships([article])

            # Store entities
            for entity_text, entity_info in result['entities'].items():
                db_conn.execute("""
                    INSERT INTO entities (entity_text, entity_type, article_id)
                    VALUES (?, ?, ?)
                """, (entity_text, entity_info['type'], article_id))

            # Store relationships
            for rel in result['relationships']:
                db_conn.execute("""
                    INSERT INTO entity_relationships (subject, predicate, object, article_id)
                    VALUES (?, ?, ?, ?)
                """, (rel['subject'], rel['predicate'], rel['object'], article_id))

            db_conn.commit()

            if own_conn:
                db_conn_mgr.__exit__(None, None, None)

            return True

        except Exception as e:
            logger.error(f"Failed to store entity relationships: {e}")
            return False

    @staticmethod
    def get_related_entities(entity: str, conn=None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get entities related to the given entity from the database.

        Args:
            entity: Entity text to find relations for
            conn: Optional database connection
            limit: Maximum number of results

        Returns:
            List of related entity dicts
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
                CREATE TABLE IF NOT EXISTS entity_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    object TEXT NOT NULL,
                    article_id INTEGER NOT NULL
                )
            """)

            entity_lower = entity.lower()
            related = []

            # Find outgoing relationships
            rows = db_conn.execute("""
                SELECT DISTINCT object, predicate, article_id
                FROM entity_relationships
                WHERE LOWER(subject) = ?
                LIMIT ?
            """, (entity_lower, limit)).fetchall()

            for row in rows:
                related.append({
                    'entity': row[0],
                    'relation': row[1],
                    'direction': 'outgoing',
                    'article_id': row[2]
                })

            # Find incoming relationships
            rows = db_conn.execute("""
                SELECT DISTINCT subject, predicate, article_id
                FROM entity_relationships
                WHERE LOWER(object) = ?
                LIMIT ?
            """, (entity_lower, limit)).fetchall()

            for row in rows:
                related.append({
                    'entity': row[0],
                    'relation': row[1],
                    'direction': 'incoming',
                    'article_id': row[2]
                })

            if own_conn:
                db_conn_mgr.__exit__(None, None, None)

            return related[:limit]

        except Exception as e:
            logger.error(f"Failed to get related entities: {e}")
            return []
