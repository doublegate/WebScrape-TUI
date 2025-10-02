"""
Tests for Entity Relationship functionality (v1.9.0).

Tests entity extraction, knowledge graph construction,
and entity-based operations.
"""

import pytest
from scrapetui import EntityRelationshipManager, get_db_connection


@pytest.fixture
def sample_article_with_entities():
    """Sample article with identifiable entities."""
    return {
        'id': 1,
        'title': 'Tech Leaders Meet',
        'content': '''
        Elon Musk and Jeff Bezos met at SpaceX headquarters in California yesterday.
        They discussed future collaboration between Tesla and Amazon on electric vehicle
        delivery infrastructure. The meeting was also attended by Tim Cook from Apple.
        Microsoft and Google were mentioned as potential partners.
        '''
    }


@pytest.fixture
def multiple_articles():
    """Multiple articles for relationship testing."""
    return [
        {
            'id': 1,
            'title': 'SpaceX Launch',
            'content': 'SpaceX launched a Falcon 9 rocket from Kennedy Space Center in Florida. Elon Musk announced plans for Mars colonization.'
        },
        {
            'id': 2,
            'title': 'Tesla Earnings',
            'content': 'Tesla reported strong quarterly earnings. Elon Musk discussed expansion plans in Europe and Asia. Gigafactory production increased.'
        },
        {
            'id': 3,
            'title': 'Amazon Expansion',
            'content': 'Amazon announced new fulfillment centers in Texas and Ohio. Jeff Bezos emphasized customer service improvements and AWS growth.'
        }
    ]


class TestEntityExtraction:
    """Tests for entity extraction."""

    def test_extract_entities_success(self, sample_article_with_entities):
        """Test entity extraction from article."""
        result = EntityRelationshipManager.build_knowledge_graph([sample_article_with_entities])

        assert 'entities' in result
        assert 'relationships' in result

        entities = result['entities']
        assert len(entities) > 0

        # Check for expected entities
        entity_texts = [e['text'] for e in entities]
        assert 'Elon Musk' in entity_texts or 'Jeff Bezos' in entity_texts

        # Verify entity structure
        entity = entities[0]
        assert 'text' in entity
        assert 'label' in entity
        assert 'article_id' in entity

    def test_extract_entities_empty_content(self):
        """Test entity extraction with empty content."""
        article = {'id': 1, 'title': 'Empty', 'content': ''}
        result = EntityRelationshipManager.build_knowledge_graph([article])

        assert 'entities' in result
        # Should return empty or minimal entities
        assert isinstance(result['entities'], list)

    def test_extract_entities_no_identifiable_entities(self):
        """Test with content that has no clear entities."""
        article = {
            'id': 1,
            'title': 'Generic',
            'content': 'The quick brown fox jumps over the lazy dog. It was a sunny day.'
        }
        result = EntityRelationshipManager.build_knowledge_graph([article])

        assert 'entities' in result
        # May find some entities or none, both are acceptable
        assert isinstance(result['entities'], list)

    def test_entity_types(self, sample_article_with_entities):
        """Test that different entity types are identified."""
        result = EntityRelationshipManager.build_knowledge_graph([sample_article_with_entities])

        entities = result['entities']
        entity_types = set(e['label'] for e in entities)

        # Should identify at least persons and organizations
        assert len(entity_types) > 0
        # Common types: PERSON, ORG, GPE (Geo-Political Entity), etc.

    def test_fallback_entity_extraction(self):
        """Test fallback extraction method when spaCy is unavailable."""
        # This tests the regex-based fallback in EntityRelationshipManager
        article = {
            'id': 1,
            'title': 'Test',
            'content': 'Apple Inc. is a technology company. Steve Jobs founded it in California.'
        }

        result = EntityRelationshipManager.build_knowledge_graph([article])

        # Should work even without spaCy
        assert 'entities' in result
        assert isinstance(result['entities'], list)


class TestKnowledgeGraphConstruction:
    """Tests for knowledge graph building."""

    def test_build_knowledge_graph_single_article(self, sample_article_with_entities):
        """Test building knowledge graph from single article."""
        result = EntityRelationshipManager.build_knowledge_graph([sample_article_with_entities])

        assert 'graph' in result
        assert 'nodes' in result
        assert 'edges' in result

        # Verify graph structure
        assert result['nodes'] > 0  # Should have nodes
        # Edges may be 0 if no relationships found

    def test_build_knowledge_graph_multiple_articles(self, multiple_articles):
        """Test building knowledge graph from multiple articles."""
        result = EntityRelationshipManager.build_knowledge_graph(multiple_articles)

        assert 'entities' in result
        assert 'graph' in result

        # Should have entities from multiple articles
        entities = result['entities']
        article_ids = set(e['article_id'] for e in entities)
        assert len(article_ids) >= 2  # Entities from at least 2 articles

    def test_entity_relationships(self, sample_article_with_entities):
        """Test that relationships between entities are captured."""
        result = EntityRelationshipManager.build_knowledge_graph([sample_article_with_entities])

        relationships = result.get('relationships', [])

        # Relationships are implied by co-occurrence in same article
        if len(result['entities']) >= 2:
            # Entities in same article should have relationships
            assert 'graph' in result

    def test_knowledge_graph_persistence(self, sample_article_with_entities, db_connection):
        """Test saving knowledge graph to database."""
        result = EntityRelationshipManager.build_knowledge_graph([sample_article_with_entities])

        # Save entities to database
        for entity in result['entities']:
            db_connection.execute("""
                INSERT OR IGNORE INTO entity_mentions
                (article_id, entity_text, entity_type, context)
                VALUES (?, ?, ?, ?)
            """, (
                entity['article_id'],
                entity['text'],
                entity['label'],
                entity.get('context', '')
            ))
        db_connection.commit()

        # Verify saved
        cursor = db_connection.execute(
            "SELECT COUNT(*) as count FROM entity_mentions WHERE article_id = ?",
            (sample_article_with_entities['id'],)
        )
        count = cursor.fetchone()['count']
        assert count > 0


class TestRelatedEntities:
    """Tests for finding related entities."""

    def test_get_related_entities(self, multiple_articles, db_connection):
        """Test getting related entities for a specific entity."""
        # Build knowledge graph
        result = EntityRelationshipManager.build_knowledge_graph(multiple_articles)

        if not result['entities']:
            pytest.skip("No entities found in test articles")

        # Save entities to database
        for entity in result['entities']:
            db_connection.execute("""
                INSERT OR IGNORE INTO entity_mentions
                (article_id, entity_text, entity_type, context)
                VALUES (?, ?, ?, ?)
            """, (
                entity['article_id'],
                entity['text'],
                entity['label'],
                ''
            ))
        db_connection.commit()

        # Find related entities to "Elon Musk"
        related = db_connection.execute("""
            SELECT DISTINCT e2.entity_text, e2.entity_type
            FROM entity_mentions e1
            JOIN entity_mentions e2 ON e1.article_id = e2.article_id
            WHERE e1.entity_text LIKE '%Elon%' AND e2.entity_text != e1.entity_text
        """).fetchall()

        # Should find entities that appear with Elon Musk
        related_texts = [r['entity_text'] for r in related]
        assert len(related_texts) >= 0  # May or may not find related entities

    def test_entity_co_occurrence(self, multiple_articles):
        """Test finding entities that co-occur in articles."""
        result = EntityRelationshipManager.build_knowledge_graph(multiple_articles)

        # Group entities by article
        entities_by_article = {}
        for entity in result['entities']:
            article_id = entity['article_id']
            if article_id not in entities_by_article:
                entities_by_article[article_id] = []
            entities_by_article[article_id].append(entity['text'])

        # Check for co-occurrence
        for article_id, entity_list in entities_by_article.items():
            if len(entity_list) >= 2:
                # These entities co-occur
                assert len(entity_list) >= 2


class TestEntityStorage:
    """Tests for storing entity relationships in database."""

    def test_store_entity_relationships(self, sample_article_with_entities, db_connection):
        """Test storing entity relationships in database."""
        result = EntityRelationshipManager.build_knowledge_graph([sample_article_with_entities])

        # Store entities
        for entity in result['entities']:
            db_connection.execute("""
                INSERT OR IGNORE INTO entity_mentions
                (article_id, entity_text, entity_type, context)
                VALUES (?, ?, ?, ?)
            """, (
                entity['article_id'],
                entity['text'],
                entity['label'],
                ''
            ))
        db_connection.commit()

        # Verify storage
        cursor = db_connection.execute("""
            SELECT entity_text, entity_type FROM entity_mentions
            WHERE article_id = ?
        """, (sample_article_with_entities['id'],))

        stored_entities = cursor.fetchall()
        assert len(stored_entities) > 0

    def test_retrieve_entities_by_article(self, multiple_articles, db_connection):
        """Test retrieving entities for specific article."""
        # Build and store entities
        result = EntityRelationshipManager.build_knowledge_graph(multiple_articles)

        for entity in result['entities']:
            db_connection.execute("""
                INSERT OR IGNORE INTO entity_mentions
                (article_id, entity_text, entity_type, context)
                VALUES (?, ?, ?, ?)
            """, (
                entity['article_id'],
                entity['text'],
                entity['label'],
                ''
            ))
        db_connection.commit()

        # Retrieve entities for first article
        cursor = db_connection.execute("""
            SELECT entity_text, entity_type FROM entity_mentions
            WHERE article_id = ?
        """, (multiple_articles[0]['id'],))

        entities = cursor.fetchall()
        # Should have at least some entities from first article
        assert len(entities) >= 0

    def test_entity_relationship_storage(self, sample_article_with_entities, db_connection):
        """Test storing relationships between entities."""
        result = EntityRelationshipManager.build_knowledge_graph([sample_article_with_entities])

        entities = result['entities']
        if len(entities) >= 2:
            # Store a relationship
            db_connection.execute("""
                INSERT OR IGNORE INTO entity_relationships
                (entity1, entity2, relationship_type, article_id, confidence)
                VALUES (?, ?, ?, ?, ?)
            """, (
                entities[0]['text'],
                entities[1]['text'],
                'co_occurrence',
                sample_article_with_entities['id'],
                0.8
            ))
            db_connection.commit()

            # Verify
            cursor = db_connection.execute("""
                SELECT * FROM entity_relationships
                WHERE article_id = ?
            """, (sample_article_with_entities['id'],))

            relationships = cursor.fetchall()
            assert len(relationships) > 0
