# WebScrape-TUI Architecture Documentation

## Overview

WebScrape-TUI is a Python-based Text User Interface (TUI) application built with the Textual framework. It follows a single-file architecture with modular class-based design for maintainability and clarity.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    WebScraperApp (Main App)                 │
│                        (Textual App)                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Scraping   │  │     Data     │  │  Analytics   │       │
│  │   Manager    │  │   Manager    │  │   Manager    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Schedule    │  │   Config     │  │   Filter     │       │
│  │  Manager     │  │  Manager     │  │   Preset     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Template    │  │  AI Provider │  │  AI Provider │       │
│  │  Manager     │  │  (Gemini)    │  │  (OpenAI)    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   SQLite Database Layer                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │ scraped_data│ │    tags     │ │ article_tags│            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │saved_scrapers││filter_presets││scheduled_scrapes│        │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
│  ┌─────────────┐                                            │
│  │  templates  │                                            │
│  └─────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     External Services                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Web Scraping │  │  Google      │  │  OpenAI      │       │
│  │ (BeautifulS.)│  │  Gemini API  │  │  GPT API     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │  Anthropic   │  │  Wayback     │                         │
│  │  Claude API  │  │  Machine     │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Application Layer (WebScraperApp)

**File:** `scrapetui.py` (main class)

**Responsibilities:**
- Main Textual App instance
- UI rendering and event handling
- Worker thread management
- Modal screen orchestration
- Keyboard shortcut handling
- Reactive state management

**Key Patterns:**
- **Reactive Variables**: `reactive[T]` for auto-updating UI
- **Worker Pattern**: `run_worker()` for async operations
- **Modal Screens**: `ModalScreen[T]` for user input
- **Callback Chains**: Sequential modal workflows

### 2. Manager Classes

#### ScheduleManager (v1.5.0)
**Lines:** 1416-1575

**Purpose:** Scheduled scraping management

**Methods:**
- `create_schedule()`: Create new schedule
- `list_schedules()`: Retrieve all/enabled schedules
- `update_schedule()`: Modify schedule parameters
- `delete_schedule()`: Remove schedule
- `record_execution()`: Track run results

**Dependencies:** APScheduler

#### AnalyticsManager (v1.6.0)
**Lines:** 1664-1957

**Purpose:** Data visualization and statistics

**Methods:**
- `get_statistics()`: Comprehensive metrics
- `generate_sentiment_chart()`: Pie chart
- `generate_timeline_chart()`: Line graph
- `generate_top_sources_chart()`: Bar chart
- `generate_tag_cloud_data()`: Tag frequencies
- `export_statistics_report()`: Text reports

**Dependencies:** matplotlib, pandas

#### ConfigManager (v1.4.0)
**Lines:** 1195-1345

**Purpose:** YAML configuration management

**Methods:**
- `load_config()`: Load from YAML file
- `save_config()`: Write to YAML file
- `merge_config()`: Deep merge defaults
- `get_default_config()`: Default settings

**Dependencies:** PyYAML

#### FilterPresetManager (v1.4.0)
**Lines:** 1347-1414

**Purpose:** Filter preset persistence

**Methods:**
- `save_preset()`: Create/update preset
- `load_preset()`: Retrieve preset
- `list_presets()`: Get all presets
- `delete_preset()`: Remove preset

#### TemplateManager (v1.3.0)
**Lines:** 1036-1117

**Purpose:** Summarization template management

**Methods:**
- `get_builtin_templates()`: 7 default templates
- `save_custom_template()`: Create custom
- `list_custom_templates()`: Retrieve user templates
- `apply_template()`: Variable substitution

### 3. AI Provider System (v1.3.0)

**Abstract Base:** `AIProvider` (lines 850-903)

**Implementations:**
- `GeminiProvider` (lines 905-967)
- `OpenAIProvider` (lines 969-1001)
- `ClaudeProvider` (lines 1003-1034)

**Interface:**
```python
class AIProvider:
    def summarize(text: str, style: str, template: str) -> str
    def analyze_sentiment(text: str) -> tuple[str, float]
```

**Factory Pattern:** `get_ai_provider()`

### 4. Database Layer

**File:** `scrapetui.py` (functions)

**Schema Functions:**
- `init_db()`: Create tables and indexes
- `get_db_connection()`: Context manager for connections

**Tables:**
1. `scraped_data`: Articles with metadata
2. `tags`: Tag names
3. `article_tags`: Many-to-many relationship
4. `saved_scrapers`: Scraper profiles
5. `scheduled_scrapes`: Schedule definitions (v1.5.0)
6. `filter_presets`: Saved filter combinations (v1.4.0)
7. `templates`: Custom summarization templates (v1.3.0)

**Connection Pattern:**
```python
with get_db_connection() as conn:
    cursor = conn.execute("SELECT ...")
    conn.commit()
```

### 5. Modal Screen System

**Pattern:** `ModalScreen[ReturnType]`

**Key Modals:**
- `ScrapeURLModal`: Custom scrape input
- `ManageScraperModal`: Scraper profile management
- `FilterScreen`: Advanced filtering (Ctrl+F)
- `ManageTagsModal`: Tag editing
- `AnalyticsModal`: Statistics dashboard (v1.6.0)
- `ScheduleManagementModal`: Schedule CRUD (v1.5.0)
- `SettingsModal`: Configuration editor (v1.4.0)
- `SelectStyleModal`: Summarization style picker
- `ConfirmModal`: Yes/No confirmations
- `HelpModal`: Keyboard shortcuts

**Callback Pattern:**
```python
def handle_result(result: T) -> None:
    if result:
        # Process result
        pass

self.push_screen(MyModal(), handle_result)
```

### 6. Scraping Engine

**Core Functions:**
- `scrape_url_action()`: Main scraping orchestrator
- `fetch_with_retry()`: HTTP with retries
- `parse_articles()`: BeautifulSoup parsing
- `wayback_url()`: Archive.org integration

**Error Handling:**
- Network timeouts
- Invalid HTML
- Missing selectors
- Rate limiting

## Data Flow

### 1. Scraping Workflow

```
User Input (URL + Selector)
    ↓
scrape_url_action()
    ↓
fetch_with_retry() → HTTP Request
    ↓
parse_articles() → BeautifulSoup
    ↓
Database Insert (scraped_data)
    ↓
UI Refresh (DataTable update)
```

### 2. AI Summarization Workflow

```
User Selects Article
    ↓
Confirmation Modal (if existing summary)
    ↓
Style Selection Modal
    ↓
AI Provider (Gemini/OpenAI/Claude)
    ↓
Database Update (summary + sentiment)
    ↓
UI Refresh
```

### 3. Analytics Workflow (v1.6.0)

```
User Presses Ctrl+Shift+V
    ↓
AnalyticsManager.get_statistics()
    ↓
SQL Aggregation Queries
    ↓
AnalyticsModal Display
    ↓
[Optional] Export Charts/Report
    ↓
matplotlib Chart Generation
    ↓
PNG/TXT File Export
```

### 4. Scheduled Scraping Workflow (v1.5.0)

```
Schedule Creation
    ↓
ScheduleManager.create_schedule()
    ↓
APScheduler Job Registration
    ↓
Background Execution (Triggers)
    ↓
scrape_url_action() (automated)
    ↓
ScheduleManager.record_execution()
    ↓
Next Run Calculation
```

## Threading Model

### Main Thread
- UI rendering (Textual framework)
- Event handling
- Reactive updates

### Worker Threads
- HTTP requests (`run_worker()`)
- AI API calls (`run_in_thread()`)
- Database operations (blocking)
- File I/O operations

### Background Threads (v1.5.0)
- APScheduler background scheduler
- Scheduled scrape execution
- Independent from UI thread

**Pattern:**
```python
async def action_example(self) -> None:
    def blocking_work():
        # Database or network operation
        return result

    result = await self.run_in_thread(blocking_work)
    # Update UI with result
```

## Configuration System (v1.4.0)

### File: `config.yaml`

**Structure:**
```yaml
app:
  default_limit: 0
  theme: "dark"

ai:
  default_provider: "gemini"
  gemini_api_key: ""
  openai_api_key: ""
  claude_api_key: ""

  default_summary_style: "overview"
  custom_templates:
    - name: "custom1"
      prompt: "..."
```

### Merge Strategy
1. Load defaults from `ConfigManager.get_default_config()`
2. Read `config.yaml` if exists
3. Deep merge user config over defaults
4. Return merged configuration

## Security Considerations

### API Keys
- Stored in `config.yaml` (gitignored)
- Loaded via `ConfigManager`
- Never logged or displayed

### Database
- SQLite with local file storage
- No remote access
- Foreign key constraints enabled
- Transaction safety via context managers

### Input Validation
- URL validation before requests
- CSS selector sanitization
- Tag input sanitization
- File path validation for exports

## Performance Optimizations

### Database
- Indexes on frequently queried columns
- Prepared statements via parameterized queries
- Connection pooling via context managers
- UNIQUE constraints for duplicate prevention

### UI
- Async workers prevent UI blocking
- Reactive variables for minimal updates
- DataTable pagination (implicit in Textual)
- Lazy loading of modals

### Scraping
- Retry logic with exponential backoff
- Request timeouts
- BeautifulSoup with lxml parser (fast)
- Limit parameter to prevent memory issues

### Analytics (v1.6.0)
- SQL aggregation over Python loops
- 30-day window for timeline queries
- LIMIT clauses for top-N queries
- Non-interactive matplotlib backend (Agg)

## Error Handling Strategy

### Levels
1. **User-facing**: Notifications via `self.notify()`
2. **Logging**: `logger.error()` / `logger.warning()`
3. **Graceful degradation**: Return None or empty results
4. **Exceptions**: Only for critical failures

### Patterns
```python
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    self.notify("User-friendly message", severity="error")
    return None
```

## File Structure

```
WebScrape-TUI/
├── scrapetui.py              # Main application (4600+ lines)
├── web_scraper_tui_v1.0.tcss # Textual CSS styling
├── config.yaml               # User configuration (gitignored)
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (gitignored)
├── scraped_data_tui_v1.0.db  # SQLite database (gitignored)
├── scraper_tui_v1.0.log      # Application logs (gitignored)
├── tests/                    # Test suite
│   ├── test_database.py      # Database tests
│   ├── test_scraping.py      # Scraping tests
│   ├── test_utils.py         # Utility tests
│   ├── test_ai_providers.py  # AI provider tests
│   ├── test_bulk_operations.py # Bulk ops tests
│   ├── test_json_export.py   # JSON export tests
│   ├── test_config_and_presets.py # Config tests
│   ├── test_scheduling.py    # Scheduling tests (v1.5.0)
│   └── test_analytics.py     # Analytics tests (v1.6.0)
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md       # This file
│   ├── DEVELOPMENT.md        # Development guide
│   ├── ROADMAP.md            # Future plans
│   └── API.md                # API documentation
├── README.md                 # User-facing documentation
├── CHANGELOG.md              # Version history
└── LICENSE                   # MIT License
```

## Testing Architecture

### Test Organization
- **Per-feature test files**: Each major feature has dedicated tests
- **Fixtures**: `temp_db` for isolated database testing
- **Mocking**: `unittest.mock` for external services
- **Coverage**: 142 tests across 9 test files

### Test Categories
1. **Unit Tests**: Individual functions and methods
2. **Integration Tests**: Component interactions
3. **Database Tests**: Schema and CRUD operations
4. **UI Tests**: Modal workflows and callbacks
5. **Edge Cases**: Error conditions and boundaries

## Extension Points

### Adding New AI Provider
1. Subclass `AIProvider`
2. Implement `summarize()` and `analyze_sentiment()`
3. Add to `get_ai_provider()` factory
4. Update `SelectAIProviderModal`

### Adding New Schedule Type (v1.5.0)
1. Add type to `AddScheduleModal` radio buttons
2. Implement trigger in `_load_scheduled_jobs()`
3. Add calculation in `ScheduleManager.create_schedule()`
4. Update documentation

### Adding New Chart Type (v1.6.0)
1. Add method to `AnalyticsManager`
2. Implement matplotlib chart generation
3. Add to `AnalyticsModal` export workflow
4. Write tests in `test_analytics.py`

### Adding New Modal Screen
1. Create class extending `ModalScreen[T]`
2. Define CSS in `web_scraper_tui_v1.0.tcss`
3. Implement `compose()` and event handlers
4. Add keyboard binding to `WebScraperApp.BINDINGS`
5. Create action handler `action_*`

## Dependencies Graph

```
textual (TUI framework)
    ↓
WebScraperApp
    ↓
┌───────────────┬───────────────┬───────────────┐
│               │               │               │
requests    BeautifulSoup  APScheduler   matplotlib
(HTTP)      (HTML parsing) (scheduling)  (charts)
│               │               │               │
└───────────────┴───────────────┴───────────────┘
                    │
                SQLite
              (persistence)
```

## Conclusion

WebScrape-TUI follows a **modular single-file architecture** that balances simplicity with extensibility. The codebase is organized into clear manager classes for distinct responsibilities, uses modern Python patterns (async/await, context managers, reactive programming), and maintains comprehensive test coverage.

The architecture supports:
- **Rapid feature addition**: New managers/modals easily integrated
- **Maintainability**: Clear separation of concerns
- **Testability**: Manager classes isolated for unit testing
- **Performance**: Async operations and optimized SQL
- **User experience**: Responsive UI with non-blocking operations

As the project grows, consider:
1. **Multi-file refactoring**: Split managers into separate modules
2. **Plugin system**: Dynamic loading of scrapers/providers
3. **REST API**: Enable programmatic access
4. **Configuration UI**: More comprehensive settings management
