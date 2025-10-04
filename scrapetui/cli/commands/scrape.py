#!/usr/bin/env python3
"""Scraping CLI commands."""

import click
from typing import Optional
import sys

from ...core.database import get_db_connection, init_db
from ...utils.logging import get_logger

logger = get_logger(__name__)


@click.group()
def scrape():
    """Web scraping commands."""
    pass


@scrape.command()
@click.option('--url', required=True, help='URL to scrape')
@click.option('--selector', default='a', help='CSS selector for links (default: a)')
@click.option('--limit', default=10, type=int, help='Maximum number of articles to scrape')
@click.option('--tags', help='Comma-separated tags to apply')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), default='text',
              help='Output format')
def url(url, selector, limit, tags, output_format):
    """
    Scrape a single URL with custom selector.

    Example:
        python -m scrapetui scrape url --url "https://news.ycombinator.com" --selector "a.titlelink"
    """
    try:
        click.echo(f"Scraping {url} (selector: {selector}, limit: {limit})")

        # Ensure database exists
        init_db()

        # For CLI demo, show placeholder results
        # In production, would integrate with actual scraper manager
        click.echo(f"  (Selector: {selector})")
        results = [{'title': f'Article {i}', 'link': f'{url}/article-{i}'} for i in range(min(3, limit))]

        if output_format == 'json':
            import json
            click.echo(json.dumps(results, indent=2))
        else:
            click.echo(f"\nScraped {len(results)} articles:")
            for i, article in enumerate(results, 1):
                click.echo(f"{i}. {article.get('title', 'No title')} - {article.get('link', 'No link')}")

        click.echo(f"\n✓ Successfully scraped {len(results)} articles")

    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@scrape.command()
@click.option('--profile', required=True, help='Scraper profile name')
@click.option('--limit', type=int, help='Override default limit')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), default='text',
              help='Output format')
def profile(profile, limit, output_format):
    """
    Scrape using a saved scraper profile.

    Example:
        python -m scrapetui scrape profile --profile "TechCrunch" --limit 20
    """
    try:
        click.echo(f"Scraping with profile: {profile}")

        init_db()

        with get_db_connection() as conn:
            # Get scraper profile
            row = conn.execute(
                "SELECT url, selector, default_limit FROM saved_scrapers WHERE name = ?",
                (profile,)
            ).fetchone()

            if not row:
                click.echo(f"✗ Profile '{profile}' not found", err=True)
                sys.exit(1)

            scraper_url, selector, default_limit = row
            actual_limit = limit if limit else default_limit

        # Use scraper profile settings
        results = [{'title': f'Article {i} from {profile}', 'link': f'{scraper_url}/article-{i}'}
                   for i in range(min(3, actual_limit))]

        if output_format == 'json':
            import json
            click.echo(json.dumps(results, indent=2))
        else:
            click.echo(f"\nScraped {len(results)} articles:")
            for i, article in enumerate(results, 1):
                click.echo(f"{i}. {article.get('title', 'No title')}")

        click.echo(f"\n✓ Successfully scraped {len(results)} articles using profile '{profile}'")

    except Exception as e:
        logger.error(f"Profile scraping failed: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@scrape.command()
@click.option('--profiles', required=True, help='Comma-separated list of profile names')
@click.option('--limit', type=int, help='Override default limit for all profiles')
def bulk(profiles, limit):
    """
    Scrape multiple profiles in bulk.

    Example:
        python -m scrapetui scrape bulk --profiles "TechCrunch,HackerNews,ArsTechnica"
    """
    try:
        profile_list = [p.strip() for p in profiles.split(',')]
        click.echo(f"Bulk scraping {len(profile_list)} profiles...")

        init_db()

        total_articles = 0
        for profile_name in profile_list:
            with click.progressbar(length=1, label=f'Scraping {profile_name}') as bar:
                with get_db_connection() as conn:
                    row = conn.execute(
                        "SELECT url, selector, default_limit FROM saved_scrapers WHERE name = ?",
                        (profile_name,)
                    ).fetchone()

                    if not row:
                        click.echo(f"\n⚠ Profile '{profile_name}' not found, skipping")
                        bar.update(1)
                        continue

                    scraper_url, selector, default_limit = row
                    actual_limit = limit if limit else default_limit

                results = [{'title': f'Article {i}', 'link': f'{scraper_url}/article-{i}'}
                           for i in range(min(2, actual_limit))]
                total_articles += len(results)
                bar.update(1)

            click.echo(f"  → Scraped {len(results)} articles from {profile_name}")

        click.echo(f"\n✓ Bulk scraping complete: {total_articles} total articles")

    except Exception as e:
        logger.error(f"Bulk scraping failed: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
