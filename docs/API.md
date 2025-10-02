# API Documentation

## Overview

This document provides comprehensive API documentation for WebScrape-TUI's internal classes, methods, and functions. While the application is currently a standalone TUI, this documentation serves developers who want to extend functionality or integrate components programmatically.

## Table of Contents

- [Manager Classes](#manager-classes)
- [AI Providers](#ai-providers)
- [Database Functions](#database-functions)
- [Utility Functions](#utility-functions)
- [Modal Screens](#modal-screens)
- [Data Structures](#data-structures)

---

## Manager Classes

### ScheduleManager

**Location:** `scrapetui.py` lines 1416-1575

Manages scheduled scraping operations using APScheduler.

#### Methods

##### `create_schedule()`

Create a new scheduled scrape.

**Signature:**
```python
@staticmethod
def create_schedule(
    name: str,
    scraper_profile_id: int,
    schedule_type: str,
    schedule_value: str,
    enabled: bool = True
) -> bool
```

**Parameters:**
- `name` (str): Unique schedule name
- `scraper_profile_id` (int): FK to saved_scrapers table
- `schedule_type` (str): One of: "hourly", "daily", "weekly", "interval"
- `schedule_value` (str): Type-specific value:
  - hourly: "" (empty)
  - daily: "HH:MM" (e.g., "09:00")
  - weekly: "day:HH:MM" (e.g., "0:09:00" for Monday 9am)
  - interval: "minutes" (e.g., "30")
- `enabled` (bool): Whether schedule is active (default: True)

**Returns:**
- `bool`: True if successful, False if failed (e.g., duplicate name)

**Example:**
```python
success = ScheduleManager.create_schedule(
    name="Daily News Scrape",
    scraper_profile_id=1,
    schedule_type="daily",
    schedule_value="09:00",
    enabled=True
)
```

##### `list_schedules()`

Retrieve all or only enabled schedules.

**Signature:**
```python
@staticmethod
def list_schedules(enabled_only: bool = False) -> List[Dict[str, Any]]
```

**Parameters:**
- `enabled_only` (bool): If True, return only enabled schedules

**Returns:**
- `List[Dict[str, Any]]`: List of schedule dictionaries with fields:
  - id, name, scraper_profile_id, schedule_type, schedule_value
  - enabled, last_run, next_run, run_count, last_status, last_error
  - created_at, profile_name, profile_url, profile_selector

**Example:**
```python
all_schedules = ScheduleManager.list_schedules()
active_only = ScheduleManager.list_schedules(enabled_only=True)
```

##### `update_schedule()`

Update schedule parameters.

**Signature:**
```python
@staticmethod
def update_schedule(
    schedule_id: int,
    name: Optional[str] = None,
    schedule_type: Optional[str] = None,
    schedule_value: Optional[str] = None,
    enabled: Optional[bool] = None
) -> bool
```

**Parameters:**
- `schedule_id` (int): Schedule ID to update
- Other parameters: If provided, update; if None, keep existing value

**Returns:**
- `bool`: True if successful, False otherwise

**Example:**
```python
# Disable schedule without changing other fields
ScheduleManager.update_schedule(schedule_id=5, enabled=False)

# Change schedule time
ScheduleManager.update_schedule(
    schedule_id=5,
    schedule_type="daily",
    schedule_value="14:00"
)
```

##### `delete_schedule()`

Delete a schedule.

**Signature:**
```python
@staticmethod
def delete_schedule(schedule_id: int) -> bool
```

**Parameters:**
- `schedule_id` (int): Schedule ID to delete

**Returns:**
- `bool`: True if successful

**Example:**
```python
ScheduleManager.delete_schedule(schedule_id=5)
```

##### `record_execution()`

Record schedule execution results.

**Signature:**
```python
@staticmethod
def record_execution(
    schedule_id: int,
    status: str,
    error_message: Optional[str] = None
) -> bool
```

**Parameters:**
- `schedule_id` (int): Schedule ID
- `status` (str): "success", "failed", or "running"
- `error_message` (Optional[str]): Error details if failed

**Returns:**
- `bool`: True if successful

**Example:**
```python
# Success
ScheduleManager.record_execution(schedule_id=5, status="success")

# Failure
ScheduleManager.record_execution(
    schedule_id=5,
    status="failed",
    error_message="Network timeout"
)
```

---

### AnalyticsManager

**Location:** `scrapetui.py` lines 1664-1957

Manages data analytics and visualization.

#### Methods

##### `get_statistics()`

Get comprehensive statistics about scraped data.

**Signature:**
```python
@staticmethod
def get_statistics() -> Dict[str, Any]
```

**Returns:**
- `Dict[str, Any]` containing:
  - `total_articles` (int): Total article count
  - `articles_with_summaries` (int): Articles with AI summaries
  - `articles_with_sentiment` (int): Articles with sentiment analysis
  - `summary_percentage` (float): Percentage with summaries
  - `sentiment_percentage` (float): Percentage with sentiment
  - `sentiment_distribution` (Dict[str, int]): {"positive": N, "negative": N, "neutral": N}
  - `top_sources` (List[Tuple[str, int]]): [(url, count), ...] top 10
  - `top_tags` (List[Tuple[str, int]]): [(tag, count), ...] top 20
  - `articles_per_day` (List[Tuple[str, int]]): [(date, count), ...] last 30 days

**Example:**
```python
stats = AnalyticsManager.get_statistics()
print(f"Total articles: {stats['total_articles']}")
print(f"Sentiment: {stats['sentiment_distribution']}")
```

##### `generate_sentiment_chart()`

Generate pie chart of sentiment distribution.

**Signature:**
```python
@staticmethod
def generate_sentiment_chart(
    output_path: Optional[str] = None
) -> Optional[str]
```

**Parameters:**
- `output_path` (Optional[str]): File path for PNG export. If None, returns base64

**Returns:**
- `Optional[str]`: File path if output_path provided, else base64 data URI, or None if no data

**Example:**
```python
# Export to file
path = AnalyticsManager.generate_sentiment_chart("/tmp/sentiment.png")

# Get base64 for embedding
base64_data = AnalyticsManager.generate_sentiment_chart()
```

##### `generate_timeline_chart()`

Generate line graph of articles scraped over time (last 30 days).

**Signature:**
```python
@staticmethod
def generate_timeline_chart(
    output_path: Optional[str] = None
) -> Optional[str]
```

**Parameters & Returns:** Same as `generate_sentiment_chart()`

##### `generate_top_sources_chart()`

Generate horizontal bar chart of top 10 sources.

**Signature:**
```python
@staticmethod
def generate_top_sources_chart(
    output_path: Optional[str] = None
) -> Optional[str]
```

**Parameters & Returns:** Same as `generate_sentiment_chart()`

##### `generate_tag_cloud_data()`

Get tag frequency data for word cloud visualization.

**Signature:**
```python
@staticmethod
def generate_tag_cloud_data() -> List[Tuple[str, int]]
```

**Returns:**
- `List[Tuple[str, int]]`: [(tag_name, usage_count), ...] sorted by count

**Example:**
```python
tags = AnalyticsManager.generate_tag_cloud_data()
for tag, count in tags[:10]:
    print(f"{tag}: {count} uses")
```

##### `export_statistics_report()`

Export comprehensive text report with all statistics.

**Signature:**
```python
@staticmethod
def export_statistics_report(output_path: str) -> bool
```

**Parameters:**
- `output_path` (str): File path for TXT report

**Returns:**
- `bool`: True if successful, False otherwise

**Example:**
```python
success = AnalyticsManager.export_statistics_report(
    "/tmp/analytics_report.txt"
)
```

---

### ConfigManager

**Location:** `scrapetui.py` lines 1195-1345

Manages YAML configuration files.

#### Methods

##### `load_config()`

Load configuration from YAML file with defaults.

**Signature:**
```python
@staticmethod
def load_config() -> Dict[str, Any]
```

**Returns:**
- `Dict[str, Any]`: Merged configuration (defaults + user config)

**Example:**
```python
config = ConfigManager.load_config()
api_key = config['ai']['gemini_api_key']
```

##### `save_config()`

Save configuration to YAML file.

**Signature:**
```python
@staticmethod
def save_config(config: Dict[str, Any]) -> bool
```

**Parameters:**
- `config` (Dict[str, Any]): Configuration dictionary

**Returns:**
- `bool`: True if successful

**Example:**
```python
config = ConfigManager.load_config()
config['app']['default_limit'] = 50
ConfigManager.save_config(config)
```

##### `get_default_config()`

Get default configuration structure.

**Signature:**
```python
@staticmethod
def get_default_config() -> Dict[str, Any]
```

**Returns:**
- `Dict[str, Any]`: Default configuration

---

### FilterPresetManager

**Location:** `scrapetui.py` lines 1347-1414

Manages filter preset persistence.

#### Methods

##### `save_preset()`

Save or update a filter preset.

**Signature:**
```python
@staticmethod
def save_preset(
    name: str,
    title_filter: str,
    url_filter: str,
    date_filter: str,
    tags_filter: str,
    sentiment_filter: str,
    use_regex: bool,
    date_filter_from: str,
    date_filter_to: str,
    tags_logic: str
) -> bool
```

**Parameters:**
- All filter parameters as strings/bool
- `name` must be unique (or will update existing)

**Returns:**
- `bool`: True if successful

##### `load_preset()`

Load a filter preset by name.

**Signature:**
```python
@staticmethod
def load_preset(name: str) -> Optional[Dict[str, Any]]
```

**Parameters:**
- `name` (str): Preset name

**Returns:**
- `Optional[Dict[str, Any]]`: Preset data or None if not found

##### `list_presets()`

List all saved presets.

**Signature:**
```python
@staticmethod
def list_presets() -> List[str]
```

**Returns:**
- `List[str]`: Preset names

##### `delete_preset()`

Delete a preset.

**Signature:**
```python
@staticmethod
def delete_preset(name: str) -> bool
```

**Parameters:**
- `name` (str): Preset name

**Returns:**
- `bool`: True if successful

---

### TemplateManager

**Location:** `scrapetui.py` lines 1036-1117

Manages AI summarization templates.

#### Methods

##### `get_builtin_templates()`

Get 7 built-in summarization templates.

**Signature:**
```python
@staticmethod
def get_builtin_templates() -> Dict[str, str]
```

**Returns:**
- `Dict[str, str]`: {"template_name": "prompt_text", ...}

**Templates:**
- overview, bullets, eli5, academic, executive, technical, news

##### `save_custom_template()`

Save a custom template.

**Signature:**
```python
@staticmethod
def save_custom_template(name: str, prompt: str) -> bool
```

**Parameters:**
- `name` (str): Template name
- `prompt` (str): Template prompt with {variables}

**Returns:**
- `bool`: True if successful

##### `list_custom_templates()`

List all custom templates.

**Signature:**
```python
@staticmethod
def list_custom_templates() -> List[Tuple[str, str]]
```

**Returns:**
- `List[Tuple[str, str]]`: [(name, prompt), ...]

##### `apply_template()`

Apply template with variable substitution.

**Signature:**
```python
@staticmethod
def apply_template(
    template: str,
    title: str,
    content: str,
    url: str,
    date: str
) -> str
```

**Parameters:**
- `template` (str): Template string with {title}, {content}, {url}, {date}
- Other parameters: Values to substitute

**Returns:**
- `str`: Template with variables replaced

**Example:**
```python
prompt = TemplateManager.apply_template(
    template="Summarize this article titled {title}: {content}",
    title="News Article",
    content="Article text...",
    url="https://example.com",
    date="2025-10-01"
)
```

---

## AI Providers

### AIProvider (Abstract Base Class)

**Location:** `scrapetui.py` lines 850-903

Base class for all AI providers.

#### Abstract Methods

##### `summarize()`

Generate article summary.

**Signature:**
```python
@abstractmethod
def summarize(
    self,
    text: str,
    style: str = "overview",
    template: Optional[str] = None
) -> str
```

**Parameters:**
- `text` (str): Article content to summarize
- `style` (str): Summarization style (overview, bullets, etc.)
- `template` (Optional[str]): Custom template override

**Returns:**
- `str`: Generated summary

**Raises:**
- `Exception`: On API failure

##### `analyze_sentiment()`

Analyze text sentiment.

**Signature:**
```python
@abstractmethod
def analyze_sentiment(self, text: str) -> Tuple[str, float]
```

**Parameters:**
- `text` (str): Text to analyze

**Returns:**
- `Tuple[str, float]`: (sentiment_label, confidence_score)
  - sentiment_label: "positive", "negative", or "neutral"
  - confidence_score: 0.0 to 1.0

---

### GeminiProvider

**Location:** `scrapetui.py` lines 905-967

Google Gemini API implementation.

**Initialization:**
```python
provider = GeminiProvider(api_key="YOUR_API_KEY")
```

**API Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent`

---

### OpenAIProvider

**Location:** `scrapetui.py` lines 969-1001

OpenAI GPT API implementation.

**Initialization:**
```python
provider = OpenAIProvider(api_key="YOUR_API_KEY")
```

**Model:** `gpt-3.5-turbo` (configurable)

---

### ClaudeProvider

**Location:** `scrapetui.py` lines 1003-1034

Anthropic Claude API implementation.

**Initialization:**
```python
provider = ClaudeProvider(api_key="YOUR_API_KEY")
```

**Model:** `claude-3-haiku-20240307`

---

## Database Functions

### `init_db()`

Initialize database with all tables and indexes.

**Signature:**
```python
def init_db() -> bool
```

**Returns:**
- `bool`: True if successful

**Tables Created:**
- scraped_data
- tags
- article_tags
- saved_scrapers
- scheduled_scrapes
- filter_presets
- templates

### `get_db_connection()`

Get database connection as context manager.

**Signature:**
```python
def get_db_connection() -> sqlite3.Connection
```

**Returns:**
- `sqlite3.Connection`: Connection with row_factory set

**Usage:**
```python
with get_db_connection() as conn:
    cursor = conn.execute("SELECT * FROM scraped_data")
    rows = cursor.fetchall()
    conn.commit()
# Connection auto-closed here
```

---

## Utility Functions

### `load_env_file()`

Load environment variables from .env file.

**Signature:**
```python
def load_env_file(file_path: str = ".env") -> None
```

**Parameters:**
- `file_path` (str): Path to .env file

### `split_tags()`

Split comma-separated tags.

**Signature:**
```python
def split_tags(tags_str: str) -> List[str]
```

**Parameters:**
- `tags_str` (str): Comma-separated tags

**Returns:**
- `List[str]`: Cleaned tag list

**Example:**
```python
tags = split_tags("python, web scraping, ai")
# Returns: ["python", "web scraping", "ai"]
```

### `validate_url()`

Validate URL format.

**Signature:**
```python
def validate_url(url: str) -> bool
```

**Parameters:**
- `url` (str): URL to validate

**Returns:**
- `bool`: True if valid HTTP/HTTPS URL

---

## Modal Screens

All modal screens extend `ModalScreen[T]` from Textual.

### Common Pattern

```python
class ExampleModal(ModalScreen[Optional[str]]):
    """Modal description."""

    DEFAULT_CSS = """
    ExampleModal > Vertical {
        width: 60;
        height: auto;
        padding: 2;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose widgets."""
        with Vertical():
            yield Label("Title")
            yield Input(placeholder="Input", id="input")
            with Horizontal(classes="modal-buttons"):
                yield Button("Submit", id="submit")
                yield Button("Cancel", id="cancel")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "submit":
            value = self.query_one("#input", Input).value
            self.dismiss(value)
        else:
            self.dismiss(None)
```

### Usage in App

```python
def handle_result(result: Optional[str]) -> None:
    if result:
        self.notify(f"Got: {result}")

self.push_screen(ExampleModal(), handle_result)
```

---

## Data Structures

### Article Record

**Database Table:** `scraped_data`

**Fields:**
- `id` (int): Primary key
- `url` (str): Source URL
- `title` (str): Article title
- `link` (str): Article link
- `timestamp` (str): Scrape timestamp (YYYY-MM-DD HH:MM:SS)
- `summary` (Optional[str]): AI-generated summary
- `sentiment` (Optional[str]): Sentiment label

### Schedule Record

**Database Table:** `scheduled_scrapes`

**Fields:**
- `id` (int): Primary key
- `name` (str): Schedule name (unique)
- `scraper_profile_id` (int): FK to saved_scrapers
- `schedule_type` (str): hourly/daily/weekly/interval
- `schedule_value` (str): Type-specific value
- `enabled` (bool): Active status
- `last_run` (Optional[str]): Last execution timestamp
- `next_run` (Optional[str]): Next execution timestamp
- `run_count` (int): Execution count
- `last_status` (Optional[str]): success/failed/running
- `last_error` (Optional[str]): Error message
- `created_at` (str): Creation timestamp

### Filter Preset Record

**Database Table:** `filter_presets`

**Fields:**
- `id` (int): Primary key
- `name` (str): Preset name (unique)
- `title_filter`, `url_filter`, `date_filter`, `tags_filter`, `sentiment_filter` (str)
- `use_regex` (bool)
- `date_filter_from`, `date_filter_to` (str)
- `tags_logic` (str): AND/OR

---

## Error Handling

### Common Exceptions

- `sqlite3.Error`: Database errors
- `requests.RequestException`: HTTP errors
- `Exception`: General AI API errors

### Logging

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
```

---

## Future API (v2.0.0)

When REST API is implemented in v2.0.0:

### Planned Endpoints

- `GET /api/articles` - List articles
- `POST /api/articles` - Create article
- `GET /api/articles/{id}` - Get article
- `PUT /api/articles/{id}` - Update article
- `DELETE /api/articles/{id}` - Delete article
- `GET /api/scrapers` - List scrapers
- `POST /api/scrapers` - Create scraper
- `GET /api/analytics` - Get statistics
- `POST /api/ai/summarize` - Summarize text
- `POST /api/ai/sentiment` - Analyze sentiment

**Authentication:** JWT tokens

**Documentation:** OpenAPI/Swagger at `/docs`

---

This API documentation will be continuously updated as new features are added. For the most current information, refer to inline code documentation and docstrings.
