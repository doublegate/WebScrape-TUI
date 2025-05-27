# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based Text User Interface (TUI) application for web scraping built with the Textual framework. The application allows users to scrape websites, store articles in a SQLite database, apply AI-powered summarization and sentiment analysis using Google's Gemini API, and manage the scraped data through an interactive terminal interface.

## Architecture

### Core Components

- **Main Application**: `scrapetui.py` - Single-file application containing the entire TUI app
- **Database**: SQLite database (`scraped_data_tui_v1.0.db`) with tables for articles, tags, and scraper profiles
- **Styling**: `web_scraper_tui_v1.0.tcss` - Textual CSS styling file
- **Configuration**: `.env` file for API keys (currently empty)

### Key Architecture Patterns

- **Textual Framework**: Uses Textual's reactive programming model with Screen/Modal patterns
- **Worker Pattern**: Async workers handle long-running operations (scraping, AI calls) without blocking UI
- **Database Context Management**: Uses `get_db_connection()` with context managers for safe DB operations
- **Modal Dialogs**: Extensive use of modal screens for user input and data display
- **Callback-based Modals**: Sequential modal dialogs using callback functions to avoid worker context issues
- **Separated UI**: Main screen shows DataTable, filter screen accessible via Ctrl+F modal dialog
- **Row Metadata Storage**: Custom metadata dictionary stores row-specific data (links, status) keyed by row ID
- **Visual Selection Indicators**: Selected rows display asterisk prefix (*ID) for clear user feedback

### Data Flow

1. User configures scraper profiles or manually enters URLs/selectors
2. Scraping worker fetches content using BeautifulSoup and stores in SQLite
3. Optional AI processing (Gemini API) for summarization and sentiment analysis
4. Data display through reactive DataTable with full-screen visibility
5. Filtering via dedicated modal screen (Ctrl+F) with real-time updates
6. Row selection via cursor navigation with visual indicators and fallback detection
7. Sequential modal workflows using callback chains for complex user interactions
8. Export functionality to CSV format with applied filters

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
- Database file: `scraped_data_tui_v1.0.db`

### API Configuration
- Gemini API key should be set in the `.env` file using `GEMINI_API_KEY` variable
- Environment variables are loaded via `load_env_file()` function
- Uses proper environment variable management for security

## Code Structure Guidelines

### Code Quality Standards (Updated v1.0.1)
- **PEP 8 Compliance**: Follow Python coding standards for readability
- **Import Optimization**: Remove unused imports to reduce memory footprint
- **Error Handling**: Use proper exception handling with multi-line formatting
- **Database Connections**: Use context managers for safe resource management
- **Multi-line Strings**: Format long strings for better readability
- **Function Signatures**: Break long parameter lists across multiple lines

### Threading and Async Patterns
- Use `self.run_worker()` for long-running operations
- Background tasks use `functools.partial()` for parameter passing
- All database operations in workers use blocking functions wrapped with `await self.run_in_thread()`
- Avoid unused variables in database connection contexts

### Modal Screen Pattern
- All user input uses modal screens (e.g., `ScrapeURLModal`, `ManageTagsModal`, `FilterScreen`, `ConfirmModal`)
- Modals return typed results via `ModalScreen[ReturnType]`
- Result handling through callback functions passed to `push_screen()`
- Filter screen preserves current filter values and applies changes reactively
- Sequential modal dialogs use callback chains to avoid Textual API worker context requirements
- Confirmation dialogs use proper CSS layout with Horizontal containers and explicit sizing

### Database Access Pattern
```python
def _blocking_db_operation():
    with get_db_connection() as conn:
        # DB operations here
        conn.commit()
        return result

result = await self.run_in_thread(_blocking_db_operation)
```

### Sequential Modal Dialog Pattern
```python
# Callback-based sequential modals to avoid worker context issues
class WebScraperApp(App[None]):
    def __init__(self):
        super().__init__()
        self._summarize_context = {}  # Store state between modals
    
    async def action_summarize_selected(self) -> None:
        # Store context for callback chain
        self._summarize_context = {'row_id': selected_id, 'link': url}
        
        if has_existing_summary:
            def handle_confirm(confirmed):
                if confirmed:
                    self._show_summary_style_selector()
                else:
                    self.notify("Cancelled.")
            self.push_screen(ConfirmModal("Re-summarize?"), handle_confirm)
        else:
            self._show_summary_style_selector()
    
    def _show_summary_style_selector(self):
        def handle_style(style):
            if style:
                context = self._summarize_context
                worker = functools.partial(self._worker, context['row_id'], style)
                self.run_worker(worker)
        self.push_screen(SelectStyleModal(), handle_style)
```

### Visual Selection Pattern
```python
# Add visual indicators to selected rows
for row_data in rows:
    row_id = row_data["id"]
    # Add asterisk to selected row's ID column
    id_display = f"*{row_id}" if self.selected_row_id == row_id else str(row_id)
    table.add_row(id_display, *other_columns, key=str(row_id))

# Refresh table after selection to show indicator
async def action_select_row(self) -> None:
    current_id = self._get_current_row_id()
    if current_id:
        self.selected_row_id = current_id
        await self.refresh_article_table()  # Show asterisk indicator
```

### Row Selection and Metadata Pattern
```python
# Store metadata when populating table
row_key = str(row_id)
tbl.add_row(*row_data, key=row_key)
self.row_metadata[row_key] = {'link': url, 'has_s': bool(summary)}

# Retrieve current row with fallback
def _get_current_row_id(self) -> int | None:
    if self.selected_row_id is not None:
        return self.selected_row_id
    tbl = self.query_one(DataTable)
    if tbl.row_count > 0:
        try:
            row_key = tbl.get_row_key_from_coordinate(tbl.cursor_coordinate)
            return int(row_key.value) if row_key else None
        except:
            pass
    return None
```

### Reactive UI Updates
- Use reactive variables for auto-updating UI components
- StatusBar shows current state via reactive properties
- DataTable refreshes trigger full data reload with metadata clearing and visual selection updates
- Row selection uses both event-driven and cursor-position fallback methods
- Visual feedback through asterisk prefixes on selected row IDs
- Callback-based modal workflows prevent async worker context errors

### Confirmation Modal Pattern
```python
# Proper ConfirmModal CSS layout
class ConfirmModal(ModalScreen[bool]):
    DEFAULT_CSS="""
    ConfirmModal > Vertical {
        width: auto;
        max-width: 80%;
        min-width: 50;        # Prevents elongated box
        height: auto;         # Auto-sizing
        padding: 2 4;
        border: thick $primary-lighten-1;
        background: $panel;
    }
    ConfirmModal Horizontal {
        width: 100%;
        height: auto;         # Essential for button display
        align-horizontal: center;
        padding-top: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self.prompt)
            with Horizontal():      # Use context manager, not classes
                yield Button(self.confirm_text, variant="primary", id="confirm")
                yield Button(self.cancel_text, id="cancel")
```

## Key Features

- **Pre-installed Scrapers**: 10 built-in scraper profiles for common sites
- **Custom Scrapers**: User-defined scraper profiles with URL patterns and selectors
- **AI Integration**: Gemini API for summarization (3 styles) and sentiment analysis
- **Dedicated Filter Screen**: Ctrl+F opens modal dialog with all filter options
- **Clean Main Interface**: Full-screen DataTable for optimal article viewing
- **Advanced Row Selection**: Keyboard and mouse click selection with visual indicators and intelligent fallback
- **Visual Selection Feedback**: Selected rows display asterisk prefix (*ID) for clear identification
- **Scraper Profile Context**: Visual indicators in status bar and modals showing current active profile
- **Sequential Modal Workflows**: Callback-based dialog chains for complex user interactions
- **Worker Context Compatibility**: Fixed Textual API push_screen_wait issues with callback patterns
- **Sorting**: 9 different sort options with proper table alias prefixes
- **Export**: CSV export with current filters applied
- **Article Reading**: Full-text article fetching and display
- **Tag Management**: Comma-separated tagging system
- **Improved Error Handling**: Fixed Textual API compatibility issues
- **Robust Confirmation Dialogs**: Fixed button display issues with proper CSS layout
- **Code Optimization (v1.0.1)**: Comprehensive formatting improvements and performance enhancements
- **Memory Efficiency**: Removed unused imports (math, json, os, Callable, etc.)
- **Database Performance**: Enhanced SQL query formatting and connection management
- **Enhanced Stability**: Better exception handling and resource cleanup

## File Locations

- Main application: `scrapetui.py`
- CSS styling: `web_scraper_tui_v1.0.tcss`
- Database: `scraped_data_tui_v1.0.db`
- Logs: `scraper_tui_v1.0.log`
- Config: `.env` (currently empty)