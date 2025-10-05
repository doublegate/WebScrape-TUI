#!/usr/bin/env python3
"""Scraping CLI commands."""

import click
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sqlite3

from ...core.database import get_db_connection, init_db
from ...utils.logging import get_logger

logger = get_logger(__name__)


@click.group()
def scrape():
    """Web scraping commands."""


@scrape.command()
@click.option('--url', required=True, help='URL to scrape')
@click.option('--selector', default='a', help='CSS selector for links (default: a)')
@click.option('--limit', default=10, type=int, help='Maximum number of articles to scrape')
@click.option('--tags', help='Comma-separated tags to apply')
@click.option('--user-id', type=int, default=1, help='User ID for ownership (default: 1 = admin)')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), default='text',
              help='Output format')
def url(url, selector, limit, tags, user_id, output_format):
    """
    Scrape a single URL with custom selector.

    Example:
        python -m scrapetui.cli scrape url --url "https://news.ycombinator.com" --selector "a.titlelink"
    """
    try:
        init_db()

        with click.progressbar(length=3, label=f'Scraping {url}') as bar:
            # Step 1: Fetch URL
            bar.label = 'Fetching URL...'
            headers = {'User-Agent': 'Mozilla/5.0 WebScraperTUI/5.0'}
            response = requests.get(url, timeout=15, headers=headers)
            response.raise_for_status()
            bar.update(1)

            # Step 2: Parse HTML
            bar.label = 'Parsing HTML...'
            soup = BeautifulSoup(response.text, 'lxml')
            items = soup.select(selector)

            if not items:
                click.echo(f"\n⚠ No items found with selector '{selector}'", err=True)
                sys.exit(1)

            bar.update(1)

            # Step 3: Store articles
            bar.label = 'Storing articles...'
            records = []
            for i, tag_item in enumerate(items):
                if limit > 0 and len(records) >= limit:
                    break

                title = tag_item.get_text(strip=True)
                link_href = tag_item.get('href')

                if title and link_href:
                    full_link = urljoin(url, link_href)
                    records.append({
                        'title': title,
                        'link': full_link,
                        'url': url
                    })

            if not records:
                click.echo("\n⚠ No valid articles found", err=True)
                sys.exit(1)

            # Insert into database
            inserted_ids = []
            skipped = 0

            with get_db_connection() as conn:
                cursor = conn.cursor()
                for record in records:
                    try:
                        cursor.execute(
                            "INSERT INTO scraped_data (url, title, link, user_id) VALUES (?, ?, ?, ?)",
                            (record['url'], record['title'], record['link'], user_id)
                        )
                        if cursor.lastrowid:
                            inserted_ids.append(cursor.lastrowid)
                            record['id'] = cursor.lastrowid
                    except sqlite3.IntegrityError:
                        skipped += 1
                        logger.debug(f"Skipped duplicate: {record['link']}")

                conn.commit()

                # Apply tags if provided
                if tags and inserted_ids:
                    tag_list = [t.strip() for t in tags.split(',') if t.strip()]
                    for tag_name in tag_list:
                        # Get or create tag
                        cursor.execute(
                            "INSERT OR IGNORE INTO tags (name) VALUES (?)",
                            (tag_name,)
                        )
                        cursor.execute(
                            "SELECT id FROM tags WHERE name = ?",
                            (tag_name,)
                        )
                        tag_row = cursor.fetchone()
                        if tag_row:
                            tag_id = tag_row[0]
                            # Apply tag to all new articles
                            for article_id in inserted_ids:
                                cursor.execute(
                                    "INSERT OR IGNORE INTO article_tags (article_id, tag_id) VALUES (?, ?)",
                                    (article_id, tag_id)
                                )
                    conn.commit()

            bar.update(1)

        # Display results
        inserted_count = len(inserted_ids)

        if output_format == 'json':
            import json
            click.echo(json.dumps({
                'url': url,
                'selector': selector,
                'inserted': inserted_count,
                'skipped': skipped,
                'articles': [r for r in records if r.get('id')]
            }, indent=2))
        else:
            click.echo(f"\n✓ Scraped {url}")
            click.echo(f"  Inserted: {inserted_count} new articles")
            click.echo(f"  Skipped: {skipped} duplicates")

            if inserted_count > 0:
                click.echo(f"\nNew articles:")
                for i, record in enumerate([r for r in records if r.get('id')][:5], 1):
                    click.echo(f"  {i}. {record['title'][:80]}")
                if inserted_count > 5:
                    click.echo(f"  ... and {inserted_count - 5} more")

        logger.info(f"CLI scrape: {inserted_count} inserted, {skipped} skipped from {url}")

    except requests.RequestException as e:
        logger.error(f"HTTP request failed: {e}")
        click.echo(f"✗ Error fetching URL: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@scrape.command()
@click.option('--profile', required=True, help='Scraper profile name')
@click.option('--limit', type=int, help='Override default limit')
@click.option('--user-id', type=int, default=1, help='User ID for ownership (default: 1 = admin)')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), default='text',
              help='Output format')
def profile(profile, limit, user_id, output_format):
    """
    Scrape using a saved scraper profile.

    Example:
        python -m scrapetui.cli scrape profile --profile "TechCrunch" --limit 20
    """
    try:
        init_db()

        # Get scraper profile
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT url, selector, default_limit, default_tags_csv FROM saved_scrapers WHERE name = ?",
                (profile,)
            ).fetchone()

            if not row:
                click.echo(f"✗ Profile '{profile}' not found", err=True)
                click.echo(f"\nAvailable profiles:")
                profiles = conn.execute("SELECT name FROM saved_scrapers ORDER BY name").fetchall()
                for p in profiles:
                    click.echo(f"  - {p[0]}")
                sys.exit(1)

            scraper_url, selector, default_limit, default_tags = row
            actual_limit = limit if limit else default_limit

        # Scrape using profile settings
        with click.progressbar(length=3, label=f'Scraping profile: {profile}') as bar:
            # Step 1: Fetch URL
            bar.label = 'Fetching URL...'
            headers = {'User-Agent': 'Mozilla/5.0 WebScraperTUI/5.0'}
            response = requests.get(scraper_url, timeout=15, headers=headers)
            response.raise_for_status()
            bar.update(1)

            # Step 2: Parse HTML
            bar.label = 'Parsing HTML...'
            soup = BeautifulSoup(response.text, 'lxml')
            items = soup.select(selector)

            if not items:
                click.echo(f"\n⚠ No items found with selector '{selector}'", err=True)
                sys.exit(1)

            bar.update(1)

            # Step 3: Store articles
            bar.label = 'Storing articles...'
            records = []
            for i, tag_item in enumerate(items):
                if actual_limit > 0 and len(records) >= actual_limit:
                    break

                title = tag_item.get_text(strip=True)
                link_href = tag_item.get('href')

                if title and link_href:
                    full_link = urljoin(scraper_url, link_href)
                    records.append({
                        'title': title,
                        'link': full_link,
                        'url': scraper_url
                    })

            if not records:
                click.echo("\n⚠ No valid articles found", err=True)
                sys.exit(1)

            # Insert into database
            inserted_ids = []
            skipped = 0

            with get_db_connection() as conn:
                cursor = conn.cursor()
                for record in records:
                    try:
                        cursor.execute(
                            "INSERT INTO scraped_data (url, title, link, user_id) VALUES (?, ?, ?, ?)",
                            (record['url'], record['title'], record['link'], user_id)
                        )
                        if cursor.lastrowid:
                            inserted_ids.append(cursor.lastrowid)
                            record['id'] = cursor.lastrowid
                    except sqlite3.IntegrityError:
                        skipped += 1
                        logger.debug(f"Skipped duplicate: {record['link']}")

                conn.commit()

                # Apply default tags if configured
                if default_tags and inserted_ids:
                    tag_list = [t.strip() for t in default_tags.split(',') if t.strip()]
                    for tag_name in tag_list:
                        cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
                        cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
                        tag_row = cursor.fetchone()
                        if tag_row:
                            tag_id = tag_row[0]
                            for article_id in inserted_ids:
                                cursor.execute(
                                    "INSERT OR IGNORE INTO article_tags (article_id, tag_id) VALUES (?, ?)",
                                    (article_id, tag_id)
                                )
                    conn.commit()

            bar.update(1)

        # Display results
        inserted_count = len(inserted_ids)

        if output_format == 'json':
            import json
            click.echo(json.dumps({
                'profile': profile,
                'url': scraper_url,
                'selector': selector,
                'inserted': inserted_count,
                'skipped': skipped,
                'articles': [r for r in records if r.get('id')]
            }, indent=2))
        else:
            click.echo(f"\n✓ Scraped using profile: {profile}")
            click.echo(f"  Inserted: {inserted_count} new articles")
            click.echo(f"  Skipped: {skipped} duplicates")

            if inserted_count > 0:
                click.echo(f"\nNew articles:")
                for i, record in enumerate([r for r in records if r.get('id')][:5], 1):
                    click.echo(f"  {i}. {record['title'][:80]}")
                if inserted_count > 5:
                    click.echo(f"  ... and {inserted_count - 5} more")

        logger.info(f"CLI scrape profile '{profile}': {inserted_count} inserted, {skipped} skipped")

    except requests.RequestException as e:
        logger.error(f"HTTP request failed: {e}")
        click.echo(f"✗ Error fetching URL: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Profile scraping failed: {e}", exc_info=True)
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@scrape.command()
@click.option('--profiles', required=True, help='Comma-separated list of profile names')
@click.option('--limit', type=int, help='Override default limit for all profiles')
@click.option('--user-id', type=int, default=1, help='User ID for ownership (default: 1 = admin)')
def bulk(profiles, limit, user_id):
    """
    Scrape multiple profiles in bulk.

    Example:
        python -m scrapetui.cli scrape bulk --profiles "TechCrunch,HackerNews,ArsTechnica"
    """
    try:
        profile_list = [p.strip() for p in profiles.split(',')]
        click.echo(f"Bulk scraping {len(profile_list)} profiles...\n")

        init_db()

        total_inserted = 0
        total_skipped = 0
        results_summary = []

        for profile_name in profile_list:
            try:
                # Get scraper profile
                with get_db_connection() as conn:
                    row = conn.execute(
                        "SELECT url, selector, default_limit, default_tags_csv FROM saved_scrapers WHERE name = ?",
                        (profile_name,)
                    ).fetchone()

                    if not row:
                        click.echo(f"⚠ Profile '{profile_name}' not found, skipping\n")
                        continue

                    scraper_url, selector, default_limit, default_tags = row
                    actual_limit = limit if limit else default_limit

                with click.progressbar(length=3, label=f'{profile_name}') as bar:
                    # Fetch and parse
                    bar.label = f'{profile_name}: Fetching...'
                    headers = {'User-Agent': 'Mozilla/5.0 WebScraperTUI/5.0'}
                    response = requests.get(scraper_url, timeout=15, headers=headers)
                    response.raise_for_status()
                    bar.update(1)

                    bar.label = f'{profile_name}: Parsing...'
                    soup = BeautifulSoup(response.text, 'lxml')
                    items = soup.select(selector)
                    bar.update(1)

                    # Store articles
                    bar.label = f'{profile_name}: Storing...'
                    records = []
                    for i, tag_item in enumerate(items):
                        if actual_limit > 0 and len(records) >= actual_limit:
                            break

                        title = tag_item.get_text(strip=True)
                        link_href = tag_item.get('href')

                        if title and link_href:
                            full_link = urljoin(scraper_url, link_href)
                            records.append({
                                'title': title,
                                'link': full_link,
                                'url': scraper_url
                            })

                    inserted_ids = []
                    skipped = 0

                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        for record in records:
                            try:
                                cursor.execute(
                                    "INSERT INTO scraped_data (url, title, link, user_id) VALUES (?, ?, ?, ?)",
                                    (record['url'], record['title'], record['link'], user_id)
                                )
                                if cursor.lastrowid:
                                    inserted_ids.append(cursor.lastrowid)
                            except sqlite3.IntegrityError:
                                skipped += 1

                        conn.commit()

                        # Apply default tags
                        if default_tags and inserted_ids:
                            tag_list = [t.strip() for t in default_tags.split(',') if t.strip()]
                            for tag_name in tag_list:
                                cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
                                cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
                                tag_row = cursor.fetchone()
                                if tag_row:
                                    tag_id = tag_row[0]
                                    for article_id in inserted_ids:
                                        cursor.execute(
                                            "INSERT OR IGNORE INTO article_tags (article_id, tag_id) VALUES (?, ?)",
                                            (article_id, tag_id)
                                        )
                            conn.commit()

                    bar.update(1)

                inserted_count = len(inserted_ids)
                total_inserted += inserted_count
                total_skipped += skipped

                results_summary.append({
                    'profile': profile_name,
                    'inserted': inserted_count,
                    'skipped': skipped
                })

                click.echo(f"  ✓ {profile_name}: {inserted_count} new, {skipped} skipped\n")

            except requests.RequestException as e:
                click.echo(f"  ✗ {profile_name}: HTTP error - {e}\n")
                logger.error(f"Bulk scrape failed for {profile_name}: {e}")
            except Exception as e:
                click.echo(f"  ✗ {profile_name}: Error - {e}\n")
                logger.error(f"Bulk scrape failed for {profile_name}: {e}", exc_info=True)

        # Final summary
        click.echo(f"{'=' * 60}")
        click.echo(f"Bulk scraping complete:")
        click.echo(f"  Total inserted: {total_inserted}")
        click.echo(f"  Total skipped: {total_skipped}")
        click.echo(f"  Profiles processed: {len(results_summary)}/{len(profile_list)}")

        logger.info(
            f"CLI bulk scrape: {total_inserted} inserted, {total_skipped} skipped "
            f"from {len(results_summary)} profiles")

    except Exception as e:
        logger.error(f"Bulk scraping failed: {e}", exc_info=True)
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
