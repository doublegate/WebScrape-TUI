#!/usr/bin/env python3
"""Command-line interface for WebScrape-TUI (Sprint 3)."""

import click
from typing import Optional

from ..utils.logging import get_logger
from ..config import get_config

logger = get_logger(__name__)
config = get_config()


@click.group()
@click.version_option(version="2.2.0", prog_name="WebScrape-TUI")
@click.pass_context
def cli(ctx):
    """
    WebScrape-TUI - Web Scraping and AI-Powered Content Analysis Tool.

    A comprehensive CLI for web scraping, article management, and AI-powered
    content analysis with multi-user support and background task processing.

    Examples:
        \b
        # Scrape a URL
        python -m scrapetui scrape --url "https://example.com" --selector "h2 a"

        # Summarize an article
        python -m scrapetui ai summarize --article-id 123

        # List all articles
        python -m scrapetui articles list

        # Create a user
        python -m scrapetui user create --username alice --role user
    """
    # Initialize context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['config'] = config


# Import and register command groups (lazy import to avoid circular dependencies)
def _register_commands():
    """Register CLI command groups."""
    try:
        from .commands.scrape import scrape as scrape_cmd
        from .commands.ai import ai as ai_cmd
        from .commands.user import user as user_cmd
        from .commands.db import db as db_cmd
        from .commands.articles import articles as articles_cmd
        from .commands.export import export as export_cmd

        cli.add_command(scrape_cmd, name="scrape")
        cli.add_command(ai_cmd, name="ai")
        cli.add_command(user_cmd, name="user")
        cli.add_command(db_cmd, name="db")
        cli.add_command(articles_cmd, name="articles")
        cli.add_command(export_cmd, name="export")
    except ImportError as e:
        logger.error(f"Failed to import CLI commands: {e}")
        raise

_register_commands()


if __name__ == "__main__":
    cli()
