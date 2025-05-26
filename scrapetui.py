#!/usr/bin/env python3
"""
WebScrape-TUI v1.0RC - Text User Interface Web Scraping Application

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
- Database: scraped_data_tui_v1.0RC.db (configurable via .env)
- Logs: scraper_tui_v1.0RC.log (configurable via .env)
- Styles: web_scraper_tui_v1.0RC.tcss
- API Keys: Set GEMINI_API_KEY in .env file for AI features
- Environment: Configure via .env file (copy from .env.example)

VERSION: 1.0RC (Release Candidate)
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
import math
import json
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple, Dict
import functools

# Textual imports
from textual.app import App, ComposeResult, CSSPathType
from textual.widgets import (
    Header, Footer, DataTable, Static, Button, Input, Label, Markdown, LoadingIndicator, Checkbox, RadioSet, RadioButton, ListView, ListItem
)
from textual.containers import Vertical, Horizontal, ScrollableContainer, Container, VerticalScroll, Grid
from textual.screen import ModalScreen
from textual.reactive import reactive
from textual.binding import Binding
from textual.logging import TextualHandler
# from textual.notifications import Notifications # Rely on App.notify()
from textual.css.query import DOMQuery

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
                        print(f"Warning: Invalid format in .env file at line {line_num}: {line}")
        except Exception as e:
            print(f"Warning: Could not read .env file: {e}")
    else:
        print("Info: No .env file found. Using default configuration.")
    
    return env_vars

# Load environment variables
env_vars = load_env_file()

# --- Globals and Configuration ---
DB_PATH = Path(env_vars.get("DATABASE_PATH", "scraped_data_tui_v1.0RC.db"))
LOG_FILE = Path(env_vars.get("LOG_FILE_PATH", "scraper_tui_v1.0RC.log"))
GEMINI_API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
GEMINI_API_KEY = env_vars.get("GEMINI_API_KEY", "")

logging.basicConfig(
    level="DEBUG",
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8'),
        TextualHandler()
    ],
    format="%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# --- Database Utilities ---
def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e: logger.critical(f"DB connection error: {e}", exc_info=True); raise

PREINSTALLED_SCRAPERS = [
    {
        "name": "Generic Article Cleaner", "url": "[USER_PROVIDES_URL]", "selector": "article, main, div[role='main']",
        "default_limit": 1, "default_tags_csv": "article, general",
        "description": "Tries to extract main content from any article-like page. Selectors are broad; may need refinement for specific sites."
    },
    {
        "name": "Wikipedia Article Text", "url": "https://en.wikipedia.org/wiki/Web_scraping", "selector": "div.mw-parser-output p",
        "default_limit": 0, "default_tags_csv": "wikipedia, reference",
        "description": "Extracts main paragraph text from Wikipedia articles. Aims to exclude infoboxes/navs."
    },
    {
        "name": "StackOverflow Q&A", "url": "[USER_PROVIDES_URL]", "selector": "#question .s-prose, .answer .s-prose",
        "default_limit": 0, "default_tags_csv": "stackoverflow, q&a, tech",
        "description": "Extracts questions and answers from StackOverflow pages. Point to a specific question URL."
    },
    {
        "name": "News Headlines (General)", "url": "[USER_PROVIDES_URL]", "selector": "h1 a, h2 a, h3 a, article header a, .headline a, .story-title a",
        "default_limit": 20, "default_tags_csv": "news, headlines",
        "description": "Attempts to extract headlines and links from news websites. Selector covers common patterns."
    },
    {
        "name": "Academic Abstract (arXiv)", "url": "https://arxiv.org/abs/2103.00020", "selector": "blockquote.abstract",
        "default_limit": 1, "default_tags_csv": "academic, abstract, arxiv",
        "description": "Specifically targets arXiv.org to extract the abstract of a paper. Replace URL with desired arXiv paper."
    },
    {
        "name": "Tech Specs (Simple Table)", "url": "[USER_PROVIDES_URL]", "selector": "table.specifications td, table.specs td",
        "default_limit": 0, "default_tags_csv": "technical, specs, table-data",
        "description": "Aims to pull cell data from simple HTML tables often found in product specifications."
    },
    {
        "name": "Forum Posts (Generic)", "url": "[USER_PROVIDES_URL]", "selector": ".post-content, .comment-text, .messageText",
        "default_limit": 0, "default_tags_csv": "forum, discussion",
        "description": "Designed for typical forum thread structures to extract individual posts/comments."
    },
    {
        "name": "Recipe Ingredients", "url": "[USER_PROVIDES_URL]", "selector": ".recipe-ingredients li, .ingredient-list p, ul.ingredients li",
        "default_limit": 0, "default_tags_csv": "recipe, ingredients, food",
        "description": "Focuses on extracting lists of ingredients from recipe web pages using common list patterns."
    },
    {
        "name": "Product Details (Basic)", "url": "[USER_PROVIDES_URL]", "selector": "h1.product-title, .product-name, span.price, .product-price, #priceblock_ourprice, .pdp-title, .pdp-price",
        "default_limit": 5, "default_tags_csv": "product, e-commerce",
        "description": "Extracts product title and price from e-commerce pages using common selectors. Limit is low as it might pick up related product info."
    },
    {
        "name": "Archived Page (Wayback)", "url": "[ARCHIVE_WAYBACK_URL]", "selector": "body", # Special handling for URL
        "default_limit": 1, "default_tags_csv": "archive, wayback",
        "description": "SPECIAL: Prompts for an original URL, then tries to fetch its latest version from the Wayback Machine. Scrapes entire body."
    }
]

def init_db():
    try:
        with get_db_connection() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS scraped_data (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT NOT NULL, title TEXT NOT NULL, link TEXT NOT NULL, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, summary TEXT, sentiment TEXT)")
            try: conn.execute("ALTER TABLE scraped_data ADD COLUMN summary TEXT")
            except sqlite3.OperationalError: pass
            try: conn.execute("ALTER TABLE scraped_data ADD COLUMN sentiment TEXT")
            except sqlite3.OperationalError: pass
            conn.execute("CREATE TABLE IF NOT EXISTS tags (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)")
            conn.execute("CREATE TABLE IF NOT EXISTS article_tags (article_id INTEGER NOT NULL, tag_id INTEGER NOT NULL, FOREIGN KEY (article_id) REFERENCES scraped_data(id) ON DELETE CASCADE, FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE, PRIMARY KEY (article_id, tag_id))")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS saved_scrapers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, url TEXT NOT NULL, selector TEXT NOT NULL,
                    default_limit INTEGER DEFAULT 0, default_tags_csv TEXT,
                    description TEXT, is_preinstalled INTEGER DEFAULT 0
                )
            """)
            try: conn.execute("ALTER TABLE saved_scrapers ADD COLUMN description TEXT")
            except sqlite3.OperationalError: pass
            try: conn.execute("ALTER TABLE saved_scrapers ADD COLUMN is_preinstalled INTEGER DEFAULT 0")
            except sqlite3.OperationalError: pass
            for idx_sql in [
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_link_unique ON scraped_data (link);", "CREATE INDEX IF NOT EXISTS idx_url ON scraped_data (url);",
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON scraped_data (timestamp);", "CREATE INDEX IF NOT EXISTS idx_title ON scraped_data (title);",
                "CREATE INDEX IF NOT EXISTS idx_sentiment ON scraped_data (sentiment);", "CREATE INDEX IF NOT EXISTS idx_tag_name ON tags (name);",
                "CREATE INDEX IF NOT EXISTS idx_article_tags_article ON article_tags (article_id);", "CREATE INDEX IF NOT EXISTS idx_article_tags_tag ON article_tags (tag_id);",
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_saved_scraper_name ON saved_scrapers (name);"
            ]: conn.execute(idx_sql)
            for ps in PREINSTALLED_SCRAPERS:
                conn.execute("""
                    INSERT OR IGNORE INTO saved_scrapers (name, url, selector, default_limit, default_tags_csv, description, is_preinstalled)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (ps["name"], ps["url"], ps["selector"], ps["default_limit"], ps["default_tags_csv"], ps["description"]))
            conn.commit()
        logger.info("Database initialized/updated successfully for v1.0RC.")
        return True
    except sqlite3.Error as e: logger.critical(f"DB init error v1.0RC: {e}", exc_info=True); return False

def get_tags_for_article(conn: sqlite3.Connection, article_id: int) -> List[str]:
    cursor = conn.execute("SELECT t.name FROM tags t JOIN article_tags at ON t.id = at.tag_id WHERE at.article_id = ? ORDER BY t.name", (article_id,))
    return [row['name'] for row in cursor.fetchall()]

def _update_tags_for_article_blocking(article_id: int, new_tags_str: str):
    with get_db_connection() as conn:
        current_tags = set(get_tags_for_article(conn, article_id))
        new_tags_list = [tag.strip().lower() for tag in new_tags_str.split(',') if tag.strip()]
        tags_to_add = [tn for tn in new_tags_list if tn not in current_tags]
        tags_to_remove = [tn for tn in current_tags if tn not in new_tags_list]
        for tag_name in tags_to_add:
            cur = conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,)); tag_id = cur.lastrowid
            if not tag_id: tag_id = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()['id']
            conn.execute("INSERT OR IGNORE INTO article_tags (article_id, tag_id) VALUES (?, ?)", (article_id, tag_id))
        for tag_name in tags_to_remove:
            tag_id_row = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()
            if tag_id_row: conn.execute("DELETE FROM article_tags WHERE article_id = ? AND tag_id = ?", (article_id, tag_id_row['id']))
        conn.commit()

def fetch_article_content(article_url: str, for_reading: bool = False) -> str | None:
    logger.info(f"Fetching content from: {article_url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 WebScraperTUI/5.0'}
        response = requests.get(article_url, timeout=20, headers=headers)
        response.raise_for_status(); soup = BeautifulSoup(response.content, "lxml")
        elements = ["article", "main", "div[role='main']", ".entry-content", ".post-content", "body"]
        text = ""
        for s in elements:
            el = soup.select_one(s)
            if el:
                if for_reading:
                    for ut in el(['script', 'style', 'nav', 'header', 'footer', 'aside', '.sidebar']): ut.decompose()
                    text = el.get_text(separator='\n', strip=True)
                else: text = el.get_text(separator=' ', strip=True)
                if len(text) > 200: break
        cleaned = "\n".join(l.strip() for l in text.splitlines() if l.strip()) if for_reading else ' '.join(text.split())
        logger.info(f"Fetched ~{len(cleaned)} chars from {article_url}"); return cleaned
    except Exception as e: logger.error(f"Err fetching {article_url}: {e}", exc_info=True); return None

def get_summary_from_llm(text_content: str, summary_style: str = "overview", max_length: int = 15000) -> str | None:
    if not text_content: return None
    if len(text_content) > max_length: text_content = text_content[:max_length]
    prompts = {
        "overview": f"Provide a concise overview (100-150 words) of:\n\n{text_content}\n\nOverview:",
        "bullets": f"Summarize into key bullet points:\n\n{text_content}\n\nBullets:",
        "eli5": f"Explain like I'm 5:\n\n{text_content}\n\nELI5:"
    }
    prompt = prompts.get(summary_style, prompts["overview"])
    payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.6, "maxOutputTokens": 600}}
    api_url = GEMINI_API_URL_TEMPLATE.format(api_key=GEMINI_API_KEY)
    logger.info(f"Requesting '{summary_style}' summary from Gemini API.")
    try:
        response = requests.post(api_url, json=payload, timeout=90); response.raise_for_status(); result = response.json()
        if result.get("candidates") and result["candidates"][0]["content"]["parts"][0].get("text"):
            summary = result["candidates"][0]["content"]["parts"][0]["text"]
            logger.info(f"Summary received (length: {len(summary)})."); return summary.strip()
        else: logger.error(f"Unexpected Gemini summary response: {result}")
    except Exception as e: logger.error(f"Err calling Gemini for summary: {e}", exc_info=True)
    return None

def get_sentiment_from_llm(text_content: str, max_length: int = 10000) -> Optional[str]:
    if not text_content: return None
    if len(text_content) > max_length: text_content = text_content[:max_length]
    prompt = f"Analyze sentiment. Respond: Positive, Negative, or Neutral.\n\nText:\n\"\"\"\n{text_content}\n\"\"\"\n\nSentiment:"
    payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.2, "maxOutputTokens": 10}}
    api_url = GEMINI_API_URL_TEMPLATE.format(api_key=GEMINI_API_KEY)
    logger.info(f"Requesting sentiment from Gemini API.")
    try:
        response = requests.post(api_url, json=payload, timeout=45); response.raise_for_status(); result = response.json()
        if result.get("candidates") and result["candidates"][0]["content"]["parts"][0].get("text"):
            s_text = result["candidates"][0]["content"]["parts"][0]["text"].strip().capitalize()
            if s_text in ["Positive", "Negative", "Neutral"]: logger.info(f"Sentiment: {s_text}."); return s_text
            else: logger.warning(f"LLM non-standard sentiment: '{s_text}'. Defaulting Neutral."); return "Neutral"
        else: logger.error(f"Unexpected Gemini sentiment response: {result}")
    except Exception as e: logger.error(f"Err calling Gemini for sentiment: {e}", exc_info=True)
    return None

def scrape_url_action(source_url: str, selector: str, limit: int = 0) -> tuple[int, int, str, Optional[List[int]]]:
    logger.info(f"Scraping {source_url} with selector '{selector}', limit {limit}")
    inserted_ids: List[int] = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 WebScraperTUI/5.0'}
        response = requests.get(source_url, timeout=15, headers=headers); response.raise_for_status()
    except Exception as e: logger.error(f"Failed to fetch {source_url}: {e}"); raise
    soup = BeautifulSoup(response.text, "lxml"); items = soup.select(selector)
    if not items: logger.warning(f"No items for '{selector}' on {source_url}"); return 0, 0, source_url, None
    records = []
    for i, tag_item in enumerate(items):
        if limit > 0 and len(records) >= limit: break
        title = tag_item.get_text(strip=True); link_href = tag_item.get("href")
        if title and link_href: records.append((source_url, title, urljoin(source_url, link_href)))
    if not records: return 0, 0, source_url, None
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            for rec_url, rec_title, rec_link in records:
                try:
                    c.execute("INSERT INTO scraped_data (url, title, link) VALUES (?, ?, ?)", (rec_url, rec_title, rec_link))
                    if c.lastrowid: inserted_ids.append(c.lastrowid)
                except sqlite3.IntegrityError: logger.debug(f"Skipping duplicate link: {rec_link}"); pass
            conn.commit()
        inserted_count, skipped_count = len(inserted_ids), len(records) - len(inserted_ids)
        logger.info(f"Scraping {source_url}: Stored {inserted_count} new, skipped {skipped_count} duplicates.")
        return inserted_count, skipped_count, source_url, inserted_ids
    except sqlite3.Error as e: logger.error(f"DB error storing from {source_url}: {e}", exc_info=True); raise

class ConfirmModal(ModalScreen[bool]):
    DEFAULT_CSS="""
    ConfirmModal {
        align: center middle;
        background: $surface-darken-1;
    }
    ConfirmModal > Vertical {
        width: auto;
        max-width: 80%;
        padding: 2 4;
        border: thick $primary-lighten-1;
        background: $panel;
    }
    ConfirmModal Label {
        margin-bottom: 1;
        width: 100%;
        text-align: center;
    }
    ConfirmModal .modal-buttons {
        width: 100%;
        align-horizontal: center;
        padding-top: 1;
    }
    """
    def __init__(self,p:str,ct:str="Confirm",clt:str="Cancel"):super().__init__();self.p,self.ct,self.clt=p,ct,clt
    def compose(self)->ComposeResult:
        with Vertical():yield Label(self.p);yield Horizontal(Button(self.ct,variant="primary",id="confirm"),Button(self.clt,id="cancel"),classes="modal-buttons")
    def on_button_pressed(self,e:Button.Pressed)->None:self.dismiss(e.button.id=="confirm")

class FilenameModal(ModalScreen[Optional[str]]):
    DEFAULT_CSS="""
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
    def __init__(self,p:str="Enter filename:",dfn:str="export.csv"):super().__init__();self.p,self.dfn=p,dfn
    def compose(self)->ComposeResult:
        with Vertical():yield Label(self.p,classes="dialog-title");yield Input(value=self.dfn,id="fn_in");yield Horizontal(Button("Save",variant="primary",id="sfn_b"),Button("Cancel",id="cfn_b"),classes="modal-buttons")
    def on_button_pressed(self,e:Button.Pressed)->None:
        if e.button.id=="sfn_b":fn=self.query_one("#fn_in",Input).value.strip();self.dismiss(fn) if fn else self.app.notify("Filename empty.",title="Error",severity="error")
        else:self.dismiss(None)

class ManageTagsModal(ModalScreen[Optional[str]]):
    DEFAULT_CSS="""
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
    def __init__(self,aid:int,ctl:List[str]):super().__init__();self.aid,self.cts=aid,", ".join(sorted(ctl))
    def compose(self)->ComposeResult:
        with Vertical():yield Label(f"Tags for Article ID: {self.aid}",classes="dialog-title");yield Label("Current:");yield Static(self.cts or "None",id="cur_tags_lbl");yield Label("New (comma-sep):");yield Input(value=self.cts,id="tags_in");yield Horizontal(Button("Save",variant="primary",id="st_b"),Button("Cancel",id="ct_b"),classes="modal-buttons")
    def on_button_pressed(self,e:Button.Pressed)->None:self.dismiss(self.query_one("#tags_in",Input).value) if e.button.id=="st_b" else self.dismiss(None)

class SelectSummaryStyleModal(ModalScreen[Optional[str]]):
    DEFAULT_CSS="""
    SelectSummaryStyleModal {
        align: center middle;
        background: $surface-darken-1;
    }
    SelectSummaryStyleModal > Vertical {
        width: 60;
        height: auto;
        border: thick $primary-lighten-1;
        padding: 1 2;
        background: $surface;
    }
    SelectSummaryStyleModal RadioSet {
        margin: 1 0;
    }
    SelectSummaryStyleModal RadioButton {
        padding: 1 0;
    }
    """
    STYLES=[("overview","Concise Overview (Default)"),("bullets","Key Bullet Points"),("eli5","ELI5 (Simple Explanation)")]
    def compose(self)->ComposeResult:
        with Vertical():yield Label("Select Summary Style",classes="dialog-title");yield RadioSet(*[RadioButton(n,id=i,value=(i=="overview")) for i,n in self.STYLES]);yield Horizontal(Button("Summarize",variant="primary",id="cs_b"),Button("Cancel",id="ccs_b"),classes="modal-buttons")
    def on_button_pressed(self,e:Button.Pressed)->None:
        if e.button.id=="cs_b":rs=self.query_one(RadioSet);self.dismiss(rs.pressed_button.id if rs.pressed_button else "overview")
        else:self.dismiss(None)

class ReadArticleModal(ModalScreen):
    DEFAULT_CSS="""
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
    def __init__(self,t:str,c:str):super().__init__();self.t,self.c=t,c
    def compose(self)->ComposeResult:
        with Vertical():yield Label(self.t,id="art_ttl_lbl");yield VerticalScroll(Markdown(self.c or "_No content._"));yield Horizontal(Button("Close",id="cr_b"),classes="modal-buttons")
    def on_button_pressed(self,e:Button.Pressed)->None:self.dismiss()

class ScrapeURLModal(ModalScreen[tuple[str, str, int] | None]):
    DEFAULT_CSS="""
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
    """
    def __init__(self,lu:str="",ls:str="h2 a",ll:int=0):super().__init__();self.lu,self.ls,self.ll=lu,ls,ll
    def compose(self)->ComposeResult:
        with Vertical():yield Label("Scrape New URL",classes="dialog-title");yield Input(value=self.lu,placeholder="URL",id="s_url_in");yield Input(value=self.ls,placeholder="CSS Selector",id="s_sel_in");yield Input(value=str(self.ll),placeholder="Limit (0=all)",id="s_lim_in",type="integer");yield Horizontal(Button("Scrape",variant="primary",id="sc_b"),Button("Cancel",id="scc_b"),classes="modal-buttons")
    def on_button_pressed(self,e:Button.Pressed)->None:
        if e.button.id=="sc_b":
            u,s,l_s=self.query_one("#s_url_in",Input).value,self.query_one("#s_sel_in",Input).value,self.query_one("#s_lim_in",Input).value
            try:l=int(l_s) if l_s.strip() else 0
            except ValueError:self.app.notify("Invalid limit.",title="Error",severity="error");return
            if not u or not s:self.app.notify("URL & Selector required.",title="Error",severity="error");return
            if hasattr(self.app, 'last_scrape_url'): self.app.last_scrape_url = u
            if hasattr(self.app, 'last_scrape_selector'): self.app.last_scrape_selector = s
            if hasattr(self.app, 'last_scrape_limit'): self.app.last_scrape_limit = l
            self.dismiss((u,s,l))
        else:self.dismiss(None)

class ArticleDetailModal(ModalScreen):
    DEFAULT_CSS="""
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
    def __init__(self,ad:sqlite3.Row,tags:List[str]):super().__init__();self.ad,self.tags=ad,tags
    def compose(self)->ComposeResult:
        ts,senti_str=(", ".join(sorted(self.tags))if self.tags else "_No tags_"),(self.ad['sentiment']or "_N/A_")
        timestamp_val = self.ad['timestamp']
        timestamp_str = timestamp_val.strftime('%Y-%m-%d %H:%M:%S') if isinstance(timestamp_val, datetime) else str(timestamp_val)
        c=f"# {self.ad['title']}\n**ID:** {self.ad['id']}\n**Src URL:** {self.ad['url']}\n**Link:** [{self.ad['link']}]({self.ad['link']})\n**Scraped:** {timestamp_str}\n**Tags:** {ts}\n**Sentiment:** {senti_str}\n---\n## Summary\n"
        c+=f"\n{self.ad['summary']}"if self.ad['summary']else"\n_Not summarized._"
        with VerticalScroll():yield Markdown(c);yield Horizontal(Button("Close",variant="primary",id="d_cls_b"),classes="modal-buttons")
    def on_button_pressed(self,e:Button.Pressed)->None:self.dismiss()

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
            if not url: self.app.notify("Original URL cannot be empty.", title="Input Error", severity="error"); return
            self.dismiss(url)
        else: self.dismiss(None)

class SavedScraperItem(ListItem):
    def __init__(self, scraper_data: sqlite3.Row):
        super().__init__()
        self.scraper_data = scraper_data
        self.prefix = "[P] " if scraper_data['is_preinstalled'] else ""
    def compose(self) -> ComposeResult:
        display_name = f"{self.prefix}{self.scraper_data['name']}"
        sub_text = self.scraper_data['description'] or self.scraper_data['url']
        if len(sub_text) > 60: sub_text = sub_text[:57] + "..."
        with Vertical(): yield Label(display_name, classes="scraper-item-name"); yield Label(f"  ({sub_text})", classes="scraper-item-subtext")

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
                yield Button("Add New",id="add_scraper",variant="success"); yield Button("Edit Selected",id="edit_scraper",variant="primary"); yield Button("Delete Selected",id="delete_scraper",variant="error")
            with Horizontal(classes="buttons-bottom"):
                yield Button("Execute Selected",id="execute_scraper",variant="success"); yield Button("Close",id="close_manage_scrapers")
    async def on_mount(self)->None:await self.load_scrapers()
    async def load_scrapers(self)->None:
        lv=self.query_one(ListView);lv.clear()
        try:
            with get_db_connection() as conn:scrapers=conn.execute("SELECT id,name,url,selector,default_limit,default_tags_csv,description,is_preinstalled FROM saved_scrapers ORDER BY is_preinstalled DESC, name COLLATE NOCASE").fetchall()
            for sd in scrapers:lv.append(SavedScraperItem(sd))
        except Exception as e:logger.error(f"Failed to load saved scrapers: {e}",exc_info=True);self.app.notify("Error loading scrapers.",severity="error")
    async def on_button_pressed(self,e:Button.Pressed)->None:
        lv=self.query_one(ListView);si=lv.highlighted_child
        if e.button.id=="add_scraper":self.dismiss(("add",None))
        elif e.button.id=="edit_scraper":
            if si and isinstance(si,SavedScraperItem):self.dismiss(("edit",si.scraper_data))
            else:self.app.notify("No scraper selected to edit.",severity="warning")
        elif e.button.id=="delete_scraper":
            if si and isinstance(si,SavedScraperItem):
                if si.scraper_data['is_preinstalled']: self.app.notify("Pre-installed profiles cannot be deleted directly. You can edit them.", severity="warning"); return
                self.dismiss(("delete",si.scraper_data['id']))
            else:self.app.notify("No scraper selected to delete.",severity="warning")
        elif e.button.id=="execute_scraper":
            if si and isinstance(si,SavedScraperItem):self.dismiss(("execute",si.scraper_data))
            else:self.app.notify("No scraper selected to execute.",severity="warning")
        elif e.button.id=="close_manage_scrapers":self.dismiss(None)

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
    def __init__(self,sd:Optional[sqlite3.Row]=None):super().__init__();self.sd=sd;self.is_edit=sd is not None
    def compose(self)->ComposeResult:
        title="Edit Scraper Profile" if self.is_edit else "Add New Scraper Profile"
        with VerticalScroll():
            yield Label(title,classes="dialog-title")
            if self.is_edit and self.sd and self.sd['is_preinstalled']: yield Static("[PRE-INSTALLED PROFILE - Edits create a custom copy if name changes]", classes="warning-text")
            yield Label("Name:"); yield Input(value=self.sd['name']if self.is_edit else"",id="scraper_name")
            yield Label("URL (use [USER_PROVIDES_URL] to prompt):"); yield Input(value=self.sd['url']if self.is_edit else"",id="scraper_url")
            yield Label("CSS Selector:"); yield Input(value=self.sd['selector']if self.is_edit else"h2 a",id="scraper_selector")
            yield Label("Default Limit (0 for all):"); yield Input(value=str(self.sd['default_limit'])if self.is_edit else"0",id="scraper_limit",type="integer")
            yield Label("Default Tags (comma-separated, optional):"); yield Input(value=self.sd['default_tags_csv']if self.is_edit and self.sd['default_tags_csv']else"",id="scraper_tags")
            yield Label("Description:"); yield Input(value=self.sd['description']if self.is_edit and self.sd['description']else"",id="scraper_description_input")
            with Horizontal(classes="modal-buttons"):yield Button("Save",variant="primary",id="save_s_cfg");yield Button("Cancel",id="cancel_s_cfg")
    def on_button_pressed(self,e:Button.Pressed)->None:
        if e.button.id=="save_s_cfg":
            data={"name":self.query_one("#scraper_name",Input).value.strip(),"url":self.query_one("#scraper_url",Input).value.strip(),"selector":self.query_one("#scraper_selector",Input).value.strip(),"default_limit":0,"default_tags_csv":self.query_one("#scraper_tags",Input).value.strip(),"description":self.query_one("#scraper_description_input",Input).value.strip(),"is_preinstalled":self.sd['is_preinstalled'] if self.is_edit and self.sd else 0}
            try:data["default_limit"]=int(self.query_one("#scraper_limit",Input).value.strip()or"0")
            except ValueError:self.app.notify("Invalid limit.",severity="error");return
            if not data["name"]or not data["url"]or not data["selector"]:self.app.notify("Name,URL,Selector required.",severity="error");return
            if self.is_edit and self.sd:
                data["id"]=self.sd["id"]
                if self.sd['is_preinstalled'] and data['name'] != self.sd['name']: data['is_preinstalled'] = 0; del data['id']
            self.dismiss(data)
        else:self.dismiss(None)

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
            ps_desc += f"- **{ps_data['name']}**: {ps_data['description']}\n  - *Example/Target URL Hint*: `{ps_data['url']}`\n  - *Suggested Selector*: `{ps_data['selector']}`\n  - *Default Tags*: `{ps_data['default_tags_csv'] or 'None'}`\n\n"
        ht=f"""\
## Keybindings & Help (v1.0RC)
| Key      | Action              | Description                                        |
|----------|---------------------|----------------------------------------------------|
| `UP`/`DN`| Navigate Table      | Move selection in articles list.                   |
| `ENTER`  | View Details        | Show full details of selected article.             |
| `s`      | Summarize           | LLM summary for selected (choose style).           |
| `ctrl+k` | Sentiment Analysis  | LLM sentiment for selected article.                |
| `d`/`del`| Delete Selected     | Delete selected article (confirm).                 |
| `ctrl+r` | Read Article        | Fetch & display full content of selected.          |
| `ctrl+t` | Manage Tags         | Add/remove tags for selected.                      |
| `r`      | Refresh List        | Reload articles from DB.                           |
| `ctrl+s` | Cycle Sort          | Change article list sorting.                       |
| `ctrl+p` | Scraper Profiles    | Manage & execute saved/pre-installed scrapers.     |
| `ctrl+n` | New Scrape          | Open dialog to scrape new URL (generic).           |
| `ctrl+e` | Export CSV          | Export current view to CSV.                        |
| `ctrl+x` | Clear DB            | Delete ALL articles (confirm).                     |
| `ctrl+l` | Toggle Theme        | Switch between Light/Dark mode.                    |
| `F1`/`ctrl+h`| Help           | Show/hide this help screen.                        |
| `q`/`ctrl+c`| Quit            | Exit application.                                  |

**Filtering:** Use input boxes for Title, Source URL, Date (YYYY-MM-DD), Tags (comma-sep, AND), Sentiment (Positive/Negative/Neutral).
{ps_desc}"""
        with VerticalScroll(): yield Markdown(ht); yield Horizontal(Button("Close",id="ch_b"),classes="modal-buttons")
    def on_button_pressed(self,e:Button.Pressed)->None:self.dismiss()
    def action_dismiss_screen(self)->None:self.dismiss()

class StatusBar(Static):
    total_articles=reactive(0);selected_id=reactive[Optional[int]](None);filter_status=reactive("");sort_status=reactive("");current_theme=reactive("Dark")
    def render(self)->str:parts=[f"Total: {self.total_articles}",f"Theme: {self.current_theme}"];(parts.append(f"Sel ID: {self.selected_id}")if self.selected_id is not None else None);(parts.append(f"Filter: {self.filter_status}")if self.filter_status else None);(parts.append(f"Sort: {self.sort_status}")if self.sort_status else None);return " | ".join(parts)

class WebScraperApp(App[None]):
    CSS_PATH="web_scraper_tui_v1.0RC.tcss"
    BINDINGS=[
        Binding("q,ctrl+c","quit","Quit",priority=True),Binding("r","refresh_data","Refresh"),
        Binding("s","summarize_selected","Summarize"),Binding("ctrl+k","sentiment_analysis_selected","Sentiment"),
        Binding("d,delete","delete_selected","Delete"),Binding("ctrl+r","read_article","Read Full"),
        Binding("ctrl+t","manage_tags","Tags"),Binding("ctrl+s","cycle_sort_order","Sort"),
        Binding("ctrl+p","manage_saved_scrapers","Profiles"),Binding("ctrl+n","scrape_new","New Scrape"),
        Binding("ctrl+e","export_csv","Export"),Binding("ctrl+x","clear_database","Clear DB"),
        Binding("ctrl+l","toggle_dark_mode","Theme"),Binding("f1,ctrl+h","toggle_help","Help")
    ]
    dark = reactive(True, layout=True)
    selected_row_id:reactive[int|None]=reactive(None);db_init_ok:bool=False
    last_scrape_url,last_scrape_selector,last_scrape_limit="","h2 a",0
    title_filter,url_filter,date_filter,tags_filter,sentiment_filter=reactive(""),reactive(""),reactive(""),reactive(""),reactive("")
    SORT_OPTIONS:List[Tuple[str,str]]=[("timestamp DESC","Date Newest"),("timestamp ASC","Date Oldest"),("title COLLATE NOCASE ASC","Title A-Z"),("title COLLATE NOCASE DESC","Title Z-A"),("sentiment ASC, timestamp DESC","Sentiment"),("id ASC","ID Asc"),("id DESC","ID Desc"),("url COLLATE NOCASE ASC","Src URL A-Z"),("url COLLATE NOCASE DESC","Src URL Z-A")]
    current_sort_index=reactive(0)
    def __init__(self):super().__init__();self.db_init_ok=init_db()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, name="Web Scraper TUI v1.0RC")
        with Container(id="app-grid"):
            with Vertical(id="filter-container"):
                yield Label("Filters:")
                with Grid(id="filter-inputs-grid"):
                    yield Input(placeholder="Title...", id="title_filter_input", classes="filter-input")
                    yield Input(placeholder="Source URL...", id="url_filter_input", classes="filter-input")
                    yield Input(placeholder="Date (YYYY-MM-DD)...", id="date_filter_input", classes="filter-input")
                    yield Input(placeholder="Tags (comma-sep)...", id="tags_filter_input", classes="filter-input")
                    yield Input(placeholder="Sentiment (Pos/Neg/Neu)...", id="sentiment_filter_input", classes="filter-input")
            yield LoadingIndicator(id="loading_indicator", classes="hidden")
            yield DataTable(id="article_table", cursor_type="row", zebra_stripes=True)
            yield StatusBar(id="status_bar")
        yield Footer()
        # yield Notifications() # Intentionally removed as App handles this

    async def on_mount(self)->None:
        sbar=self.query_one(StatusBar);sbar.current_theme="Dark" if self.dark else "Light"
        if not self.db_init_ok:self.notify("CRITICAL: DB init failed!",title="DB Error",severity="error",timeout=0);return
        tbl=self.query_one(DataTable);tbl.add_columns("ID","S","Sentiment","Title","Source URL","Tags","Scraped At");sbar.sort_status=self.SORT_OPTIONS[self.current_sort_index][1]
        await self.refresh_article_table();self.query_one("#title_filter_input",Input).focus()

    async def refresh_article_table(self)->None:
        tbl=self.query_one(DataTable);cur_row=tbl.cursor_row;tbl.clear();s_col,s_disp=self.SORT_OPTIONS[self.current_sort_index];self.query_one(StatusBar).sort_status=s_disp
        bq="SELECT sd.id,sd.title,sd.url,sd.timestamp,sd.summary IS NOT NULL as has_s,sd.link,sd.sentiment,GROUP_CONCAT(DISTINCT t.name) as tags_c FROM scraped_data sd LEFT JOIN article_tags at ON sd.id=at.article_id LEFT JOIN tags t ON at.tag_id=t.id"
        conds,params,fdesc=[],{},[]
        if self.title_filter:conds.append("sd.title LIKE :tf");params["tf"]=f"%{self.title_filter}%";fdesc.append(f"Title~'{self.title_filter}'")
        if self.url_filter:conds.append("sd.url LIKE :uf");params["uf"]=f"%{self.url_filter}%";fdesc.append(f"URL~'{self.url_filter}'")
        if self.date_filter:
            try:datetime.strptime(self.date_filter,"%Y-%m-%d");conds.append("date(sd.timestamp)=:df");params["df"]=self.date_filter;fdesc.append(f"Date='{self.date_filter}'")
            except ValueError:
                if self.date_filter:self.notify("Invalid date format.",title="Filter Error",severity="warning")
        if self.tags_filter:
            tfs=[t.strip().lower() for t in self.tags_filter.split(',') if t.strip()]
            if tfs:
                for i,tn in enumerate(tfs):pn=f"tgf_{i}";conds.append(f"sd.id IN (SELECT at_s.article_id FROM article_tags at_s JOIN tags t_s ON at_s.tag_id=t_s.id WHERE t_s.name=:{pn})");params[pn]=tn
                fdesc.append(f"Tags='{', '.join(tfs)}'")
        if self.sentiment_filter:
            sval=self.sentiment_filter.strip().capitalize()
            if sval in ["Positive","Negative","Neutral"]:conds.append("sd.sentiment LIKE :sf");params["sf"]=f"%{sval}%";fdesc.append(f"Sentiment='{sval}'")
            elif sval:self.notify("Sentiment filter: Positive, Negative, or Neutral.",title="Filter Info",severity="info")
        if conds:bq+=" WHERE "+" AND ".join(conds)
        bq+=" GROUP BY sd.id ORDER BY "+s_col
        self.query_one(StatusBar).filter_status=", ".join(fdesc) if fdesc else "None"
        try:
            with get_db_connection() as conn:rows=conn.execute(bq,params).fetchall()
            for r_d in rows:
                s_ind="✓" if r_d["has_s"] else " ";tags_d=(", ".join(sorted(r_d["tags_c"].split(','))) if r_d["tags_c"] else "");senti_d=r_d["sentiment"] or "-"
                timestamp_val = r_d["timestamp"];timestamp_str = timestamp_val.strftime('%Y-%m-%d %H:%M:%S') if isinstance(timestamp_val, datetime) else str(timestamp_val)
                tbl.add_row(r_d["id"],s_ind,senti_d,r_d["title"],r_d["url"],tags_d,timestamp_str,key=str(r_d["id"]),meta={'link':r_d['link'],'has_s':bool(r_d['has_s']),'tags':r_d["tags_c"] or ""})
            self.query_one(StatusBar).total_articles=len(rows)
            if cur_row is not None and cur_row<len(rows):tbl.cursor_row=cur_row
            elif len(rows)>0:tbl.cursor_row=0
            if not rows and any([self.title_filter,self.url_filter,self.date_filter,self.tags_filter,self.sentiment_filter]):self.notify("No articles match filters.",title="Filter Info",severity="info",timeout=3)
            elif not rows:self.notify("No articles in DB.",title="Info",severity="info",timeout=3)
        except Exception as e:logger.error(f"Refresh err: {e}",exc_info=True);self.notify(f"Refresh err: {e}",title="DB Error",severity="error");self.query_one(StatusBar).total_articles=0
    async def on_input_changed(self,e:Input.Changed)->None:
        if e.input.id=="title_filter_input":self.title_filter=e.value
        elif e.input.id=="url_filter_input":self.url_filter=e.value
        elif e.input.id=="date_filter_input":self.date_filter=e.value
        elif e.input.id=="tags_filter_input":self.tags_filter=e.value
        elif e.input.id=="sentiment_filter_input":self.sentiment_filter=e.value
        await self.refresh_article_table()
    def on_data_table_row_selected(self,e:DataTable.RowSelected)->None:self.selected_row_id=int(e.row_key.value)if e.row_key else None;self.query_one(StatusBar).selected_id=self.selected_row_id;logger.debug(f"Row selected, ID: {self.selected_row_id}")
    def _toggle_loading(self,show:bool)->None:self.query_one(LoadingIndicator).remove_class("hidden")if show else self.query_one(LoadingIndicator).add_class("hidden")
    async def action_refresh_data(self)->None:self.notify("Refreshing...",title="Data Update",severity="info",timeout=2);await self.refresh_article_table()
    async def action_toggle_dark_mode(self)->None:self.dark=not self.dark;self.query_one(StatusBar).current_theme="Dark" if self.dark else "Light"
    async def action_view_details(self)->None:
        if self.selected_row_id is None:self.notify("No row selected.",title="Info",severity="warning");return
        try:
            with get_db_connection() as conn:ad=conn.execute("SELECT * FROM scraped_data WHERE id=?",(self.selected_row_id,)).fetchone();tags=get_tags_for_article(conn,self.selected_row_id)
            if ad:self.push_screen(ArticleDetailModal(ad,tags))
            else:self.notify(f"Not found: ID {self.selected_row_id}.",title="Error",severity="error")
        except Exception as e:logger.error(f"Err details ID {self.selected_row_id}: {e}",exc_info=True);self.notify(f"Err details: {e}",title="Error",severity="error")

    async def _summarize_worker(self,eid:int,link:str,style:str)->None:
        self._toggle_loading(True)
        self.notify(f"Starting '{style}' summary ID {eid}...",title="Summarizing",severity="info",timeout=3)
        try:
            txt=fetch_article_content(link,False)
            if not txt:self.notify(f"No content for ID {eid}.",title="Summ Error",severity="error"); self._toggle_loading(False); return
            summ=get_summary_from_llm(txt,style)
            if summ:
                def _update_summary_blocking():
                    with get_db_connection() as conn_blocking:
                        conn_blocking.execute("UPDATE scraped_data SET summary=? WHERE id=?",(summ,eid));conn_blocking.commit()
                _update_summary_blocking()
                self.notify(f"Summary for ID {eid} done.",title="Success",severity="info");await self.refresh_article_table()
            else:self.notify(f"No summary for ID {eid}.",title="Summ Error",severity="error")
        except Exception as e:logger.error(f"Err summ ID {eid}: {e}",exc_info=True);self.notify(f"Err summ ID {eid}: {e}",title="Error",severity="error")
        finally:self._toggle_loading(False)
    async def action_summarize_selected(self)->None:
        if self.selected_row_id is None:self.notify("No row selected.",title="Info",severity="warning");return
        meta=self.query_one(DataTable).get_row_meta(str(self.selected_row_id))
        if not meta or'link'not in meta:self.notify(f"No link for ID {self.selected_row_id}.",title="Error",severity="error");return
        if meta.get('has_s'):
            if not await self.app.push_screen_wait(ConfirmModal(f"ID {self.selected_row_id} has summary. Re-summarize?")):self.notify("Cancelled.",title="Info",severity="info");return
        style=await self.app.push_screen_wait(SelectSummaryStyleModal())
        if style is None:self.notify("Cancelled (no style).",title="Info",severity="info");return
        worker_with_args = functools.partial(self._summarize_worker, self.selected_row_id, meta['link'], style)
        self.run_worker(worker_with_args, group="llm", exclusive=True)

    async def _sentiment_worker(self,eid:int,link:str)->None:
        self._toggle_loading(True)
        self.notify(f"Analyzing sentiment for ID {eid}...",title="Sentiment Analysis",severity="info",timeout=3)
        try:
            def _get_summary_blocking():
                with get_db_connection() as conn_blocking:
                    return conn_blocking.execute("SELECT summary FROM scraped_data WHERE id=?",(eid,)).fetchone()
            ad = _get_summary_blocking()
            txt_to_analyze=ad['summary']if ad and ad['summary']else fetch_article_content(link,False)
            if not txt_to_analyze:self.notify(f"No content to analyze for ID {eid}.",title="Sentiment Error",severity="error"); self._toggle_loading(False); return
            s_res=get_sentiment_from_llm(txt_to_analyze)
            if s_res:
                def _update_sentiment_blocking():
                    with get_db_connection() as conn_blocking:
                        conn_blocking.execute("UPDATE scraped_data SET sentiment=? WHERE id=?",(s_res,eid));conn_blocking.commit()
                _update_sentiment_blocking()
                self.notify(f"Sentiment for ID {eid}: {s_res}.",title="Sentiment Updated",severity="info");await self.refresh_article_table()
            else:self.notify(f"Failed to get sentiment for ID {eid}.",title="Sentiment Error",severity="error")
        except Exception as e:logger.error(f"Err sentiment worker ID {eid}: {e}",exc_info=True);self.notify(f"Err analyzing sentiment ID {eid}: {e}",title="Error",severity="error")
        finally:self._toggle_loading(False)
    async def action_sentiment_analysis_selected(self)->None:
        if self.selected_row_id is None:self.notify("No row selected for sentiment.",title="Info",severity="warning");return
        meta=self.query_one(DataTable).get_row_meta(str(self.selected_row_id))
        if not meta or'link'not in meta:self.notify(f"No link for ID {self.selected_row_id}.",title="Error",severity="error");return
        worker_with_args = functools.partial(self._sentiment_worker, self.selected_row_id, meta['link'])
        self.run_worker(worker_with_args, group="llm", exclusive=True)

    async def _scrape_url_worker(self,url:str,selector:str,limit:int,default_tags_csv:Optional[str]=None)->None:
        self._toggle_loading(True)
        self.notify(f"Scraping {url}...",title="Scraping",severity="info",timeout=3)
        try:
            inserted,skipped,scraped_url,inserted_ids = scrape_url_action(url,selector,limit)
            self.last_scrape_url=scraped_url
            if inserted_ids and default_tags_csv:
                logger.info(f"Applying default tags '{default_tags_csv}' to {len(inserted_ids)} new articles.")
                def _apply_tags_blocking():
                    with get_db_connection() as conn_blocking:
                        for aid in inserted_ids:_update_tags_for_article_blocking(aid,default_tags_csv)
                _apply_tags_blocking()
                self.notify(f"Applied default tags to {len(inserted_ids)} new articles.",title="Tags Applied",severity="info")
            self.notify(f"Scrape of {url} done. New: {inserted}, Skipped: {skipped}.",title="Scrape Finished",severity="info")
            await self.refresh_article_table()
        except Exception as e:logger.error(f"Err scrape worker {url}: {e}",exc_info=True);self.notify(f"Err scraping {url}: {e}",title="Scrape Error",severity="error")
        finally:self._toggle_loading(False)
    async def _handle_scrape_new_result(self,result:tuple[str,str,int]|None,default_tags_csv:Optional[str]=None)->None:
        if result:
            url,selector,limit=result
            worker_with_args = functools.partial(self._scrape_url_worker, url, selector, limit, default_tags_csv)
            self.run_worker(worker_with_args, group="scraping",exclusive=True)
    async def action_scrape_new(self)->None:await self.app.push_screen(ScrapeURLModal(self.last_scrape_url,self.last_scrape_selector,self.last_scrape_limit),self._handle_scrape_new_result)
    async def action_delete_selected(self)->None:
        if self.selected_row_id is None:self.notify("No row selected.",title="Info",severity="warning");return
        if not await self.app.push_screen_wait(ConfirmModal(f"Delete article ID {self.selected_row_id}?")):self.notify("Cancelled.",title="Info",severity="info");return
        try:
            def _delete_blocking():
                with get_db_connection() as conn_blocking:
                    cur=conn_blocking.execute("DELETE FROM scraped_data WHERE id=?",(self.selected_row_id,));conn_blocking.commit()
                    return cur.rowcount
            rowcount = _delete_blocking()
            if rowcount >0:self.notify(f"Deleted ID {self.selected_row_id}.",title="Success",severity="info");self.selected_row_id=None;self.query_one(StatusBar).selected_id=None;await self.refresh_article_table()
            else:self.notify(f"Not found ID {self.selected_row_id}.",title="Warning",severity="warning")
        except Exception as e:logger.error(f"Err del ID {self.selected_row_id}: {e}",exc_info=True);self.notify(f"Err del ID {self.selected_row_id}: {e}",title="Error",severity="error")
    async def action_clear_database(self)->None:
        if not await self.app.push_screen_wait(ConfirmModal("Delete ALL articles from DB? Irreversible!",confirm_text="Yes, Delete All")):self.notify("Clear DB cancelled.",title="Info",severity="info");return
        self._toggle_loading(True)
        try:
            def _clear_db_blocking():
                with get_db_connection() as conn_blocking:conn_blocking.executescript("DELETE FROM article_tags;DELETE FROM tags;DELETE FROM scraped_data;DELETE FROM saved_scrapers WHERE is_preinstalled=0;DELETE FROM sqlite_sequence WHERE name IN ('scraped_data','tags','saved_scrapers');");conn_blocking.commit()
            _clear_db_blocking()
            self.notify("User data cleared (pre-installed scrapers kept).",title="DB Cleared",severity="info");logger.info("DB cleared.");self.selected_row_id=None;self.query_one(StatusBar).selected_id=None;await self.refresh_article_table()
        except Exception as e:logger.error(f"Err clearing DB: {e}",exc_info=True);self.notify(f"Err clearing DB: {e}",title="DB Error",severity="error")
        finally:self._toggle_loading(False)
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
        if self.selected_row_id is None:self.notify("No row selected.",title="Info",severity="warning");return
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
        dfn=f"scraped_articles_{datetime.now():%Y%m%d_%H%M%S}.csv";fn=await self.app.push_screen_wait(FilenameModal(default_filename=dfn))
        if fn:
            worker_with_args = functools.partial(self._export_csv_worker, fn)
            self.run_worker(worker_with_args, group="exporting", exclusive=True)

    async def _read_article_worker(self,eid:int,link:str,title:str)->None:
        self._toggle_loading(True);self.notify(f"Fetching '{title[:30]}...' (ID {eid})",title="Reading Article",severity="info")
        try:
            content=fetch_article_content(link,True)
            if content is not None:await self.app.push_screen(ReadArticleModal(title,content))
            else:self.notify(f"No content for article ID {eid}.",title="Read Error",severity="error")
        except Exception as e:logger.error(f"Err read worker ID {eid}: {e}",exc_info=True);self.notify(f"Err reading ID {eid}: {e}",title="Read Error",severity="error")
        finally:self._toggle_loading(False)
    async def action_read_article(self)->None:
        if self.selected_row_id is None:self.notify("No row selected.",title="Info",severity="warning");return
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
            sd=await self.app.push_screen_wait(AddEditScraperModal())
            if sd:
                try:
                    def _add_scraper_blocking():
                        with get_db_connection() as conn_blocking:conn_blocking.execute("INSERT INTO saved_scrapers (name,url,selector,default_limit,default_tags_csv,description,is_preinstalled) VALUES (:name,:url,:selector,:default_limit,:default_tags_csv,:description,0)",sd);conn_blocking.commit()
                    _add_scraper_blocking()
                    self.notify(f"Scraper '{sd['name']}' added.",title="Success",severity="info")
                except sqlite3.IntegrityError:self.notify(f"Scraper name '{sd['name']}' already exists.",title="Error",severity="error")
                except Exception as e:logger.error(f"Err adding scraper: {e}",exc_info=True);self.notify(f"Error adding scraper: {e}",severity="error")
        elif action=="edit" and data:
            sd=await self.app.push_screen_wait(AddEditScraperModal(scraper_data=data))
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
        elif action=="delete" and data: 
            sid_to_del=data
            try:
                def _get_scraper_name_blocking():
                    with get_db_connection() as conn_blocking:
                        return conn_blocking.execute("SELECT name,is_preinstalled FROM saved_scrapers WHERE id=?",(sid_to_del,)).fetchone()
                s_to_del = _get_scraper_name_blocking()
                if not s_to_del:self.notify("Scraper not found.",severity="error");return
                if s_to_del['is_preinstalled']: self.notify("Pre-installed profiles cannot be deleted. Edit them to create custom versions.", severity="warning"); return
                confirmed=await self.app.push_screen_wait(ConfirmModal(f"Delete saved scraper '{s_to_del['name']}'?"))
                if confirmed:
                    def _delete_scraper_blocking():
                        with get_db_connection() as conn_blocking:conn_blocking.execute("DELETE FROM saved_scrapers WHERE id=?",(sid_to_del,));conn_blocking.commit()
                    _delete_scraper_blocking()
                    self.notify(f"Scraper '{s_to_del['name']}' deleted.",title="Success",severity="info")
            except Exception as e:logger.error(f"Err deleting scraper: {e}",exc_info=True);self.notify(f"Error deleting scraper: {e}",severity="error")
        elif action=="execute" and data: 
            scrape_target_url = data['url']
            final_url_to_scrape = scrape_target_url
            if scrape_target_url == "[ARCHIVE_WAYBACK_URL]":
                original_url = await self.app.push_screen_wait(OriginalURLModal())
                if not original_url: self.notify("Wayback scrape cancelled.", title="Info", severity="information"); return
                final_url_to_scrape = f"https://web.archive.org/web/timestamp_latest/{quote_plus(original_url)}"
                self.notify(f"Attempting to fetch latest archive for: {original_url}", title="Archive Fetch", severity="information")
            elif scrape_target_url == "[USER_PROVIDES_URL]":
                self.last_scrape_url = "" 
                self.last_scrape_selector = data['selector']
                self.last_scrape_limit = data['default_limit']
                self.notify(f"Profile '{data['name']}' loaded. Please provide target URL.", title="Scraper Profile", severity="information")
                callback_with_tags = functools.partial(self._handle_scrape_new_result, default_tags_csv=data['default_tags_csv'])
                await self.app.push_screen(ScrapeURLModal("", data['selector'], data['default_limit']), callback_with_tags)
                return 
            self.last_scrape_url = final_url_to_scrape
            self.last_scrape_selector = data['selector']
            self.last_scrape_limit = data['default_limit']
            default_tags = data['default_tags_csv']
            self.notify(f"Executing scraper profile '{data['name']}'. Parameters loaded.", title="Scraper Profile", severity="information")
            callback_with_tags = functools.partial(self._handle_scrape_new_result, default_tags_csv=default_tags)
            await self.app.push_screen(ScrapeURLModal(final_url_to_scrape, data['selector'], data['default_limit']), callback_with_tags)

    async def action_manage_saved_scrapers(self)->None:await self.app.push_screen(ManageScrapersModal(),self._handle_manage_scrapers_result)

def print_startup_banner():
    """Display welcome banner when starting the application."""
    banner = """
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                   ║
║  ██╗    ██╗███████╗██████╗ ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗     ║
║  ██║    ██║██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝     ║
║  ██║ █╗ ██║█████╗  ██████╔╝███████╗██║     ██████╔╝███████║██████╔╝█████╗       ║
║  ██║███╗██║██╔══╝  ██╔══██╗╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝       ║
║  ╚███╔███╔╝███████╗██████╔╝███████║╚██████╗██║  ██║██║  ██║██║     ███████╗     ║
║   ╚══╝╚══╝ ╚══════╝╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝     ║
║                                                                                   ║
║                           ████████╗██╗   ██╗██╗                                 ║
║                           ╚══██╔══╝██║   ██║██║                                 ║
║                              ██║   ██║   ██║██║                                 ║
║                              ██║   ██║   ██║██║                                 ║
║                              ██║   ╚██████╔╝██║                                 ║
║                              ╚═╝    ╚═════╝ ╚═╝                                 ║
║                                                                                   ║
║                             Text User Interface Web Scraper                      ║
║                                        Version 1.0                               ║
║                                                                                   ║
║   ╔═══════════════════════════════════════════════════════════════════════════╗   ║
║   ║                              Features                                    ║   ║
║   ║                                                                           ║   ║
║   ║  • Interactive terminal-based web scraping interface                     ║   ║
║   ║  • Pre-configured scraper profiles for popular websites                  ║   ║
║   ║  • Custom scraper creation with CSS selectors                            ║   ║
║   ║  • SQLite database for persistent article storage                        ║   ║
║   ║  • AI-powered summarization and sentiment analysis                       ║   ║
║   ║  • Advanced filtering and sorting capabilities                           ║   ║
║   ║  • CSV export functionality                                              ║   ║
║   ║  • Tag-based article organization                                        ║   ║
║   ║                                                                           ║   ║
║   ║  Navigation: Use arrow keys, Tab, Enter, and Esc                         ║   ║
║   ║  Press 'q' to quit, 'h' for help, 'ctrl+s' to scrape                    ║   ║
║   ║                                                                           ║   ║
║   ╚═══════════════════════════════════════════════════════════════════════════╝   ║
║                                                                                   ║
║                     Starting application... Please wait...                       ║
║                                                                                   ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_shutdown_banner():
    """Display farewell banner when exiting the application."""
    banner = """
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                   ║
║                          Thank you for using WebScrape-TUI!                      ║
║                                                                                   ║
║                              ╔═══════════════════════╗                           ║
║                              ║     Session Summary   ║                           ║
║                              ║                       ║                           ║
║                              ║  Application closed   ║                           ║
║                              ║  gracefully. All data ║                           ║
║                              ║  has been saved to    ║                           ║
║                              ║  the local database.  ║                           ║
║                              ║                       ║                           ║
║                              ║  Database Location:   ║                           ║
║                              ║  scraped_data_tui_    ║                           ║
║                              ║  v1.0RC.db            ║                           ║
║                              ║                       ║                           ║
║                              ║  Logs saved to:       ║                           ║
║                              ║  scraper_tui_v1.0RC   ║                           ║
║                              ║  .log                 ║                           ║
║                              ╚═══════════════════════╝                           ║
║                                                                                   ║
║   ██████╗  ██████╗  ██████╗ ██████╗ ██████╗ ██╗   ██╗███████╗██╗                ║
║  ██╔════╝ ██╔═══██╗██╔═══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝██╔════╝██║                ║
║  ██║  ███╗██║   ██║██║   ██║██║  ██║██████╔╝ ╚████╔╝ █████╗  ██║                ║
║  ██║   ██║██║   ██║██║   ██║██║  ██║██╔══██╗  ╚██╔╝  ██╔══╝  ╚═╝                ║
║  ╚██████╔╝╚██████╔╝╚██████╔╝██████╔╝██████╔╝   ██║   ███████╗██╗                ║
║   ╚═════╝  ╚═════╝  ╚═════╝ ╚═════╝ ╚═════╝    ╚═╝   ╚══════╝╚═╝                ║
║                                                                                   ║
║           Visit our GitHub repository for updates and documentation:             ║
║                    https://github.com/doublegate/WebScrape-TUI                   ║
║                                                                                   ║
║                        Happy scraping! Come back soon! 🚀                       ║
║                                                                                   ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

if __name__=="__main__":
    import time
    
    print_startup_banner()
    time.sleep(2)  # 2-second pause before starting the application
    
    css_file_content="""
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
    css_file=Path("web_scraper_tui_v1.0RC.tcss")
    if not css_file.exists():
        with open(css_file,"w",encoding="utf-8") as f:f.write(css_file_content)
        logger.info(f"Created CSS file: {css_file.resolve()}")
    try:
        app = WebScraperApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user.")
    finally:
        print_shutdown_banner()
