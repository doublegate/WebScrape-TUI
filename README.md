# WebScrape-TUI v1.0

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Textual](https://img.shields.io/badge/TUI-Textual-green.svg)](https://textual.textualize.io/)

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
- **Advanced Filtering**: Dedicated filter screen (Ctrl+F) with multi-field filtering
- **Visual Row Selection**: Spacebar and mouse click selection with asterisk indicators and cursor navigation
- **Scraper Profile Context**: Visual indicators showing current scraper profile in status bar and modals
- **Sequential Modal Dialogs**: Callback-based workflows preventing worker context errors
- **Flexible Sorting**: 9 different sorting options with proper SQL table aliases
- **Tag System**: Comma-separated tagging for article categorization
- **CSV Export**: Export filtered data for external analysis
- **Transaction Safety**: Context managers ensure data integrity

### 🤖 AI Integration
- **Google Gemini API**: State-of-the-art AI for content analysis
- **Multiple Summarization Styles**: Brief, detailed, and bullet-point summaries
- **Sentiment Analysis**: Confidence-scored sentiment detection
- **Async Processing**: Non-blocking AI operations to maintain UI responsiveness
- **Optimized API Calls**: Efficient request handling and error management
- **Configurable API Keys**: Easy setup for AI features

### 🔧 Code Quality & Performance
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

## 📋 Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [Features Deep Dive](#-features-deep-dive)
- [API Integration](#-api-integration)
- [Database Schema](#-database-schema)
- [Keyboard Shortcuts](#-keyboard-shortcuts)
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

### API Keys Setup
For AI features, configure your Google Gemini API key using environment variables:

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the .env file:**
   ```bash
   # Open .env file and set your API key
   GEMINI_API_KEY=your_actual_api_key_here
   ```

3. **Get your API key:**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy the key to your `.env` file

**Important:** The `.env` file is automatically ignored by Git to keep your API keys secure.

### Environment Configuration
All configuration is managed through the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key for AI features | *(empty)* |
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

**Filtering Articles:**
- Press `Ctrl+F` to open the dedicated filter dialog
- Set filters for title, URL, date range, tags, or sentiment
- Use "Clear All" to reset all filters quickly
- Filters preserve current values when reopening
- Apply filters to return to main screen with filtered results

**Sorting Options:**
- Date (newest/oldest first)
- Title (A-Z/Z-A)
- URL (A-Z/Z-A)
- Sentiment (positive/negative first)

**Exporting Data:**
- Press `E` to export current view to CSV
- Includes all applied filters
- Preserves column structure

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

**AI Analysis:**
- Configure Gemini API key in `.env` file
- Automatic summarization in multiple styles
- Sentiment analysis with confidence scores
- Async processing for performance

## 🔧 Features Deep Dive

### Pre-installed Scraper Profiles

| Website | Profile Name | Description |
|---------|--------------|-------------|
| Hacker News | HN Front Page | Latest technology news and discussions |
| Reddit | Reddit Hot Posts | Trending posts from various subreddits |
| Medium | Medium Latest | Recent articles from Medium platform |
| Dev.to | Dev.to Posts | Developer-focused articles and tutorials |
| TechCrunch | TC Startup News | Startup and technology news |
| Ars Technica | Ars Articles | In-depth technology analysis |
| The Verge | Verge News | Consumer technology news |
| GitHub | GitHub Trending | Trending repositories |
| Stack Overflow | SO Questions | Latest programming questions |
| Product Hunt | PH Products | New product launches |

### Custom Scraper Creation

Create powerful custom scrapers with:
- **URL Patterns**: Support for wildcards and regex
- **CSS Selectors**: Target specific page elements
- **Default Limits**: Set standard article counts
- **Tag Templates**: Pre-populate tags for scraped content
- **Descriptions**: Document scraper purpose and usage

### Database Schema

```sql
-- Articles table
CREATE TABLE scraped_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    title TEXT,
    content TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    summary_brief TEXT,
    summary_detailed TEXT,
    summary_bullets TEXT,
    sentiment_label TEXT,
    sentiment_confidence REAL
);

-- Tags system
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE article_tags (
    article_id INTEGER,
    tag_id INTEGER,
    FOREIGN KEY (article_id) REFERENCES scraped_data(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id),
    PRIMARY KEY (article_id, tag_id)
);

-- Scraper profiles
CREATE TABLE saved_scrapers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    url TEXT NOT NULL,
    selector TEXT NOT NULL,
    default_limit INTEGER DEFAULT 10,
    default_tags_csv TEXT DEFAULT '',
    description TEXT DEFAULT '',
    is_preinstalled BOOLEAN DEFAULT 0
);
```

## ⌨️ Keyboard Shortcuts & Mouse Support

### Global Shortcuts
| Key | Action |
|-----|--------|
| `q` | Quit application |
| `h` | Show help dialog |
| `Ctrl+N` | New scrape dialog |
| `Ctrl+P` | Saved scrapers |
| `Ctrl+T` | Manage tags |
| `Ctrl+F` | Open filter dialog |
| `Ctrl+E` | Export to CSV |
| `R` | Refresh data |

### Navigation & Selection
| Input | Action |
|-------|--------|
| `↑/↓` | Navigate table rows |
| `Space` | Select/unselect current row (shows *ID indicator) |
| `Mouse Click` | Select/unselect clicked row (same as Space) |
| `Enter` | View article details |
| `Tab` | Next input field |
| `Shift+Tab` | Previous input field |
| `Esc` | Close dialog/Cancel |

### Data Management
| Key | Action |
|-----|--------|
| `s` | Summarize selected article |
| `Ctrl+K` | Sentiment analysis for selected |
| `Ctrl+R` | Read full article content |
| `d`/`Del` | Remove selected article |
| `Ctrl+T` | Manage tags for selected |
| `R` | Refresh view |

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

**3. AI features not working**
- Verify Gemini API key is set in `.env` file
- Ensure `.env` file exists (copy from `.env.example`)
- Check API quota and billing in Google AI Studio
- Review network connectivity
- Validate API key permissions

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

# Install in development mode
pip install -e .
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Start developing!
```

### Areas for Contribution

- **New scraper profiles** for popular websites
- **UI/UX improvements** and accessibility features
- **Performance optimizations** for large datasets
- **Additional AI integrations** (OpenAI, Claude, etc.)
- **Export formats** (JSON, XML, PDF)
- **Documentation** and tutorials
- **Testing** and quality assurance
- **Bug fixes** and stability improvements

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

### Recent Updates (v1.0.1)
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

### Upcoming Features
- [ ] **Plugin System**: Extensible architecture for custom processors
- [ ] **Scheduled Scraping**: Automated scraping with cron-like scheduling
- [ ] **Data Visualization**: Charts and graphs for scraped data analysis
- [ ] **Advanced Search**: Full-text search with indexing
- [ ] **Bulk Operations**: Multi-select for batch operations
- [ ] **Configuration Files**: YAML/JSON configuration management
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
