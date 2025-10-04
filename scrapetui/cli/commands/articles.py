#!/usr/bin/env python3
"""Article management CLI commands."""

import click
import sys
import json

from ...core.database import get_db_connection, init_db
from ...utils.logging import get_logger

logger = get_logger(__name__)


@click.group()
def articles():
    """Article management commands."""
    pass


@articles.command()
@click.option('--limit', default=20, type=int, help='Number of articles to list')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json', 'table']), default='table',
              help='Output format')
def list(limit, output_format):
    """
    List articles.

    Example:
        python -m scrapetui articles list --limit 50
    """
    try:
        init_db()

        with get_db_connection() as conn:
            rows = conn.execute("""
                SELECT id, title, url, timestamp, sentiment
                FROM scraped_data
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,)).fetchall()

        if not rows:
            click.echo("No articles found")
            return

        if output_format == 'json':
            articles = []
            for row in rows:
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'url': row[2],
                    'timestamp': row[3],
                    'sentiment': row[4]
                })
            click.echo(json.dumps(articles, indent=2))

        elif output_format == 'table':
            click.echo(f"{'ID':<6} {'Title':<50} {'Sentiment':<12} {'Date':<20}")
            click.echo("-" * 100)

            for row in rows:
                article_id, title, url, timestamp, sentiment = row
                title_str = (title[:47] + "...") if title and len(title) > 50 else (title or "No title")
                sentiment_str = sentiment or "-"

                click.echo(f"{article_id:<6} {title_str:<50} {sentiment_str:<12} {timestamp:<20}")

            click.echo(f"\nTotal: {len(rows)} articles")

        else:
            for row in rows:
                article_id, title, url, timestamp, sentiment = row
                click.echo(f"{article_id}: {title} ({timestamp})")

    except Exception as e:
        logger.error(f"Article listing failed: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@articles.command()
@click.option('--article-id', required=True, type=int, help='Article ID to display')
def show(article_id):
    """
    Show full article details.

    Example:
        python -m scrapetui articles show --article-id 123
    """
    try:
        init_db()

        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM scraped_data WHERE id = ?",
                (article_id,)
            ).fetchone()

            if not row:
                click.echo(f"✗ Article {article_id} not found", err=True)
                sys.exit(1)

        click.echo(f"\nArticle ID: {row[0]}")
        click.echo(f"Title: {row[2]}")
        click.echo(f"URL: {row[1]}")
        click.echo(f"Link: {row[3]}")
        click.echo(f"Timestamp: {row[4]}")
        click.echo(f"Sentiment: {row[6] or 'Not analyzed'}")
        click.echo(f"\nSummary:")
        click.echo(f"  {row[5] or 'No summary'}")
        click.echo(f"\nContent:")
        click.echo(f"  {row[7][:500] if row[7] else 'No content'}...")

    except Exception as e:
        logger.error(f"Article display failed: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@articles.command()
@click.option('--article-id', required=True, type=int, help='Article ID to delete')
def delete(article_id):
    """
    Delete an article.

    Example:
        python -m scrapetui articles delete --article-id 123
    """
    try:
        init_db()

        with get_db_connection() as conn:
            # Check article exists
            row = conn.execute(
                "SELECT title FROM scraped_data WHERE id = ?",
                (article_id,)
            ).fetchone()

            if not row:
                click.echo(f"✗ Article {article_id} not found", err=True)
                sys.exit(1)

            title = row[0]

            if not click.confirm(f"Delete article '{title}'?"):
                click.echo("Cancelled")
                return

            # Delete article
            conn.execute("DELETE FROM scraped_data WHERE id = ?", (article_id,))
            conn.commit()

        click.echo(f"✓ Article {article_id} deleted successfully")

    except Exception as e:
        logger.error(f"Article deletion failed: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
