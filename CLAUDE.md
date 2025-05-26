# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based Text User Interface (TUI) application for web scraping built with the Textual framework. The application allows users to scrape websites, store articles in a SQLite database, apply AI-powered summarization and sentiment analysis using Google's Gemini API, and manage the scraped data through an interactive terminal interface.

## Architecture

### Core Components

- **Main Application**: `scrapetui.py` - Single-file application containing the entire TUI app
- **Database**: SQLite database (`scraped_data_tui_v5.db`) with tables for articles, tags, and scraper profiles
- **Styling**: `web_scraper_tui_v5.tcss` - Textual CSS styling file
- **Configuration**: `.env` file for API keys (currently empty)

### Key Architecture Patterns

- **Textual Framework**: Uses Textual's reactive programming model with Screen/Modal patterns
- **Worker Pattern**: Async workers handle long-running operations (scraping, AI calls) without blocking UI
- **Database Context Management**: Uses `get_db_connection()` with context managers for safe DB operations
- **Modal Dialogs**: Extensive use of modal screens for user input and data display

### Data Flow

1. User configures scraper profiles or manually enters URLs/selectors
2. Scraping worker fetches content using BeautifulSoup and stores in SQLite
3. Optional AI processing (Gemini API) for summarization and sentiment analysis
4. Data display through reactive DataTable with filtering and sorting
5. Export functionality to CSV format

## Common Development Commands

### Running the Application
```bash
python3 scrapetui.py
```

### Dependencies
The application requires these Python packages:
- `textual` - TUI framework
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `lxml` - XML/HTML parser (used by BeautifulSoup)

Install with:
```bash
pip install textual requests beautifulsoup4 lxml
```

### Database Management
- Database is auto-created on first run
- Schema includes: `scraped_data`, `tags`, `article_tags`, `saved_scrapers`
- Database file: `scraped_data_tui_v5.db`

### API Configuration
- Gemini API key should be set in the `GEMINI_API_KEY` constant in `scrapetui.py`
- Currently uses placeholder empty string - requires manual configuration

## Code Structure Guidelines

### Threading and Async Patterns
- Use `self.run_worker()` for long-running operations
- Background tasks use `functools.partial()` for parameter passing
- All database operations in workers use blocking functions wrapped with `await self.run_in_thread()`

### Modal Screen Pattern
- All user input uses modal screens (e.g., `ScrapeURLModal`, `ManageTagsModal`)
- Modals return typed results via `ModalScreen[ReturnType]`
- Result handling through callback functions passed to `push_screen()`

### Database Access Pattern
```python
def _blocking_db_operation():
    with get_db_connection() as conn:
        # DB operations here
        conn.commit()
        return result

result = await self.run_in_thread(_blocking_db_operation)
```

### Reactive UI Updates
- Use reactive variables for auto-updating UI components
- StatusBar shows current state via reactive properties
- DataTable refreshes trigger full data reload

## Key Features

- **Pre-installed Scrapers**: 10 built-in scraper profiles for common sites
- **Custom Scrapers**: User-defined scraper profiles with URL patterns and selectors
- **AI Integration**: Gemini API for summarization (3 styles) and sentiment analysis
- **Filtering**: Multi-field filtering (title, URL, date, tags, sentiment)
- **Sorting**: 9 different sort options for article list
- **Export**: CSV export with current filters applied
- **Article Reading**: Full-text article fetching and display
- **Tag Management**: Comma-separated tagging system

## File Locations

- Main application: `scrapetui.py`
- CSS styling: `web_scraper_tui_v5.tcss`
- Database: `scraped_data_tui_v5.db`
- Logs: `scraper_tui_v5.log`
- Config: `.env` (currently empty)