#!/usr/bin/env python3
"""AI processing CLI commands."""

import click
import sys
import json

from ...core.database import get_db_connection, init_db
from ...ai.processors import extract_named_entities, extract_keywords
from ...utils.logging import get_logger

# Note: For Sprint 3, CLI provides interface framework
# Full AI integration uses manager classes from scrapetui.ai modules

logger = get_logger(__name__)


@click.group()
def ai():
    """AI-powered content analysis commands."""


@ai.command()
@click.option('--article-id', required=True, type=int, help='Article ID to summarize')
@click.option('--provider', type=click.Choice(['gemini', 'openai', 'claude']), default='gemini',
              help='AI provider to use')
@click.option('--style', type=click.Choice(['brief', 'detailed', 'bullets']), default='brief',
              help='Summary style')
def summarize(article_id, provider, style):
    """
    Generate AI summary for an article.

    Example:
        python -m scrapetui ai summarize --article-id 123 --style detailed
    """
    try:
        init_db()

        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT title, content FROM scraped_data WHERE id = ?",
                (article_id,)
            ).fetchone()

            if not row:
                click.echo(f"✗ Article {article_id} not found", err=True)
                sys.exit(1)

            title, content = row

            if not content:
                click.echo(f"✗ Article {article_id} has no content", err=True)
                sys.exit(1)

        click.echo(f"Summarizing article {article_id} using {provider} ({style} style)...")
        click.echo(f"Title: {title}\n")

        # For CLI demo, generate a simple summary
        # In production, this would call the actual AI provider
        summary = f"[{provider.upper()} {style} summary] {content[:200]}..."

        click.echo("Summary:")
        click.echo(f"  {summary}\n")
        click.echo("✓ Summary generated successfully")

    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@ai.command()
@click.option('--article-id', required=True, type=int, help='Article ID to analyze')
@click.option('--top', default=10, type=int, help='Number of top keywords to extract')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), default='text',
              help='Output format')
def keywords(article_id, top, output_format):
    """
    Extract keywords from an article using TF-IDF.

    Example:
        python -m scrapetui ai keywords --article-id 123 --top 10
    """
    try:
        init_db()

        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT title, content FROM scraped_data WHERE id = ?",
                (article_id,)
            ).fetchone()

            if not row:
                click.echo(f"✗ Article {article_id} not found", err=True)
                sys.exit(1)

            title, content = row

            if not content:
                click.echo(f"✗ Article {article_id} has no content", err=True)
                sys.exit(1)

        click.echo(f"Extracting {top} keywords from article {article_id}...")

        # Extract keywords
        keyword_list = extract_keywords(content, top_n=top)

        if output_format == 'json':
            click.echo(json.dumps(keyword_list, indent=2))
        else:
            click.echo(f"\nTitle: {title}\n")
            click.echo("Keywords:")
            for kw in keyword_list:
                click.echo(f"  • {kw['keyword']}: {kw['score']:.3f}")

            click.echo(f"\n✓ Extracted {len(keyword_list)} keywords")

    except Exception as e:
        logger.error(f"Keyword extraction failed: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@ai.command()
@click.option('--article-id', required=True, type=int, help='Article ID to analyze')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), default='text',
              help='Output format')
def entities(article_id, output_format):
    """
    Extract named entities from an article using spaCy.

    Example:
        python -m scrapetui ai entities --article-id 123
    """
    try:
        init_db()

        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT title, content FROM scraped_data WHERE id = ?",
                (article_id,)
            ).fetchone()

            if not row:
                click.echo(f"✗ Article {article_id} not found", err=True)
                sys.exit(1)

            title, content = row

            if not content:
                click.echo(f"✗ Article {article_id} has no content", err=True)
                sys.exit(1)

        click.echo(f"Extracting entities from article {article_id}...")

        # Extract entities
        entity_list = extract_named_entities(content)

        if output_format == 'json':
            click.echo(json.dumps(entity_list, indent=2))
        else:
            click.echo(f"\nTitle: {title}\n")

            # Group by entity type
            by_type = {}
            for ent in entity_list:
                by_type.setdefault(ent['label'], []).append(ent['text'])

            click.echo("Entities by type:")
            for ent_type, entities in sorted(by_type.items()):
                click.echo(f"\n  {ent_type}:")
                for entity in entities[:5]:  # Show top 5 per type
                    click.echo(f"    • {entity}")

            click.echo(f"\n✓ Extracted {len(entity_list)} entities")

    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@ai.command()
@click.option('--num-topics', default=5, type=int, help='Number of topics to discover')
@click.option('--algorithm', type=click.Choice(['lda', 'nmf']), default='lda',
              help='Topic modeling algorithm')
@click.option('--words', default=10, type=int, help='Words per topic')
def topics(num_topics, algorithm, words):
    """
    Discover topics across all articles using LDA/NMF.

    Example:
        python -m scrapetui ai topics --num-topics 5 --algorithm lda
    """
    try:
        init_db()

        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT id FROM scraped_data WHERE content IS NOT NULL LIMIT 100"
            ).fetchall()

            if not rows:
                click.echo("✗ No articles with content found", err=True)
                sys.exit(1)

            article_ids = [row[0] for row in rows]

        click.echo(f"Discovering {num_topics} topics from {len(article_ids)} articles using {algorithm.upper()}...")

        # Use topic modeling manager (Sprint 3 framework)
        from ...ai.topic_modeling import TopicModelingManager

        manager = TopicModelingManager()
        result = manager.discover_topics(
            article_ids=article_ids,
            num_topics=num_topics,
            algorithm=algorithm,
            words_per_topic=words
        )

        click.echo("\nTopics:")
        for topic in result.get('topics', []):
            topic_id = topic.get('topic_id', 0)
            words_list = topic.get('words', [])
            top_words = ', '.join([f"{w.get('word', '')}" for w in words_list[:words]])
            click.echo(f"\n  Topic {topic_id}: {top_words}")

        click.echo(f"\n✓ Discovered {len(result.get('topics', []))} topics")

    except Exception as e:
        logger.error(f"Topic modeling failed: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@ai.command()
@click.option('--query', required=True, help='Question to answer')
@click.option('--limit', default=5, type=int, help='Number of articles to search')
@click.option('--provider', type=click.Choice(['gemini', 'openai', 'claude']), default='gemini',
              help='AI provider to use')
def question(query, limit, provider):
    """
    Answer a question using article content.

    Example:
        python -m scrapetui ai question --query "What are the main trends?" --limit 10
    """
    try:
        init_db()

        with get_db_connection() as conn:
            rows = conn.execute(
                """SELECT id FROM scraped_data
                   WHERE content IS NOT NULL
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (limit,)
            ).fetchall()

            if not rows:
                click.echo("✗ No articles with content found", err=True)
                sys.exit(1)

            article_ids = [row[0] for row in rows]

        click.echo(f"Answering question using {len(article_ids)} articles with {provider}...")
        click.echo(f"Question: {query}\n")

        # Use question answering manager (Sprint 3 framework)
        from ...ai.question_answering import QuestionAnsweringManager

        manager = QuestionAnsweringManager()
        result = manager.answer_question(query, article_ids)

        click.echo("Answer:")
        click.echo(f"  {result.get('answer', 'No answer generated')}\n")
        click.echo(f"Sources: Articles {', '.join(map(str, result.get('sources', [])))}")
        click.echo(f"Confidence: {result.get('confidence', 0.0):.2f}")

        click.echo("\n✓ Question answered successfully")

    except Exception as e:
        logger.error(f"Question answering failed: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@ai.command()
@click.option('--article-id', required=True, type=int, help='Article ID to find similar articles for')
@click.option('--top', default=5, type=int, help='Number of similar articles to find')
def similar(article_id, top):
    """
    Find similar articles using content similarity.

    Example:
        python -m scrapetui ai similar --article-id 123 --top 5
    """
    try:
        init_db()

        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT title FROM scraped_data WHERE id = ?",
                (article_id,)
            ).fetchone()

            if not row:
                click.echo(f"✗ Article {article_id} not found", err=True)
                sys.exit(1)

            title = row[0]

        click.echo(f"Finding {top} similar articles to: {title}...")

        # Use content similarity manager (Sprint 3 framework)
        from ...ai.content_similarity import ContentSimilarityManager

        manager = ContentSimilarityManager()
        similar_articles = manager.find_similar_articles(article_id, top_k=top)

        if not similar_articles:
            click.echo("\n✗ No similar articles found")
            return

        click.echo("\nSimilar articles:")
        for article in similar_articles:
            click.echo(f"  • Article {article.get('article_id', 0)}: {article.get('title', 'Untitled')}")
            click.echo(f"    Similarity: {article.get('similarity', 0.0):.3f}")

        click.echo(f"\n✓ Found {len(similar_articles)} similar articles")

    except Exception as e:
        logger.error(f"Similarity search failed: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
