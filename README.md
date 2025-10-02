# WebScrape-TUI v1.6.0

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Textual](https://img.shields.io/badge/TUI-Textual-green.svg)](https://textual.textualize.io/)
[![Version](https://img.shields.io/badge/version-1.6.0-blue.svg)](https://github.com/doublegate/WebScrape-TUI/releases)

A comprehensive Python-based Text User Interface (TUI) application for web scraping, data management, and AI-powered content analysis built with the modern Textual framework.

![WebScrape-TUI Banner](WebScrape-TUI.png)

## 🚀 Features

### 🖥️ Interactive Terminal Interface

- **Modern TUI**: Built with Textual framework for responsive terminal-based interaction
- **Clean Main Interface**: Full-screen DataTable for optimal article viewing and navigation
- **Dedicated Filter Screen**: Ctrl+F opens comprehensive filter modal dialog
- **Modal Dialogs**: Intuitive popup windows for user input and data display
- **Real-time Tables**: Dynamic data tables with live sorting and visual selection indicators
- **Intelligent Row Selection**: Spacebar selection with asterisk indicators (*ID) and cursor fallback
- **Sequential Modal Workflows**: Callback-based dialog chains for complex interactions
- **Status Indicators**: Visual feedback for operations and progress tracking
- **Keyboard Navigation**: Full keyboard support with intuitive shortcuts

### 🌐 Advanced Web Scraping

- **Pre-configured Profiles**: 10+ built-in scraper profiles for popular websites
- **Custom Scrapers**: Create your own scraper profiles with URL patterns and CSS selectors
- **Robust Parsing**: BeautifulSoup4-powered HTML parsing with error handling
- **Archive Support**: Wayback Machine integration for historical content
- **Retry Mechanisms**: Automatic retry logic for failed requests

### 🗄️ Data Management

- **SQLite Database**: Persistent storage with normalized schema design
- **Filter Presets** (v1.4.0): Save and load common filter combinations with one click
- **Advanced Filtering** (v1.3.0): Regex support, date ranges, AND/OR tag logic
- **Bulk Selection** (v1.2.0): Multi-select articles with visual [✓] indicators
- **Select All/Deselect All** (v1.2.0): Ctrl+A/Ctrl+D for quick bulk operations
- **Bulk Delete** (v1.2.0): Delete multiple articles at once with confirmation
- **Visual Row Selection**: Spacebar and mouse click selection with indicators
- **Scraper Profile Context**: Visual indicators showing current scraper profile in status bar and modals
- **Sequential Modal Dialogs**: Callback-based workflows preventing worker context errors
- **Flexible Sorting**: 9 different sorting options with proper SQL table aliases
- **Tag System**: Comma-separated tagging for article categorization with AND/OR logic (v1.3.0)
- **CSV Export**: Export filtered data to CSV format
- **JSON Export** (v1.2.0): Export to structured JSON with metadata and nested tags
- **Transaction Safety**: Context managers ensure data integrity

### 🤖 AI Integration

- **Multiple AI Providers** (v1.3.0): Google Gemini, OpenAI GPT, Anthropic Claude support
- **Provider Selection** (v1.3.0): Easy switching between AI providers (Ctrl+P)
- **Custom Templates** (v1.3.0): 7 built-in + user-defined summarization templates
- **Template Variables** (v1.3.0): Dynamic {title}, {content}, {url}, {date} substitution
- **Multiple Summarization Styles**: Overview, bullets, ELI5, academic, executive, technical, news
- **Sentiment Analysis**: Confidence-scored sentiment detection across all providers
- **Async Processing**: Non-blocking AI operations to maintain UI responsiveness
- **Optimized API Calls**: Efficient request handling and error management
- **Configurable API Keys**: Easy setup for multiple AI providers

### 🔧 Configuration & Performance

- **YAML Configuration** (v1.4.0): Human-readable config files with deep merge support
- **Settings Modal** (v1.4.0): In-app configuration editor (Ctrl+,)
- **Optimized Codebase**: Comprehensive formatting and performance improvements
- **Memory Efficiency**: Removed unused imports and optimized resource usage
- **Enhanced Error Handling**: Robust exception management and logging
- **Clean Architecture**: PEP 8 compliant code structure
- **Database Optimization**: Efficient SQL queries and connection management
- **Async Operations**: Non-blocking workers for responsive UI

### 📖 Content Management

- **Full-text Reading**: Complete article fetching and display
- **Markdown Rendering**: Enhanced readability with formatted text
- **Article Preview**: Quick preview before full content view
- **Content Deduplication**: Smart handling of duplicate articles

### 📊 Data Visualization & Analytics (v1.6.0)

- **Comprehensive Statistics**: Real-time analytics dashboard accessible via Ctrl+Shift+V
- **Sentiment Analysis Visualization**: Pie chart showing positive/negative/neutral sentiment distribution
- **Timeline Charts**: Line graph of articles scraped over last 30 days with trend analysis
- **Top Sources Analysis**: Horizontal bar chart showing top 10 most-scraped sources
- **Tag Analytics**: Tag cloud data with usage frequency and top 20 tags display
- **Professional Chart Export**: PNG charts with timestamps for reports and presentations
- **Statistics Reports**: Comprehensive text reports with all metrics in formatted sections
- **Real-time Data**: All analytics reflect current database state instantly
- **Export Capabilities**: One-click export of all charts and detailed text reports

### 📅 Scheduled Scraping & Automation (v1.5.0)

- **Background Scheduler**: APScheduler-powered automated scraping system
- **Multiple Schedule Types**: Hourly, daily, weekly, interval, and cron-style scheduling
- **Schedule Management**: Create, enable/disable, update, and delete schedules via Ctrl+Shift+A
- **Execution Tracking**: Monitor last run, next run, run count, and success/failure status
- **Error Logging**: Comprehensive error tracking for failed scheduled scrapes
- **Profile Integration**: Schedule any saved scraper profile for automatic execution

## 📋 Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [Features Deep Dive](#-features-deep-dive)
- [API Integration](#-api-integration)
- [Database Schema](#-database-schema)
- [Keyboard Shortcuts](#-keyboard-shortcuts)
- [Documentation](#-documentation)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [Changelog](#-changelog)
- [License](#-license)

## 🛠️ Installation

### Prerequisites

- **Python 3.8+** (Python 3.9+ recommended)
- **Terminal with Unicode support** for proper display
- **Internet connection** for web scraping

### Method 1: Clone and Install

```bash
# Clone the repository
git clone https://github.com/doublegate/WebScrape-TUI.git
cd WebScrape-TUI

# Install dependencies
pip install -r requirements.txt

# Run the application
python scrapetui.py
```

### Method 2: Manual Dependencies

```bash
# Install required packages individually
pip install textual requests beautifulsoup4 lxml

# Download and run
python scrapetui.py
```

### Dependencies

- **textual** (>=0.38.0) - Modern Python TUI framework
- **requests** (>=2.28.0) - HTTP library for web requests
- **beautifulsoup4** (>=4.11.0) - HTML parsing library
- **lxml** (>=4.9.0) - Fast XML/HTML parser backend
- **PyYAML** (>=6.0.0) - YAML configuration file parser (v1.4.0)
- **APScheduler** (>=3.10.0) - Background task scheduling for automation (v1.5.0)
- **matplotlib** (>=3.7.0) - Chart generation and data visualization (v1.6.0)
- **pandas** (>=2.0.0) - Data analysis and statistics (v1.6.0)

## 🚀 Quick Start

1. **Launch the application:**
   ```bash
   python scrapetui.py
   ```

2. **First time setup:**
   - The application creates a SQLite database automatically
   - CSS styling file is generated if not present
   - No additional configuration required to start

3. **Basic scraping:**
   - Press `Ctrl+S` to open the scraping dialog
   - Enter a URL and CSS selector
   - Set the number of articles to scrape
   - Click "Start Scraping" to begin

4. **Using pre-configured scrapers:**
   - Press `S` to open saved scrapers
   - Select from 10+ pre-installed profiles
   - Execute scraper or customize for your needs

## ⚙️ Configuration

### Configuration File (v1.4.0)

WebScrape-TUI now uses a YAML configuration file (`config.yaml`) for managing application settings. The configuration file is created automatically on first run with sensible defaults.

**Configuration Sections:**

```yaml
ai:
  default_provider: 'gemini'  # Default AI provider (gemini/openai/claude)
  default_model: null         # Optional specific model selection

export:
  default_format: 'csv'       # Default export format (csv/json)
  output_directory: '.'       # Export file destination

ui:
  theme: 'default'            # UI theme
  table_columns: [...]        # Visible table columns

database:
  auto_vacuum: false          # Automatic database optimization
  backup_on_exit: false       # Backup database on application exit

logging:
  level: 'INFO'               # Logging verbosity (DEBUG/INFO/WARNING/ERROR)
  max_file_size_mb: 10        # Maximum log file size
```

**In-App Configuration:**
- Press `Ctrl+,` to open the Settings modal
- Edit settings through the interactive interface
- Changes are saved to `config.yaml` automatically

### API Keys Setup (v1.3.0)

For AI features, configure your API keys for supported providers using environment variables:

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the .env file with your API keys:**
   ```bash
   # Choose one or more AI providers (at least one required for AI features)

   # Google Gemini (default provider)
   GEMINI_API_KEY=your_gemini_api_key_here

   # OpenAI GPT (optional)
   OPENAI_API_KEY=your_openai_api_key_here

   # Anthropic Claude (optional)
   CLAUDE_API_KEY=your_claude_api_key_here
   ```

3. **Get your API keys:**
   - **Google Gemini**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - **OpenAI**: Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
   - **Anthropic Claude**: Visit [Anthropic Console](https://console.anthropic.com/)

4. **Select provider in-app:**
   - Press `Ctrl+P` to open provider selection modal
   - Choose from configured providers
   - Provider selection persists across sessions

**Important:** The `.env` file is automatically ignored by Git to keep your API keys secure.

### Environment Configuration

All configuration is managed through the `.env` file:

| Variable | Description | Default |
|:---------|:------------|:--------|
| `GEMINI_API_KEY` | Google Gemini API key for AI features | *(empty)* |
| `OPENAI_API_KEY` | OpenAI GPT API key for AI features (v1.3.0) | *(empty)* |
| `CLAUDE_API_KEY` | Anthropic Claude API key for AI features (v1.3.0) | *(empty)* |
| `DATABASE_PATH` | Custom database file location | `scraped_data_tui_v1.0.db` |
| `LOG_FILE_PATH` | Custom log file location | `scraper_tui_v1.0.log` |
| `LOG_LEVEL` | Logging verbosity level | `DEBUG` |

### Database Location

The SQLite database is stored as `scraped_data_tui_v1.0.db` in the application directory (configurable via `.env`).

### Logging

Logs are written to `scraper_tui_v1.0.log` with configurable levels (configurable via `.env`).

### Styling

Customize the appearance by editing `web_scraper_tui_v1.0.tcss`.

## 📖 Usage Guide

### Starting Your First Scrape

1. **Manual URL Scraping:**
   - Press `Ctrl+S` or use the menu
   - Enter target URL
   - Specify CSS selector (e.g., `article`, `.post-title`, `#content`)
   - Set article limit
   - Add optional tags
   - Start scraping

2. **Using Scraper Profiles:**
   - Press `S` for saved scrapers
   - Choose from pre-installed profiles:
     - Hacker News
     - Reddit
     - Medium
     - Dev.to
     - And many more...
   - Execute or customize as needed

### Managing Your Data

**Filtering Articles (v1.4.0 Enhanced):**
- Press `Ctrl+F` to open the advanced filter dialog
- **Regex Support**: Toggle regex mode for title/URL pattern matching
- **Date Range**: Filter by from/to dates instead of single date
- **Tag Logic**: Choose AND (all tags) or OR (any tag) matching
- **Filter Presets** (v1.4.0): Save and load common filter combinations
  - Press `Ctrl+Shift+S` to save current filters as a preset
  - Press `Ctrl+Shift+F` to load or delete saved presets
  - Presets store all filter parameters (title, URL, dates, tags, sentiment, regex, logic)
- Use "Clear All" to reset all filters quickly
- Filters preserve current values when reopening
- Apply filters to return to main screen with filtered results

**Sorting Options:**
- Date (newest/oldest first)
- Title (A-Z/Z-A)
- URL (A-Z/Z-A)
- Sentiment (positive/negative first)

**Exporting Data:**
- Press `Ctrl+E` to export current view to CSV
- Press `Ctrl+J` to export to JSON format (v1.2.0)
- Includes all applied filters in both formats
- JSON export includes metadata and nested tags
- Preserves column structure and filter information

### Advanced Features

**Tag Management:**
- Press `T` to manage tags
- Add/remove tags from articles
- Use comma-separated format
- Search and filter by tags

**Article Reading:**
- Press `Enter` on any article to read full content
- Markdown formatting for better readability
- Navigate with arrow keys and scroll

**AI Analysis (v1.3.0 Enhanced):**
- Configure one or more AI provider API keys in `.env` file
- **Multiple Providers**: Choose between Gemini, OpenAI GPT, or Claude (Ctrl+P)
- **Custom Templates**: Select from 7 built-in or create your own summarization templates
- **Template Variables**: Use {title}, {content}, {url}, {date} in custom templates
- **Summarization Styles**: Overview, Bullets, ELI5, Academic, Executive, Technical, News
- Sentiment analysis with confidence scores across all providers
- Async processing for performance

## 🔧 Features Deep Dive

### Pre-installed Scraper Profiles (24 Total)

**Popular Tech & News Sites:**
| Website | Profile Name | Description |
|:--------|:-------------|:------------|
| Hacker News | HN Front Page | Latest technology news and discussions |
| Reddit | Reddit Subreddit Posts | Trending posts from subreddits (old.reddit.com) |
| Medium | Medium Articles | Articles from Medium topics and publications |
| Dev.to | Dev.to Articles | Developer articles and tutorials |
| GitHub | GitHub Trending Repos | Trending open-source repositories |
| TechCrunch | TechCrunch News | Startup and technology news |
| Ars Technica | Ars Technica Articles | In-depth technology and science analysis |
| The Verge | The Verge Articles | Consumer technology news and reviews |
| Product Hunt | Product Hunt Products | New product launches and discoveries |
| Lobsters | Lobsters Tech News | Computing-focused link aggregation |

**Specialized Scrapers:**
| Type | Profile Name | Description |
|:-----|:-------------|:------------|
| Wikipedia | Wikipedia Article Text | Paragraph extraction from Wikipedia articles |
| Stack Overflow | StackOverflow Q&A | Questions and answers extraction |
| Academic | Academic Abstract (arXiv) | Research paper abstracts from arXiv.org |
| E-commerce | Product Details (Basic) | Product titles and prices |
| Recipes | Recipe Ingredients | Ingredient lists from recipe sites |
| Forums | Forum Posts (Generic) | Posts and comments from forums |
| Tables | Tech Specs (Simple Table) | Table data extraction |
| Archive | Archived Page (Wayback) | Wayback Machine integration |
| RSS | RSS Feed Parser (Generic) | RSS/Atom feed parsing |
| Documentation | Documentation Pages | ReadTheDocs, GitHub Pages, etc. |
| Blogs | Blog Posts (WordPress) | WordPress blog articles |
| Video | YouTube Video Descriptions | YouTube video metadata |
| News | News Headlines (General) | Headlines from news websites |
| Generic | Generic Article Cleaner | Universal article content extraction |

### Custom Scraper Creation

Create powerful custom scrapers with:

- **URL Patterns**: Support for wildcards and regex
- **CSS Selectors**: Target specific page elements
- **Default Limits**: Set standard article counts
- **Tag Templates**: Pre-populate tags for scraped content
- **Descriptions**: Document scraper purpose and usage

### Database Schema (Updated v1.3.0)

```sql
-- Articles table
CREATE TABLE scraped_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    link TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    summary TEXT,
    sentiment TEXT
);

-- Tags system
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE article_tags (
    article_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    FOREIGN KEY (article_id) REFERENCES scraped_data(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, tag_id)
);

-- Scraper profiles
CREATE TABLE saved_scrapers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    url TEXT NOT NULL,
    selector TEXT NOT NULL,
    default_limit INTEGER DEFAULT 0,
    default_tags_csv TEXT,
    description TEXT,
    is_preinstalled INTEGER DEFAULT 0
);

-- Summarization templates (v1.3.0)
CREATE TABLE summarization_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    template TEXT NOT NULL,
    description TEXT,
    is_builtin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Filter presets (v1.4.0)
CREATE TABLE filter_presets (
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
);
```

## ⌨️ Keyboard Shortcuts & Mouse Support

### Global Shortcuts

| Key | Action |
|:----|:-------|
| `q` / `Ctrl+C` | Quit application |
| `F1` / `Ctrl+H` | Show help dialog |
| `Ctrl+N` | New scrape dialog |
| `Ctrl+M` | Saved scrapers / Manage profiles |
| `Ctrl+P` | **Select AI Provider** (v1.3.0) |
| `Ctrl+period` | **Settings** (v1.4.0) |
| `Ctrl+Shift+A` | **Manage Schedules** (v1.5.0) |
| `Ctrl+Shift+V` | **View Analytics** (v1.6.0) |
| `Ctrl+T` | Manage tags for selected article |
| `Ctrl+F` | Open advanced filter dialog |
| `Ctrl+Shift+F` | **Manage Filter Presets** (v1.4.0) |
| `Ctrl+Shift+S` | **Save Current Filters as Preset** (v1.4.0) |
| `Ctrl+E` | Export to CSV |
| `Ctrl+J` | **Export to JSON** (v1.2.0) |
| `Ctrl+L` | Toggle dark/light theme |
| `Ctrl+S` | Cycle sort order |
| `r` | Refresh data |

### Navigation & Selection

| Input | Action |
|:------|:-------|
| `↑/↓` | Navigate table rows |
| `Space` | Toggle bulk selection (shows [✓] indicator) |
| `Mouse Click` | Select/unselect clicked row (same as Space) |
| `Ctrl+A` | **Select all visible articles** (v1.2.0) |
| `Ctrl+D` | **Deselect all articles** (v1.2.0) |
| `Enter` | View article details |
| `Tab` | Next input field |
| `Shift+Tab` | Previous input field |
| `Esc` | Close dialog/Cancel |

### Data Management

| Key | Action |
|:----|:-------|
| `s` | Summarize selected article |
| `Ctrl+K` | Sentiment analysis for selected |
| `Ctrl+R` | Read full article content |
| `d`/`Del` | Remove selected article |
| `Ctrl+Shift+D` | **Bulk delete selected articles** (v1.2.0) |
| `Ctrl+T` | Manage tags for selected |
| `R` | Refresh view |

## 📚 Documentation

WebScrape-TUI includes comprehensive documentation in the `docs/` directory:

### Core Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design, components, data flow, and extension points
- **[Development Guide](docs/DEVELOPMENT.md)** - Setup, workflows, testing, code style, and contribution guidelines
- **[API Documentation](docs/API.md)** - Manager classes, AI providers, database functions, and data structures
- **[Roadmap](docs/ROADMAP.md)** - Future features, milestones, and contribution opportunities
- **[Project Status](docs/PROJECT-STATUS.md)** - Current health, metrics, and progress tracking
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Comprehensive problem-solving guide with solutions

### Quick Links

| Need | Document |
|------|----------|
| Understanding the codebase | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Contributing code | [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) |
| Using APIs programmatically | [docs/API.md](docs/API.md) |
| Solving problems | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |
| Planning contributions | [docs/ROADMAP.md](docs/ROADMAP.md) |
| Checking project health | [docs/PROJECT-STATUS.md](docs/PROJECT-STATUS.md) |

See [docs/README.md](docs/README.md) for a complete documentation index and reading paths.

## 🔍 Troubleshooting

### Common Issues

**1. Application won't start**

```bash
# Check Python version
python --version  # Should be 3.8+

# Install missing dependencies
pip install textual requests beautifulsoup4 lxml

# Check terminal compatibility
echo $TERM  # Should support Unicode
```

**2. Scraping fails**

- Verify URL accessibility in browser
- Check CSS selector validity
- Review website's robots.txt
- Ensure stable internet connection

**3. AI features not working (v1.3.0)**

- Verify at least one AI provider API key is set in `.env` file
- Ensure `.env` file exists (copy from `.env.example`)
- Press `Ctrl+P` to check which providers are configured
- Check API quota and billing:
  - Gemini: [Google AI Studio](https://makersuite.google.com/)
  - OpenAI: [OpenAI Usage](https://platform.openai.com/usage)
  - Claude: [Anthropic Console](https://console.anthropic.com/)
- Review network connectivity
- Validate API key permissions and format

**4. Database errors**

- Check file permissions in application directory
- Ensure sufficient disk space
- Verify SQLite is available
- Review log files for specifics

**5. Display issues**

- Use terminal with Unicode support
- Increase terminal size (minimum 80x24)
- Check color support
- Update terminal emulator

### Performance Optimization

**For large datasets:**

- Use filters to limit displayed data
- Regular database maintenance
- Export and archive old data
- Optimize CSS selectors

**For slow scraping:**

- Reduce concurrent requests
- Implement delays between requests
- Use more specific selectors
- Check target website rate limits

### Debugging

Enable detailed logging:

```python
# In scrapetui.py, modify logging level
logging.basicConfig(level="DEBUG")
```

Log locations:

- **Main log**: `scraper_tui_v1.0.log`
- **Database**: Check for `.db-journal` files
- **Application errors**: Console output

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Quick Contribution Guide

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**: Follow the existing code style
4. **Add tests**: Ensure new features are tested
5. **Update documentation**: Keep README and docs current
6. **Submit a pull request**: Describe your changes clearly

### Development Setup

```bash
# Clone your fork
git clone https://github.com/doublegate/WebScrape-TUI.git
cd WebScrape-TUI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ --cov=scrapetui --cov-report=html

# View coverage report
open htmlcov/index.html  # Or your browser of choice

# Start developing!
python scrapetui.py
```

### Testing

WebScrape-TUI includes a comprehensive test suite with 100+ tests:

**Test Categories:**
- **Database Tests** (14 tests): CRUD operations, schema validation, tag management
- **Scraping Tests** (20 tests): HTML parsing, HTTP requests, error handling
- **Utility Tests** (26 tests): Environment loading, data validation, text processing
- **Bulk Operations Tests** (12 tests): Multi-select, bulk delete, SQL queries (v1.2.0)
- **JSON Export Tests** (14 tests): Format validation, data conversion (v1.2.0)
- **AI Provider Tests** (15 tests): Provider abstraction, template substitution (v1.3.0)
- **Config & Presets Tests** (14 tests): YAML handling, filter presets, deep merge (v1.4.0)

**Running Tests:**
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_ai_providers.py

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=scrapetui --cov-report=html
```

**Test Results (v1.4.0):**
- 127 total tests across 8 categories
- All scheduling, configuration, filter presets, and AI provider tests passing ✓
- Comprehensive coverage of v1.4.0 features
- 100% pass rate across all test suites

### Areas for Contribution

- **New scraper profiles** for popular websites
- **UI/UX improvements** and accessibility features
- **Performance optimizations** for large datasets
- **Additional export formats** (XML, PDF, Markdown)
- **Documentation** and tutorials
- **Testing** and quality assurance
- **Bug fixes** and stability improvements

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

### Recent Updates (v1.6.0)
- **Data Visualization**: Pie charts, line graphs, and bar charts for analytics
- **Statistics Dashboard**: Comprehensive analytics accessible via Ctrl+Shift+V
- **Chart Export**: Professional PNG charts with timestamps for reports
- **Analytics Reports**: Detailed text reports with all metrics and statistics
- **Real-time Metrics**: Sentiment distribution, top sources, tag frequencies, timeline trends
- **Comprehensive Testing**: 142 tests with 16 new tests for analytics features
- **New Dependencies**: matplotlib and pandas for data visualization and analysis

### Previous Updates (v1.5.0)
- **Scheduled Scraping**: Automated background scraping with APScheduler
- **Schedule Management**: Create, edit, enable/disable, and delete schedules
- **Multiple Schedule Types**: Hourly, daily, weekly, and custom interval scheduling
- **Execution Tracking**: Monitor last run, next run, run count, and status
- **Background Automation**: Hands-free data collection without manual intervention
- **Comprehensive Testing**: 127 tests with 16 new tests for scheduling features

### Previous Updates (v1.4.0)
- **YAML Configuration**: Human-readable config files with automatic creation and deep merge
- **Settings Modal**: In-app configuration editor with live updates (Ctrl+,)
- **Filter Presets**: Save and load filter combinations with database persistence
- **Enhanced Database**: New filter_presets table with full parameter support
- **Comprehensive Testing**: 111 tests with 14 new tests for v1.4.0 features
- **Keyboard Shortcuts**: Ctrl+comma (Settings), Ctrl+Shift+F (Presets), Ctrl+Shift+S (Save)

### Previous Updates (v1.3.0)
- **Multi-Provider AI**: Google Gemini, OpenAI GPT, and Anthropic Claude integration
- **Custom Templates**: 7 built-in templates with custom template management
- **Advanced Filtering**: Regex support, date ranges, AND/OR tag logic
- **Enhanced Testing**: 100+ tests across 6 categories
- **Improved UX**: Quick provider selection (Ctrl+P) and enhanced filter UI
- **Database Updates**: New tables for templates and filter presets

### Previous Updates (v1.0.1)
- **Code Quality & Performance**: Comprehensive code optimization and formatting improvements
- **Import Optimization**: Removed unused imports reducing memory footprint (math, json, os, etc.)
- **Database Performance**: Enhanced SQL query formatting and connection management
- **Logic Improvements**: Fixed unused variables and improved error handling patterns
- **Code Readability**: Improved multi-line string formatting and parameter organization
- **Stability Enhancements**: Better exception handling and resource management
- **Developer Experience**: Cleaner code structure following PEP 8 standards

### Previous Updates (v1.0RC-patch3)
- **Fixed Confirmation Dialogs**: Resolved elongated blue box issue - buttons now display properly
- **Enhanced Modal Layout**: Improved ConfirmModal CSS with proper Horizontal container sizing
- **Better Delete Operations**: All confirmation dialogs now work correctly for delete actions
- **Visual Improvements**: Proper button layout and spacing in confirmation modals

### Previous Updates (v1.0RC-patch2)
- **Visual Selection Indicators**: Selected rows show asterisk prefix (*ID) for clear feedback
- **Fixed Summarization**: Resolved worker context errors with callback-based modal workflows
- **Enhanced Row Selection**: Spacebar selection with immediate visual feedback
- **Sequential Modal Dialogs**: Callback chains for complex interactions (confirm → style selection)
- **Improved User Experience**: Real-time table updates showing selection state
- **Worker Context Compatibility**: All modal dialogs now use callback patterns
- **UI Restructure**: Separated main screen (DataTable) from filter screen (Ctrl+F modal)
- **Enhanced Row Selection**: Intelligent cursor-based selection with fallback detection
- **Textual API Compatibility**: Fixed DataTable metadata and cursor positioning issues
- **Improved Filtering**: Dedicated filter dialog with state preservation
- **SQL Optimization**: Added table aliases to prevent ambiguous column errors
- **Better Navigation**: Full-screen DataTable for optimal article viewing
- **Version Update**: Renamed from v5 to v1.0RC with consistent file references
- **Enhanced UI**: Beautiful startup and shutdown banners
- **Documentation**: Comprehensive README and documentation
- **Code Quality**: Detailed inline documentation and type hints
- **Stability**: Improved error handling and logging

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 WebScrape-TUI Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🎯 Roadmap

### Completed Features ✅
- [x] **YAML Configuration**: Human-readable config files (v1.4.0)
- [x] **Filter Presets**: Save and load filter combinations (v1.4.0)
- [x] **Multiple AI Providers**: Gemini, OpenAI, Claude (v1.3.0)
- [x] **Advanced Filtering**: Regex, date ranges, AND/OR tag logic (v1.3.0)
- [x] **Custom Templates**: Built-in and user-defined summarization templates (v1.3.0)
- [x] **Bulk Operations**: Multi-select for batch delete operations (v1.2.0)
- [x] **JSON Export**: Full export with metadata and nested structure (v1.2.0)

### Upcoming Features (v1.5.0+)
- [ ] **Scheduled Scraping** (v1.5.0): Automated scraping with cron-like scheduling
- [ ] **Plugin System**: Extensible architecture for custom processors
- [ ] **Data Visualization**: Charts and graphs for scraped data analysis
- [ ] **Advanced Search**: Full-text search with indexing
- [ ] **Docker Support**: Containerized deployment options
- [ ] **Web Interface**: Optional web UI for remote access
- [ ] **API Server**: REST API for programmatic access
- [ ] **Cloud Storage**: Integration with cloud storage providers

### Long-term Vision
- **Enterprise Features**: Multi-user support and role-based access
- **Machine Learning**: Custom ML models for content classification
- **Real-time Monitoring**: Live website change detection
- **Collaboration Tools**: Team sharing and annotation features
- **Mobile Support**: Mobile-optimized interface
- **Integration Ecosystem**: Connect with popular tools and services

## 📞 Support

### Getting Help
- **Documentation**: Check this README and inline help (`h` key)
- **Issues**: [GitHub Issues](https://github.com/doublegate/WebScrape-TUI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/doublegate/WebScrape-TUI/discussions)
- **Email**: [support@webscrape-tui.com](mailto:support@webscrape-tui.com)

### Reporting Bugs
Please include:
- Operating system and Python version
- Steps to reproduce the issue
- Expected vs actual behavior
- Log files and error messages
- Screenshots if applicable

### Feature Requests
We love new ideas! Please:
- Check existing issues first
- Describe the use case clearly
- Explain why the feature would be valuable
- Provide examples if possible

---

**Happy Scraping!** 🚀

*WebScrape-TUI v1.0 - Making web scraping accessible and powerful for everyone.*
