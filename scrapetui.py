#!/usr/bin/env python3
"""
WebScrape-TUI v1.0 - Text User Interface Web Scraping Application

A comprehensive Python-based terminal application for web scraping, data management,
and AI-powered content analysis built with the Textual framework.

PURPOSE:
This application provides an intuitive text-based user interface for scraping websites,
storing articles in a SQLite database, and applying AI-powered analysis including
summarization and sentiment analysis using Google's Gemini API.

KEY FEATURES:

• Interactive TUI built with Textual framework
  - Responsive terminal-based interface
  - Modal dialogs for user input
  - Real-time data tables with sorting and filtering
  - Status indicators and progress feedback

• Web Scraping Capabilities
  - Pre-configured scraper profiles for popular websites
  - Custom scraper creation with URL patterns and CSS selectors
  - BeautifulSoup-powered HTML parsing
  - Robust error handling and retry mechanisms

• Database Management
  - SQLite database for persistent data storage
  - Normalized schema with articles, tags, and scraper profiles
  - Transaction-safe operations with context managers
  - Automatic schema migrations and updates

• AI Integration
  - Google Gemini API integration for content analysis
  - Multiple summarization styles (brief, detailed, bullet points)
  - Sentiment analysis with confidence scoring
  - Async processing to maintain UI responsiveness

• Data Management
  - Advanced filtering by title, URL, date, tags, and sentiment
  - Multiple sorting options (date, title, URL, sentiment, etc.)
  - Tag-based organization system
  - CSV export functionality with applied filters

• Content Reading
  - Full-text article fetching and display
  - Markdown rendering for enhanced readability
  - Article preview and detailed view modes

TECHNICAL IMPLEMENTATION:

• Architecture Patterns:
  - Async/await for non-blocking operations
  - Worker pattern for background tasks
  - Modal screen pattern for user interactions
  - Reactive programming with Textual's reactive system

• Core Technologies:
  - Textual: Modern Python TUI framework
  - SQLite: Embedded database for data persistence
  - BeautifulSoup4: HTML parsing and content extraction
  - Requests: HTTP client for web scraping
  - LXML: Fast XML/HTML parser backend

• Data Flow:
  1. User configures scraper profiles or manual URL/selector input
  2. Background workers fetch content using BeautifulSoup
  3. Articles stored in normalized SQLite database
  4. Optional AI processing via Gemini API
  5. Reactive UI updates with filtered/sorted data display
  6. Export capabilities for data analysis

PENDING FEATURES & IMPROVEMENTS:
• Enhanced scraper profile management
• Additional AI model integrations
• Bulk operations for article management
• Advanced search capabilities
• Data visualization components
• Plugin system for custom processors
• Configuration file management
• Advanced export formats (JSON, XML)
• Scheduled scraping capabilities
• Content deduplication algorithms

CONFIGURATION:
- Database: scraped_data_tui_v1.0.db (configurable via .env)
- Logs: scraper_tui_v1.0.log (configurable via .env)
- Styles: web_scraper_tui_v1.0.tcss
- API Keys: Set GEMINI_API_KEY in .env file for AI features
- Environment: Configure via .env file (copy from .env.example)

VERSION: 1.0 (Stable Release)
AUTHOR: WebScrape-TUI Development Team
LICENSE: MIT
PYTHON: Requires Python 3.8+

For usage instructions, see README.md
For contribution guidelines, see CONTRIBUTING.md
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus
import logging
import csv
import json
import yaml
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, List, Optional, Tuple, Dict
from abc import ABC, abstractmethod
import functools

# APScheduler imports for scheduling functionality
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

# Data visualization and analytics imports (v1.6.0)
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless chart generation
import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter
from io import BytesIO
import base64

# Textual imports
from textual.app import App, ComposeResult
from textual.widgets import (
    Header, Footer, DataTable, Static, Button, Input, Label, Markdown,
    LoadingIndicator, RadioSet, RadioButton, ListView, ListItem, Checkbox
)
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.reactive import reactive
from textual.binding import Binding
from textual.logging import TextualHandler
# from textual.notifications import Notifications # Rely on App.notify()


# --- Environment Configuration ---
def load_env_file(env_path: Path = Path(".env")) -> Dict[str, str]:
    """
    Load environment variables from .env file.

    Args:
        env_path: Path to the .env file

    Returns:
        Dictionary of environment variables
    """
    env_vars = {}
    if env_path.exists():
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    # Parse KEY=VALUE format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        env_vars[key] = value
                    else:
                        print(f"Warning: Invalid format in .env file at "
                              f"line {line_num}: {line}")
        except Exception as e:
            print(f"Warning: Could not read .env file: {e}")
    else:
        print("Info: No .env file found. Using default configuration.")

    return env_vars


# Load environment variables
env_vars = load_env_file()

# --- Globals and Configuration ---
DB_PATH = Path(env_vars.get("DATABASE_PATH", "scraped_data_tui_v1.0.db"))
LOG_FILE = Path(env_vars.get("LOG_FILE_PATH", "scraper_tui_v1.0.log"))
GEMINI_API_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent?key={api_key}"
)
GEMINI_API_KEY = env_vars.get("GEMINI_API_KEY", "")
OPENAI_API_KEY = env_vars.get("OPENAI_API_KEY", "")
CLAUDE_API_KEY = env_vars.get("CLAUDE_API_KEY", "")

logging.basicConfig(
    level=env_vars.get("LOG_LEVEL", "DEBUG"),
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8'),
        TextualHandler()
    ],
    format=("%(asctime)s - %(name)s - %(levelname)s - "
            "%(module)s:%(lineno)d - %(message)s")
)
logger = logging.getLogger(__name__)

# Reduce noise from third-party libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("markdown_it").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("textual").setLevel(logging.INFO)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


# --- Database Utilities ---
def get_db_connection():
    try:
        conn = sqlite3.connect(
            DB_PATH,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.critical(f"DB connection error: {e}", exc_info=True)
        raise


PREINSTALLED_SCRAPERS = [
    {
        "name": "Generic Article Cleaner",
        "url": "[USER_PROVIDES_URL]",
        "selector": "article, main, div[role='main']",
        "default_limit": 1,
        "default_tags_csv": "article, general",
        "description": (
            "Tries to extract main content from any "
            "article-like page. Selectors are broad; may need "
            "refinement for specific sites."
        )
    },
    {
        "name": "Wikipedia Article Text",
        "url": "https://en.wikipedia.org/wiki/Web_scraping",
        "selector": "div.mw-parser-output p",
        "default_limit": 0,
        "default_tags_csv": "wikipedia, reference",
        "description": (
            "Extracts main paragraph text from Wikipedia "
            "articles. Aims to exclude infoboxes/navs."
        )
    },
    {
        "name": "StackOverflow Q&A",
        "url": "[USER_PROVIDES_URL]",
        "selector": "#question .s-prose, .answer .s-prose",
        "default_limit": 0,
        "default_tags_csv": "stackoverflow, q&a, tech",
        "description": (
            "Extracts questions and answers from StackOverflow "
            "pages. Point to a specific question URL."
        )
    },
    {
        "name": "News Headlines (General)",
        "url": "[USER_PROVIDES_URL]",
        "selector": (
            "h1 a, h2 a, h3 a, article header a, "
            ".headline a, .story-title a"
        ),
        "default_limit": 20,
        "default_tags_csv": "news, headlines",
        "description": (
            "Attempts to extract headlines and links from "
            "news websites. Selector covers common patterns."
        )
    },
    {
        "name": "Academic Abstract (arXiv)",
        "url": "https://arxiv.org/abs/2103.00020",
        "selector": "blockquote.abstract",
        "default_limit": 1,
        "default_tags_csv": "academic, abstract, arxiv",
        "description": (
            "Specifically targets arXiv.org to extract the "
            "abstract of a paper. Replace URL with desired "
            "arXiv paper."
        )
    },
    {
        "name": "Tech Specs (Simple Table)",
        "url": "[USER_PROVIDES_URL]",
        "selector": "table.specifications td, table.specs td",
        "default_limit": 0,
        "default_tags_csv": "technical, specs, table-data",
        "description": (
            "Aims to pull cell data from simple HTML tables "
            "often found in product specifications."
        )
    },
    {
        "name": "Forum Posts (Generic)",
        "url": "[USER_PROVIDES_URL]",
        "selector": ".post-content, .comment-text, .messageText",
        "default_limit": 0,
        "default_tags_csv": "forum, discussion",
        "description": (
            "Designed for typical forum thread structures "
            "to extract individual posts/comments."
        )
    },
    {
        "name": "Recipe Ingredients",
        "url": "[USER_PROVIDES_URL]",
        "selector": (
            ".recipe-ingredients li, .ingredient-list p, "
            "ul.ingredients li"
        ),
        "default_limit": 0,
        "default_tags_csv": "recipe, ingredients, food",
        "description": (
            "Focuses on extracting lists of ingredients from "
            "recipe web pages using common list patterns."
        )
    },
    {
        "name": "Product Details (Basic)",
        "url": "[USER_PROVIDES_URL]",
        "selector": (
            "h1.product-title, .product-name, span.price, "
            ".product-price, #priceblock_ourprice, .pdp-title, "
            ".pdp-price"
        ),
        "default_limit": 5,
        "default_tags_csv": "product, e-commerce",
        "description": (
            "Extracts product title and price from e-commerce "
            "pages using common selectors. Limit is low as it "
            "might pick up related product info."
        )
    },
    {
        "name": "Archived Page (Wayback)",
        "url": "[ARCHIVE_WAYBACK_URL]",
        "selector": "body",  # Special handling for URL
        "default_limit": 1,
        "default_tags_csv": "archive, wayback",
        "description": (
            "SPECIAL: Prompts for an original URL, then tries "
            "to fetch its latest version from the Wayback "
            "Machine. Scrapes entire body."
        )
    },
    {
        "name": "Hacker News Front Page",
        "url": "https://news.ycombinator.com/",
        "selector": "tr.athing",
        "default_limit": 30,
        "default_tags_csv": "hackernews, tech, news",
        "description": (
            "Scrapes the latest tech news and discussions from "
            "Hacker News front page. Extracts titles and links."
        )
    },
    {
        "name": "Reddit Subreddit Posts",
        "url": "https://old.reddit.com/r/python/",
        "selector": "div.thing",
        "default_limit": 25,
        "default_tags_csv": "reddit, social, discussion",
        "description": (
            "Extracts posts from Reddit using old.reddit.com interface. "
            "Change /r/python/ to any subreddit of interest."
        )
    },
    {
        "name": "Medium Articles",
        "url": "https://medium.com/tag/technology",
        "selector": "article, div[data-testid='article-preview']",
        "default_limit": 20,
        "default_tags_csv": "medium, blog, article",
        "description": (
            "Scrapes articles from Medium. Works best with topic tags "
            "or publication pages. Adjust tag in URL as needed."
        )
    },
    {
        "name": "Dev.to Articles",
        "url": "https://dev.to/",
        "selector": "article.crayons-story",
        "default_limit": 20,
        "default_tags_csv": "dev.to, programming, tutorial",
        "description": (
            "Extracts developer articles from Dev.to community. "
            "Great for programming tutorials and tech discussions."
        )
    },
    {
        "name": "GitHub Trending Repos",
        "url": "https://github.com/trending",
        "selector": "article.Box-row",
        "default_limit": 25,
        "default_tags_csv": "github, opensource, trending",
        "description": (
            "Scrapes trending repositories from GitHub. "
            "Can filter by language: /trending/python, /trending/rust, etc."
        )
    },
    {
        "name": "TechCrunch News",
        "url": "https://techcrunch.com/",
        "selector": "article.post-block",
        "default_limit": 20,
        "default_tags_csv": "techcrunch, startup, news",
        "description": (
            "Extracts latest startup and technology news from TechCrunch. "
            "Covers startups, funding, and tech industry news."
        )
    },
    {
        "name": "Ars Technica Articles",
        "url": "https://arstechnica.com/",
        "selector": "article, header.article-header",
        "default_limit": 15,
        "default_tags_csv": "arstechnica, tech, science",
        "description": (
            "Scrapes in-depth technology and science articles "
            "from Ars Technica."
        )
    },
    {
        "name": "The Verge Articles",
        "url": "https://www.theverge.com/",
        "selector": "div.duet--content-cards--content-card",
        "default_limit": 20,
        "default_tags_csv": "theverge, tech, consumer",
        "description": (
            "Extracts consumer technology news and reviews "
            "from The Verge."
        )
    },
    {
        "name": "Product Hunt Products",
        "url": "https://www.producthunt.com/",
        "selector": "li[data-test='post-item']",
        "default_limit": 20,
        "default_tags_csv": "producthunt, products, startup",
        "description": (
            "Scrapes new product launches from Product Hunt. "
            "Discover the latest tech products and tools."
        )
    },
    {
        "name": "Lobsters Tech News",
        "url": "https://lobste.rs/",
        "selector": "div.story",
        "default_limit": 25,
        "default_tags_csv": "lobsters, tech, programming",
        "description": (
            "Extracts computing-focused links from Lobsters community. "
            "High-quality tech discussions and articles."
        )
    },
    {
        "name": "RSS Feed Parser (Generic)",
        "url": "[USER_PROVIDES_URL]",
        "selector": "item, entry",
        "default_limit": 50,
        "default_tags_csv": "rss, feed, syndication",
        "description": (
            "Attempts to parse RSS/Atom feeds. "
            "Works with standard XML feed formats. "
            "Provide feed URL (ending in .xml, .rss, /feed, etc.)"
        )
    },
    {
        "name": "Documentation Pages",
        "url": "[USER_PROVIDES_URL]",
        "selector": (
            "article.documentation, div.doc-content, "
            "main.content, div.markdown-body"
        ),
        "default_limit": 1,
        "default_tags_csv": "documentation, reference, guide",
        "description": (
            "Extracts content from documentation pages. "
            "Works with common doc site patterns (ReadTheDocs, "
            "GitHub Pages, etc.)"
        )
    },
    {
        "name": "Blog Posts (WordPress)",
        "url": "[USER_PROVIDES_URL]",
        "selector": "article.post, div.post-content, article.hentry",
        "default_limit": 10,
        "default_tags_csv": "blog, wordpress, article",
        "description": (
            "Targets WordPress-based blogs using standard article "
            "selectors. Works with most WordPress themes."
        )
    },
    {
        "name": "YouTube Video Descriptions",
        "url": "[USER_PROVIDES_URL]",
        "selector": (
            "ytd-watch-metadata, "
            "ytd-video-description-transcript-section-renderer"
        ),
        "default_limit": 1,
        "default_tags_csv": "youtube, video, description",
        "description": (
            "Attempts to extract video title and description "
            "from YouTube watch pages. May require specific selectors."
        )
    }
]


def init_db():
    try:
        with get_db_connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS scraped_data ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "url TEXT NOT NULL, "
                "title TEXT NOT NULL, "
                "link TEXT NOT NULL, "
                "timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
                "summary TEXT, "
                "sentiment TEXT)"
            )
            try:
                conn.execute("ALTER TABLE scraped_data ADD COLUMN summary TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE scraped_data ADD COLUMN sentiment TEXT")
            except sqlite3.OperationalError:
                pass
            conn.execute(
                "CREATE TABLE IF NOT EXISTS tags ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "name TEXT NOT NULL UNIQUE)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS article_tags ("
                "article_id INTEGER NOT NULL, "
                "tag_id INTEGER NOT NULL, "
                "FOREIGN KEY (article_id) REFERENCES scraped_data(id) "
                "ON DELETE CASCADE, "
                "FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE, "
                "PRIMARY KEY (article_id, tag_id))"
            )
            conn.execute("""
                CREATE TABLE IF NOT EXISTS saved_scrapers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    url TEXT NOT NULL,
                    selector TEXT NOT NULL,
                    default_limit INTEGER DEFAULT 0,
                    default_tags_csv TEXT,
                    description TEXT,
                    is_preinstalled INTEGER DEFAULT 0
                )
            """)
            try:
                conn.execute(
                    "ALTER TABLE saved_scrapers ADD COLUMN description TEXT"
                )
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute(
                    "ALTER TABLE saved_scrapers ADD COLUMN "
                    "is_preinstalled INTEGER DEFAULT 0"
                )
            except sqlite3.OperationalError:
                pass

            # Add summarization templates table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS summarization_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    template TEXT NOT NULL,
                    description TEXT,
                    is_builtin INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Add filter presets table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS filter_presets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    title_filter TEXT,
                    url_filter TEXT,
                    date_from TEXT,
                    date_to TEXT,
                    tags_filter TEXT,
                    sentiment_filter TEXT,
                    use_regex INTEGER DEFAULT 0,
                    tags_logic TEXT DEFAULT 'AND',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Migrate old filter_presets if date_filter column exists
            try:
                conn.execute("ALTER TABLE filter_presets ADD COLUMN date_from TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE filter_presets ADD COLUMN date_to TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE filter_presets ADD COLUMN use_regex INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE filter_presets ADD COLUMN tags_logic TEXT DEFAULT 'AND'")
            except sqlite3.OperationalError:
                pass

            # Add scheduled scrapes table (v1.5.0)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_scrapes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    scraper_profile_id INTEGER,
                    schedule_type TEXT NOT NULL,
                    schedule_value TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    last_run TIMESTAMP,
                    next_run TIMESTAMP,
                    run_count INTEGER DEFAULT 0,
                    last_status TEXT,
                    last_error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (scraper_profile_id) REFERENCES saved_scrapers(id) ON DELETE CASCADE
                )
            """)

            index_statements = [
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_link_unique "
                "ON scraped_data (link);",
                "CREATE INDEX IF NOT EXISTS idx_url ON scraped_data (url);",
                "CREATE INDEX IF NOT EXISTS idx_timestamp "
                "ON scraped_data (timestamp);",
                "CREATE INDEX IF NOT EXISTS idx_title ON scraped_data (title);",
                "CREATE INDEX IF NOT EXISTS idx_sentiment "
                "ON scraped_data (sentiment);",
                "CREATE INDEX IF NOT EXISTS idx_tag_name ON tags (name);",
                "CREATE INDEX IF NOT EXISTS idx_article_tags_article "
                "ON article_tags (article_id);",
                "CREATE INDEX IF NOT EXISTS idx_article_tags_tag "
                "ON article_tags (tag_id);",
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_saved_scraper_name "
                "ON saved_scrapers (name);"
            ]
            for idx_sql in index_statements:
                conn.execute(idx_sql)
            for ps in PREINSTALLED_SCRAPERS:
                conn.execute("""
                    INSERT OR IGNORE INTO saved_scrapers (
                        name, url, selector, default_limit,
                        default_tags_csv, description, is_preinstalled
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (ps["name"], ps["url"], ps["selector"],
                      ps["default_limit"], ps["default_tags_csv"],
                      ps["description"]))

            # Insert built-in summarization templates
            builtin_templates = [
                ("Overview", "Provide a concise overview (100-150 words) of the following content:\n\n{content}\n\nOverview:", "Standard overview summary (100-150 words)"),
                ("Bullet Points", "Summarize the following content into key bullet points:\n\n{content}\n\nKey Points:", "Bullet-point summary of main ideas"),
                ("ELI5", "Explain the following content like I'm 5 years old:\n\n{content}\n\nSimple Explanation:", "Simplified explanation for general audience"),
                ("Academic", "Provide an academic-style summary with key findings, methodology, and conclusions:\n\n{content}\n\nAcademic Summary:", "Formal academic summary with structured analysis"),
                ("Executive Summary", "Create an executive summary highlighting key business insights, recommendations, and action items:\n\n{content}\n\nExecutive Summary:", "Business-focused summary with actionable insights"),
                ("Technical Brief", "Summarize the technical aspects, implementation details, and specifications:\n\n{content}\n\nTechnical Summary:", "Technical summary for engineering audience"),
                ("News Brief", "Write a news-style summary with who, what, when, where, why, and how:\n\n{content}\n\nNews Summary:", "Journalistic 5W1H summary format")
            ]
            for name, template, description in builtin_templates:
                conn.execute("""
                    INSERT OR IGNORE INTO summarization_templates (name, template, description, is_builtin)
                    VALUES (?, ?, ?, 1)
                """, (name, template, description))

            conn.commit()
        logger.info("Database initialized/updated successfully for v1.0.")
        return True
    except sqlite3.Error as e:
        logger.critical(f"DB init error v1.0: {e}", exc_info=True)
        return False


def get_tags_for_article(conn: sqlite3.Connection, article_id: int) -> List[str]:
    cursor = conn.execute(
        "SELECT t.name FROM tags t "
        "JOIN article_tags at ON t.id = at.tag_id "
        "WHERE at.article_id = ? ORDER BY t.name",
        (article_id,)
    )
    return [row['name'] for row in cursor.fetchall()]


def _update_tags_for_article_blocking(article_id: int, new_tags_str: str):
    with get_db_connection() as conn:
        current_tags = set(get_tags_for_article(conn, article_id))
        new_tags_list = [tag.strip().lower() for tag in new_tags_str.split(',') if tag.strip()]
        tags_to_add = [tn for tn in new_tags_list if tn not in current_tags]
        tags_to_remove = [tn for tn in current_tags if tn not in new_tags_list]
        for tag_name in tags_to_add:
            cur = conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
            tag_id = cur.lastrowid
            if not tag_id:
                tag_id = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()['id']
            conn.execute("INSERT OR IGNORE INTO article_tags (article_id, tag_id) VALUES (?, ?)", (article_id, tag_id))
        for tag_name in tags_to_remove:
            tag_id_row = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()
            if tag_id_row:
                conn.execute("DELETE FROM article_tags WHERE article_id = ? AND tag_id = ?", (article_id, tag_id_row['id']))
        conn.commit()


def fetch_article_content(article_url: str, for_reading: bool = False) -> str | None:
    logger.info(f"Fetching content from: {article_url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 WebScraperTUI/5.0'}
        response = requests.get(article_url, timeout=20, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml")
        elements = ["article", "main", "div[role='main']", ".entry-content", ".post-content", "body"]
        text = ""
        for s in elements:
            el = soup.select_one(s)
            if el:
                if for_reading:
                    for ut in el(['script', 'style', 'nav', 'header', 'footer', 'aside', '.sidebar']):
                        ut.decompose()
                    text = el.get_text(separator='\n', strip=True)
                else:
                    text = el.get_text(separator=' ', strip=True)
                if len(text) > 200:
                    break
        if for_reading:
            cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        else:
            cleaned = ' '.join(text.split())
        logger.info(f"Fetched ~{len(cleaned)} chars from {article_url}")
        return cleaned
    except Exception as e:
        logger.error(f"Err fetching {article_url}: {e}", exc_info=True)
        return None


# --- AI Provider Abstraction Layer ---

class AIProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def get_summary(self, text: str, style: str = "overview", template: Optional[str] = None) -> Optional[str]:
        """Generate a summary of the text."""
        pass

    @abstractmethod
    def get_sentiment(self, text: str) -> Optional[str]:
        """Analyze sentiment of the text. Returns: Positive, Negative, or Neutral."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for display."""
        pass

    @property
    @abstractmethod
    def available_models(self) -> List[str]:
        """List of available models for this provider."""
        pass


class GeminiProvider(AIProvider):
    """Google Gemini AI provider."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        super().__init__(api_key)
        self.model = model
        self.api_url_template = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "{model}:generateContent?key={api_key}"
        )

    @property
    def name(self) -> str:
        return "Google Gemini"

    @property
    def available_models(self) -> List[str]:
        return ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]

    def get_summary(self, text: str, style: str = "overview", template: Optional[str] = None, max_length: int = 15000) -> Optional[str]:
        if not text:
            return None
        if len(text) > max_length:
            text = text[:max_length]

        # Use custom template if provided, otherwise use default prompts
        if template:
            prompt = template.replace("{content}", text)
        else:
            prompts = {
                "overview": f"Provide a concise overview (100-150 words) of:\n\n{text}\n\nOverview:",
                "bullets": f"Summarize into key bullet points:\n\n{text}\n\nBullets:",
                "eli5": f"Explain like I'm 5:\n\n{text}\n\nELI5:"
            }
            prompt = prompts.get(style, prompts["overview"])

        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.6, "maxOutputTokens": 600}
        }
        api_url = self.api_url_template.format(model=self.model, api_key=self.api_key)
        logger.info(f"Requesting '{style}' summary from {self.name}.")

        try:
            response = requests.post(api_url, json=payload, timeout=90)
            response.raise_for_status()
            result = response.json()
            if result.get("candidates") and result["candidates"][0]["content"]["parts"][0].get("text"):
                summary = result["candidates"][0]["content"]["parts"][0]["text"]
                logger.info(f"Summary received (length: {len(summary)}).")
                return summary.strip()
            else:
                logger.error(f"Unexpected {self.name} summary response: {result}")
        except Exception as e:
            logger.error(f"Error calling {self.name} for summary: {e}", exc_info=True)
        return None

    def get_sentiment(self, text: str, max_length: int = 10000) -> Optional[str]:
        if not text:
            return None
        if len(text) > max_length:
            text = text[:max_length]

        prompt = (f"Analyze sentiment. Respond: Positive, Negative, or Neutral.\n\n"
                  f"Text:\n\"\"\"\n{text}\n\"\"\"\n\nSentiment:")
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 10}
        }
        api_url = self.api_url_template.format(model=self.model, api_key=self.api_key)
        logger.info(f"Requesting sentiment from {self.name}.")

        try:
            response = requests.post(api_url, json=payload, timeout=45)
            response.raise_for_status()
            result = response.json()
            if (result.get("candidates") and
                    result["candidates"][0]["content"]["parts"][0].get("text")):
                s_text = result["candidates"][0]["content"]["parts"][0]["text"].strip().capitalize()
                if s_text in ["Positive", "Negative", "Neutral"]:
                    logger.info(f"Sentiment: {s_text}.")
                    return s_text
                else:
                    logger.warning(f"LLM non-standard sentiment: '{s_text}'. Defaulting Neutral.")
                    return "Neutral"
            else:
                logger.error(f"Unexpected {self.name} sentiment response: {result}")
        except Exception as e:
            logger.error(f"Error calling {self.name} for sentiment: {e}", exc_info=True)
        return None


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        super().__init__(api_key)
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"

    @property
    def name(self) -> str:
        return "OpenAI"

    @property
    def available_models(self) -> List[str]:
        return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]

    def get_summary(self, text: str, style: str = "overview", template: Optional[str] = None, max_length: int = 15000) -> Optional[str]:
        if not text:
            return None
        if len(text) > max_length:
            text = text[:max_length]

        # Use custom template if provided, otherwise use default prompts
        if template:
            prompt = template.replace("{content}", text)
        else:
            prompts = {
                "overview": f"Provide a concise overview (100-150 words) of:\n\n{text}\n\nOverview:",
                "bullets": f"Summarize into key bullet points:\n\n{text}\n\nBullets:",
                "eli5": f"Explain like I'm 5:\n\n{text}\n\nELI5:"
            }
            prompt = prompts.get(style, prompts["overview"])

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.6,
            "max_tokens": 600
        }
        logger.info(f"Requesting '{style}' summary from {self.name}.")

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            result = response.json()
            if result.get("choices") and len(result["choices"]) > 0:
                summary = result["choices"][0]["message"]["content"]
                logger.info(f"Summary received (length: {len(summary)}).")
                return summary.strip()
            else:
                logger.error(f"Unexpected {self.name} summary response: {result}")
        except Exception as e:
            logger.error(f"Error calling {self.name} for summary: {e}", exc_info=True)
        return None

    def get_sentiment(self, text: str, max_length: int = 10000) -> Optional[str]:
        if not text:
            return None
        if len(text) > max_length:
            text = text[:max_length]

        prompt = (f"Analyze sentiment. Respond with ONLY one word: Positive, Negative, or Neutral.\n\n"
                  f"Text:\n\"\"\"\n{text}\n\"\"\"\n\nSentiment:")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 10
        }
        logger.info(f"Requesting sentiment from {self.name}.")

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=45)
            response.raise_for_status()
            result = response.json()
            if result.get("choices") and len(result["choices"]) > 0:
                s_text = result["choices"][0]["message"]["content"].strip().capitalize()
                if s_text in ["Positive", "Negative", "Neutral"]:
                    logger.info(f"Sentiment: {s_text}.")
                    return s_text
                else:
                    logger.warning(f"LLM non-standard sentiment: '{s_text}'. Defaulting Neutral.")
                    return "Neutral"
            else:
                logger.error(f"Unexpected {self.name} sentiment response: {result}")
        except Exception as e:
            logger.error(f"Error calling {self.name} for sentiment: {e}", exc_info=True)
        return None


class ClaudeProvider(AIProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-20241022"):
        super().__init__(api_key)
        self.model = model
        self.api_url = "https://api.anthropic.com/v1/messages"

    @property
    def name(self) -> str:
        return "Anthropic Claude"

    @property
    def available_models(self) -> List[str]:
        return ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"]

    def get_summary(self, text: str, style: str = "overview", template: Optional[str] = None, max_length: int = 15000) -> Optional[str]:
        if not text:
            return None
        if len(text) > max_length:
            text = text[:max_length]

        # Use custom template if provided, otherwise use default prompts
        if template:
            prompt = template.replace("{content}", text)
        else:
            prompts = {
                "overview": f"Provide a concise overview (100-150 words) of:\n\n{text}\n\nOverview:",
                "bullets": f"Summarize into key bullet points:\n\n{text}\n\nBullets:",
                "eli5": f"Explain like I'm 5:\n\n{text}\n\nELI5:"
            }
            prompt = prompts.get(style, prompts["overview"])

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 600,
            "temperature": 0.6
        }
        logger.info(f"Requesting '{style}' summary from {self.name}.")

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            result = response.json()
            if result.get("content") and len(result["content"]) > 0:
                summary = result["content"][0]["text"]
                logger.info(f"Summary received (length: {len(summary)}).")
                return summary.strip()
            else:
                logger.error(f"Unexpected {self.name} summary response: {result}")
        except Exception as e:
            logger.error(f"Error calling {self.name} for summary: {e}", exc_info=True)
        return None

    def get_sentiment(self, text: str, max_length: int = 10000) -> Optional[str]:
        if not text:
            return None
        if len(text) > max_length:
            text = text[:max_length]

        prompt = (f"Analyze sentiment. Respond with ONLY one word: Positive, Negative, or Neutral.\n\n"
                  f"Text:\n\"\"\"\n{text}\n\"\"\"\n\nSentiment:")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 10,
            "temperature": 0.2
        }
        logger.info(f"Requesting sentiment from {self.name}.")

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=45)
            response.raise_for_status()
            result = response.json()
            if result.get("content") and len(result["content"]) > 0:
                s_text = result["content"][0]["text"].strip().capitalize()
                if s_text in ["Positive", "Negative", "Neutral"]:
                    logger.info(f"Sentiment: {s_text}.")
                    return s_text
                else:
                    logger.warning(f"LLM non-standard sentiment: '{s_text}'. Defaulting Neutral.")
                    return "Neutral"
            else:
                logger.error(f"Unexpected {self.name} sentiment response: {result}")
        except Exception as e:
            logger.error(f"Error calling {self.name} for sentiment: {e}", exc_info=True)
        return None


# Global AI provider instance
_current_ai_provider: Optional[AIProvider] = None


def get_ai_provider() -> Optional[AIProvider]:
    """Get the currently configured AI provider."""
    global _current_ai_provider
    if _current_ai_provider is None:
        # Initialize default provider (Gemini)
        if GEMINI_API_KEY:
            _current_ai_provider = GeminiProvider(GEMINI_API_KEY)
    return _current_ai_provider


def set_ai_provider(provider: AIProvider) -> None:
    """Set the current AI provider."""
    global _current_ai_provider
    _current_ai_provider = provider


# --- Template Manager ---

class TemplateManager:
    """Manages custom summarization templates."""

    @staticmethod
    def get_all_templates() -> List[Dict[str, Any]]:
        """Get all templates from database."""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, name, template, description, is_builtin
                    FROM summarization_templates
                    ORDER BY is_builtin DESC, name ASC
                """)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error loading templates: {e}")
            return []

    @staticmethod
    def get_template_by_name(name: str) -> Optional[str]:
        """Get template text by name."""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    "SELECT template FROM summarization_templates WHERE name = ?",
                    (name,)
                )
                row = cursor.fetchone()
                return row['template'] if row else None
        except Exception as e:
            logger.error(f"Error loading template '{name}': {e}")
            return None

    @staticmethod
    def save_template(name: str, template: str, description: str = "") -> bool:
        """Save or update a custom template."""
        try:
            with get_db_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO summarization_templates (name, template, description, is_builtin)
                    VALUES (?, ?, ?, 0)
                """, (name, template, description))
                conn.commit()
                logger.info(f"Template '{name}' saved successfully.")
                return True
        except Exception as e:
            logger.error(f"Error saving template '{name}': {e}")
            return False

    @staticmethod
    def delete_template(name: str) -> bool:
        """Delete a custom template (cannot delete built-in)."""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM summarization_templates WHERE name = ? AND is_builtin = 0",
                    (name,)
                )
                conn.commit()
                if cursor.rowcount > 0:
                    logger.info(f"Template '{name}' deleted successfully.")
                    return True
                else:
                    logger.warning(f"Cannot delete built-in template '{name}'.")
                    return False
        except Exception as e:
            logger.error(f"Error deleting template '{name}': {e}")
            return False

    @staticmethod
    def apply_template(template: str, content: str, title: str = "", url: str = "", date: str = "") -> str:
        """Apply template variables to content."""
        # Replace variable placeholders
        result = template.replace("{content}", content)
        result = result.replace("{title}", title)
        result = result.replace("{url}", url)
        result = result.replace("{date}", date)
        return result


class ConfigManager:
    """Manages application configuration with YAML/JSON persistence."""

    DEFAULT_CONFIG = {
        'ai': {
            'default_provider': 'gemini',
            'default_model': None,
        },
        'export': {
            'default_format': 'csv',
            'output_directory': '.',
        },
        'ui': {
            'theme': 'default',
            'table_columns': ['ID', 'Title', 'URL', 'Link', 'Timestamp', 'Summary', 'Sentiment', 'Tags'],
        },
        'database': {
            'auto_vacuum': False,
            'backup_on_exit': False,
        },
        'logging': {
            'level': 'INFO',
            'max_file_size_mb': 10,
        }
    }

    CONFIG_PATH = Path('config.yaml')

    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """Load configuration from YAML file or create default."""
        if cls.CONFIG_PATH.exists():
            try:
                with open(cls.CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                    # Merge with defaults for any missing keys
                    return cls._merge_config(cls.DEFAULT_CONFIG.copy(), config)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                return cls.DEFAULT_CONFIG.copy()
        else:
            # Create default config file
            cls.save_config(cls.DEFAULT_CONFIG)
            return cls.DEFAULT_CONFIG.copy()

    @classmethod
    def save_config(cls, config: Dict[str, Any]) -> bool:
        """Save configuration to YAML file."""
        try:
            with open(cls.CONFIG_PATH, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    @classmethod
    def save_as_json(cls, config: Dict[str, Any], path: Path) -> bool:
        """Save configuration as JSON (alternative format)."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save JSON config: {e}")
            return False

    @classmethod
    def _merge_config(cls, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge override config into base config."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = cls._merge_config(result[key], value)
            else:
                result[key] = value
        return result


class FilterPresetManager:
    """Manages filter presets with database persistence."""

    @staticmethod
    def save_preset(name: str, title_filter: str, url_filter: str, date_from: str,
                   date_to: str, tags_filter: str, sentiment_filter: str,
                   use_regex: bool, tags_logic: str) -> bool:
        """Save a new filter preset or update existing."""
        try:
            with get_db_connection() as conn:
                # Check if preset exists
                cursor = conn.execute(
                    "SELECT id FROM filter_presets WHERE name = ?",
                    (name,)
                )
                existing = cursor.fetchone()

                if existing:
                    # Update existing preset
                    conn.execute(
                        """
                        UPDATE filter_presets
                        SET title_filter = ?, url_filter = ?, date_from = ?,
                            date_to = ?, tags_filter = ?, sentiment_filter = ?,
                            use_regex = ?, tags_logic = ?
                        WHERE name = ?
                        """,
                        (title_filter, url_filter, date_from, date_to,
                         tags_filter, sentiment_filter, int(use_regex), tags_logic, name)
                    )
                else:
                    # Insert new preset
                    conn.execute(
                        """
                        INSERT INTO filter_presets
                        (name, title_filter, url_filter, date_from, date_to,
                         tags_filter, sentiment_filter, use_regex, tags_logic)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (name, title_filter, url_filter, date_from, date_to,
                         tags_filter, sentiment_filter, int(use_regex), tags_logic)
                    )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving filter preset: {e}")
            return False

    @staticmethod
    def load_preset(name: str) -> Optional[Dict[str, Any]]:
        """Load a filter preset by name."""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT title_filter, url_filter, date_from, date_to,
                           tags_filter, sentiment_filter, use_regex, tags_logic
                    FROM filter_presets
                    WHERE name = ?
                    """,
                    (name,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        'title_filter': row['title_filter'] or '',
                        'url_filter': row['url_filter'] or '',
                        'date_from': row['date_from'] or '',
                        'date_to': row['date_to'] or '',
                        'tags_filter': row['tags_filter'] or '',
                        'sentiment_filter': row['sentiment_filter'] or '',
                        'use_regex': bool(row['use_regex']),
                        'tags_logic': row['tags_logic'] or 'AND'
                    }
                return None
        except Exception as e:
            logger.error(f"Error loading filter preset: {e}")
            return None

    @staticmethod
    def list_presets() -> List[str]:
        """List all available filter preset names."""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    "SELECT name FROM filter_presets ORDER BY created_at DESC"
                )
                return [row['name'] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error listing filter presets: {e}")
            return []

    @staticmethod
    def delete_preset(name: str) -> bool:
        """Delete a filter preset."""
        try:
            with get_db_connection() as conn:
                conn.execute("DELETE FROM filter_presets WHERE name = ?", (name,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting filter preset: {e}")
            return False


class ScheduleManager:
    """Manages scheduled scraping with APScheduler integration (v1.5.0)."""

    @staticmethod
    def create_schedule(name: str, scraper_profile_id: int, schedule_type: str,
                       schedule_value: str, enabled: bool = True) -> bool:
        """
        Create a new scheduled scrape.

        Args:
            name: Unique schedule name
            scraper_profile_id: ID of scraper profile to execute
            schedule_type: Type of schedule ('interval', 'cron', 'daily', 'weekly')
            schedule_value: Schedule parameters (e.g., '60' for 60 minutes, '0 9 * * *' for cron)
            enabled: Whether schedule is active

        Returns:
            True if successful, False otherwise
        """
        try:
            with get_db_connection() as conn:
                # Calculate next run time based on schedule
                next_run = ScheduleManager._calculate_next_run(schedule_type, schedule_value)

                conn.execute("""
                    INSERT INTO scheduled_scrapes
                    (name, scraper_profile_id, schedule_type, schedule_value, enabled, next_run)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, scraper_profile_id, schedule_type, schedule_value, int(enabled), next_run))
                conn.commit()
                logger.info(f"Schedule '{name}' created successfully")
                return True
        except sqlite3.IntegrityError as e:
            logger.error(f"Schedule name '{name}' already exists: {e}")
            return False
        except Exception as e:
            logger.error(f"Error creating schedule: {e}")
            return False

    @staticmethod
    def update_schedule(schedule_id: int, name: Optional[str] = None,
                       scraper_profile_id: Optional[int] = None,
                       schedule_type: Optional[str] = None,
                       schedule_value: Optional[str] = None,
                       enabled: Optional[bool] = None) -> bool:
        """Update an existing schedule."""
        try:
            with get_db_connection() as conn:
                # Build dynamic update query
                updates = []
                params = []

                if name is not None:
                    updates.append("name = ?")
                    params.append(name)
                if scraper_profile_id is not None:
                    updates.append("scraper_profile_id = ?")
                    params.append(scraper_profile_id)
                if schedule_type is not None and schedule_value is not None:
                    updates.append("schedule_type = ?")
                    updates.append("schedule_value = ?")
                    params.append(schedule_type)
                    params.append(schedule_value)
                    # Recalculate next run
                    next_run = ScheduleManager._calculate_next_run(schedule_type, schedule_value)
                    updates.append("next_run = ?")
                    params.append(next_run)
                if enabled is not None:
                    updates.append("enabled = ?")
                    params.append(int(enabled))

                if not updates:
                    return True  # Nothing to update

                params.append(schedule_id)
                query = f"UPDATE scheduled_scrapes SET {', '.join(updates)} WHERE id = ?"
                conn.execute(query, params)
                conn.commit()
                logger.info(f"Schedule ID {schedule_id} updated successfully")
                return True
        except Exception as e:
            logger.error(f"Error updating schedule: {e}")
            return False

    @staticmethod
    def delete_schedule(schedule_id: int) -> bool:
        """Delete a scheduled scrape."""
        try:
            with get_db_connection() as conn:
                conn.execute("DELETE FROM scheduled_scrapes WHERE id = ?", (schedule_id,))
                conn.commit()
                logger.info(f"Schedule ID {schedule_id} deleted successfully")
                return True
        except Exception as e:
            logger.error(f"Error deleting schedule: {e}")
            return False

    @staticmethod
    def list_schedules(enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all scheduled scrapes.

        Args:
            enabled_only: If True, only return enabled schedules

        Returns:
            List of schedule dictionaries
        """
        try:
            with get_db_connection() as conn:
                query = """
                    SELECT
                        ss.id, ss.name, ss.scraper_profile_id, ss.schedule_type,
                        ss.schedule_value, ss.enabled, ss.last_run, ss.next_run,
                        ss.run_count, ss.last_status, ss.last_error, ss.created_at,
                        sp.name as profile_name
                    FROM scheduled_scrapes ss
                    LEFT JOIN saved_scrapers sp ON ss.scraper_profile_id = sp.id
                """
                if enabled_only:
                    query += " WHERE ss.enabled = 1"
                query += " ORDER BY ss.created_at DESC"

                cursor = conn.execute(query)
                schedules = []
                for row in cursor.fetchall():
                    schedules.append({
                        'id': row['id'],
                        'name': row['name'],
                        'scraper_profile_id': row['scraper_profile_id'],
                        'profile_name': row['profile_name'],
                        'schedule_type': row['schedule_type'],
                        'schedule_value': row['schedule_value'],
                        'enabled': bool(row['enabled']),
                        'last_run': row['last_run'],
                        'next_run': row['next_run'],
                        'run_count': row['run_count'],
                        'last_status': row['last_status'],
                        'last_error': row['last_error'],
                        'created_at': row['created_at']
                    })
                return schedules
        except Exception as e:
            logger.error(f"Error listing schedules: {e}")
            return []

    @staticmethod
    def get_schedule(schedule_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific schedule by ID."""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute("""
                    SELECT
                        ss.id, ss.name, ss.scraper_profile_id, ss.schedule_type,
                        ss.schedule_value, ss.enabled, ss.last_run, ss.next_run,
                        ss.run_count, ss.last_status, ss.last_error, ss.created_at,
                        sp.name as profile_name, sp.url, sp.selector
                    FROM scheduled_scrapes ss
                    LEFT JOIN saved_scrapers sp ON ss.scraper_profile_id = sp.id
                    WHERE ss.id = ?
                """, (schedule_id,))
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row['id'],
                        'name': row['name'],
                        'scraper_profile_id': row['scraper_profile_id'],
                        'profile_name': row['profile_name'],
                        'profile_url': row['url'],
                        'profile_selector': row['selector'],
                        'schedule_type': row['schedule_type'],
                        'schedule_value': row['schedule_value'],
                        'enabled': bool(row['enabled']),
                        'last_run': row['last_run'],
                        'next_run': row['next_run'],
                        'run_count': row['run_count'],
                        'last_status': row['last_status'],
                        'last_error': row['last_error'],
                        'created_at': row['created_at']
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting schedule: {e}")
            return None

    @staticmethod
    def record_execution(schedule_id: int, status: str, error: Optional[str] = None) -> bool:
        """
        Record a schedule execution result.

        Args:
            schedule_id: Schedule ID
            status: Execution status ('success', 'failed', 'running')
            error: Error message if failed

        Returns:
            True if successful
        """
        try:
            with get_db_connection() as conn:
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Get current schedule to calculate next run
                cursor = conn.execute(
                    "SELECT schedule_type, schedule_value FROM scheduled_scrapes WHERE id = ?",
                    (schedule_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return False

                next_run = ScheduleManager._calculate_next_run(
                    row['schedule_type'],
                    row['schedule_value']
                )

                conn.execute("""
                    UPDATE scheduled_scrapes
                    SET last_run = ?, last_status = ?, last_error = ?,
                        run_count = run_count + 1, next_run = ?
                    WHERE id = ?
                """, (now, status, error, next_run, schedule_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error recording execution: {e}")
            return False

    @staticmethod
    def _calculate_next_run(schedule_type: str, schedule_value: str) -> str:
        """
        Calculate next run time based on schedule type.

        Args:
            schedule_type: Type of schedule ('interval', 'cron', 'daily', 'weekly', 'hourly')
            schedule_value: Schedule parameters

        Returns:
            ISO formatted datetime string for next run
        """
        now = datetime.now()

        try:
            if schedule_type == 'hourly':
                next_run = now + timedelta(hours=1)
            elif schedule_type == 'daily':
                # Parse HH:MM format from schedule_value
                try:
                    hour, minute = map(int, schedule_value.split(':'))
                    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if next_run <= now:
                        next_run += timedelta(days=1)
                except:
                    next_run = now + timedelta(days=1)
            elif schedule_type == 'weekly':
                # Parse day_of_week:HH:MM format (0=Monday, 6=Sunday)
                try:
                    parts = schedule_value.split(':')
                    day_of_week = int(parts[0])
                    hour, minute = int(parts[1]), int(parts[2])

                    days_ahead = day_of_week - now.weekday()
                    if days_ahead <= 0:  # Target day already happened this week
                        days_ahead += 7
                    next_run = now + timedelta(days=days_ahead)
                    next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
                except:
                    next_run = now + timedelta(weeks=1)
            elif schedule_type == 'interval':
                # Minutes interval
                try:
                    minutes = int(schedule_value)
                    next_run = now + timedelta(minutes=minutes)
                except:
                    next_run = now + timedelta(hours=1)
            elif schedule_type == 'cron':
                # For cron, we'll use a simplified next-hour approach
                # Full cron parsing would require croniter library
                next_run = now + timedelta(hours=1)
            else:
                next_run = now + timedelta(hours=1)

            return next_run.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logger.error(f"Error calculating next run: {e}")
            return (now + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')


class AnalyticsManager:
    """Manages data analytics and visualization (v1.6.0)."""

    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        """
        Get comprehensive statistics about scraped data.

        Returns:
            Dictionary containing various statistics
        """
        try:
            with get_db_connection() as conn:
                stats = {}

                # Total articles
                cursor = conn.execute("SELECT COUNT(*) as total FROM scraped_data")
                stats['total_articles'] = cursor.fetchone()['total']

                # Articles with summaries
                cursor = conn.execute("SELECT COUNT(*) as total FROM scraped_data WHERE summary IS NOT NULL")
                stats['articles_with_summaries'] = cursor.fetchone()['total']

                # Articles with sentiment
                cursor = conn.execute("SELECT COUNT(*) as total FROM scraped_data WHERE sentiment IS NOT NULL")
                stats['articles_with_sentiment'] = cursor.fetchone()['total']

                # Sentiment distribution
                cursor = conn.execute("""
                    SELECT sentiment, COUNT(*) as count
                    FROM scraped_data
                    WHERE sentiment IS NOT NULL
                    GROUP BY sentiment
                """)
                sentiment_dist = {row['sentiment']: row['count'] for row in cursor.fetchall()}
                stats['sentiment_distribution'] = sentiment_dist

                # Top sources
                cursor = conn.execute("""
                    SELECT url, COUNT(*) as count
                    FROM scraped_data
                    GROUP BY url
                    ORDER BY count DESC
                    LIMIT 10
                """)
                stats['top_sources'] = [(row['url'], row['count']) for row in cursor.fetchall()]

                # Top tags
                cursor = conn.execute("""
                    SELECT t.name, COUNT(*) as count
                    FROM tags t
                    JOIN article_tags at ON t.id = at.tag_id
                    GROUP BY t.id, t.name
                    ORDER BY count DESC
                    LIMIT 20
                """)
                stats['top_tags'] = [(row['name'], row['count']) for row in cursor.fetchall()]

                # Articles per day (last 30 days)
                cursor = conn.execute("""
                    SELECT DATE(timestamp) as date, COUNT(*) as count
                    FROM scraped_data
                    WHERE timestamp >= datetime('now', '-30 days')
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """)
                stats['articles_per_day'] = [(row['date'], row['count']) for row in cursor.fetchall()]

                # Summary statistics
                stats['summary_percentage'] = (
                    (stats['articles_with_summaries'] / stats['total_articles'] * 100)
                    if stats['total_articles'] > 0 else 0
                )
                stats['sentiment_percentage'] = (
                    (stats['articles_with_sentiment'] / stats['total_articles'] * 100)
                    if stats['total_articles'] > 0 else 0
                )

                return stats
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

    @staticmethod
    def generate_sentiment_chart(output_path: Optional[str] = None) -> Optional[str]:
        """
        Generate a pie chart showing sentiment distribution.

        Args:
            output_path: Optional file path to save chart. If None, returns base64 encoded image.

        Returns:
            File path if saved, or base64 encoded image string
        """
        try:
            stats = AnalyticsManager.get_statistics()
            sentiment_dist = stats.get('sentiment_distribution', {})

            if not sentiment_dist:
                logger.warning("No sentiment data available for chart")
                return None

            # Create pie chart
            plt.figure(figsize=(10, 6))
            labels = list(sentiment_dist.keys())
            sizes = list(sentiment_dist.values())
            colors = []
            for label in labels:
                if 'positive' in label.lower():
                    colors.append('#4CAF50')
                elif 'negative' in label.lower():
                    colors.append('#F44336')
                else:
                    colors.append('#FFC107')

            plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            plt.axis('equal')
            plt.title('Sentiment Distribution', fontsize=16, fontweight='bold')

            if output_path:
                plt.savefig(output_path, dpi=150, bbox_inches='tight')
                plt.close()
                return output_path
            else:
                # Return base64 encoded image
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                plt.close()
                buffer.seek(0)
                img_base64 = base64.b64encode(buffer.read()).decode()
                return f"data:image/png;base64,{img_base64}"
        except Exception as e:
            logger.error(f"Error generating sentiment chart: {e}")
            return None

    @staticmethod
    def generate_timeline_chart(output_path: Optional[str] = None) -> Optional[str]:
        """
        Generate a line chart showing articles scraped over time.

        Args:
            output_path: Optional file path to save chart. If None, returns base64 encoded image.

        Returns:
            File path if saved, or base64 encoded image string
        """
        try:
            stats = AnalyticsManager.get_statistics()
            articles_per_day = stats.get('articles_per_day', [])

            if not articles_per_day:
                logger.warning("No timeline data available for chart")
                return None

            # Create line chart
            dates = [item[0] for item in articles_per_day]
            counts = [item[1] for item in articles_per_day]

            plt.figure(figsize=(12, 6))
            plt.plot(dates, counts, marker='o', linestyle='-', linewidth=2, markersize=6, color='#2196F3')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Number of Articles', fontsize=12)
            plt.title('Articles Scraped Over Time (Last 30 Days)', fontsize=16, fontweight='bold')
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            if output_path:
                plt.savefig(output_path, dpi=150, bbox_inches='tight')
                plt.close()
                return output_path
            else:
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                plt.close()
                buffer.seek(0)
                img_base64 = base64.b64encode(buffer.read()).decode()
                return f"data:image/png;base64,{img_base64}"
        except Exception as e:
            logger.error(f"Error generating timeline chart: {e}")
            return None

    @staticmethod
    def generate_top_sources_chart(output_path: Optional[str] = None) -> Optional[str]:
        """
        Generate a horizontal bar chart showing top sources.

        Args:
            output_path: Optional file path to save chart. If None, returns base64 encoded image.

        Returns:
            File path if saved, or base64 encoded image string
        """
        try:
            stats = AnalyticsManager.get_statistics()
            top_sources = stats.get('top_sources', [])

            if not top_sources:
                logger.warning("No source data available for chart")
                return None

            # Create horizontal bar chart
            sources = [item[0][:50] + '...' if len(item[0]) > 50 else item[0] for item in top_sources]
            counts = [item[1] for item in top_sources]

            plt.figure(figsize=(12, 8))
            plt.barh(sources, counts, color='#9C27B0')
            plt.xlabel('Number of Articles', fontsize=12)
            plt.ylabel('Source', fontsize=12)
            plt.title('Top 10 Sources by Article Count', fontsize=16, fontweight='bold')
            plt.gca().invert_yaxis()  # Highest at top
            plt.tight_layout()

            if output_path:
                plt.savefig(output_path, dpi=150, bbox_inches='tight')
                plt.close()
                return output_path
            else:
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                plt.close()
                buffer.seek(0)
                img_base64 = base64.b64encode(buffer.read()).decode()
                return f"data:image/png;base64,{img_base64}"
        except Exception as e:
            logger.error(f"Error generating top sources chart: {e}")
            return None

    @staticmethod
    def generate_tag_cloud_data() -> List[Tuple[str, int]]:
        """
        Generate tag cloud data (tag frequencies).

        Returns:
            List of (tag_name, count) tuples sorted by count descending
        """
        try:
            stats = AnalyticsManager.get_statistics()
            return stats.get('top_tags', [])
        except Exception as e:
            logger.error(f"Error generating tag cloud data: {e}")
            return []

    @staticmethod
    def export_statistics_report(output_path: str) -> bool:
        """
        Export a comprehensive statistics report to a text file.

        Args:
            output_path: Path to save the report

        Returns:
            True if successful, False otherwise
        """
        try:
            stats = AnalyticsManager.get_statistics()

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("WebScrape-TUI Analytics Report\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")

                f.write("OVERVIEW\n")
                f.write("-" * 80 + "\n")
                f.write(f"Total Articles: {stats.get('total_articles', 0)}\n")
                f.write(f"Articles with Summaries: {stats.get('articles_with_summaries', 0)} ({stats.get('summary_percentage', 0):.1f}%)\n")
                f.write(f"Articles with Sentiment: {stats.get('articles_with_sentiment', 0)} ({stats.get('sentiment_percentage', 0):.1f}%)\n\n")

                f.write("SENTIMENT DISTRIBUTION\n")
                f.write("-" * 80 + "\n")
                for sentiment, count in stats.get('sentiment_distribution', {}).items():
                    f.write(f"  {sentiment}: {count}\n")
                f.write("\n")

                f.write("TOP 10 SOURCES\n")
                f.write("-" * 80 + "\n")
                for i, (source, count) in enumerate(stats.get('top_sources', []), 1):
                    f.write(f"{i:2d}. {source[:70]:<70} ({count} articles)\n")
                f.write("\n")

                f.write("TOP 20 TAGS\n")
                f.write("-" * 80 + "\n")
                for i, (tag, count) in enumerate(stats.get('top_tags', []), 1):
                    f.write(f"{i:2d}. {tag:<30} ({count} uses)\n")
                f.write("\n")

                f.write("=" * 80 + "\n")

            logger.info(f"Statistics report exported to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting statistics report: {e}")
            return False


# Legacy function wrappers for backward compatibility
def get_summary_from_llm(text_content: str, summary_style: str = "overview", max_length: int = 15000, template: Optional[str] = None) -> str | None:
    """Legacy wrapper that uses the current AI provider."""
    provider = get_ai_provider()
    if provider is None:
        logger.error("No AI provider configured. Set API keys in .env file.")
        return None
    return provider.get_summary(text_content, summary_style, template, max_length)


def get_sentiment_from_llm(text_content: str, max_length: int = 10000) -> Optional[str]:
    """Legacy wrapper that uses the current AI provider."""
    provider = get_ai_provider()
    if provider is None:
        logger.error("No AI provider configured. Set API keys in .env file.")
        return None
    return provider.get_sentiment(text_content, max_length)


def scrape_url_action(
    source_url: str, selector: str, limit: int = 0
) -> tuple[int, int, str, Optional[List[int]]]:
    logger.info(
        f"Scraping {source_url} with selector '{selector}', limit {limit}"
    )
    inserted_ids: List[int] = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 WebScraperTUI/5.0'}
        response = requests.get(source_url, timeout=15, headers=headers)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to fetch {source_url}: {e}")
        raise
    soup = BeautifulSoup(response.text, "lxml")
    items = soup.select(selector)
    if not items:
        logger.warning(f"No items for '{selector}' on {source_url}")
        return 0, 0, source_url, None
    records = []
    for i, tag_item in enumerate(items):
        if limit > 0 and len(records) >= limit:
            break
        title = tag_item.get_text(strip=True)
        link_href = tag_item.get("href")
        if title and link_href:
            records.append((source_url, title, urljoin(source_url, link_href)))
    if not records:
        return 0, 0, source_url, None
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            for rec_url, rec_title, rec_link in records:
                try:
                    c.execute("INSERT INTO scraped_data (url, title, link) VALUES (?, ?, ?)", (rec_url, rec_title, rec_link))
                    if c.lastrowid:
                        inserted_ids.append(c.lastrowid)
                except sqlite3.IntegrityError:
                    logger.debug(f"Skipping duplicate link: {rec_link}")
                    pass
            conn.commit()
        inserted_count, skipped_count = len(inserted_ids), len(records) - len(inserted_ids)
        logger.info(f"Scraping {source_url}: Stored {inserted_count} new, skipped {skipped_count} duplicates.")
        return inserted_count, skipped_count, source_url, inserted_ids
    except sqlite3.Error as e:
        logger.error(f"DB error storing from {source_url}: {e}", exc_info=True)
        raise


class ConfirmModal(ModalScreen[bool]):
    DEFAULT_CSS = """
    ConfirmModal {
        align: center middle;
        background: $surface-darken-1;
    }
    ConfirmModal > Vertical {
        width: auto;
        max-width: 80%;
        min-width: 50;
        height: auto;
        padding: 2 4;
        border: thick $primary-lighten-1;
        background: $panel;
    }
    ConfirmModal Label {
        margin-bottom: 1;
        width: 100%;
        text-align: center;
    }
    ConfirmModal Horizontal {
        width: 100%;
        height: auto;
        align-horizontal: center;
        padding-top: 1;
    }
    ConfirmModal Button {
        margin: 0 1;
        min-width: 10;
    }
    """
    BINDINGS = [Binding("escape", "dismiss_modal", "Cancel"), Binding("enter", "confirm_action", "Confirm")]

    def __init__(self, prompt: str, confirm_text: str = "Confirm", cancel_text: str = "Cancel"):
        super().__init__()
        self.prompt = prompt
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self.prompt)
            with Horizontal():
                yield Button(self.confirm_text, variant="primary", id="confirm")
                yield Button(self.cancel_text, id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm")

    def action_dismiss_modal(self) -> None:
        self.dismiss(False)

    def action_confirm_action(self) -> None:
        self.dismiss(True)


class FilenameModal(ModalScreen[Optional[str]]):
    DEFAULT_CSS = """
    FilenameModal {
        align: center middle;
        background: $surface-darken-1;
    }
    FilenameModal > Vertical {
        width: 60;
        height: auto;
        border: thick $primary-lighten-1;
        padding: 1 2;
        background: $surface;
    }
    FilenameModal Input {
        margin-bottom: 1;
    }
    FilenameModal Button {
        margin-top: 1;
    }
    FilenameModal Label.dialog-title {
        text-style: bold;
        width: 100%;
        text-align: center;
        margin-bottom: 1;
    }
    """

    def __init__(self, p: str = "Enter filename:", dfn: str = "export.csv"):
        super().__init__()
        self.p, self.dfn = p, dfn

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self.p, classes="dialog-title")
            yield Input(value=self.dfn, id="fn_in")
            yield Horizontal(
                Button("Save", variant="primary", id="sfn_b"),
                Button("Cancel", id="cfn_b"),
                classes="modal-buttons"
            )

    def on_button_pressed(self, e: Button.Pressed) -> None:
        if e.button.id == "sfn_b":
            fn = self.query_one("#fn_in", Input).value.strip()
            if fn:
                self.dismiss(fn)
            else:
                self.app.notify("Filename empty.", title="Error", severity="error")
        else:
            self.dismiss(None)


class ManageTagsModal(ModalScreen[Optional[str]]):
    DEFAULT_CSS = """
    ManageTagsModal {
        align: center middle;
        background: $surface-darken-1;
    }
    ManageTagsModal > Vertical {
        width: 70;
        height: auto;
        border: thick $primary-lighten-1;
        padding: 1 2;
        background: $surface;
    }
    ManageTagsModal Label {
        margin-bottom: 0.5;
    }
    ManageTagsModal Input {
        margin-bottom: 1;
    }
    ManageTagsModal #cur_tags_lbl {
        color: $text-muted;
        text-style: italic;
        max-height: 3;
        overflow-y: auto;
        border: round $primary-darken-1;
        padding: 0 1;
    }
    """

    def __init__(self, aid: int, ctl: List[str]):
        super().__init__()
        self.aid, self.cts = aid, ", ".join(sorted(ctl))

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"Tags for Article ID: {self.aid}", classes="dialog-title")
            yield Label("Current:")
            yield Static(self.cts or "None", id="cur_tags_lbl")
            yield Label("New (comma-sep):")
            yield Input(value=self.cts, id="tags_in")
            yield Horizontal(
                Button("Save", variant="primary", id="st_b"),
                Button("Cancel", id="ct_b"),
                classes="modal-buttons"
            )

    def on_button_pressed(self, e: Button.Pressed) -> None:
        if e.button.id == "st_b":
            self.dismiss(self.query_one("#tags_in", Input).value)
        else:
            self.dismiss(None)


class SelectSummaryStyleModal(ModalScreen[Optional[str]]):
    DEFAULT_CSS = """
    SelectSummaryStyleModal {
        align: center middle;
        background: $surface-darken-1;
    }
    SelectSummaryStyleModal > Vertical {
        width: 70;
        height: auto;
        max-height: 80%;
        border: thick $primary-lighten-1;
        padding: 1 2;
        background: $surface;
    }
    SelectSummaryStyleModal VerticalScroll {
        height: auto;
        max-height: 20;
        margin: 1 0;
    }
    SelectSummaryStyleModal RadioSet {
        height: auto;
    }
    SelectSummaryStyleModal RadioButton {
        padding: 1 0;
    }
    """

    def __init__(self):
        super().__init__()
        self.templates = TemplateManager.get_all_templates()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Select Summarization Template", classes="dialog-title")
            with VerticalScroll():
                # Create radio buttons from database templates
                radio_buttons = []
                for i, template in enumerate(self.templates):
                    label = f"{template['name']}"
                    if template['description']:
                        label += f" - {template['description']}"
                    radio_buttons.append(
                        RadioButton(label, id=f"template_{template['id']}", value=(i == 0))
                    )
                yield RadioSet(*radio_buttons)
            with Horizontal(classes="modal-buttons"):
                yield Button("Summarize", variant="primary", id="cs_b")
                yield Button("Manage Templates", id="manage_templates_b")
                yield Button("Cancel", id="ccs_b")

    def on_button_pressed(self, e: Button.Pressed) -> None:
        if e.button.id == "cs_b":
            rs = self.query_one(RadioSet)
            if rs.pressed_button:
                # Extract template ID from button id (format: "template_{id}")
                template_id = int(rs.pressed_button.id.split("_")[1])
                # Find the template name
                template = next((t for t in self.templates if t['id'] == template_id), None)
                if template:
                    self.dismiss(f"template:{template['name']}")
                else:
                    self.dismiss(None)
            else:
                self.dismiss(None)
        elif e.button.id == "manage_templates_b":
            # TODO: Open template management modal
            self.dismiss(None)
        else:
            self.dismiss(None)


class ViewSummaryModal(ModalScreen):
    CSS = """
    ViewSummaryModal {
        align: center middle;
        background: $surface-darken-1;
    }
    ViewSummaryModal > VerticalScroll {
        width: 90%;
        max-width: 100;
        height: 80%;
        max-height: 35;
        border: thick $primary-lighten-1;
        padding: 1 2;
        background: $surface;
    }
    """
    BINDINGS = [Binding("escape", "dismiss", "Close")]

    def __init__(self, title: str, summary_data: dict):
        super().__init__()
        self.article_title = title
        self.summary_data = summary_data

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label(f"Summary: {self.article_title}", id="summary_title", classes="dialog-title")

            if self.summary_data.get('summary'):
                yield Label("Summary:", classes="section-header")
                yield Static(self.summary_data['summary'], classes="summary-content")
            else:
                yield Label("No summary available for this article.", classes="no-content")

            if self.summary_data.get('sentiment'):
                yield Label("Sentiment Analysis:", classes="section-header")
                yield Static(self.summary_data['sentiment'], classes="sentiment-content")

            yield Horizontal(Button("Close", id="close_btn"), classes="modal-buttons")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()

    def action_dismiss(self) -> None:
        self.dismiss()


class ReadArticleModal(ModalScreen):
    DEFAULT_CSS = """
    ReadArticleModal {
        align: center middle;
        background: $surface-darken-1;
    }
    ReadArticleModal > Vertical {
        width: 90%;
        height: 90%;
        border: thick $primary-lighten-1;
        background: $surface;
        padding: 1;
    }
    ReadArticleModal #art_ttl_lbl {
        text-style: bold;
        margin-bottom: 1;
        text-align: center;
        background: $primary-background-darken-1;
        padding: 0 1;
        color: $text;
    }
    ReadArticleModal VerticalScroll {
        border: panel $primary;
        padding: 1;
        background: $surface;
    }
    ReadArticleModal Markdown {
        width: 100%;
    }
    """

    def __init__(self, t: str, c: str):
        super().__init__()
        self.t, self.c = t, c

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self.t, id="art_ttl_lbl")
            yield VerticalScroll(Markdown(self.c or "_No content._"))
            yield Horizontal(Button("Close", id="cr_b"), classes="modal-buttons")

    def on_button_pressed(self, e: Button.Pressed) -> None:
        self.dismiss()


class AIProviderSelectionModal(ModalScreen[Optional[str]]):
    """Modal for selecting AI provider."""
    DEFAULT_CSS = """
    AIProviderSelectionModal {
        align: center middle;
        background: $surface-darken-1;
    }
    AIProviderSelectionModal > Vertical {
        width: 60;
        height: auto;
        border: thick $primary-lighten-1;
        background: $surface;
        padding: 2;
    }
    AIProviderSelectionModal Label {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    AIProviderSelectionModal RadioSet {
        height: auto;
        margin-bottom: 1;
    }
    AIProviderSelectionModal Horizontal {
        width: 100%;
        height: auto;
        align-horizontal: center;
        padding-top: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.current_provider = get_ai_provider()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Select AI Provider")
            with RadioSet(id="provider_radioset"):
                yield RadioButton("Google Gemini", value=GEMINI_API_KEY != "", id="gemini_radio")
                yield RadioButton("OpenAI GPT", value=OPENAI_API_KEY != "", id="openai_radio")
                yield RadioButton("Anthropic Claude", value=CLAUDE_API_KEY != "", id="claude_radio")
            with Horizontal():
                yield Button("Select", variant="primary", id="select_btn")
                yield Button("Cancel", id="cancel_btn")

    def on_mount(self) -> None:
        # Pre-select current provider
        if self.current_provider:
            name = self.current_provider.name
            if "Gemini" in name:
                self.query_one("#gemini_radio", RadioButton).value = True
            elif "OpenAI" in name:
                self.query_one("#openai_radio", RadioButton).value = True
            elif "Claude" in name:
                self.query_one("#claude_radio", RadioButton).value = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "select_btn":
            radioset = self.query_one("#provider_radioset", RadioSet)
            pressed_idx = radioset.pressed_index
            if pressed_idx == 0 and GEMINI_API_KEY:
                self.dismiss("gemini")
            elif pressed_idx == 1 and OPENAI_API_KEY:
                self.dismiss("openai")
            elif pressed_idx == 2 and CLAUDE_API_KEY:
                self.dismiss("claude")
            else:
                self.dismiss(None)
        else:
            self.dismiss(None)


class ScrapeURLModal(ModalScreen[tuple[str, str, int] | None]):
    DEFAULT_CSS = """
    ScrapeURLModal {
        align: center middle;
        background: $surface-darken-1;
    }
    ScrapeURLModal > Vertical {
        width: 70;
        height: auto;
        border: thick $primary-lighten-1;
        padding: 1 2;
        background: $surface;
    }
    ScrapeURLModal Input {
        margin-bottom: 1;
    }
    ScrapeURLModal Button {
        margin-top: 1;
    }
    ScrapeURLModal Label.dialog-title {
        text-style: bold;
        width: 100%;
        text-align: center;
        margin-bottom: 1;
    }
    ScrapeURLModal Static.profile-context {
        text-align: center;
        color: $accent;
        margin-bottom: 1;
    }
    """

    def __init__(self, lu: str = "", ls: str = "h2 a", ll: int = 0):
        super().__init__()
        self.lu, self.ls, self.ll = lu, ls, ll

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Scrape New URL", classes="dialog-title")
            yield Static(f"Profile: {self.app.current_scraper_profile}", classes="profile-context")
            yield Input(value=self.lu, placeholder="URL", id="s_url_in")
            yield Input(value=self.ls, placeholder="CSS Selector", id="s_sel_in")
            yield Input(value=str(self.ll), placeholder="Limit (0=all)", id="s_lim_in", type="integer")
            yield Horizontal(
                Button("Scrape", variant="primary", id="sc_b"),
                Button("Cancel", id="scc_b"),
                classes="modal-buttons"
            )

    def on_button_pressed(self, e: Button.Pressed) -> None:
        if e.button.id == "sc_b":
            u = self.query_one("#s_url_in", Input).value
            s = self.query_one("#s_sel_in", Input).value
            l_s = self.query_one("#s_lim_in", Input).value
            try:
                limit = int(l_s) if l_s.strip() else 0
            except ValueError:
                self.app.notify("Invalid limit.", title="Error", severity="error")
                return
            if not u or not s:
                self.app.notify("URL & Selector required.", title="Error", severity="error")
                return
            if hasattr(self.app, 'last_scrape_url'):
                self.app.last_scrape_url = u
            if hasattr(self.app, 'last_scrape_selector'):
                self.app.last_scrape_selector = s
            if hasattr(self.app, 'last_scrape_limit'):
                self.app.last_scrape_limit = limit
            self.dismiss((u, s, limit))
        else:
            self.dismiss(None)


class ArticleDetailModal(ModalScreen):
    DEFAULT_CSS = """
    ArticleDetailModal {
        align: center middle;
        background: $surface-darken-1;
    }
    ArticleDetailModal > ScrollableContainer {
        width: 80%;
        max-width: 100;
        height: 80%;
        max-height: 38;
        border: thick $primary-lighten-1;
        padding: 0;
        background: $surface;
    }
    ArticleDetailModal Markdown {
        padding: 1 2;
    }
    ArticleDetailModal Button {
        width: 100%;
        margin-top: 1;
    }
    """

    def __init__(self, ad: sqlite3.Row, tags: List[str]):
        super().__init__()
        self.ad, self.tags = ad, tags

    def compose(self) -> ComposeResult:
        ts = ", ".join(sorted(self.tags)) if self.tags else "_No tags_"
        senti_str = self.ad['sentiment'] or "_N/A_"
        timestamp_val = self.ad['timestamp']
        if isinstance(timestamp_val, datetime):
            timestamp_str = timestamp_val.strftime('%Y-%m-%d %H:%M:%S')
        else:
            timestamp_str = str(timestamp_val)
        c = (f"# {self.ad['title']}\n"
             f"**ID:** {self.ad['id']}\n"
             f"**Src URL:** {self.ad['url']}\n"
             f"**Link:** [{self.ad['link']}]({self.ad['link']})\n"
             f"**Scraped:** {timestamp_str}\n"
             f"**Tags:** {ts}\n"
             f"**Sentiment:** {senti_str}\n"
             f"---\n## Summary\n")
        c += f"\n{self.ad['summary']}" if self.ad['summary'] else "\n_Not summarized._"
        with VerticalScroll():
            yield Markdown(c)
            yield Horizontal(Button("Close", variant="primary", id="d_cls_b"), classes="modal-buttons")

    def on_button_pressed(self, e: Button.Pressed) -> None:
        self.dismiss()


class OriginalURLModal(ModalScreen[Optional[str]]):
    DEFAULT_CSS = """
    OriginalURLModal {
        align: center middle;
        background: $surface-darken-1;
    }
    OriginalURLModal > Vertical {
        width: 70;
        height: auto;
        border: thick $primary-lighten-1;
        padding: 1 2;
        background: $surface;
    }
    OriginalURLModal Input {
        margin-bottom: 1;
    }
    OriginalURLModal Button {
        margin-top: 1;
    }
    """

    def __init__(self, prompt_text: str = "Enter Original URL for Archival Fetch:"):
        super().__init__()
        self.prompt_text = prompt_text

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self.prompt_text, classes="dialog-title")
            yield Input(placeholder="e.g., https://example.com/article", id="original_url_input")
            with Horizontal(classes="modal-buttons"):
                yield Button("Fetch Archive", variant="primary", id="fetch_archive_url")
                yield Button("Cancel", id="cancel_archive_url")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "fetch_archive_url":
            url = self.query_one("#original_url_input", Input).value.strip()
            if not url:
                self.app.notify("Original URL cannot be empty.", title="Input Error", severity="error")
                return
            self.dismiss(url)
        else:
            self.dismiss(None)


class SavedScraperItem(ListItem):
    def __init__(self, scraper_data: sqlite3.Row):
        super().__init__()
        self.scraper_data = scraper_data
        self.prefix = "[P] " if scraper_data['is_preinstalled'] else ""

    def compose(self) -> ComposeResult:
        display_name = f"{self.prefix}{self.scraper_data['name']}"
        sub_text = self.scraper_data['description'] or self.scraper_data['url']
        if len(sub_text) > 60:
            sub_text = sub_text[:57] + "..."
        with Vertical():
            yield Label(display_name, classes="scraper-item-name")
            yield Label(f"  ({sub_text})", classes="scraper-item-subtext")


class ManageScrapersModal(ModalScreen[Optional[Tuple[str, Any]]]):
    DEFAULT_CSS = """
    ManageScrapersModal {
        align: center middle;
        background: $surface-darken-1;
    }
    ManageScrapersModal > Vertical {
        width: 85%;
        max-width: 110;
        height: 85%;
        max-height: 35;
        border: thick $primary-lighten-1;
        padding: 1;
        background: $surface;
    }
    ManageScrapersModal ListView {
        height: 1fr;
        margin-bottom: 1;
        border: panel $primary;
    }
    ManageScrapersModal .buttons-top, ManageScrapersModal .buttons-bottom {
        layout: horizontal;
        height: auto;
        align-horizontal: center;
        margin-top: 1;
    }
    ManageScrapersModal Button {
        margin: 0 1;
    }
    .scraper-item-name {
        text-style: bold;
    }
    .scraper-item-subtext {
        color: $text-muted;
        text-style: italic;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Manage Scraper Profiles", classes="dialog-title")
            yield ListView(id="scrapers_list_view")
            with Horizontal(classes="buttons-top"):
                yield Button("Add New", id="add_scraper", variant="success")
                yield Button("Edit Selected", id="edit_scraper", variant="primary")
                yield Button("Delete Selected", id="delete_scraper", variant="error")
            with Horizontal(classes="buttons-bottom"):
                yield Button("Execute Selected", id="execute_scraper", variant="success")
                yield Button("Close", id="close_manage_scrapers")

    async def on_mount(self) -> None:
        await self.load_scrapers()

    async def load_scrapers(self) -> None:
        lv = self.query_one(ListView)
        lv.clear()
        try:
            with get_db_connection() as conn:
                scrapers = conn.execute(
                    "SELECT id,name,url,selector,default_limit,default_tags_csv,description,is_preinstalled "
                    "FROM saved_scrapers ORDER BY is_preinstalled DESC, name COLLATE NOCASE"
                ).fetchall()
            for sd in scrapers:
                lv.append(SavedScraperItem(sd))
        except Exception as e:
            logger.error(f"Failed to load saved scrapers: {e}", exc_info=True)
            self.app.notify("Error loading scrapers.", severity="error")

    async def on_button_pressed(self, e: Button.Pressed) -> None:
        lv = self.query_one(ListView)
        si = lv.highlighted_child
        if e.button.id == "add_scraper":
            self.dismiss(("add", None))
        elif e.button.id == "edit_scraper":
            if si and isinstance(si, SavedScraperItem):
                self.dismiss(("edit", si.scraper_data))
            else:
                self.app.notify("No scraper selected to edit.", severity="warning")
        elif e.button.id == "delete_scraper":
            if si and isinstance(si, SavedScraperItem):
                if si.scraper_data['is_preinstalled']:
                    self.app.notify("Pre-installed profiles cannot be deleted directly. You can edit them.", severity="warning")
                    return
                self.dismiss(("delete", si.scraper_data['id']))
            else:
                self.app.notify("No scraper selected to delete.", severity="warning")
        elif e.button.id == "execute_scraper":
            if si and isinstance(si, SavedScraperItem):
                self.dismiss(("execute", si.scraper_data))
            else:
                self.app.notify("No scraper selected to execute.", severity="warning")
        elif e.button.id == "close_manage_scrapers":
            self.dismiss(None)


class AddEditScraperModal(ModalScreen[Optional[Dict[str, Any]]]):
    DEFAULT_CSS = """
    AddEditScraperModal {
        align: center middle;
        background: $surface-darken-1;
    }
    AddEditScraperModal > VerticalScroll {
        width: 70%;
        max-width: 90;
        max-height: 90%;
        border: thick $primary-lighten-1;
        padding: 1 2;
        background: $surface;
    }
    AddEditScraperModal Input, AddEditScraperModal Label, AddEditScraperModal Static {
        margin-bottom: 1;
    }
    AddEditScraperModal Label {
        margin-top: 1;
    }
    AddEditScraperModal #scraper_description_input {
        height: 3;
        border: round $primary-border;
        padding: 0 1;
    }
    AddEditScraperModal Static.warning-text {
        color: $warning;
        padding: 0 1;
        text-align: center;
    }
    """

    def __init__(self, sd: Optional[sqlite3.Row] = None):
        super().__init__()
        self.sd = sd
        self.is_edit = sd is not None

    def compose(self) -> ComposeResult:
        title = "Edit Scraper Profile" if self.is_edit else "Add New Scraper Profile"
        with VerticalScroll():
            yield Label(title, classes="dialog-title")
            if self.is_edit and self.sd and self.sd['is_preinstalled']:
                yield Static("[PRE-INSTALLED PROFILE - Edits create a custom copy if name changes]", classes="warning-text")
            yield Label("Name:")
            yield Input(value=self.sd['name'] if self.is_edit else "", id="scraper_name")
            yield Label("URL (use [USER_PROVIDES_URL] to prompt):")
            yield Input(value=self.sd['url'] if self.is_edit else "", id="scraper_url")
            yield Label("CSS Selector:")
            yield Input(value=self.sd['selector'] if self.is_edit else "h2 a", id="scraper_selector")
            yield Label("Default Limit (0 for all):")
            yield Input(
                value=str(self.sd['default_limit']) if self.is_edit else "0",
                id="scraper_limit",
                type="integer"
            )
            yield Label("Default Tags (comma-separated, optional):")
            yield Input(
                value=self.sd['default_tags_csv'] if self.is_edit and self.sd['default_tags_csv'] else "",
                id="scraper_tags"
            )
            yield Label("Description:")
            yield Input(
                value=self.sd['description'] if self.is_edit and self.sd['description'] else "",
                id="scraper_description_input"
            )
            with Horizontal(classes="modal-buttons"):
                yield Button("Save", variant="primary", id="save_s_cfg")
                yield Button("Cancel", id="cancel_s_cfg")

    def on_button_pressed(self, e: Button.Pressed) -> None:
        if e.button.id == "save_s_cfg":
            data = {
                "name": self.query_one("#scraper_name", Input).value.strip(),
                "url": self.query_one("#scraper_url", Input).value.strip(),
                "selector": self.query_one("#scraper_selector", Input).value.strip(),
                "default_limit": 0,
                "default_tags_csv": self.query_one("#scraper_tags", Input).value.strip(),
                "description": self.query_one("#scraper_description_input", Input).value.strip(),
                "is_preinstalled": self.sd['is_preinstalled'] if self.is_edit and self.sd else 0
            }
            try:
                data["default_limit"] = int(self.query_one("#scraper_limit", Input).value.strip() or "0")
            except ValueError:
                self.app.notify("Invalid limit.", severity="error")
                return
            if not data["name"] or not data["url"] or not data["selector"]:
                self.app.notify("Name,URL,Selector required.", severity="error")
                return
            if self.is_edit and self.sd:
                data["id"] = self.sd["id"]
                if self.sd['is_preinstalled'] and data['name'] != self.sd['name']:
                    data['is_preinstalled'] = 0
                    del data['id']
            self.dismiss(data)
        else:
            self.dismiss(None)


class FilterScreen(ModalScreen[bool]):
    CSS = """
    FilterScreen {
        align: center middle;
        background: $surface-darken-1;
    }
    FilterScreen > Vertical {
        width: 85%;
        max-width: 90;
        height: auto;
        max-height: 85%;
        border: thick $primary-lighten-1;
        padding: 1 2;
        background: $surface;
    }
    FilterScreen VerticalScroll {
        height: auto;
        max-height: 30;
    }
    FilterScreen Horizontal {
        width: 100%;
        height: auto;
    }
    """
    BINDINGS = [Binding("escape", "dismiss", "Close"), Binding("enter", "apply_filters", "Apply")]

    def __init__(self, app_ref):
        super().__init__()
        self.app_ref = app_ref

    def compose(self) -> ComposeResult:
        from textual.widgets import Checkbox
        with Vertical():
            yield Label("Advanced Article Filters (v1.3.0)", classes="dialog-title")
            with VerticalScroll():
                yield Label("Title Filter:")
                yield Input(placeholder="Title (supports regex)...", id="title_filter_input", value=self.app_ref.title_filter)

                yield Label("URL Filter:")
                yield Input(placeholder="Source URL (supports regex)...", id="url_filter_input", value=self.app_ref.url_filter)

                yield Checkbox("Use Regex for Title/URL filters", id="use_regex_checkbox", value=self.app_ref.use_regex)

                yield Label("Date Range:")
                with Horizontal():
                    yield Input(placeholder="From (YYYY-MM-DD)...", id="date_from_input", value=self.app_ref.date_filter_from)
                    yield Input(placeholder="To (YYYY-MM-DD)...", id="date_to_input", value=self.app_ref.date_filter_to)

                yield Label("Tags Filter (comma-separated):")
                yield Input(placeholder="Tags...", id="tags_filter_input", value=self.app_ref.tags_filter)

                with Horizontal():
                    yield Label("Tags Logic:")
                    with RadioSet(id="tags_logic_radioset"):
                        yield RadioButton("AND (all tags)", id="tags_and", value=(self.app_ref.tags_logic == "AND"))
                        yield RadioButton("OR (any tag)", id="tags_or", value=(self.app_ref.tags_logic == "OR"))

                yield Label("Sentiment Filter:")
                yield Input(placeholder="Sentiment (Pos/Neg/Neu)...", id="sentiment_filter_input", value=self.app_ref.sentiment_filter)

            with Horizontal(classes="modal-buttons"):
                yield Button("Save Preset", id="save_preset_btn")
                yield Button("Load Preset", id="load_preset_btn")
                yield Button("Clear All", id="clear_btn")
                yield Button("Apply", id="apply_btn", variant="primary")
                yield Button("Cancel", id="cancel_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "apply_btn":
            self.action_apply_filters()
        elif event.button.id == "clear_btn":
            for input_widget in self.query(Input):
                input_widget.value = ""
            self.query_one("#use_regex_checkbox", Checkbox).value = False
            self.query_one("#tags_and", RadioButton).value = True
        elif event.button.id == "save_preset_btn":
            # TODO: Implement save preset modal
            self.app_ref.notify("Save preset: Coming soon", severity="info")
        elif event.button.id == "load_preset_btn":
            # TODO: Implement load preset modal
            self.app_ref.notify("Load preset: Coming soon", severity="info")
        elif event.button.id == "cancel_btn":
            self.dismiss(False)

    def action_apply_filters(self) -> None:
        from textual.widgets import Checkbox
        self.app_ref.title_filter = self.query_one("#title_filter_input", Input).value
        self.app_ref.url_filter = self.query_one("#url_filter_input", Input).value
        self.app_ref.use_regex = self.query_one("#use_regex_checkbox", Checkbox).value
        self.app_ref.date_filter_from = self.query_one("#date_from_input", Input).value
        self.app_ref.date_filter_to = self.query_one("#date_to_input", Input).value
        self.app_ref.tags_filter = self.query_one("#tags_filter_input", Input).value

        # Get tags logic from radio buttons
        radioset = self.query_one("#tags_logic_radioset", RadioSet)
        if radioset.pressed_button:
            self.app_ref.tags_logic = "AND" if radioset.pressed_button.id == "tags_and" else "OR"

        self.app_ref.sentiment_filter = self.query_one("#sentiment_filter_input", Input).value

        # Keep legacy date_filter for backwards compatibility
        if self.app_ref.date_filter_from:
            self.app_ref.date_filter = self.app_ref.date_filter_from

        self.dismiss(True)

    def action_dismiss(self) -> None:
        self.dismiss(False)


class FilterPresetModal(ModalScreen[Optional[str]]):
    """Modal for managing filter presets."""

    DEFAULT_CSS = """
    FilterPresetModal > Vertical {
        width: 70;
        height: auto;
        max-height: 80%;
        padding: 2;
        border: thick $primary-lighten-1;
        background: $panel;
    }
    FilterPresetModal Horizontal {
        width: 100%;
        height: auto;
        align-horizontal: center;
        padding-top: 1;
    }
    FilterPresetModal ListView {
        height: 15;
        border: solid $primary;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Filter Presets (Ctrl+Shift+F)", classes="dialog-title")
            yield Label("Select a preset to load:")

            # List of presets
            presets = FilterPresetManager.list_presets()
            with ListView(id="preset_list"):
                if not presets:
                    yield ListItem(Label("(No saved presets)"))
                else:
                    for preset_name in presets:
                        yield ListItem(Label(preset_name))

            with Horizontal(classes="modal-buttons"):
                yield Button("Load", variant="primary", id="load_btn")
                yield Button("Delete", variant="error", id="delete_btn")
                yield Button("Cancel", id="cancel_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "load_btn":
            list_view = self.query_one("#preset_list", ListView)
            if list_view.index is not None and list_view.index >= 0:
                try:
                    item = list(list_view.children)[list_view.index]
                    label = item.query_one(Label)
                    preset_name = label.renderable
                    if preset_name != "(No saved presets)":
                        self.dismiss(preset_name)
                        return
                except:
                    pass
            self.app.notify("Please select a preset", severity="warning")
        elif event.button.id == "delete_btn":
            list_view = self.query_one("#preset_list", ListView)
            if list_view.index is not None and list_view.index >= 0:
                try:
                    item = list(list_view.children)[list_view.index]
                    label = item.query_one(Label)
                    preset_name = label.renderable
                    if preset_name != "(No saved presets)":
                        if FilterPresetManager.delete_preset(preset_name):
                            self.app.notify(f"Deleted preset: {preset_name}", severity="information")
                            # Refresh list
                            list_view.clear()
                            presets = FilterPresetManager.list_presets()
                            if not presets:
                                list_view.append(ListItem(Label("(No saved presets)")))
                            else:
                                for pn in presets:
                                    list_view.append(ListItem(Label(pn)))
                        else:
                            self.app.notify("Failed to delete preset", severity="error")
                        return
                except:
                    pass
            self.app.notify("Please select a preset", severity="warning")
        else:  # cancel_btn
            self.dismiss(None)


class SavePresetModal(ModalScreen[Optional[str]]):
    """Modal for saving current filters as a preset."""

    DEFAULT_CSS = """
    SavePresetModal > Vertical {
        width: 50;
        height: auto;
        padding: 2;
        border: thick $primary-lighten-1;
        background: $panel;
    }
    SavePresetModal Horizontal {
        width: 100%;
        height: auto;
        align-horizontal: center;
        padding-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Save Filter Preset", classes="dialog-title")
            yield Label("Enter preset name:")
            yield Input(placeholder="Preset name...", id="preset_name_input")
            with Horizontal(classes="modal-buttons"):
                yield Button("Save", variant="primary", id="save_btn")
                yield Button("Cancel", id="cancel_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_btn":
            name_input = self.query_one("#preset_name_input", Input)
            name = name_input.value.strip()
            if name:
                self.dismiss(name)
            else:
                self.app.notify("Please enter a preset name", severity="warning")
        else:
            self.dismiss(None)


class SettingsModal(ModalScreen[bool]):
    """Modal for application settings."""

    DEFAULT_CSS = """
    SettingsModal > VerticalScroll {
        width: 70;
        height: auto;
        max-height: 80%;
        padding: 2;
        border: thick $primary-lighten-1;
        background: $panel;
    }
    SettingsModal Horizontal {
        width: 100%;
        height: auto;
        align-horizontal: center;
        padding-top: 1;
    }
    SettingsModal Label {
        margin-bottom: 1;
    }
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.modified = False

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("Application Settings (Ctrl+G)", classes="dialog-title")

            yield Label("\n=== AI Configuration ===")
            yield Label("Default AI Provider:")
            with RadioSet(id="ai_provider_radio"):
                providers = ['gemini', 'openai', 'claude']
                current = self.config.get('ai', {}).get('default_provider', 'gemini')
                for provider in providers:
                    yield RadioButton(
                        provider.capitalize(),
                        value=(provider == current),
                        id=f"provider_{provider}"
                    )

            yield Label("\n=== Export Configuration ===")
            yield Label("Default Export Format:")
            with RadioSet(id="export_format_radio"):
                formats = ['csv', 'json']
                current_format = self.config.get('export', {}).get('default_format', 'csv')
                for fmt in formats:
                    yield RadioButton(
                        fmt.upper(),
                        value=(fmt == current_format),
                        id=f"format_{fmt}"
                    )

            yield Label("Export Output Directory:")
            yield Input(
                value=self.config.get('export', {}).get('output_directory', '.'),
                placeholder="Output directory...",
                id="output_dir_input"
            )

            yield Label("\n=== Database Configuration ===")
            yield Checkbox(
                "Auto-vacuum database on startup",
                value=self.config.get('database', {}).get('auto_vacuum', False),
                id="auto_vacuum_check"
            )
            yield Checkbox(
                "Backup database on exit",
                value=self.config.get('database', {}).get('backup_on_exit', False),
                id="backup_check"
            )

            with Horizontal(classes="modal-buttons"):
                yield Button("Save", variant="primary", id="save_settings_btn")
                yield Button("Cancel", id="cancel_settings_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_settings_btn":
            # Update config from UI
            # AI provider
            for provider in ['gemini', 'openai', 'claude']:
                radio = self.query_one(f"#provider_{provider}", RadioButton)
                if radio.value:
                    self.config['ai']['default_provider'] = provider
                    break

            # Export format
            for fmt in ['csv', 'json']:
                radio = self.query_one(f"#format_{fmt}", RadioButton)
                if radio.value:
                    self.config['export']['default_format'] = fmt
                    break

            # Output directory
            output_dir = self.query_one("#output_dir_input", Input).value
            self.config['export']['output_directory'] = output_dir

            # Database options
            self.config['database']['auto_vacuum'] = self.query_one("#auto_vacuum_check", Checkbox).value
            self.config['database']['backup_on_exit'] = self.query_one("#backup_check", Checkbox).value

            # Save config
            if ConfigManager.save_config(self.config):
                self.app.notify("Settings saved successfully", severity="information")
                self.dismiss(True)
            else:
                self.app.notify("Failed to save settings", severity="error")
        else:
            self.dismiss(False)


class ScheduleManagementModal(ModalScreen[Optional[int]]):
    """Modal for managing scheduled scrapes (v1.5.0)."""

    DEFAULT_CSS = """
    ScheduleManagementModal {
        align: center middle;
        background: $surface-darken-1;
    }
    ScheduleManagementModal > Vertical {
        width: 90%;
        max-width: 100;
        height: 85%;
        max-height: 35;
        border: thick $primary-lighten-1;
        padding: 1 2;
        background: $surface;
    }
    ScheduleManagementModal DataTable {
        height: 20;
    }
    """

    BINDINGS = [Binding("escape", "dismiss_screen", "Close")]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("📅 Scheduled Scrapes", id="schedule-title")
            yield DataTable(id="schedule_table", cursor_type="row", zebra_stripes=True)
            with Horizontal(classes="modal-buttons"):
                yield Button("Add Schedule", id="add_schedule", variant="primary")
                yield Button("Enable/Disable", id="toggle_schedule")
                yield Button("Delete", id="delete_schedule", variant="error")
                yield Button("Close", id="close_btn")

    async def on_mount(self) -> None:
        """Initialize the schedule table."""
        table = self.query_one("#schedule_table", DataTable)
        table.add_columns("ID", "Name", "Profile", "Type", "Schedule", "Enabled", "Next Run", "Last Run", "Run Count", "Status")
        await self._refresh_schedules()

    async def _refresh_schedules(self) -> None:
        """Refresh the schedules table."""
        table = self.query_one("#schedule_table", DataTable)
        table.clear()

        schedules = ScheduleManager.list_schedules()
        for schedule in schedules:
            enabled_str = "✓" if schedule['enabled'] else "✗"
            next_run = schedule['next_run'] or "Not set"
            last_run = schedule['last_run'] or "Never"
            status = schedule['last_status'] or "-"

            table.add_row(
                str(schedule['id']),
                schedule['name'],
                schedule['profile_name'] or f"ID:{schedule['scraper_profile_id']}",
                schedule['schedule_type'],
                schedule['schedule_value'],
                enabled_str,
                next_run,
                last_run,
                str(schedule['run_count']),
                status,
                key=str(schedule['id'])
            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close_btn":
            self.dismiss(None)
        elif event.button.id == "add_schedule":
            def handle_new_schedule(result):
                if result:
                    self.run_worker(self._refresh_schedules())
                    self.app.notify("Schedule created successfully", severity="information")
            self.app.push_screen(AddScheduleModal(), handle_new_schedule)
        elif event.button.id == "toggle_schedule":
            table = self.query_one("#schedule_table", DataTable)
            if table.row_count > 0:
                try:
                    row_key = table.get_row_key_from_coordinate(table.cursor_coordinate)
                    schedule_id = int(row_key.value)
                    schedule = ScheduleManager.get_schedule(schedule_id)
                    if schedule:
                        new_enabled = not schedule['enabled']
                        if ScheduleManager.update_schedule(schedule_id, enabled=new_enabled):
                            await self._refresh_schedules()
                            status = "enabled" if new_enabled else "disabled"
                            self.app.notify(f"Schedule {status}", severity="information")
                except Exception as e:
                    self.app.notify(f"Error toggling schedule: {e}", severity="error")
        elif event.button.id == "delete_schedule":
            table = self.query_one("#schedule_table", DataTable)
            if table.row_count > 0:
                try:
                    row_key = table.get_row_key_from_coordinate(table.cursor_coordinate)
                    schedule_id = int(row_key.value)

                    def handle_delete_confirm(confirmed):
                        if confirmed:
                            if ScheduleManager.delete_schedule(schedule_id):
                                self.run_worker(self._refresh_schedules())
                                self.app.notify("Schedule deleted", severity="information")
                            else:
                                self.app.notify("Failed to delete schedule", severity="error")

                    self.app.push_screen(
                        ConfirmModal("Delete this schedule?", "Delete", "Cancel"),
                        handle_delete_confirm
                    )
                except Exception as e:
                    self.app.notify(f"Error deleting schedule: {e}", severity="error")

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)


class AddScheduleModal(ModalScreen[bool]):
    """Modal for creating a new scheduled scrape (v1.5.0)."""

    DEFAULT_CSS = """
    AddScheduleModal {
        align: center middle;
        background: $surface-darken-1;
    }
    AddScheduleModal > Vertical {
        width: 80%;
        max-width: 80;
        height: auto;
        border: thick $primary-lighten-1;
        padding: 2;
        background: $surface;
    }
    AddScheduleModal Input {
        margin: 1 0;
    }
    AddScheduleModal RadioSet {
        height: auto;
        margin: 1 0;
    }
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("➕ Add Scheduled Scrape")
            yield Label("Schedule Name:")
            yield Input(placeholder="e.g., Daily News Scrape", id="schedule_name")

            yield Label("Scraper Profile:")
            yield Input(placeholder="Profile ID (from Profiles list)", id="profile_id")

            yield Label("Schedule Type:")
            with RadioSet(id="schedule_type"):
                yield RadioButton("Hourly (every hour)", id="type_hourly")
                yield RadioButton("Daily (HH:MM format, e.g., 09:00)", id="type_daily", value=True)
                yield RadioButton("Weekly (day:HH:MM, e.g., 0:09:00 for Monday 9am)", id="type_weekly")
                yield RadioButton("Interval (minutes, e.g., 30)", id="type_interval")

            yield Label("Schedule Value:")
            yield Input(placeholder="e.g., 09:00 for daily at 9am", id="schedule_value")

            with Horizontal(classes="modal-buttons"):
                yield Button("Create", id="create_btn", variant="primary")
                yield Button("Cancel", id="cancel_btn")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel_btn":
            self.dismiss(False)
        elif event.button.id == "create_btn":
            name_input = self.query_one("#schedule_name", Input)
            profile_input = self.query_one("#profile_id", Input)
            value_input = self.query_one("#schedule_value", Input)
            type_radio = self.query_one("#schedule_type", RadioSet)

            name = name_input.value.strip()
            profile_id_str = profile_input.value.strip()
            value = value_input.value.strip()

            # Determine schedule type
            if self.query_one("#type_hourly", RadioButton).value:
                schedule_type = "hourly"
            elif self.query_one("#type_daily", RadioButton).value:
                schedule_type = "daily"
            elif self.query_one("#type_weekly", RadioButton).value:
                schedule_type = "weekly"
            elif self.query_one("#type_interval", RadioButton).value:
                schedule_type = "interval"
            else:
                schedule_type = "daily"

            # Validate inputs
            if not name:
                self.app.notify("Schedule name is required", severity="error")
                return
            if not profile_id_str:
                self.app.notify("Profile ID is required", severity="error")
                return
            if not value:
                self.app.notify("Schedule value is required", severity="error")
                return

            try:
                profile_id = int(profile_id_str)
            except ValueError:
                self.app.notify("Profile ID must be a number", severity="error")
                return

            # Create the schedule
            if ScheduleManager.create_schedule(name, profile_id, schedule_type, value, enabled=True):
                self.dismiss(True)
            else:
                self.app.notify("Failed to create schedule (name may already exist)", severity="error")

    def action_cancel(self) -> None:
        self.dismiss(False)


class AnalyticsModal(ModalScreen):
    """Modal for viewing analytics and statistics (v1.6.0)."""

    DEFAULT_CSS = """
    AnalyticsModal {
        align: center middle;
        background: $surface-darken-1;
    }
    AnalyticsModal > VerticalScroll {
        width: 90%;
        max-width: 120;
        height: 90%;
        max-height: 40;
        border: thick $primary-lighten-1;
        padding: 1 2;
        background: $surface;
    }
    AnalyticsModal Button {
        margin: 1 2;
    }
    """

    BINDINGS = [Binding("escape", "dismiss_screen", "Close")]

    def compose(self) -> ComposeResult:
        stats = AnalyticsManager.get_statistics()

        # Build markdown content with statistics
        content = "# 📊 Data Analytics & Statistics\n\n"
        content += "## Overview\n\n"
        content += f"- **Total Articles**: {stats.get('total_articles', 0)}\n"
        content += f"- **With Summaries**: {stats.get('articles_with_summaries', 0)} ({stats.get('summary_percentage', 0):.1f}%)\n"
        content += f"- **With Sentiment**: {stats.get('articles_with_sentiment', 0)} ({stats.get('sentiment_percentage', 0):.1f}%)\n\n"

        # Sentiment distribution
        content += "## Sentiment Distribution\n\n"
        sentiment_dist = stats.get('sentiment_distribution', {})
        if sentiment_dist:
            for sentiment, count in sentiment_dist.items():
                content += f"- **{sentiment}**: {count}\n"
        else:
            content += "*No sentiment data available*\n"
        content += "\n"

        # Top sources
        content += "## Top 10 Sources\n\n"
        top_sources = stats.get('top_sources', [])
        if top_sources:
            for i, (source, count) in enumerate(top_sources, 1):
                source_display = source[:60] + "..." if len(source) > 60 else source
                content += f"{i}. **{source_display}** ({count} articles)\n"
        else:
            content += "*No source data available*\n"
        content += "\n"

        # Top tags
        content += "## Top 20 Tags\n\n"
        top_tags = stats.get('top_tags', [])
        if top_tags:
            # Display tags in a more compact format
            tag_list = ", ".join([f"**{tag}** ({count})" for tag, count in top_tags[:10]])
            content += tag_list + "\n\n"
            if len(top_tags) > 10:
                tag_list2 = ", ".join([f"**{tag}** ({count})" for tag, count in top_tags[10:20]])
                content += tag_list2 + "\n"
        else:
            content += "*No tag data available*\n"
        content += "\n"

        # Timeline info
        content += "## Recent Activity\n\n"
        articles_per_day = stats.get('articles_per_day', [])
        if articles_per_day:
            content += f"Data collected over **{len(articles_per_day)} days** (last 30 days)\n"
            total_recent = sum(count for _, count in articles_per_day)
            avg_per_day = total_recent / len(articles_per_day) if articles_per_day else 0
            content += f"Average: **{avg_per_day:.1f} articles/day**\n"
        else:
            content += "*No recent activity data*\n"

        with VerticalScroll():
            yield Markdown(content)
            with Horizontal(classes="modal-buttons"):
                yield Button("Export Charts", id="export_charts", variant="primary")
                yield Button("Export Report", id="export_report")
                yield Button("Close", id="close_btn")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close_btn":
            self.dismiss()
        elif event.button.id == "export_charts":
            # Export all charts
            def export_worker():
                try:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    AnalyticsManager.generate_sentiment_chart(f"sentiment_chart_{timestamp}.png")
                    AnalyticsManager.generate_timeline_chart(f"timeline_chart_{timestamp}.png")
                    AnalyticsManager.generate_top_sources_chart(f"sources_chart_{timestamp}.png")
                    return True
                except Exception as e:
                    logger.error(f"Error exporting charts: {e}")
                    return False

            success = await self.app.run_in_thread(export_worker)
            if success:
                self.app.notify("Charts exported successfully", severity="information")
            else:
                self.app.notify("Failed to export charts", severity="error")
        elif event.button.id == "export_report":
            # Export text report
            def export_report_worker():
                try:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    return AnalyticsManager.export_statistics_report(f"analytics_report_{timestamp}.txt")
                except Exception as e:
                    logger.error(f"Error exporting report: {e}")
                    return False

            success = await self.app.run_in_thread(export_report_worker)
            if success:
                self.app.notify("Report exported successfully", severity="information")
            else:
                self.app.notify("Failed to export report", severity="error")

    def action_dismiss_screen(self) -> None:
        self.dismiss()


class HelpModal(ModalScreen):
    DEFAULT_CSS = """
    HelpModal {
        align: center middle;
        background: $surface-darken-1;
    }
    HelpModal > VerticalScroll {
        width: 90%;
        max-width: 120;
        height: 90%;
        max-height: 40;
        border: thick $primary-lighten-1;
        padding: 1 2;
        background: $surface;
    }
    /* Styling for h2/h3 inside Markdown is not directly supported this way.
       Style the Markdown widget itself or use Rich console markup in the Markdown text.
    */
    """
    BINDINGS = [Binding("escape", "dismiss_screen", "Close Help")]

    def compose(self) -> ComposeResult:
        ps_desc = "\n\n### Pre-installed Scraper Profiles:\n\n"
        for ps_data in PREINSTALLED_SCRAPERS:
            ps_desc += (
                f"- **{ps_data['name']}**: {ps_data['description']}\n"
                f"  - *Example/Target URL Hint*: `{ps_data['url']}`\n"
                f"  - *Suggested Selector*: `{ps_data['selector']}`\n"
                f"  - *Default Tags*: "
                f"`{ps_data['default_tags_csv'] or 'None'}`\n\n"
            )
        ht = f"""\
## Keybindings & Help (v1.6.0)

### Navigation & Display
| Key           | Action              | Description                                        |
|---------------|---------------------|----------------------------------------------------|
| `UP`/`DOWN`   | Navigate Table      | Move selection in articles list.                   |
| `ENTER`       | View Details        | Show full details of selected article.             |
| `r`           | Refresh List        | Reload articles from database.                     |
| `ctrl+l`      | Toggle Theme        | Switch between Light/Dark mode.                    |

### Scraping & Data Entry
| Key           | Action              | Description                                        |
|---------------|---------------------|----------------------------------------------------|
| `ctrl+n`      | New Scrape          | Open dialog to scrape new URL (generic).           |
| `ctrl+m`      | Scraper Profiles    | Manage & execute saved/pre-installed scrapers.     |
| `ctrl+shift+a`| Manage Schedules    | Create/edit scheduled scraping automation.         |

### Article Management
| Key           | Action              | Description                                        |
|---------------|---------------------|----------------------------------------------------|
| `d`/`DELETE`  | Delete Selected     | Delete selected article (confirm).                 |
| `ctrl+r`      | Read Article        | Fetch & display full content of selected.          |
| `ctrl+t`      | Manage Tags         | Add/remove tags for selected article.              |
| `SPACE`       | Toggle Selection    | Toggle bulk selection for current article.         |
| `ctrl+a`      | Select All          | Select all articles in current view.               |
| `ctrl+d`      | Deselect All        | Clear all bulk selections.                         |
| `ctrl+shift+d`| Bulk Delete         | Delete all selected articles (confirm).            |
| `ctrl+x`      | Clear Database      | Delete ALL articles (confirm).                     |

### AI Features
| Key           | Action              | Description                                        |
|---------------|---------------------|----------------------------------------------------|
| `s`           | Summarize           | AI summary for selected (choose style).            |
| `ctrl+k`      | Sentiment Analysis  | AI sentiment for selected article.                 |
| `ctrl+p`      | Select AI Provider  | Switch between Gemini/OpenAI/Claude.               |

### Filtering & Sorting
| Key           | Action              | Description                                        |
|---------------|---------------------|----------------------------------------------------|
| `ctrl+f`      | Open Filters        | Filter by Title, URL, Date, Tags, Sentiment.       |
| `ctrl+shift+f`| Filter Presets      | Manage saved filter combinations.                  |
| `ctrl+shift+s`| Save Filter Preset  | Save current filters as a preset.                  |
| `ctrl+s`      | Cycle Sort          | Change article list sorting order.                 |

### Export & Analytics
| Key           | Action              | Description                                        |
|---------------|---------------------|----------------------------------------------------|
| `ctrl+e`      | Export CSV          | Export current view to CSV file.                   |
| `ctrl+j`      | Export JSON         | Export current view to JSON file.                  |
| `ctrl+shift+v`| View Analytics      | Open analytics dashboard with charts.              |

### Configuration & Help
| Key           | Action              | Description                                        |
|---------------|---------------------|----------------------------------------------------|
| `ctrl+g`      | Settings            | Open application settings editor.                  |
| `F1`/`ctrl+h` | Help                | Show/hide this help screen.                        |
| `q`/`ctrl+c`  | Quit                | Exit application.                                  |

**Tips:**
- Use `ctrl+f` for advanced filtering (regex, date ranges, tag logic).
- Use `ctrl+shift+f` to save/load frequently-used filter combinations.
- Press `SPACE` to bulk-select articles, then `ctrl+shift+d` to delete multiple at once.
- Analytics (`ctrl+shift+v`) provides sentiment charts, timelines, and source statistics.
{ps_desc}"""
        with VerticalScroll():
            yield Markdown(ht)
            yield Horizontal(Button("Close", id="ch_b"), classes="modal-buttons")

    def on_button_pressed(self, e: Button.Pressed) -> None:
        self.dismiss()

    def action_dismiss_screen(self) -> None:
        self.dismiss()


class StatusBar(Static):
    total_articles = reactive(0)
    selected_id = reactive[Optional[int]](None)
    bulk_selected_count = reactive(0)
    filter_status = reactive("")
    sort_status = reactive("")
    current_theme = reactive("Dark")
    scraper_profile = reactive("Manual Entry")

    def render(self) -> str:
        parts = [
            f"Total: {self.total_articles}",
            f"Profile: {self.scraper_profile}",
            f"Theme: {self.current_theme}"
        ]
        if self.selected_id is not None:
            parts.append(f"Sel ID: {self.selected_id}")
        if self.bulk_selected_count > 0:
            parts.append(f"Bulk: {self.bulk_selected_count} selected")
        if self.filter_status:
            parts.append(f"Filter: {self.filter_status}")
        if self.sort_status:
            parts.append(f"Sort: {self.sort_status}")
        return " | ".join(parts)


class WebScraperApp(App[None]):
    CSS_PATH = "web_scraper_tui_v1.0.tcss"
    BINDINGS = [
        Binding("q,ctrl+c", "quit", "Quit", priority=True),
        Binding("r", "refresh_data", "Refresh"),
        Binding("enter", "view_details", "View Details"),
        Binding("space", "select_row", "Toggle Selection"),
        Binding("v", "view_summary", "View Summary"),
        Binding("s", "summarize_selected", "Summarize"),
        Binding("ctrl+k", "sentiment_analysis_selected", "Sentiment"),
        Binding("d,delete", "delete_selected", "Delete"),
        Binding("ctrl+r", "read_article", "Read Full"),
        Binding("ctrl+t", "manage_tags", "Tags"),
        Binding("ctrl+s", "cycle_sort_order", "Sort"),
        Binding("ctrl+m", "manage_saved_scrapers", "Profiles"),
        Binding("ctrl+n", "scrape_new", "New Scrape"),
        Binding("ctrl+e", "export_csv", "Export CSV"),
        Binding("ctrl+j", "export_json", "Export JSON"),
        Binding("ctrl+x", "clear_database", "Clear DB"),
        Binding("ctrl+f", "open_filters", "Filters"),
        Binding("ctrl+l", "toggle_dark_mode", "Theme"),
        Binding("ctrl+a", "select_all", "Select All"),
        Binding("ctrl+d", "deselect_all", "Deselect All"),
        Binding("ctrl+shift+d", "bulk_delete", "Bulk Delete"),
        Binding("ctrl+p", "select_ai_provider", "AI Provider"),
        Binding("ctrl+g", "open_settings", "Settings"),
        Binding("ctrl+shift+f", "manage_filter_presets", "Filter Presets"),
        Binding("ctrl+shift+s", "save_filter_preset", "Save Preset"),
        Binding("ctrl+shift+a", "manage_schedules", "Schedules"),
        Binding("ctrl+shift+v", "view_analytics", "Analytics"),
        Binding("f1,ctrl+h", "toggle_help", "Help")
    ]
    dark = reactive(True, layout=True)
    selected_row_id: reactive[int | None] = reactive(None)
    selected_row_ids: reactive[set] = reactive(set)  # Bulk selection
    db_init_ok: bool = False
    last_scrape_url, last_scrape_selector, last_scrape_limit = "", "h2 a", 0
    title_filter = reactive("")
    url_filter = reactive("")
    date_filter = reactive("")
    tags_filter = reactive("")
    sentiment_filter = reactive("")
    # Advanced filtering options (v1.3.0)
    use_regex = reactive(False)
    date_filter_from = reactive("")
    date_filter_to = reactive("")
    tags_logic = reactive("AND")  # AND or OR
    current_scraper_profile: reactive[str] = reactive("Manual Entry")
    SORT_OPTIONS: List[Tuple[str, str]] = [
        ("sd.timestamp DESC", "Date Newest"),
        ("sd.timestamp ASC", "Date Oldest"),
        ("sd.title COLLATE NOCASE ASC", "Title A-Z"),
        ("sd.title COLLATE NOCASE DESC", "Title Z-A"),
        ("sd.sentiment ASC, sd.timestamp DESC", "Sentiment"),
        ("sd.id ASC", "ID Asc"),
        ("sd.id DESC", "ID Desc"),
        ("sd.url COLLATE NOCASE ASC", "Src URL A-Z"),
        ("sd.url COLLATE NOCASE DESC", "Src URL Z-A")
    ]
    current_sort_index = reactive(0)

    def __init__(self):
        super().__init__()
        self.db_init_ok = init_db()
        self.row_metadata = {}
        self._summarize_context = {}
        self.config = ConfigManager.load_config()
        # Initialize background scheduler (v1.5.0)
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        logger.info("Background scheduler started")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, name="Web Scraper TUI v1.0")
        yield DataTable(id="article_table", cursor_type="row", zebra_stripes=True)
        yield LoadingIndicator(id="loading_indicator", classes="hidden")
        yield StatusBar(id="status_bar")
        yield Footer()
        # yield Notifications() # Intentionally removed as App handles this

    async def on_mount(self) -> None:
        sbar = self.query_one(StatusBar)
        sbar.current_theme = "Dark" if self.dark else "Light"
        sbar.scraper_profile = self.current_scraper_profile
        if not self.db_init_ok:
            self.notify("CRITICAL: DB init failed!", title="DB Error", severity="error", timeout=0)
            return
        tbl = self.query_one(DataTable)
        tbl.add_columns("ID", "S", "Sentiment", "Title", "Source URL", "Tags", "Scraped At")
        sbar.sort_status = self.SORT_OPTIONS[self.current_sort_index][1]
        await self.refresh_article_table()
        tbl.focus()
        # Load and schedule enabled scrapes (v1.5.0)
        self._load_scheduled_scrapes()

    def _load_scheduled_scrapes(self) -> None:
        """Load enabled schedules from database and add them to APScheduler."""
        try:
            schedules = ScheduleManager.list_schedules(enabled_only=True)
            for schedule in schedules:
                self._add_schedule_to_scheduler(schedule)
            logger.info(f"Loaded {len(schedules)} enabled schedules")
        except Exception as e:
            logger.error(f"Error loading schedules: {e}")

    def _add_schedule_to_scheduler(self, schedule: Dict[str, Any]) -> None:
        """Add a schedule to APScheduler."""
        try:
            schedule_id = schedule['id']
            schedule_type = schedule['schedule_type']
            schedule_value = schedule['schedule_value']

            # Create appropriate trigger
            if schedule_type == 'hourly':
                trigger = IntervalTrigger(hours=1)
            elif schedule_type == 'daily':
                # Parse HH:MM
                hour, minute = map(int, schedule_value.split(':'))
                trigger = CronTrigger(hour=hour, minute=minute)
            elif schedule_type == 'weekly':
                # Parse day:HH:MM (0=Monday, 6=Sunday)
                parts = schedule_value.split(':')
                day_of_week = int(parts[0])
                hour, minute = int(parts[1]), int(parts[2])
                trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
            elif schedule_type == 'interval':
                # Minutes interval
                minutes = int(schedule_value)
                trigger = IntervalTrigger(minutes=minutes)
            else:
                logger.warning(f"Unknown schedule type: {schedule_type}")
                return

            # Add job to scheduler
            self.scheduler.add_job(
                func=self._execute_scheduled_scrape,
                trigger=trigger,
                args=[schedule_id],
                id=f"schedule_{schedule_id}",
                replace_existing=True,
                name=schedule['name']
            )
            logger.info(f"Added schedule '{schedule['name']}' (ID: {schedule_id}) to scheduler")
        except Exception as e:
            logger.error(f"Error adding schedule to scheduler: {e}")

    def _execute_scheduled_scrape(self, schedule_id: int) -> None:
        """
        Execute a scheduled scrape (runs in background thread).

        Args:
            schedule_id: ID of the schedule to execute
        """
        try:
            logger.info(f"Executing scheduled scrape ID {schedule_id}")
            ScheduleManager.record_execution(schedule_id, 'running')

            # Get schedule details
            schedule = ScheduleManager.get_schedule(schedule_id)
            if not schedule:
                logger.error(f"Schedule ID {schedule_id} not found")
                ScheduleManager.record_execution(schedule_id, 'failed', 'Schedule not found')
                return

            if not schedule['enabled']:
                logger.warning(f"Schedule ID {schedule_id} is disabled, skipping")
                return

            # Get scraper profile details
            profile_url = schedule['profile_url']
            profile_selector = schedule['profile_selector']

            if not profile_url or not profile_selector:
                error_msg = "Invalid scraper profile (missing URL or selector)"
                logger.error(f"Schedule ID {schedule_id}: {error_msg}")
                ScheduleManager.record_execution(schedule_id, 'failed', error_msg)
                return

            # Execute the scrape
            inserted, skipped, url, ids = scrape_url_action(
                profile_url,
                profile_selector,
                limit=0  # No limit for scheduled scrapes
            )

            # Record success
            success_msg = f"Scraped {inserted} new articles, skipped {skipped} duplicates"
            logger.info(f"Schedule ID {schedule_id} completed: {success_msg}")
            ScheduleManager.record_execution(schedule_id, 'success')

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error executing schedule ID {schedule_id}: {e}", exc_info=True)
            ScheduleManager.record_execution(schedule_id, 'failed', error_msg)

    async def on_unmount(self) -> None:
        """Cleanup when app is shutting down."""
        try:
            if hasattr(self, 'scheduler') and self.scheduler:
                self.scheduler.shutdown(wait=False)
                logger.info("Background scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")

    async def refresh_article_table(self) -> None:
        tbl = self.query_one(DataTable)
        cur_row = tbl.cursor_row
        tbl.clear()
        s_col, s_disp = self.SORT_OPTIONS[self.current_sort_index]
        self.query_one(StatusBar).sort_status = s_disp
        bq = ("SELECT sd.id, sd.title, sd.url, sd.timestamp, "
              "sd.summary IS NOT NULL as has_s, sd.link, sd.sentiment, "
              "GROUP_CONCAT(DISTINCT t.name) as tags_c "
              "FROM scraped_data sd "
              "LEFT JOIN article_tags at ON sd.id = at.article_id "
              "LEFT JOIN tags t ON at.tag_id = t.id")
        conds, params, fdesc = [], {}, []

        # Title filter with optional regex support
        if self.title_filter:
            if self.use_regex:
                # For regex, we'll need to filter in Python after fetching
                fdesc.append(f"Title~regex'{self.title_filter}'")
            else:
                conds.append("sd.title LIKE :tf")
                params["tf"] = f"%{self.title_filter}%"
                fdesc.append(f"Title~'{self.title_filter}'")

        # URL filter with optional regex support
        if self.url_filter:
            if self.use_regex:
                # For regex, we'll need to filter in Python after fetching
                fdesc.append(f"URL~regex'{self.url_filter}'")
            else:
                conds.append("sd.url LIKE :uf")
                params["uf"] = f"%{self.url_filter}%"
                fdesc.append(f"URL~'{self.url_filter}'")

        # Date range filtering
        if self.date_filter_from or self.date_filter_to:
            if self.date_filter_from:
                try:
                    datetime.strptime(self.date_filter_from, "%Y-%m-%d")
                    conds.append("date(sd.timestamp) >= :df_from")
                    params["df_from"] = self.date_filter_from
                    fdesc.append(f"Date>={self.date_filter_from}")
                except ValueError:
                    self.notify("Invalid 'from' date format.", title="Filter Error", severity="warning")
            if self.date_filter_to:
                try:
                    datetime.strptime(self.date_filter_to, "%Y-%m-%d")
                    conds.append("date(sd.timestamp) <= :df_to")
                    params["df_to"] = self.date_filter_to
                    fdesc.append(f"Date<={self.date_filter_to}")
                except ValueError:
                    self.notify("Invalid 'to' date format.", title="Filter Error", severity="warning")
        elif self.date_filter:
            # Legacy single date filter
            try:
                datetime.strptime(self.date_filter, "%Y-%m-%d")
                conds.append("date(sd.timestamp) = :df")
                params["df"] = self.date_filter
                fdesc.append(f"Date='{self.date_filter}'")
            except ValueError:
                if self.date_filter:
                    self.notify("Invalid date format.", title="Filter Error", severity="warning")

        # Tags filter with AND/OR logic
        if self.tags_filter:
            tfs = [t.strip().lower() for t in self.tags_filter.split(',') if t.strip()]
            if tfs:
                if self.tags_logic == "OR":
                    # OR logic: article must have at least one of the tags
                    tag_placeholders = ", ".join([f":tgf_{i}" for i in range(len(tfs))])
                    conds.append(f"sd.id IN (SELECT at_s.article_id FROM article_tags at_s JOIN tags t_s ON at_s.tag_id = t_s.id WHERE t_s.name IN ({tag_placeholders}))")
                    for i, tn in enumerate(tfs):
                        params[f"tgf_{i}"] = tn
                    fdesc.append(f"Tags(OR)='{', '.join(tfs)}'")
                else:
                    # AND logic: article must have all tags (original behavior)
                    for i, tn in enumerate(tfs):
                        pn = f"tgf_{i}"
                        conds.append(f"sd.id IN (SELECT at_s.article_id FROM article_tags at_s JOIN tags t_s ON at_s.tag_id = t_s.id WHERE t_s.name = :{pn})")
                        params[pn] = tn
                    fdesc.append(f"Tags(AND)='{', '.join(tfs)}'")

        # Sentiment filter
        if self.sentiment_filter:
            sval = self.sentiment_filter.strip().capitalize()
            if sval in ["Positive", "Negative", "Neutral"]:
                conds.append("sd.sentiment LIKE :sf")
                params["sf"] = f"%{sval}%"
                fdesc.append(f"Sentiment='{sval}'")
            elif sval:
                self.notify("Sentiment filter: Positive, Negative, or Neutral.", title="Filter Info", severity="info")
        if conds:
            bq += " WHERE " + " AND ".join(conds)
        bq += " GROUP BY sd.id ORDER BY " + s_col
        self.query_one(StatusBar).filter_status = ", ".join(fdesc) if fdesc else "None"
        try:
            with get_db_connection() as conn:
                rows = conn.execute(bq, params).fetchall()
            logger.debug(f"Query returned {len(rows)} rows")

            # Apply regex filtering if enabled (post-SQL filter)
            if self.use_regex and (self.title_filter or self.url_filter):
                filtered_rows = []
                for r_d in rows:
                    try:
                        matches = True
                        if self.title_filter:
                            if not re.search(self.title_filter, r_d["title"], re.IGNORECASE):
                                matches = False
                        if matches and self.url_filter:
                            if not re.search(self.url_filter, r_d["url"], re.IGNORECASE):
                                matches = False
                        if matches:
                            filtered_rows.append(r_d)
                    except re.error as e:
                        self.notify(f"Invalid regex: {e}", title="Regex Error", severity="error")
                        break
                rows = filtered_rows
                logger.debug(f"After regex filtering: {len(rows)} rows")

            self.row_metadata.clear()
            for r_d in rows:
                s_ind = "✓" if r_d["has_s"] else " "
                tags_d = ", ".join(sorted(r_d["tags_c"].split(','))) if r_d["tags_c"] else ""
                senti_d = r_d["sentiment"] or "-"
                timestamp_val = r_d["timestamp"]
                timestamp_str = timestamp_val.strftime('%Y-%m-%d %H:%M:%S') if isinstance(timestamp_val, datetime) else str(timestamp_val)
                row_key = str(r_d["id"])
                # Add visual indicator for bulk selection
                if r_d["id"] in self.selected_row_ids:
                    id_display = f"[✓] {r_d['id']}"
                elif self.selected_row_id == r_d["id"]:
                    id_display = f"*{r_d['id']}"
                else:
                    id_display = str(r_d["id"])
                tbl.add_row(id_display, s_ind, senti_d, r_d["title"], r_d["url"], tags_d, timestamp_str, key=row_key)
                self.row_metadata[row_key] = {'link': r_d['link'], 'has_s': bool(r_d['has_s']), 'tags': r_d["tags_c"] or ""}
            self.query_one(StatusBar).total_articles = len(rows)
            logger.debug(f"Added {len(rows)} rows to table, table now has {tbl.row_count} rows")
            if cur_row is not None and cur_row < len(rows):
                tbl.move_cursor(row=cur_row)
            elif len(rows) > 0:
                tbl.move_cursor(row=0)
            if not rows and any([self.title_filter, self.url_filter, self.date_filter, self.tags_filter, self.sentiment_filter]):
                self.notify("No articles match filters.", title="Filter Info", severity="info", timeout=3)
            elif not rows:
                self.notify("No articles in DB.", title="Info", severity="info", timeout=3)
        except Exception as e:
            logger.error(f"Refresh err: {e}", exc_info=True)
            self.notify(f"Refresh err: {e}", title="DB Error", severity="error")
            self.query_one(StatusBar).total_articles = 0

    async def action_open_filters(self) -> None:
        def handle_filter_result(result):
            if result:  # If filters were applied
                self.call_later(self.refresh_article_table)
        self.push_screen(FilterScreen(self), handle_filter_result)

    async def action_select_row(self) -> None:
        current_id = self._get_current_row_id()
        if current_id is not None:
            # Toggle bulk selection
            if current_id in self.selected_row_ids:
                self.selected_row_ids.discard(current_id)
                logger.debug(f"Row removed from bulk selection, ID: {current_id}")
                self.notify(f"Removed article ID {current_id} from selection", title="Selection", severity="info", timeout=2)
            else:
                self.selected_row_ids.add(current_id)
                logger.debug(f"Row added to bulk selection, ID: {current_id}")
                self.notify(f"Added article ID {current_id} to selection", title="Selection", severity="info", timeout=2)

            # Update status bar
            self.query_one(StatusBar).bulk_selected_count = len(self.selected_row_ids)

            # Also update single selection for compatibility
            self.selected_row_id = current_id if len(self.selected_row_ids) == 1 else None
            self.query_one(StatusBar).selected_id = self.selected_row_id

            # Refresh table to show selection indicator
            await self.refresh_article_table()

    async def action_view_summary(self) -> None:
        current_id = self._get_current_row_id()
        if current_id is None:
            self.notify("No row selected.", title="Info", severity="warning")
            return
        self.selected_row_id = current_id
        try:
            def _get_summary_data_blocking():
                with get_db_connection() as conn_blocking:
                    return conn_blocking.execute("SELECT title, summary, sentiment FROM scraped_data WHERE id=?", (self.selected_row_id,)).fetchone()

            summary_data = _get_summary_data_blocking()
            if summary_data:
                summary_info = {
                    'summary': summary_data['summary'] if summary_data['summary'] else None,
                    'sentiment': summary_data['sentiment'] if summary_data['sentiment'] else None
                }
                if summary_info['summary'] or summary_info['sentiment']:
                    self.push_screen(ViewSummaryModal(summary_data['title'], summary_info))
                else:
                    self.notify("No summary or sentiment data available for this article.", title="Info", severity="info")
            else:
                self.notify(f"Article ID {self.selected_row_id} not found.", title="Error", severity="error")
        except Exception as e:
            logger.error(f"Error viewing summary for ID {self.selected_row_id}: {e}", exc_info=True)
            self.notify(f"Error loading summary: {e}", title="Error", severity="error")

    async def on_data_table_row_selected(self, e: DataTable.RowSelected) -> None:
        self.selected_row_id = int(e.row_key.value) if e.row_key else None
        self.query_one(StatusBar).selected_id = self.selected_row_id
        logger.debug(f"Row selected, ID: {self.selected_row_id}")
        await self.refresh_article_table()

    async def on_data_table_cell_selected(self, e: DataTable.CellSelected) -> None:
        """Handle mouse clicks on DataTable cells for row selection."""
        if e.row_key:
            row_id = int(e.row_key.value)
            # Toggle selection like spacebar does
            if self.selected_row_id == row_id:
                self.selected_row_id = None
                self.query_one(StatusBar).selected_id = None
                logger.debug(f"Row unselected via mouse click, ID: {row_id}")
                self.notify(f"Unselected article ID {row_id}", title="Selection", severity="info", timeout=2)
            else:
                self.selected_row_id = row_id
                self.query_one(StatusBar).selected_id = self.selected_row_id
                logger.debug(f"Row selected via mouse click, ID: {self.selected_row_id}")
                self.notify(f"Selected article ID {row_id}", title="Selection", severity="info", timeout=2)
            # Refresh table to show selection indicator
            await self.refresh_article_table()

    def _get_current_row_id(self) -> int | None:
        if self.selected_row_id is not None:
            return self.selected_row_id
        tbl = self.query_one(DataTable)
        if tbl.row_count > 0:
            try:
                # Get the row key at the current cursor position
                cursor_row = tbl.cursor_row
                if cursor_row < tbl.row_count:
                    # Get the row at cursor position and extract the ID from the first column
                    row_data = tbl.get_row_at(cursor_row)
                    if row_data and len(row_data) > 0:
                        return int(row_data[0])  # First column is the ID
            except Exception as e:
                logger.debug(f"Error getting current row ID: {e}")
        return None

    def _toggle_loading(self, show: bool) -> None:
        if show:
            self.query_one(LoadingIndicator).remove_class("hidden")
        else:
            self.query_one(LoadingIndicator).add_class("hidden")

    async def action_refresh_data(self) -> None:
        self.notify("Refreshing...", title="Data Update", severity="info", timeout=2)
        await self.refresh_article_table()

    async def action_toggle_dark_mode(self) -> None:
        self.dark = not self.dark
        self.query_one(StatusBar).current_theme = "Dark" if self.dark else "Light"

    async def action_view_details(self) -> None:
        current_id = self._get_current_row_id()
        if current_id is None:
            self.notify("No row selected.", title="Info", severity="warning")
            return
        self.selected_row_id = current_id
        try:
            with get_db_connection() as conn:
                ad = conn.execute("SELECT * FROM scraped_data WHERE id=?", (self.selected_row_id,)).fetchone()
                tags = get_tags_for_article(conn, self.selected_row_id)
            if ad:
                self.push_screen(ArticleDetailModal(ad, tags))
            else:
                self.notify(f"Not found: ID {self.selected_row_id}.", title="Error", severity="error")
        except Exception as e:
            logger.error(f"Err details ID {self.selected_row_id}: {e}", exc_info=True)
            self.notify(f"Err details: {e}", title="Error", severity="error")

    async def _summarize_worker(self, eid: int, link: str, style: str, title: str = "", url: str = "") -> None:
        self._toggle_loading(True)
        # Check if style is a template reference
        is_template = style.startswith("template:")
        display_name = style.split(":", 1)[1] if is_template else style
        self.notify(f"Starting '{display_name}' summary ID {eid}...", title="Summarizing", severity="info", timeout=3)
        try:
            txt = fetch_article_content(link, False)
            if not txt:
                self.notify(f"No content for ID {eid}.", title="Summ Error", severity="error")
                self._toggle_loading(False)
                return

            # Handle template-based summarization
            if is_template:
                template_name = style.split(":", 1)[1]
                template_text = TemplateManager.get_template_by_name(template_name)
                if template_text:
                    # Apply template variables
                    prompt = TemplateManager.apply_template(template_text, txt, title, url)
                    summ = get_summary_from_llm(txt, "overview", template=prompt)
                else:
                    self.notify(f"Template '{template_name}' not found.", title="Error", severity="error")
                    self._toggle_loading(False)
                    return
            else:
                # Legacy style-based summarization
                summ = get_summary_from_llm(txt, style)

            if summ:
                def _update_summary_blocking():
                    with get_db_connection() as conn_blocking:
                        conn_blocking.execute("UPDATE scraped_data SET summary=? WHERE id=?", (summ, eid))
                        conn_blocking.commit()
                _update_summary_blocking()
                self.notify(f"Summary for ID {eid} done.", title="Success", severity="info")
                await self.refresh_article_table()
            else:
                self.notify(f"No summary for ID {eid}.", title="Summ Error", severity="error")
        except Exception as e:
            logger.error(f"Err summ ID {eid}: {e}", exc_info=True)
            self.notify(f"Err summ ID {eid}: {e}", title="Error", severity="error")
        finally:
            self._toggle_loading(False)

    async def action_summarize_selected(self) -> None:
        current_id = self._get_current_row_id()
        if current_id is None:
            self.notify("No row selected.", title="Info", severity="warning")
            return
        self.selected_row_id = current_id
        row_key = str(self.selected_row_id)
        meta = self.row_metadata.get(row_key)
        if not meta or 'link' not in meta:
            self.notify(f"No link for ID {self.selected_row_id}.", title="Error", severity="error")
            return

        # Get article details for template variables
        def _get_article_info():
            with get_db_connection() as conn:
                cursor = conn.execute("SELECT title, url FROM scraped_data WHERE id = ?", (self.selected_row_id,))
                row = cursor.fetchone()
                return (row['title'], row['url']) if row else ("", "")

        title, url = _get_article_info()

        # Store summarization context for callbacks
        self._summarize_context = {
            'row_id': self.selected_row_id,
            'link': meta['link'],
            'title': title,
            'url': url
        }

        if meta.get('has_s'):
            def handle_confirm_result(confirmed):
                if confirmed:
                    self._show_summary_style_selector()
                else:
                    self.notify("Cancelled.", title="Info", severity="info")
            self.push_screen(ConfirmModal(f"ID {self.selected_row_id} has summary. Re-summarize?"), handle_confirm_result)
        else:
            self._show_summary_style_selector()

    def _show_summary_style_selector(self):
        def handle_style_result(style):
            if style is not None:
                context = self._summarize_context
                worker_with_args = functools.partial(
                    self._summarize_worker,
                    context['row_id'],
                    context['link'],
                    style,
                    context.get('title', ''),
                    context.get('url', '')
                )
                self.run_worker(worker_with_args, group="llm", exclusive=True)
            else:
                self.notify("Cancelled (no style).", title="Info", severity="info")
        self.push_screen(SelectSummaryStyleModal(), handle_style_result)

    async def _sentiment_worker(self, eid: int, link: str) -> None:
        self._toggle_loading(True)
        self.notify(f"Analyzing sentiment for ID {eid}...", title="Sentiment Analysis", severity="info", timeout=3)
        try:
            def _get_summary_blocking():
                with get_db_connection() as conn_blocking:
                    return conn_blocking.execute("SELECT summary FROM scraped_data WHERE id=?", (eid,)).fetchone()
            ad = _get_summary_blocking()
            txt_to_analyze = ad['summary'] if ad and ad['summary'] else fetch_article_content(link, False)
            if not txt_to_analyze:
                self.notify(f"No content to analyze for ID {eid}.", title="Sentiment Error", severity="error")
                self._toggle_loading(False)
                return
            s_res = get_sentiment_from_llm(txt_to_analyze)
            if s_res:
                def _update_sentiment_blocking():
                    with get_db_connection() as conn_blocking:
                        conn_blocking.execute("UPDATE scraped_data SET sentiment=? WHERE id=?", (s_res, eid))
                        conn_blocking.commit()
                _update_sentiment_blocking()
                self.notify(f"Sentiment for ID {eid}: {s_res}.", title="Sentiment Updated", severity="info")
                await self.refresh_article_table()
            else:
                self.notify(f"Failed to get sentiment for ID {eid}.", title="Sentiment Error", severity="error")
        except Exception as e:
            logger.error(f"Err sentiment worker ID {eid}: {e}", exc_info=True)
            self.notify(f"Err analyzing sentiment ID {eid}: {e}", title="Error", severity="error")
        finally:
            self._toggle_loading(False)

    async def action_sentiment_analysis_selected(self) -> None:
        current_id = self._get_current_row_id()
        if current_id is None:
            self.notify("No row selected for sentiment.", title="Info", severity="warning")
            return
        self.selected_row_id = current_id
        row_key = str(self.selected_row_id)
        meta = self.row_metadata.get(row_key)
        if not meta or 'link' not in meta:
            self.notify(f"No link for ID {self.selected_row_id}.", title="Error", severity="error")
            return
        worker_with_args = functools.partial(self._sentiment_worker, self.selected_row_id, meta['link'])
        self.run_worker(worker_with_args, group="llm", exclusive=True)

    async def _scrape_url_worker(self, url: str, selector: str, limit: int, default_tags_csv: Optional[str] = None) -> None:
        self._toggle_loading(True)
        self.notify(f"Scraping {url}...", title="Scraping", severity="info", timeout=3)
        try:
            inserted, skipped, scraped_url, inserted_ids = scrape_url_action(url, selector, limit)
            self.last_scrape_url = scraped_url
            if inserted_ids and default_tags_csv:
                logger.info(f"Applying default tags '{default_tags_csv}' to {len(inserted_ids)} new articles.")

                def _apply_tags_blocking():
                    for aid in inserted_ids:
                        _update_tags_for_article_blocking(aid, default_tags_csv)
                _apply_tags_blocking()
                self.notify(f"Applied default tags to {len(inserted_ids)} new articles.", title="Tags Applied", severity="info")
            self.notify(f"Scrape of {url} done. New: {inserted}, Skipped: {skipped}.", title="Scrape Finished", severity="info")
            await self.refresh_article_table()
        except Exception as e:
            logger.error(f"Err scrape worker {url}: {e}", exc_info=True)
            self.notify(f"Err scraping {url}: {e}", title="Scrape Error", severity="error")
        finally:
            self._toggle_loading(False)

    async def _handle_scrape_new_result(self, result: tuple[str, str, int] | None, default_tags_csv: Optional[str] = None) -> None:
        if result:
            url, selector, limit = result
            worker_with_args = functools.partial(self._scrape_url_worker, url, selector, limit, default_tags_csv)
            self.run_worker(worker_with_args, group="scraping", exclusive=True)

    async def action_scrape_new(self) -> None:
        self.current_scraper_profile = "Manual Entry"
        self.query_one(StatusBar).scraper_profile = self.current_scraper_profile
        await self.app.push_screen(ScrapeURLModal(self.last_scrape_url, self.last_scrape_selector, self.last_scrape_limit), self._handle_scrape_new_result)

    async def action_delete_selected(self) -> None:
        current_id = self._get_current_row_id()
        if current_id is None:
            self.notify("No row selected.", title="Info", severity="warning")
            return
        self.selected_row_id = current_id

        def handle_delete_confirmation(confirmed):
            if confirmed:
                try:
                    def _delete_blocking():
                        with get_db_connection() as conn_blocking:
                            cur = conn_blocking.execute("DELETE FROM scraped_data WHERE id=?", (self.selected_row_id,))
                            conn_blocking.commit()
                            return cur.rowcount
                    rowcount = _delete_blocking()
                    if rowcount >0:
                        self.notify(f"Deleted ID {self.selected_row_id}.",title="Success",severity="info")
                        self.selected_row_id=None
                        self.query_one(StatusBar).selected_id=None
                        self.call_later(self.refresh_article_table)
                    else:
                        self.notify(f"Not found ID {self.selected_row_id}.",title="Warning",severity="warning")
                except Exception as e:
                    logger.error(f"Err del ID {self.selected_row_id}: {e}",exc_info=True)
                    self.notify(f"Err del ID {self.selected_row_id}: {e}",title="Error",severity="error")
            else:
                self.notify("Cancelled.",title="Info",severity="info")

        self.push_screen(ConfirmModal(f"Delete article ID {self.selected_row_id}?"), handle_delete_confirmation)

    async def action_select_all(self) -> None:
        """Select all visible articles in the current view."""
        try:
            with get_db_connection() as conn:
                # Get all IDs from current filtered view
                bq = "SELECT sd.id FROM scraped_data sd"
                conds, params = [], {}
                if self.title_filter:
                    conds.append("sd.title LIKE :tf")
                    params["tf"] = f"%{self.title_filter}%"
                if self.url_filter:
                    conds.append("sd.url LIKE :uf")
                    params["uf"] = f"%{self.url_filter}%"
                if conds:
                    bq += " WHERE " + " AND ".join(conds)
                rows = conn.execute(bq, params).fetchall()
                self.selected_row_ids = set(row["id"] for row in rows)
                self.query_one(StatusBar).bulk_selected_count = len(self.selected_row_ids)
                await self.refresh_article_table()
                self.notify(f"Selected {len(self.selected_row_ids)} articles", title="Selection", severity="info")
        except Exception as e:
            logger.error(f"Error in select_all: {e}", exc_info=True)
            self.notify(f"Error selecting all: {e}", title="Error", severity="error")

    async def action_deselect_all(self) -> None:
        """Deselect all articles."""
        count = len(self.selected_row_ids)
        self.selected_row_ids.clear()
        self.selected_row_id = None
        self.query_one(StatusBar).bulk_selected_count = 0
        self.query_one(StatusBar).selected_id = None
        await self.refresh_article_table()
        self.notify(f"Deselected {count} articles", title="Selection", severity="info")

    async def action_bulk_delete(self) -> None:
        """Delete all selected articles."""
        if not self.selected_row_ids:
            self.notify("No articles selected for bulk delete.", title="Info", severity="warning")
            return

        count = len(self.selected_row_ids)
        selected_ids = list(self.selected_row_ids)

        def handle_bulk_delete_confirmation(confirmed):
            if confirmed:
                try:
                    def _bulk_delete_blocking():
                        with get_db_connection() as conn_blocking:
                            placeholders = ','.join('?' * len(selected_ids))
                            cur = conn_blocking.execute(
                                f"DELETE FROM scraped_data WHERE id IN ({placeholders})",
                                selected_ids
                            )
                            conn_blocking.commit()
                            return cur.rowcount
                    rowcount = _bulk_delete_blocking()
                    self.selected_row_ids.clear()
                    self.selected_row_id = None
                    self.query_one(StatusBar).bulk_selected_count = 0
                    self.query_one(StatusBar).selected_id = None
                    self.notify(f"Deleted {rowcount} articles.", title="Bulk Delete Success", severity="info")
                    logger.info(f"Bulk deleted {rowcount} articles")
                    self.call_later(self.refresh_article_table)
                except Exception as e:
                    logger.error(f"Error bulk deleting: {e}", exc_info=True)
                    self.notify(f"Error bulk deleting: {e}", title="Error", severity="error")
            else:
                self.notify("Bulk delete cancelled.", title="Info", severity="info")

        self.push_screen(
            ConfirmModal(
                f"Delete {count} selected articles? This cannot be undone!",
                confirm_text="Yes, Delete All"
            ),
            handle_bulk_delete_confirmation
        )

    async def action_clear_database(self)->None:
        def handle_clear_confirmation(confirmed):
            if confirmed:
                self._toggle_loading(True)
                try:
                    def _clear_db_blocking():
                        with get_db_connection() as conn_blocking:conn_blocking.executescript("DELETE FROM article_tags;DELETE FROM tags;DELETE FROM scraped_data;DELETE FROM saved_scrapers WHERE is_preinstalled=0;DELETE FROM sqlite_sequence WHERE name IN ('scraped_data','tags','saved_scrapers');");conn_blocking.commit()
                    _clear_db_blocking()
                    self.notify("User data cleared (pre-installed scrapers kept).",title="DB Cleared",severity="info")
                    logger.info("DB cleared.")
                    self.selected_row_id=None
                    self.query_one(StatusBar).selected_id=None
                    self.call_later(self.refresh_article_table)
                except Exception as e:
                    logger.error(f"Err clearing DB: {e}",exc_info=True)
                    self.notify(f"Err clearing DB: {e}",title="DB Error",severity="error")
                finally:
                    self._toggle_loading(False)
            else:
                self.notify("Clear DB cancelled.",title="Info",severity="info")

        self.push_screen(ConfirmModal("Delete ALL articles from DB? Irreversible!",confirm_text="Yes, Delete All"), handle_clear_confirmation)

    async def action_select_ai_provider(self) -> None:
        """Open AI provider selection modal."""
        def handle_provider_selection(provider_key: Optional[str]) -> None:
            if provider_key:
                if provider_key == "gemini" and GEMINI_API_KEY:
                    set_ai_provider(GeminiProvider(GEMINI_API_KEY))
                    self.notify("AI Provider: Google Gemini", title="Provider Changed", severity="info")
                elif provider_key == "openai" and OPENAI_API_KEY:
                    set_ai_provider(OpenAIProvider(OPENAI_API_KEY))
                    self.notify("AI Provider: OpenAI GPT", title="Provider Changed", severity="info")
                elif provider_key == "claude" and CLAUDE_API_KEY:
                    set_ai_provider(ClaudeProvider(CLAUDE_API_KEY))
                    self.notify("AI Provider: Anthropic Claude", title="Provider Changed", severity="info")
                else:
                    self.notify("API key not configured in .env", title="Error", severity="error")
        self.push_screen(AIProviderSelectionModal(), handle_provider_selection)

    async def action_open_settings(self) -> None:
        """Open settings modal (Ctrl+G)."""
        def handle_settings_result(saved: bool) -> None:
            if saved:
                self.config = ConfigManager.load_config()
                self.notify("Settings reloaded", title="Settings", severity="info")
        self.push_screen(SettingsModal(self.config), handle_settings_result)

    async def action_manage_filter_presets(self) -> None:
        """Open filter presets management modal (Ctrl+Shift+F)."""
        def handle_preset_selection(preset_name: Optional[str]) -> None:
            if preset_name:
                preset_data = FilterPresetManager.load_preset(preset_name)
                if preset_data:
                    # Apply preset filters
                    self.title_filter = preset_data['title_filter']
                    self.url_filter = preset_data['url_filter']
                    self.date_filter_from = preset_data['date_from']
                    self.date_filter_to = preset_data['date_to']
                    self.tags_filter = preset_data['tags_filter']
                    self.sentiment_filter = preset_data['sentiment_filter']
                    self.use_regex = preset_data['use_regex']
                    self.tags_logic = preset_data['tags_logic']
                    self.notify(f"Loaded preset: {preset_name}", title="Preset Loaded", severity="info")
                    # Refresh table with new filters
                    self.run_worker(self.refresh_article_table())
                else:
                    self.notify("Failed to load preset", title="Error", severity="error")
        self.push_screen(FilterPresetModal(), handle_preset_selection)

    async def action_save_filter_preset(self) -> None:
        """Save current filters as a preset (Ctrl+Shift+S)."""
        def handle_preset_name(name: Optional[str]) -> None:
            if name:
                success = FilterPresetManager.save_preset(
                    name,
                    self.title_filter,
                    self.url_filter,
                    self.date_filter_from,
                    self.date_filter_to,
                    self.tags_filter,
                    self.sentiment_filter,
                    self.use_regex,
                    self.tags_logic
                )
                if success:
                    self.notify(f"Saved preset: {name}", title="Preset Saved", severity="info")
                else:
                    self.notify("Failed to save preset", title="Error", severity="error")
        self.push_screen(SavePresetModal(), handle_preset_name)

    async def action_manage_schedules(self) -> None:
        """Open schedule management modal (Ctrl+Shift+A)."""
        def handle_schedule_result(result: Optional[int]) -> None:
            if result:
                self.notify("Schedule management complete", severity="info")
        self.push_screen(ScheduleManagementModal(), handle_schedule_result)

    async def action_view_analytics(self) -> None:
        """Open analytics modal (Ctrl+Shift+V)."""
        self.push_screen(AnalyticsModal())

    async def action_toggle_help(self)->None:await self.app.push_screen(HelpModal())
    async def action_cycle_sort_order(self)->None:self.current_sort_index=(self.current_sort_index+1)%len(self.SORT_OPTIONS);await self.refresh_article_table();self.notify(f"Sorted by: {self.SORT_OPTIONS[self.current_sort_index][1]}",title="Sort Changed",severity="info",timeout=2)
    async def _handle_manage_tags_result(self,aid:int,nts:Optional[str])->None:
        if nts is not None:
            self._toggle_loading(True)
            try:
                _update_tags_for_article_blocking(aid,nts)
                self.notify(f"Tags updated for ID {aid}.",title="Tags Updated",severity="info");await self.refresh_article_table()
            except Exception as e:logger.error(f"Err tags ID {aid}: {e}",exc_info=True);self.notify(f"Err tags: {e}",title="Tag Error",severity="error")
            finally:self._toggle_loading(False)
    async def action_manage_tags(self)->None:
        current_id=self._get_current_row_id()
        if current_id is None:self.notify("No row selected.",title="Info",severity="warning");return
        self.selected_row_id=current_id
        try:
            def _get_tags_blocking():
                with get_db_connection() as conn_blocking:
                    return get_tags_for_article(conn_blocking, self.selected_row_id) # type: ignore
            ct = _get_tags_blocking()
            await self.app.push_screen(ManageTagsModal(self.selected_row_id,ct),lambda ts:self._handle_manage_tags_result(self.selected_row_id,ts)) # type: ignore
        except Exception as e:logger.error(f"Err prep tags ID {self.selected_row_id}: {e}",exc_info=True);self.notify(f"Err tag manager: {e}",title="Error",severity="error")

    async def _export_csv_worker(self,filename:str)->None:
        self._toggle_loading(True)
        self.notify(f"Exporting to {filename}...",title="Exporting CSV",severity="info")
        try:
            s_col,_=self.SORT_OPTIONS[self.current_sort_index]
            def _fetch_for_export_blocking():
                bq_export="SELECT sd.id,sd.title,sd.url,sd.link,sd.timestamp,sd.summary,sd.sentiment,GROUP_CONCAT(DISTINCT t.name) as tags_c FROM scraped_data sd LEFT JOIN article_tags at ON sd.id=at.article_id LEFT JOIN tags t ON at.tag_id=t.id"
                conds_export,params_export=[],{}
                if self.title_filter:conds_export.append("sd.title LIKE :tf");params_export["tf"]=f"%{self.title_filter}%"
                if self.url_filter:conds_export.append("sd.url LIKE :uf");params_export["uf"]=f"%{self.url_filter}%"
                if self.date_filter:conds_export.append("date(sd.timestamp)=:df");params_export["df"]=self.date_filter
                if self.tags_filter:
                    tfs_export=[t.strip().lower() for t in self.tags_filter.split(',') if t.strip()]
                    for i,tn_export in enumerate(tfs_export):pn_export=f"tgf_{i}";conds_export.append(f"sd.id IN (SELECT at_s.article_id FROM article_tags at_s JOIN tags t_s ON at_s.tag_id=t_s.id WHERE t_s.name=:{pn_export})");params_export[pn_export]=tn_export
                if self.sentiment_filter:sval_export=self.sentiment_filter.strip().capitalize();conds_export.append("sd.sentiment LIKE :sf");params_export["sf"]=f"%{sval_export}%"
                if conds_export:bq_export+=" WHERE "+" AND ".join(conds_export)
                bq_export+=" GROUP BY sd.id ORDER BY "+s_col
                with get_db_connection() as conn_blocking:
                    return conn_blocking.execute(bq_export,params_export).fetchall()
            rows_to_export = _fetch_for_export_blocking()
            if not rows_to_export:self.notify("No data to export.",title="Export Info",severity="info"); self._toggle_loading(False); return
            def _write_csv_blocking():
                fp=Path(filename)
                with open(fp,'w',newline='',encoding='utf-8') as csvf:
                    fn=['ID','Title','Source URL','Article Link','Timestamp','Summary','Sentiment','Tags'];w=csv.DictWriter(csvf,fieldnames=fn);w.writeheader()
                    for r_data in rows_to_export:
                        timestamp_val = r_data['timestamp']
                        timestamp_str = timestamp_val.strftime('%Y-%m-%d %H:%M:%S') if isinstance(timestamp_val, datetime) else str(timestamp_val)
                        w.writerow({'ID':r_data['id'],'Title':r_data['title'],'Source URL':r_data['url'],'Article Link':r_data['link'],'Timestamp':timestamp_str,'Summary':r_data['summary'],'Sentiment':r_data['sentiment'],'Tags':r_data['tags_c']})
                return fp.resolve(), len(rows_to_export)
            resolved_path, num_rows = _write_csv_blocking()
            self.notify(f"Data exported to {resolved_path}",title="CSV Exported",severity="info");logger.info(f"Exported {num_rows} rows to {resolved_path}")
        except Exception as e:logger.error(f"Err export CSV '{filename}': {e}",exc_info=True);self.notify(f"Err export CSV: {e}",title="Export Error",severity="error")
        finally:self._toggle_loading(False)
    async def action_export_csv(self)->None:
        dfn=f"scraped_articles_{datetime.now():%Y%m%d_%H%M%S}.csv"
        def handle_filename_result(fn):
            if fn:
                worker_with_args = functools.partial(self._export_csv_worker, fn)
                self.run_worker(worker_with_args, group="exporting", exclusive=True)
        self.push_screen(FilenameModal(default_filename=dfn), handle_filename_result)

    async def _export_json_worker(self, filename: str) -> None:
        """Export articles to JSON format."""
        self._toggle_loading(True)
        self.notify(f"Exporting to {filename}...", title="Exporting JSON", severity="info")
        try:
            s_col, _ = self.SORT_OPTIONS[self.current_sort_index]

            def _fetch_for_export_blocking():
                bq_export = (
                    "SELECT sd.id, sd.title, sd.url, sd.link, sd.timestamp, "
                    "sd.summary, sd.sentiment, sd.content, "
                    "GROUP_CONCAT(DISTINCT t.name) as tags_c "
                    "FROM scraped_data sd "
                    "LEFT JOIN article_tags at ON sd.id = at.article_id "
                    "LEFT JOIN tags t ON at.tag_id = t.id"
                )
                conds_export, params_export = [], {}
                if self.title_filter:
                    conds_export.append("sd.title LIKE :tf")
                    params_export["tf"] = f"%{self.title_filter}%"
                if self.url_filter:
                    conds_export.append("sd.url LIKE :uf")
                    params_export["uf"] = f"%{self.url_filter}%"
                if self.date_filter:
                    conds_export.append("date(sd.timestamp) = :df")
                    params_export["df"] = self.date_filter
                if self.tags_filter:
                    tfs_export = [t.strip().lower() for t in self.tags_filter.split(',') if t.strip()]
                    for i, tn_export in enumerate(tfs_export):
                        pn_export = f"tgf_{i}"
                        conds_export.append(
                            f"sd.id IN (SELECT at_s.article_id FROM article_tags at_s "
                            f"JOIN tags t_s ON at_s.tag_id = t_s.id WHERE t_s.name = :{pn_export})"
                        )
                        params_export[pn_export] = tn_export
                if self.sentiment_filter:
                    sval_export = self.sentiment_filter.strip().capitalize()
                    conds_export.append("sd.sentiment LIKE :sf")
                    params_export["sf"] = f"%{sval_export}%"
                if conds_export:
                    bq_export += " WHERE " + " AND ".join(conds_export)
                bq_export += " GROUP BY sd.id ORDER BY " + s_col
                with get_db_connection() as conn_blocking:
                    return conn_blocking.execute(bq_export, params_export).fetchall()

            rows_to_export = _fetch_for_export_blocking()
            if not rows_to_export:
                self.notify("No data to export.", title="Export Info", severity="info")
                self._toggle_loading(False)
                return

            def _write_json_blocking():
                fp = Path(filename)
                articles = []
                for r_data in rows_to_export:
                    timestamp_val = r_data['timestamp']
                    timestamp_str = (
                        timestamp_val.strftime('%Y-%m-%d %H:%M:%S')
                        if isinstance(timestamp_val, datetime)
                        else str(timestamp_val)
                    )
                    tags_list = (
                        [t.strip() for t in r_data['tags_c'].split(',') if t.strip()]
                        if r_data['tags_c']
                        else []
                    )
                    article_data = {
                        'id': r_data['id'],
                        'title': r_data['title'],
                        'source_url': r_data['url'],
                        'article_link': r_data['link'],
                        'timestamp': timestamp_str,
                        'summary': r_data['summary'],
                        'sentiment': r_data['sentiment'],
                        'content': r_data['content'],
                        'tags': tags_list
                    }
                    articles.append(article_data)

                export_data = {
                    'export_date': datetime.now().isoformat(),
                    'total_articles': len(articles),
                    'filters_applied': {
                        'title': self.title_filter if self.title_filter else None,
                        'url': self.url_filter if self.url_filter else None,
                        'date': self.date_filter if self.date_filter else None,
                        'tags': self.tags_filter if self.tags_filter else None,
                        'sentiment': self.sentiment_filter if self.sentiment_filter else None
                    },
                    'articles': articles
                }

                with open(fp, 'w', encoding='utf-8') as jsonf:
                    json.dump(export_data, jsonf, indent=2, ensure_ascii=False)
                return fp.resolve(), len(articles)

            resolved_path, num_rows = _write_json_blocking()
            self.notify(
                f"Data exported to {resolved_path}",
                title="JSON Exported",
                severity="info"
            )
            logger.info(f"Exported {num_rows} rows to {resolved_path}")
        except Exception as e:
            logger.error(f"Error exporting JSON '{filename}': {e}", exc_info=True)
            self.notify(f"Error exporting JSON: {e}", title="Export Error", severity="error")
        finally:
            self._toggle_loading(False)

    async def action_export_json(self) -> None:
        """Export articles to JSON format."""
        dfn = f"scraped_articles_{datetime.now():%Y%m%d_%H%M%S}.json"

        def handle_filename_result(fn):
            if fn:
                worker_with_args = functools.partial(self._export_json_worker, fn)
                self.run_worker(worker_with_args, group="exporting", exclusive=True)

        self.push_screen(FilenameModal(default_filename=dfn), handle_filename_result)

    async def _read_article_worker(self,eid:int,link:str,title:str)->None:
        self._toggle_loading(True);self.notify(f"Fetching '{title[:30]}...' (ID {eid})",title="Reading Article",severity="info")
        try:
            content=fetch_article_content(link,True)
            if content is not None:await self.app.push_screen(ReadArticleModal(title,content))
            else:self.notify(f"No content for article ID {eid}.",title="Read Error",severity="error")
        except Exception as e:logger.error(f"Err read worker ID {eid}: {e}",exc_info=True);self.notify(f"Err reading ID {eid}: {e}",title="Read Error",severity="error")
        finally:self._toggle_loading(False)
    async def action_read_article(self)->None:
        current_id=self._get_current_row_id()
        if current_id is None:self.notify("No row selected.",title="Info",severity="warning");return
        self.selected_row_id=current_id
        try:
            def _get_article_data_blocking():
                with get_db_connection() as conn_blocking:
                    return conn_blocking.execute("SELECT title,link FROM scraped_data WHERE id=?",(self.selected_row_id,)).fetchone() # type: ignore
            ad = _get_article_data_blocking()
            if not ad:self.notify(f"Article ID {self.selected_row_id} not found.",title="Error",severity="error");return
            worker_with_args = functools.partial(self._read_article_worker, self.selected_row_id, ad['link'], ad['title'])
            self.run_worker(worker_with_args, group="reading", exclusive=True)
        except Exception as e:logger.error(f"Err prep read ID {self.selected_row_id}: {e}",exc_info=True);self.notify(f"Err prep read: {e}",title="Error",severity="error")

    async def _handle_manage_scrapers_result(self,result:Optional[Tuple[str,Any]])->None:
        if not result:return
        action,data=result
        if action=="add":
            def handle_add_scraper_result(sd):
                if sd:
                    try:
                        def _add_scraper_blocking():
                            with get_db_connection() as conn_blocking:conn_blocking.execute("INSERT INTO saved_scrapers (name,url,selector,default_limit,default_tags_csv,description,is_preinstalled) VALUES (:name,:url,:selector,:default_limit,:default_tags_csv,:description,0)",sd);conn_blocking.commit()
                        _add_scraper_blocking()
                        self.notify(f"Scraper '{sd['name']}' added.",title="Success",severity="info")
                    except sqlite3.IntegrityError:self.notify(f"Scraper name '{sd['name']}' already exists.",title="Error",severity="error")
                    except Exception as e:logger.error(f"Err adding scraper: {e}",exc_info=True);self.notify(f"Error adding scraper: {e}",severity="error")
            self.push_screen(AddEditScraperModal(), handle_add_scraper_result)
        elif action=="edit" and data:
            def handle_edit_scraper_result(sd):
                if sd:
                    try:
                        def _edit_scraper_blocking():
                            with get_db_connection() as conn_blocking:
                                if 'id' in sd: 
                                     conn_blocking.execute("UPDATE saved_scrapers SET name=:name,url=:url,selector=:selector,default_limit=:default_limit,default_tags_csv=:default_tags_csv,description=:description,is_preinstalled=:is_preinstalled WHERE id=:id",sd)
                                else: 
                                     conn_blocking.execute("INSERT INTO saved_scrapers (name,url,selector,default_limit,default_tags_csv,description,is_preinstalled) VALUES (:name,:url,:selector,:default_limit,:default_tags_csv,:description,0)",sd)
                                conn_blocking.commit()
                        _edit_scraper_blocking()
                        self.notify(f"Scraper '{sd['name']}' saved.",title="Success",severity="info")
                    except sqlite3.IntegrityError:self.notify(f"Scraper name '{sd['name']}' conflict.",title="Error",severity="error")
                    except Exception as e:logger.error(f"Err saving scraper: {e}",exc_info=True);self.notify(f"Error saving scraper: {e}",severity="error")
            self.push_screen(AddEditScraperModal(scraper_data=data), handle_edit_scraper_result)
        elif action=="delete" and data: 
            sid_to_del=data
            try:
                def _get_scraper_name_blocking():
                    with get_db_connection() as conn_blocking:
                        return conn_blocking.execute("SELECT name,is_preinstalled FROM saved_scrapers WHERE id=?",(sid_to_del,)).fetchone()
                s_to_del = _get_scraper_name_blocking()
                if not s_to_del:self.notify("Scraper not found.",severity="error");return
                if s_to_del['is_preinstalled']: self.notify("Pre-installed profiles cannot be deleted. Edit them to create custom versions.", severity="warning"); return
                def handle_delete_scraper_confirmation(confirmed):
                    if confirmed:
                        def _delete_scraper_blocking():
                            with get_db_connection() as conn_blocking:conn_blocking.execute("DELETE FROM saved_scrapers WHERE id=?",(sid_to_del,));conn_blocking.commit()
                        _delete_scraper_blocking()
                        self.notify(f"Scraper '{s_to_del['name']}' deleted.",title="Success",severity="info")
                self.push_screen(ConfirmModal(f"Delete saved scraper '{s_to_del['name']}'?"), handle_delete_scraper_confirmation)
            except Exception as e:logger.error(f"Err deleting scraper: {e}",exc_info=True);self.notify(f"Error deleting scraper: {e}",severity="error")
        elif action=="execute" and data: 
            scrape_target_url = data['url']
            final_url_to_scrape = scrape_target_url
            if scrape_target_url == "[ARCHIVE_WAYBACK_URL]":
                def handle_original_url_result(original_url):
                    if original_url:
                        final_url = f"https://web.archive.org/web/timestamp_latest/{quote_plus(original_url)}"
                        self.notify(f"Attempting to fetch latest archive for: {original_url}", title="Archive Fetch", severity="information")
                        # Execute the scraping with the final URL
                        worker_with_args = functools.partial(self._scrape_url_worker, final_url, data['selector'], data['default_limit'], data.get('default_tags_csv'))
                        self.run_worker(worker_with_args, group="scraping", exclusive=True)
                    else:
                        self.notify("Wayback scrape cancelled.", title="Info", severity="information")
                self.push_screen(OriginalURLModal(), handle_original_url_result)
                return  # Exit early since we'll handle the scraping in the callback
            elif scrape_target_url == "[USER_PROVIDES_URL]":
                self.last_scrape_url = "" 
                self.last_scrape_selector = data['selector']
                self.last_scrape_limit = data['default_limit']
                self.current_scraper_profile = data['name']
                self.query_one(StatusBar).scraper_profile = self.current_scraper_profile
                self.notify(f"Profile '{data['name']}' loaded. Please provide target URL.", title="Scraper Profile", severity="information")
                callback_with_tags = functools.partial(self._handle_scrape_new_result, default_tags_csv=data['default_tags_csv'])
                await self.app.push_screen(ScrapeURLModal("", data['selector'], data['default_limit']), callback_with_tags)
                return 
            self.last_scrape_url = final_url_to_scrape
            self.last_scrape_selector = data['selector']
            self.last_scrape_limit = data['default_limit']
            default_tags = data['default_tags_csv']
            self.current_scraper_profile = data['name']
            self.query_one(StatusBar).scraper_profile = self.current_scraper_profile
            self.notify(f"Executing scraper profile '{data['name']}'. Parameters loaded.", title="Scraper Profile", severity="information")
            callback_with_tags = functools.partial(self._handle_scrape_new_result, default_tags_csv=default_tags)
            await self.app.push_screen(ScrapeURLModal(final_url_to_scrape, data['selector'], data['default_limit']), callback_with_tags)

    async def action_manage_saved_scrapers(self) -> None:
        await self.app.push_screen(ManageScrapersModal(), self._handle_manage_scrapers_result)


def print_startup_banner():
    """Display welcome banner when starting the application."""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  ██╗    ██╗███████╗██████╗ ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗  ║
║  ██║    ██║██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝  ║
║  ██║ █╗ ██║█████╗  ██████╔╝███████╗██║     ██████╔╝███████║██████╔╝█████╗    ║
║  ██║███╗██║██╔══╝  ██╔══██╗╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝    ║
║  ╚███╔███╔╝███████╗██████╔╝███████║╚██████╗██║  ██║██║  ██║██║     ███████╗  ║
║   ╚══╝╚══╝ ╚══════╝╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝  ║
║                                                                              ║
║                       Text User Interface Web Scraper                        ║
║                                Version 1.6.0                                 ║
║                                                                              ║
║   ╔══════════════════════════════════════════════════════════════════════╗   ║
║   ║                              Features                                ║   ║
║   ║                                                                      ║   ║
║   ║  • Interactive terminal-based web scraping interface                 ║   ║
║   ║  • Pre-configured scraper profiles for popular websites              ║   ║
║   ║  • Custom scraper creation with CSS selectors                        ║   ║
║   ║  • SQLite database for persistent article storage                    ║   ║
║   ║  • AI-powered summarization and sentiment analysis                   ║   ║
║   ║  • Advanced filtering and sorting capabilities                       ║   ║
║   ║  • CSV export functionality                                          ║   ║
║   ║  • Tag-based article organization                                    ║   ║
║   ║                                                                      ║   ║
║   ╚══════════════════════════════════════════════════════════════════════╝   ║
║                                                                              ║
║                     Starting application... Please wait...                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_shutdown_banner():
    """Display farewell banner when exiting the application."""
    banner = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║                Thank you for using WebScrape-TUI!                 ║
║                                                                   ║
║                                                                   ║
║   ██████╗  ██████╗  ██████╗ ██████╗ ██████╗ ██╗   ██╗███████╗██╗  ║
║  ██╔════╝ ██╔═══██╗██╔═══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝██╔════╝██║  ║
║  ██║  ███╗██║   ██║██║   ██║██║  ██║██████╔╝ ╚████╔╝ █████╗  ██║  ║
║  ██║   ██║██║   ██║██║   ██║██║  ██║██╔══██╗  ╚██╔╝  ██╔══╝  ╚═╝  ║
║  ╚██████╔╝╚██████╔╝╚██████╔╝██████╔╝██████╔╝   ██║   ███████╗██╗  ║
║   ╚═════╝  ╚═════╝  ╚═════╝ ╚═════╝ ╚═════╝    ╚═╝   ╚══════╝╚═╝  ║
║                                                                   ║
║    Visit our GitHub repository for updates and documentation:     ║
║           https://github.com/doublegate/WebScrape-TUI             ║
║                                                                   ║
║                Happy scraping! Come back soon!                    ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


if __name__ == "__main__":
    import time

    print_startup_banner()
    time.sleep(2)  # 2-second pause before starting the application

    css_file_content = """
Screen{layout:vertical;overflow:hidden}Header{dock:top}Footer{dock:bottom}
#app-grid{layout:vertical;overflow:hidden;height:1fr}
#filter-container{height:auto;padding:0 1;background:$boost}
#filter-container Label{padding:1 0 0 0;color:$text-muted}
#filter-inputs-grid{grid-size:1 5;grid-gutter:0 1;padding:0 0 1 0}
.filter-input{width:1fr}
DataTable{height:1fr;width:100%;margin-bottom:0}
DataTable .datatable--header-label { text-overflow: ellipsis; } /* Prevent header text wrapping */
DataTable .tags-column { width: 20%; } /* Give more space to tags column */
StatusBar{dock:bottom;height:1;padding:0 1;background:$primary-background;color:$text;width:100%}
LoadingIndicator{width:100%;height:100%;background:$surface-darken-2 50%;align:center middle;display:block;overlay:screen;}
LoadingIndicator.hidden{display:none}
.modal-buttons{width:100%;align-horizontal:center;padding-top:1}
.modal-buttons Button{margin:0 1}
Label.dialog-title{text-style:bold;width:100%;text-align:center;margin-bottom:1}
ManageTagsModal #cur_tags_lbl{margin-bottom:1;max-height:3;overflow-y:auto;border:round $primary-darken-1;padding:0 1}
ReadArticleModal VerticalScroll{border:panel $primary;padding:1;background:$surface}
ReadArticleModal #art_ttl_lbl{background:$primary-background-darken-1;padding:0 1;color:$text}
ManageScrapersModal ListView{border:panel $primary-background;background:$surface-lighten-1}
ManageScrapersModal ListView:focus{border:panel $primary}
ManageScrapersModal ListItem{padding:0 1;} /* Vertical padding 0, horizontal 1 */
ManageScrapersModal ListItem:hover{background:$primary 20%}
ManageScrapersModal ListItem.--highlight{background:$primary 40%}
ManageScrapersModal .buttons-top Button,ManageScrapersModal .buttons-bottom Button{width:auto;padding:0 2}
AddEditScraperModal Input#scraper_description_input { height: 3; border: round $primary-border; padding: 0 1; } /* Basic multiline-like appearance */
AddEditScraperModal Static.warning-text { color: $warning; padding: 0 1; text-align: center; }
.scraper-item-name{text-style:bold;}
.scraper-item-subtext{color:$text-muted;text-style:italic;}
    """
    css_file = Path("web_scraper_tui_v1.0.tcss")
    if not css_file.exists():
        with open(css_file, "w", encoding="utf-8") as f:
            f.write(css_file_content)
        logger.info(f"Created CSS file: {css_file.resolve()}")
    try:
        app = WebScraperApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user.")
    finally:
        print_shutdown_banner()
