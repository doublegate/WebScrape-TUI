#!/usr/bin/env python3
"""Export CLI commands for WebScrape-TUI."""

import click
import csv
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from ...core.database import get_db_connection, init_db
from ...utils.logging import get_logger

logger = get_logger(__name__)


@click.group()
def export():
    """Export articles in various formats (CSV, JSON, Excel, PDF)."""
    pass


def _build_export_query(
    search: Optional[str] = None,
    tag: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user_id: Optional[int] = None,
    sentiment: Optional[str] = None,
    limit: Optional[int] = None
) -> tuple[str, dict]:
    """
    Build SQL query with filters for export.

    Returns:
        Tuple of (query_string, parameters_dict)
    """
    query = """
        SELECT
            sd.id,
            sd.title,
            sd.url,
            sd.link,
            sd.timestamp,
            sd.summary,
            sd.sentiment,
            sd.user_id,
            GROUP_CONCAT(DISTINCT t.name) as tags
        FROM scraped_data sd
        LEFT JOIN article_tags at ON sd.id = at.article_id
        LEFT JOIN tags t ON at.tag_id = t.id
    """

    conditions = []
    params = {}

    if search:
        conditions.append("(sd.title LIKE :search OR sd.summary LIKE :search)")
        params["search"] = f"%{search}%"

    if tag:
        conditions.append("""
            sd.id IN (
                SELECT at2.article_id
                FROM article_tags at2
                JOIN tags t2 ON at2.tag_id = t2.id
                WHERE t2.name = :tag
            )
        """)
        params["tag"] = tag

    if date_from:
        conditions.append("date(sd.timestamp) >= :date_from")
        params["date_from"] = date_from

    if date_to:
        conditions.append("date(sd.timestamp) <= :date_to")
        params["date_to"] = date_to

    if user_id is not None:
        conditions.append("sd.user_id = :user_id")
        params["user_id"] = user_id

    if sentiment:
        conditions.append("sd.sentiment LIKE :sentiment")
        params["sentiment"] = f"%{sentiment}%"

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " GROUP BY sd.id ORDER BY sd.timestamp DESC"

    if limit:
        query += f" LIMIT {limit}"

    return query, params


def _fetch_articles(
    search: Optional[str] = None,
    tag: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user_id: Optional[int] = None,
    sentiment: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Fetch articles from database with filters."""
    query, params = _build_export_query(
        search=search,
        tag=tag,
        date_from=date_from,
        date_to=date_to,
        user_id=user_id,
        sentiment=sentiment,
        limit=limit
    )

    with get_db_connection() as conn:
        rows = conn.execute(query, params).fetchall()

        articles = []
        for row in rows:
            # Convert row to dictionary
            article = {
                'id': row['id'],
                'title': row['title'],
                'url': row['url'],
                'link': row['link'],
                'timestamp': row['timestamp'],
                'summary': row['summary'],
                'sentiment': row['sentiment'],
                'user_id': row['user_id'],
                'tags': row['tags'] if row['tags'] else ''
            }
            articles.append(article)

        return articles


@export.command('csv')
@click.option('--output', '-o', required=True, type=click.Path(), help='Output CSV file path')
@click.option('--search', help='Search text in title/content')
@click.option('--tag', help='Filter by tag')
@click.option('--date-from', help='Articles after date (YYYY-MM-DD)')
@click.option('--date-to', help='Articles before date (YYYY-MM-DD)')
@click.option('--user-id', type=int, help='Filter by user ID')
@click.option('--sentiment', help='Filter by sentiment (Positive, Negative, Neutral)')
@click.option('--limit', type=int, help='Limit number of results')
def export_csv(output, search, tag, date_from, date_to, user_id, sentiment, limit):
    """
    Export articles to CSV format.

    Examples:
        \b
        # Export all articles
        python -m scrapetui.cli export csv --output articles.csv

        # Export with filters
        python -m scrapetui.cli export csv --output tech.csv --tag "technology" --limit 100

        # Export specific date range
        python -m scrapetui.cli export csv --output recent.csv --date-from "2025-10-01"
    """
    try:
        init_db()

        with click.progressbar(length=3, label='Exporting to CSV') as bar:
            # Step 1: Fetch articles
            bar.label = 'Fetching articles...'
            articles = _fetch_articles(
                search=search,
                tag=tag,
                date_from=date_from,
                date_to=date_to,
                user_id=user_id,
                sentiment=sentiment,
                limit=limit
            )
            bar.update(1)

            if not articles:
                click.echo("No articles found matching the criteria.", err=True)
                sys.exit(1)

            # Step 2: Write to CSV
            bar.label = f'Writing {len(articles)} articles...'
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['ID', 'Title', 'Source URL', 'Article Link', 'Timestamp',
                             'Summary', 'Sentiment', 'User ID', 'Tags']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for article in articles:
                    # Format timestamp
                    timestamp_val = article['timestamp']
                    if isinstance(timestamp_val, datetime):
                        timestamp_str = timestamp_val.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        timestamp_str = str(timestamp_val)

                    writer.writerow({
                        'ID': article['id'],
                        'Title': article['title'],
                        'Source URL': article['url'],
                        'Article Link': article['link'],
                        'Timestamp': timestamp_str,
                        'Summary': article['summary'] or '',
                        'Sentiment': article['sentiment'] or '',
                        'User ID': article['user_id'],
                        'Tags': article['tags']
                    })

            bar.update(1)

            # Step 3: Done
            bar.label = 'Complete'
            bar.update(1)

        resolved_path = output_path.resolve()
        click.echo(f"\n✓ Exported {len(articles)} articles to {resolved_path}")
        logger.info(f"CSV export: {len(articles)} articles to {resolved_path}")

    except Exception as e:
        logger.error(f"CSV export failed: {e}", exc_info=True)
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@export.command('json')
@click.option('--output', '-o', required=True, type=click.Path(), help='Output JSON file path')
@click.option('--search', help='Search text in title/content')
@click.option('--tag', help='Filter by tag')
@click.option('--date-from', help='Articles after date (YYYY-MM-DD)')
@click.option('--date-to', help='Articles before date (YYYY-MM-DD)')
@click.option('--user-id', type=int, help='Filter by user ID')
@click.option('--sentiment', help='Filter by sentiment (Positive, Negative, Neutral)')
@click.option('--limit', type=int, help='Limit number of results')
@click.option('--pretty', is_flag=True, help='Pretty-print JSON output')
def export_json(output, search, tag, date_from, date_to, user_id, sentiment, limit, pretty):
    """
    Export articles to JSON format.

    Examples:
        \b
        # Export all articles (pretty-printed)
        python -m scrapetui.cli export json --output articles.json --pretty

        # Export with filters
        python -m scrapetui.cli export json --output tech.json --tag "technology"

        # Export compact JSON
        python -m scrapetui.cli export json --output data.json --limit 1000
    """
    try:
        init_db()

        with click.progressbar(length=3, label='Exporting to JSON') as bar:
            # Step 1: Fetch articles
            bar.label = 'Fetching articles...'
            articles = _fetch_articles(
                search=search,
                tag=tag,
                date_from=date_from,
                date_to=date_to,
                user_id=user_id,
                sentiment=sentiment,
                limit=limit
            )
            bar.update(1)

            if not articles:
                click.echo("No articles found matching the criteria.", err=True)
                sys.exit(1)

            # Step 2: Convert timestamps to strings
            bar.label = f'Processing {len(articles)} articles...'
            for article in articles:
                timestamp_val = article['timestamp']
                if isinstance(timestamp_val, datetime):
                    article['timestamp'] = timestamp_val.isoformat()
                else:
                    article['timestamp'] = str(timestamp_val)
            bar.update(1)

            # Step 3: Write to JSON
            bar.label = 'Writing JSON file...'
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(
                    {
                        'exported_at': datetime.now().isoformat(),
                        'total_articles': len(articles),
                        'filters': {
                            'search': search,
                            'tag': tag,
                            'date_from': date_from,
                            'date_to': date_to,
                            'user_id': user_id,
                            'sentiment': sentiment,
                            'limit': limit
                        },
                        'articles': articles
                    },
                    jsonfile,
                    indent=2 if pretty else None,
                    ensure_ascii=False
                )
            bar.update(1)

        resolved_path = output_path.resolve()
        click.echo(f"\n✓ Exported {len(articles)} articles to {resolved_path}")
        logger.info(f"JSON export: {len(articles)} articles to {resolved_path}")

    except Exception as e:
        logger.error(f"JSON export failed: {e}", exc_info=True)
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@export.command('excel')
@click.option('--output', '-o', required=True, type=click.Path(), help='Output Excel file path')
@click.option('--search', help='Search text in title/content')
@click.option('--tag', help='Filter by tag')
@click.option('--date-from', help='Articles after date (YYYY-MM-DD)')
@click.option('--date-to', help='Articles before date (YYYY-MM-DD)')
@click.option('--user-id', type=int, help='Filter by user ID')
@click.option('--sentiment', help='Filter by sentiment (Positive, Negative, Neutral)')
@click.option('--limit', type=int, help='Limit number of results')
@click.option('--include-charts', is_flag=True, help='Include charts and visualizations')
@click.option('--template', type=click.Choice(['standard', 'executive', 'detailed']),
              default='standard', help='Export template style')
def export_excel(output, search, tag, date_from, date_to, user_id, sentiment, limit,
                include_charts, template):
    """
    Export articles to Excel (XLSX) format with formatting.

    Requires: openpyxl package

    Examples:
        \b
        # Basic export
        python -m scrapetui.cli export excel --output articles.xlsx

        # Export with charts
        python -m scrapetui.cli export excel --output report.xlsx --include-charts

        # Executive template
        python -m scrapetui.cli export excel --output executive.xlsx --template executive
    """
    try:
        # Check if openpyxl is available
        try:
            import importlib.util
            spec = importlib.util.find_spec("openpyxl")
            if spec is None:
                raise ImportError("openpyxl not found")
        except ImportError:
            click.echo("✗ Excel export requires 'openpyxl' package.", err=True)
            click.echo("  Install with: pip install openpyxl", err=True)
            sys.exit(1)

        init_db()

        # Import ExcelExportManager from monolithic scrapetui.py
        import importlib.util
        from pathlib import Path as PathLib

        scrapetui_path = PathLib(__file__).parent.parent.parent.parent / 'scrapetui.py'
        spec = importlib.util.spec_from_file_location("scrapetui_monolith", scrapetui_path)
        scrapetui_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scrapetui_module)

        ExcelExportManager = scrapetui_module.ExcelExportManager

        with click.progressbar(length=3, label='Exporting to Excel') as bar:
            # Step 1: Fetch articles
            bar.label = 'Fetching articles...'
            articles = _fetch_articles(
                search=search,
                tag=tag,
                date_from=date_from,
                date_to=date_to,
                user_id=user_id,
                sentiment=sentiment,
                limit=limit
            )
            bar.update(1)

            if not articles:
                click.echo("No articles found matching the criteria.", err=True)
                sys.exit(1)

            # Step 2: Convert to required format
            bar.label = f'Processing {len(articles)} articles...'
            formatted_articles = []
            for article in articles:
                formatted_articles.append({
                    'id': article['id'],
                    'title': article['title'],
                    'url': article['url'],
                    'link': article['link'],
                    'timestamp': article['timestamp'],
                    'summary': article['summary'] or '',
                    'sentiment': article['sentiment'] or '',
                    'user_id': article['user_id'],
                    'tags': article['tags']
                })
            bar.update(1)

            # Step 3: Export to Excel
            bar.label = 'Generating Excel file...'
            success = ExcelExportManager.export_to_excel(
                articles=formatted_articles,
                output_path=output,
                include_charts=include_charts,
                template=template
            )
            bar.update(1)

        if success:
            resolved_path = Path(output).resolve()
            click.echo(f"\n✓ Exported {len(articles)} articles to {resolved_path}")
            logger.info(f"Excel export: {len(articles)} articles to {resolved_path}")
        else:
            click.echo("✗ Excel export failed", err=True)
            sys.exit(1)

    except Exception as e:
        logger.error(f"Excel export failed: {e}", exc_info=True)
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@export.command('pdf')
@click.option('--output', '-o', required=True, type=click.Path(), help='Output PDF file path')
@click.option('--search', help='Search text in title/content')
@click.option('--tag', help='Filter by tag')
@click.option('--date-from', help='Articles after date (YYYY-MM-DD)')
@click.option('--date-to', help='Articles before date (YYYY-MM-DD)')
@click.option('--user-id', type=int, help='Filter by user ID')
@click.option('--sentiment', help='Filter by sentiment (Positive, Negative, Neutral)')
@click.option('--limit', type=int, help='Limit number of results')
@click.option('--include-charts', is_flag=True, help='Include charts and visualizations')
@click.option('--template', type=click.Choice(['standard', 'executive', 'detailed']),
              default='standard', help='Report template style')
def export_pdf(output, search, tag, date_from, date_to, user_id, sentiment, limit,
              include_charts, template):
    """
    Export articles to PDF report format.

    Requires: reportlab package

    Examples:
        \b
        # Basic report
        python -m scrapetui.cli export pdf --output articles.pdf

        # Executive report with charts
        python -m scrapetui.cli export pdf --output report.pdf --template executive --include-charts

        # Filtered report
        python -m scrapetui.cli export pdf --output tech.pdf --tag "technology" --limit 50
    """
    try:
        # Check if reportlab is available
        try:
            import importlib.util
            spec = importlib.util.find_spec("reportlab")
            if spec is None:
                raise ImportError("reportlab not found")
        except ImportError:
            click.echo("✗ PDF export requires 'reportlab' package.", err=True)
            click.echo("  Install with: pip install reportlab", err=True)
            sys.exit(1)

        init_db()

        # Import PDFExportManager from monolithic scrapetui.py
        import importlib.util
        from pathlib import Path as PathLib

        scrapetui_path = PathLib(__file__).parent.parent.parent.parent / 'scrapetui.py'
        spec = importlib.util.spec_from_file_location("scrapetui_monolith", scrapetui_path)
        scrapetui_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scrapetui_module)

        PDFExportManager = scrapetui_module.PDFExportManager

        with click.progressbar(length=3, label='Exporting to PDF') as bar:
            # Step 1: Fetch articles
            bar.label = 'Fetching articles...'
            articles = _fetch_articles(
                search=search,
                tag=tag,
                date_from=date_from,
                date_to=date_to,
                user_id=user_id,
                sentiment=sentiment,
                limit=limit
            )
            bar.update(1)

            if not articles:
                click.echo("No articles found matching the criteria.", err=True)
                sys.exit(1)

            # Step 2: Convert to required format
            bar.label = f'Processing {len(articles)} articles...'
            formatted_articles = []
            for article in articles:
                formatted_articles.append({
                    'id': article['id'],
                    'title': article['title'],
                    'url': article['url'],
                    'link': article['link'],
                    'timestamp': article['timestamp'],
                    'summary': article['summary'] or '',
                    'sentiment': article['sentiment'] or '',
                    'user_id': article['user_id'],
                    'tags': article['tags']
                })
            bar.update(1)

            # Step 3: Export to PDF
            bar.label = 'Generating PDF report...'
            success = PDFExportManager.export_to_pdf(
                articles=formatted_articles,
                output_path=output,
                include_charts=include_charts,
                template=template
            )
            bar.update(1)

        if success:
            resolved_path = Path(output).resolve()
            click.echo(f"\n✓ Exported {len(articles)} articles to {resolved_path}")
            logger.info(f"PDF export: {len(articles)} articles to {resolved_path}")
        else:
            click.echo("✗ PDF export failed", err=True)
            sys.exit(1)

    except Exception as e:
        logger.error(f"PDF export failed: {e}", exc_info=True)
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    export()
