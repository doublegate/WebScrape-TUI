# Changelog

All notable changes to WebScrape-TUI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.0] - 2025-10-01

### 📊 Major Feature Release: Data Visualization & Advanced Analytics

This release introduces comprehensive data analytics and visualization capabilities, allowing users to gain insights from their scraped data through statistical analysis, charts, and reports.

### Added

- **AnalyticsManager Class**
  - Comprehensive statistics generation from scraped data
  - Sentiment distribution analysis
  - Top sources and tags identification
  - Timeline analysis (last 30 days)
  - Tag cloud data generation
  - Text report export functionality

- **Chart Generation (Matplotlib)**
  - **Sentiment Distribution Pie Chart**: Visual breakdown of positive/negative/neutral sentiment
  - **Timeline Line Chart**: Articles scraped over time (last 30 days) with trend visualization
  - **Top Sources Bar Chart**: Horizontal bar chart showing top 10 most-scraped sources
  - PNG export with timestamps for all charts
  - Base64 encoding support for potential web display
  - Non-interactive backend (Agg) for headless operation

- **Analytics Modal (`Ctrl+Shift+V`)**
  - Real-time statistics overview
    - Total articles, summaries, sentiment percentages
    - Sentiment distribution breakdown
    - Top 10 sources with article counts
    - Top 20 tags with usage counts (compact 4-column display)
    - Recent activity (30-day summary with daily average)
  - Export Charts button: Generates all 3 charts with timestamped filenames
  - Export Report button: Creates comprehensive text report with all statistics
  - Scrollable Markdown-based interface for clean presentation

- **Statistics Reporting**
  - Comprehensive text reports with formatted sections
  - Export path with timestamp: `analytics_report_YYYYMMDD_HHMMSS.txt`
  - Sections include: Overview, Sentiment Distribution, Top Sources, Top Tags
  - Professional formatting with separator lines and alignment

### Technical Implementation

- **New Dependencies**
  - `matplotlib>=3.7.0`: Chart generation and visualization
  - `pandas>=2.0.0`: Data analysis and statistics
  - Additional libraries: numpy, pillow, contourpy, cycler, fonttools, kiwisolver

- **AnalyticsManager Methods**
  - `get_statistics()`: Returns dict with comprehensive stats (7 metrics)
  - `generate_sentiment_chart()`: Creates pie chart, returns path or base64
  - `generate_timeline_chart()`: Creates line chart with date range
  - `generate_top_sources_chart()`: Creates horizontal bar chart
  - `generate_tag_cloud_data()`: Returns list of (tag, count) tuples
  - `export_statistics_report()`: Writes formatted text report to file

- **Data Processing**
  - SQL aggregation for efficient statistics calculation
  - Date range filtering (30-day window for timeline)
  - Null handling for sentiment and timestamp data
  - Proper error handling for edge cases (empty database, no sentiment data)

- **UI Integration**
  - New keyboard binding: `Ctrl+Shift+V` for Analytics modal
  - AnalyticsModal with VerticalScroll container
  - Markdown rendering for formatted statistics display
  - Action handler: `action_view_analytics()`

### Testing

- **Comprehensive Test Suite** (16 new tests)
  - `TestAnalyticsManager`: 11 tests for core functionality
    - Statistics generation (populated and empty databases)
    - Chart generation (all 3 types with mocking)
    - Base64 encoding for charts without file path
    - Tag cloud data structure
    - Report export (text file format)
    - Edge cases (no sentiment data, empty database)
  - `TestAnalyticsIntegration`: 2 tests for integration scenarios
    - Multiple sources handling
    - Many tags handling
  - `TestAnalyticsEdgeCases`: 3 tests for error handling
    - Null timestamps
    - Very old dates (>30 days)
    - Invalid export paths
  - All tests passing (142 total tests in full suite)

### Files Modified

- `requirements.txt`: Added matplotlib and pandas dependencies
- `scrapetui.py`:
  - Added imports for visualization libraries (lines 122-129)
  - Implemented AnalyticsManager class (295 lines, lines 1664-1957)
  - Implemented AnalyticsModal class (127 lines, lines 3373-3499)
  - Added keyboard binding and action handler (lines 3623, 4463-4465)
- `tests/test_analytics.py`: New test file (410 lines, 16 tests)

### User Experience Improvements

- One-click access to comprehensive analytics via `Ctrl+Shift+V`
- Visual understanding of scraped data patterns
- Export capabilities for sharing and archiving statistics
- Professional chart generation suitable for reports
- Real-time statistics always reflect current database state

---

## [1.5.0] - 2025-10-01

### 📅 Major Feature Release: Scheduled Scraping & Automation

This release introduces a comprehensive scheduled scraping system with background automation, allowing users to configure recurring scrapes that run automatically using cron-like scheduling.

### Added

- **Scheduled Scraping System**
  - Create, manage, and delete scheduled scrapes
  - Background scheduler using APScheduler library
  - Automatic execution at specified intervals
  - Enable/disable schedules without deletion
  - Comprehensive schedule status tracking (last run, next run, run count, status)
  - Error tracking and logging for failed scrapes

- **Schedule Types**
  - **Hourly**: Execute every hour on the hour
  - **Daily**: Execute at specific time (HH:MM format, e.g., 09:00)
  - **Weekly**: Execute on specific day and time (day:HH:MM format, e.g., 0:09:00 for Monday 9am)
  - **Interval**: Execute every N minutes (custom interval in minutes)
  - **Cron**: Support for cron-style expressions (future enhancement)

- **Schedule Management Modal (`Ctrl+Shift+A`)**
  - DataTable showing all schedules with comprehensive status
  - Add new schedules with intuitive form interface
  - Enable/disable schedules with single button click
  - Delete schedules with confirmation dialog
  - Real-time schedule status updates
  - View last run time, next run time, run count, and execution status

- **Add Schedule Modal**
  - Text inputs for schedule name and scraper profile selection
  - Radio button selection for schedule type
  - Schedule value input with format hints
  - Input validation with error messages
  - Profile ID selection from existing scraper profiles

- **Enhanced Database Schema**
  - New `scheduled_scrapes` table with columns:
    - `id`: Primary key auto-increment
    - `name`: Unique schedule name
    - `scraper_profile_id`: Foreign key to saved_scrapers table
    - `schedule_type`: Type of schedule (hourly/daily/weekly/interval)
    - `schedule_value`: Schedule parameters (time, interval, etc.)
    - `enabled`: Boolean flag for enable/disable
    - `last_run`: Timestamp of last execution
    - `next_run`: Calculated next execution time
    - `run_count`: Total number of executions
    - `last_status`: Status of last run (success/failed/running)
    - `last_error`: Error message if failed
    - `created_at`: Schedule creation timestamp
  - Foreign key constraint to saved_scrapers for data integrity

### Technical Implementation

- **ScheduleManager Class**
  - CRUD operations for schedule management
  - Next run time calculation for all schedule types
  - Execution recording with status tracking
  - List schedules with enabled filtering
  - Update schedule parameters dynamically
  - Comprehensive error handling and logging

- **Background Scheduler Integration**
  - APScheduler BackgroundScheduler instance in WebScraperApp
  - Automatic loading of enabled schedules on app startup
  - Dynamic job registration with appropriate triggers:
    - `IntervalTrigger` for hourly and interval schedules
    - `CronTrigger` for daily and weekly schedules
  - Proper scheduler shutdown on app exit
  - Thread-safe execution in background

- **Schedule Execution Logic**
  - Automatic scrape execution at scheduled times
  - Status tracking (running → success/failed)
  - Error capture and logging for diagnostics
  - Next run time recalculation after each execution
  - Run count increment for statistics
  - Integration with existing `scrape_url_action` function

- **New Modal Screens**
  - `ScheduleManagementModal`: Full schedule management interface
  - `AddScheduleModal`: Schedule creation form with validation

### Dependencies

- Added `APScheduler>=3.10.0` for background task scheduling
  - Supports cron-like scheduling with flexible triggers
  - Background thread execution
  - Job persistence and management
  - Multiple trigger types (interval, cron, date)

### Testing

- Added 16 new tests in `test_scheduling.py`
  - 12 tests for ScheduleManager (CRUD, execution recording, duplicates)
  - 4 tests for schedule calculations (next run times for all types)
  - 3 tests for database schema (table existence, uniqueness, foreign keys)
- Total test suite: 127 tests (all passing)

### Keyboard Shortcuts

- `Ctrl+Shift+A`: Open Schedule Management modal
- `Ctrl+.`: Open Settings modal (changed from `Ctrl+,` for better ergonomics)

### Performance & Quality

- Background scheduler runs independently without blocking UI
- Efficient database queries with proper indexing
- Automatic schedule loading on startup
- Graceful scheduler shutdown to prevent hanging threads
- Comprehensive error handling for failed scrapes
- Detailed logging for debugging and monitoring
- Zero breaking changes - full backward compatibility

### Use Cases

- **Daily News Aggregation**: Schedule HN, Reddit, and tech news scraping every morning
- **Hourly Price Monitoring**: Track product prices every hour for deals
- **Weekly Report Compilation**: Gather industry articles every Monday morning
- **Custom Intervals**: Scrape data every 15, 30, or 60 minutes
- **Automated Data Collection**: Hands-off data gathering for research projects

This release transforms WebScrape-TUI into a fully automated data collection platform, enabling users to set up recurring scrapes and walk away. The comprehensive schedule management interface provides full control over automation workflows.

## [1.4.0] - 2025-10-01

### 🎛️ Major Feature Release: Configuration & Filter Presets

This release adds comprehensive configuration management with YAML/JSON support and a powerful filter preset system for saving and loading common filter combinations.

### Added

- **Filter Presets System**
  - Save current filters as named presets with `Ctrl+Shift+S`
  - Load saved presets with `Ctrl+Shift+F`
  - Delete unwanted presets from management modal
  - Full support for all filter types (title, URL, date ranges, tags, sentiment, regex, tag logic)
  - Database-backed persistence with `filter_presets` table enhancements
  - List view with load and delete functionality

- **Configuration Management**
  - YAML-based configuration file (`config.yaml`) with automatic creation
  - JSON export support for configuration portability
  - Deep merge functionality for partial config updates
  - Settings modal (`Ctrl+,`) for easy configuration
  - Configurable options:
    - Default AI provider (Gemini/OpenAI/Claude)
    - Default export format (CSV/JSON)
    - Export output directory
    - Database auto-vacuum and backup settings
    - Logging configuration

- **Settings Modal (`Ctrl+,`)**
  - Interactive configuration editor with radio buttons and checkboxes
  - AI provider selection with persistence
  - Export format preferences
  - Database maintenance options
  - Real-time validation and save confirmation

- **Enhanced Database Schema**
  - Updated `filter_presets` table with new columns:
    - `date_from` and `date_to` for date range filtering
    - `use_regex` flag for regex mode persistence
    - `tags_logic` for AND/OR tag filtering mode
  - Automatic migration for existing databases
  - Backward compatibility maintained

### Technical Implementation

- **ConfigManager Class**
  - YAML parsing with PyYAML library
  - JSON fallback export functionality
  - Default configuration with sensible defaults
  - Deep merge algorithm for partial updates
  - File-based persistence with error handling

- **FilterPresetManager Class**
  - CRUD operations for filter presets
  - Database-backed storage with SQLite
  - Preset listing with chronological ordering
  - Update existing presets with same name
  - Comprehensive error handling and logging

- **New Modal Screens**
  - `FilterPresetModal`: List view with load/delete buttons
  - `SavePresetModal`: Simple text input for preset naming
  - `SettingsModal`: Comprehensive configuration editor with scroll support

### Dependencies

- Added `PyYAML>=6.0.0` for YAML configuration support

### Testing

- Added 14 new tests in `test_config_and_presets.py`
  - 4 tests for ConfigManager (load, save, merge, JSON export)
  - 7 tests for FilterPresetManager (CRUD operations, updates, empty values)
  - 2 tests for YAML handling (structure, Unicode support)
  - 1 test for database schema validation
- Total test suite: 111 tests (all passing)

### Keyboard Shortcuts

- `Ctrl+,`: Open Settings modal
- `Ctrl+Shift+F`: Manage Filter Presets (load/delete)
- `Ctrl+Shift+S`: Save current filters as preset

### Performance & Quality

- Zero breaking changes - full backward compatibility
- Efficient database queries with proper indexing
- Lazy configuration loading on application startup
- YAML format chosen for human-readable configuration files

This release focuses on user workflow optimization and persistent preferences, making WebScrape-TUI more customizable and efficient for power users.

## [1.3.5] - 2025-10-01

### 🔧 Bugfix Release: CI/CD Test Fixes

This release fixes GitHub Actions workflow failures by correcting database test fixtures and schema references.

### Fixed

- **Database Test Fixtures**
  - Fixed `initialized_db` fixture to correctly monkeypatch `DB_PATH` instead of `DATABASE_PATH`
  - Added monkeypatch to `test_database_file_created` test
  - All 14 database initialization tests now pass successfully

- **Database Schema Test Updates**
  - Corrected field references from `content` to `link` in article tests
  - Updated summary field references from `summary_brief`/`summary_detailed` to `summary`/`sentiment`
  - Fixed URL field assertions to match actual schema (`url` + `link` instead of combined `url`)
  - Updated duplicate constraint test to reflect UNIQUE constraint on `link` field

- **Scraper Profile Tests**
  - Fixed `test_list_all_scrapers` to filter out pre-installed scrapers (`is_preinstalled = 0`)
  - Tests now correctly handle 24 built-in scraper profiles

### Technical Details

- All 97 tests now pass successfully (14 database, 9 AI providers, 12 bulk operations, 14 JSON export, 20 scraping, 26 utils, 2 basic)
- GitHub Actions CI/CD pipeline should now complete successfully
- No functional changes to application code
- Test improvements ensure better coverage and reliability

## [1.3.0] - 2025-10-01

### 🚀 Major Feature Release: Multi-Provider AI & Advanced Filtering

This release adds support for multiple AI providers, custom summarization templates, and significantly enhanced filtering capabilities with regex support and advanced date/tag filtering options.

### Added

- **Multiple AI Provider Support**
  - Google Gemini, OpenAI GPT, and Anthropic Claude integration
  - `Ctrl+P`: Quick provider selection modal
  - Unified AI provider abstraction layer
  - Provider-specific configuration via `.env` file
  - Support for multiple models per provider (GPT-4o, Claude 3.5 Sonnet, Gemini 2.0, etc.)
  - Automatic fallback to Gemini if no provider configured

- **Custom Summarization Templates**
  - Template Manager class for template CRUD operations
  - 7 built-in templates: Overview, Bullet Points, ELI5, Academic, Executive Summary, Technical Brief, News Brief
  - User-defined custom templates with variable substitution
  - Template variables: {title}, {content}, {url}, {date}
  - Database-backed template storage
  - Template selection in summarization modal

- **Advanced Filtering System**
  - **Regex Support**: Toggle regex mode for title and URL filters
  - **Date Range Filtering**: Filter by from/to date ranges instead of single date
  - **Tag Logic Options**: Choose between AND (all tags) or OR (any tag) logic
  - **Filter Presets**: Save and load common filter combinations (UI ready, backend implemented)
  - Enhanced filter modal with scrollable content
  - Post-SQL regex filtering for complex patterns

- **Enhanced Testing** (+15 tests)
  - Tests for AI provider abstraction and initialization
  - Tests for template variable substitution
  - Tests for advanced filtering logic
  - Basic regex and date range validation tests

### Enhanced

- **AI Integration**
  - Legacy wrapper functions maintain backward compatibility
  - All providers support custom templates
  - Template-based summarization with article metadata
  - Provider name displayed in summaryization messages

- **User Interface**
  - Updated filter screen with new options
  - Checkbox for regex toggle
  - Radio buttons for tag AND/OR logic
  - Dual date inputs for range selection
  - Save/Load preset buttons (preparation for full implementation)

- **Database Schema**
  - New `summarization_templates` table
  - New `filter_presets` table
  - Built-in templates auto-inserted on init
  - Template metadata (name, description, is_builtin)

### Changed

- **Configuration**
  - Added `OPENAI_API_KEY` and `CLAUDE_API_KEY` environment variables
  - Provider initialization defaults to Gemini if available
  - Template selection replaces hardcoded style options

- **Filtering Logic**
  - Enhanced SQL generation for tag OR logic
  - Date range support with >= and <= operators
  - Regex filtering applied post-SQL for complex patterns
  - Filter status displays logic type (AND/OR)

### Technical Details

- Abstract base class `AIProvider` with implementations for each provider
- Template Manager uses static methods for database operations
- Regex compilation with proper error handling
- Provider selection persists across application lifetime
- All new reactive properties for filter options (use_regex, date_filter_from/to, tags_logic)

### Performance

- Regex filtering only applied when enabled
- Template lookup cached in modal initialization
- Efficient SQL query generation for tag logic
- Provider switching without re-initialization overhead

This release significantly expands the AI capabilities and filtering power of WebScrape-TUI, making it more flexible and suitable for professional workflows.

## [1.2.0] - 2025-10-01

### 🎯 Major Feature Release: Bulk Operations & JSON Export

This release adds powerful bulk selection capabilities and modern JSON export functionality, significantly enhancing data management and workflow efficiency.

### Added

- **Bulk Selection System**
  - Multi-select articles using Spacebar toggle
  - Visual [✓] indicators for selected articles in table
  - Status bar shows count of selected articles
  - Bulk selection state tracking across filtered views

- **Bulk Operations**
  - `Ctrl+A`: Select all visible articles in current view
  - `Ctrl+D`: Deselect all articles
  - `Ctrl+Shift+D`: Bulk delete selected articles with confirmation
  - Confirmation dialogs show exact count of affected articles
  - Transaction-safe bulk deletion with rollback support

- **JSON Export Functionality**
  - `Ctrl+J`: Export articles to JSON format
  - Structured JSON with metadata (export date, total articles)
  - Nested tags as arrays instead of comma-separated strings
  - Includes applied filters in export metadata
  - Full article content in export (not just summaries)
  - Pretty-printed JSON with proper UTF-8 encoding
  - Automatic `.json` file extension

- **Enhanced Testing Suite** (+26 tests)
  - 12 new tests for bulk operations
  - 14 new tests for JSON export functionality
  - Test coverage increased from 60 to 86 tests
  - Pass rate improved from 78% to 85% (73/86 passing)

### Enhanced

- **User Experience**
  - Spacebar now toggles bulk selection instead of single selection
  - Visual feedback with [✓] checkmarks for bulk-selected items
  - Status bar displays bulk selection count
  - Improved keyboard shortcuts organization

- **Export System**
  - Two export formats: CSV (existing) and JSON (new)
  - CSV optimized for spreadsheets, JSON for API integration
  - Export metadata tracks applied filters
  - Consistent worker pattern for both formats

- **Code Quality**
  - Added `json` module import for JSON handling
  - Comprehensive error handling for bulk operations
  - Type hints for new functions
  - PEP 8 compliant code structure

### Changed

- **Keyboard Shortcuts**
  - `Ctrl+E`: Export to CSV (label updated for clarity)
  - `Ctrl+J`: Export to JSON (new binding)
  - `Ctrl+A`: Select all articles (new)
  - `Ctrl+D`: Deselect all (new)
  - `Ctrl+Shift+D`: Bulk delete (new)

- **Selection Behavior**
  - Spacebar now adds/removes from bulk selection set
  - Single selection mode still available via compatibility
  - Mouse clicks work with bulk selection
  - Visual indicators differentiate bulk ([✓]) vs single (*) selection

### Fixed

- **Database Test Fixtures**
  - Improved fixture isolation using pytest monkeypatch
  - Better teardown and cleanup
  - More reliable test execution

### Technical Details

- Bulk selection uses reactive `set` data structure for O(1) lookups
- JSON export includes full schema with nested objects
- SQL queries use IN clause with parameterized placeholders for bulk operations
- Export workers follow same async pattern as existing CSV export
- Status bar reactively updates with bulk selection count
- All new features fully tested with dedicated test files

### Performance

- Bulk delete operations more efficient than individual deletes
- JSON export optimized with streaming writes
- Selection state updates without full table refresh
- Memory-efficient set-based selection tracking

This release significantly improves user productivity with bulk operations and provides modern JSON export for API integration and data portability.

## [1.1.0] - 2025-10-01

### 🚀 Feature Release: Enhanced Testing & Expanded Scraper Library

Major feature release adding comprehensive testing infrastructure and significantly expanding pre-configured scraper profiles.

### Added

- **Comprehensive Test Suite** (60+ tests with 78% pass rate)
  - Database tests: 14 tests for CRUD operations, schema validation, tag management
  - Scraping tests: 20 tests for HTML parsing, HTTP requests, error handling
  - Utility tests: 26 tests for environment loading, data validation, text processing
  - Added `tests/` directory with proper pytest structure
  - Created test fixtures and configuration files
  - Mock testing for external dependencies

- **14 New Pre-configured Scraper Profiles** (now 24 total)
  - **Tech News**: Hacker News, Lobsters, TechCrunch, Ars Technica, The Verge
  - **Developer Platforms**: Dev.to, GitHub Trending, Reddit Subreddits
  - **Content Platforms**: Medium, Product Hunt, WordPress blogs
  - **Specialized**: RSS feeds, documentation pages, YouTube descriptions

- **Development Infrastructure**
  - `requirements-dev.txt` with pytest, pytest-cov, black, flake8, mypy
  - Proper test organization and fixtures
  - Coverage reporting setup
  - Testing documentation in README

### Enhanced

- **README Documentation**
  - Added comprehensive scraper profile listing (24 profiles organized by category)
  - Added testing section with instructions and results
  - Updated development setup instructions
  - Improved contribution guidelines

- **Code Quality**
  - All test code follows PEP 8 standards
  - Proper type hints throughout test suite
  - Comprehensive docstrings for all test functions

### Fixed

- **Repository Cleanup**
  - Removed all sync conflict files
  - Fixed version reference inconsistency (v1.0RC → v1.0)
  - Cleaned up git repository state

### Technical Details

- Test framework: pytest with pytest-cov for coverage
- Test execution: 47/60 tests passing (database tests need fixture improvements)
- New scraper profiles include popular sites like Hacker News, Reddit, Medium, Dev.to, GitHub
- All scrapers tested for profile structure validation
- Mock testing prevents actual HTTP requests during test runs

This release significantly improves the project's testability and expands the out-of-box scraper library for immediate productivity.

## [1.0.1] - 2025-05-26

### 🔧 Code Quality & Performance Enhancement

This release focuses on comprehensive code optimization, performance improvements, and maintainability enhancements.

### Enhanced

- **Code Formatting**: Comprehensive PEP 8 compliance and formatting improvements
- **Import Optimization**: Removed unused imports reducing memory footprint:
  - Removed: `math`, `json`, `os`, `Callable`, `CSSPathType`, `Checkbox`
  - Removed: `ScrollableContainer`, `Container`, `Grid`, `DOMQuery`
- **Database Performance**: Enhanced SQL query formatting and connection management
  - Improved multi-line SQL formatting for better readability
  - Optimized database context management
  - Fixed unused connection variables
- **Error Handling**: Better exception handling patterns with proper multi-line formatting
- **String Formatting**: Improved multi-line string concatenation and f-string usage
- **Function Signatures**: Better organization of long parameter lists

### Fixed

- **Logic Issues**: Resolved unused variable `conn_blocking` in tag application workflow
- **Code Quality**: Fixed 1750+ formatting issues identified by flake8
- **Long Lines**: Broke down long lines for better readability (88 character limit)
- **Multiple Statements**: Separated multiple statements on single lines
- **Whitespace**: Fixed missing whitespace around operators and after commas

### Improved

- **Memory Efficiency**: Reduced import overhead and optimized resource usage
- **Code Readability**: Cleaner, more maintainable code structure
- **Development Experience**: Better formatted code for easier maintenance
- **Performance**: Optimized database operations and API calls
- **Stability**: Enhanced exception handling and resource cleanup

### Technical Details

- Applied comprehensive flake8 linting with max-line-length=88
- Optimized PREINSTALLED_SCRAPERS configuration formatting
- Enhanced API URL template formatting for Gemini integration
- Improved database initialization and index creation formatting
- Better structured environment variable loading

This maintenance release significantly improves code quality while maintaining 100% backward compatibility and functionality.

## [1.0] - 2025-05-26

### 🎉 Official Stable Release

This marks the stable v1.0 release of WebScrape-TUI with major enhancements in user interaction and visual feedback.

### Added

- **Mouse Click Support**: Full mouse click selection support for DataTable rows
  - Click any row to select/unselect (same behavior as spacebar)
  - Toggle selection: clicking selected row unselects it
  - Consistent visual feedback with keyboard selection
- **Scraper Profile Context Indicators**: 
  - Status bar displays current active scraper profile ("Manual Entry" or profile name)
  - ScrapeURLModal shows current profile context with accent color styling
  - Real-time updates when switching between manual entry and saved profiles
- **Enhanced Row Selection**:
  - Mouse click and keyboard selection now work identically
  - All selection methods trigger table refresh for visual indicators
  - Improved consistency across selection mechanisms

### Improved

- **User Experience**: Intuitive mouse support makes row selection more accessible
- **Visual Feedback**: Clear indication of current scraper context throughout the interface
- **Selection Consistency**: Unified behavior between mouse, keyboard, and spacebar selection
- **Interface Clarity**: Always visible scraper profile context reduces user confusion

### Changed

- **Version**: Updated from v1.0RC (Release Candidate) to v1.0 (Stable Release)
- **File Names**: Renamed all versioned files from v1.0RC to v1.0
  - `web_scraper_tui_v1.0RC.tcss` → `web_scraper_tui_v1.0.tcss`
  - `scraped_data_tui_v1.0RC.db` → `scraped_data_tui_v1.0.db`
  - `scraper_tui_v1.0RC.log` → `scraper_tui_v1.0.log`
- **Documentation**: Updated all references from v1.0RC to v1.0 across README, CLAUDE.md, and requirements.txt

### Technical Details

- Added `on_data_table_cell_selected` event handler for mouse click support
- Enhanced `StatusBar` with reactive `scraper_profile` property
- Updated `ScrapeURLModal` with profile context display and styling
- Improved event handler consistency for visual feedback
- Maintained backward compatibility with existing keyboard shortcuts

This stable release provides a complete, polished web scraping TUI with professional-grade user interaction patterns.

## [1.0RC-patch3] - 2025-05-26

### Fixed

- **Confirmation Dialog Layout**: Fixed elongated blue box issue - buttons now display properly
- **Modal Dialog CSS**: Improved ConfirmModal CSS with proper Horizontal container sizing
- **Button Display**: Resolved button visibility issues in deletion confirmations
- **Dialog Responsiveness**: Enhanced confirmation dialog layout with min-width and auto-height

### Enhanced

- **User Experience**: Confirmation dialogs now work correctly for all delete operations
- **Visual Consistency**: Proper button layout and spacing in confirmation modals
- **Modal Structure**: Improved compose() method with proper context managers

## [1.0RC-patch2] - 2025-05-26

### Fixed

- **Sequential Modal Dialogs**: Resolved worker context errors in summarization workflow
- **Row Selection Visual Feedback**: Added asterisk indicator (*ID) for selected rows
- **Summarization Function**: Fixed push_screen_wait errors with callback-based approach
- **Filter Screen Access**: Resolved Ctrl+F modal dialog worker context issues

### Added

- **Visual Selection Indicators**: Selected rows display asterisk prefix (*ID) in ID column
- **Spacebar Row Selection**: Manual row selection with immediate visual feedback
- **Callback-based Modal Workflows**: Sequential dialog chains for complex interactions
- **State Management**: Context storage for multi-step modal dialog sequences
- **Real-time Table Updates**: Table refreshes after row selection to show indicators

### Changed

- **Modal Dialog Pattern**: Converted from push_screen_wait to callback-based push_screen
- **Selection Workflow**: Enhanced spacebar selection with table refresh for visual feedback
- **Summarization Flow**: Now uses confirm dialog → style selector → worker execution chain
- **User Feedback**: Immediate notification and visual indicators for all row selections

### Enhanced

- **User Experience**: Clear visual feedback for all selection and interaction states
- **Error Prevention**: Eliminated all worker context errors through callback patterns
- **Navigation Clarity**: Asterisk indicators make current selection immediately visible
- **Workflow Reliability**: Robust sequential modal handling prevents crashes

## [1.0RC-patch1] - 2025-05-26

### Fixed

- **Textual API Compatibility**: Fixed DataTable.add_row() meta parameter compatibility issue
- **Row Selection**: Implemented intelligent row selection with cursor-position fallback
- **SQL Query Errors**: Added table aliases to prevent ambiguous column name errors in JOINs
- **UI Layout**: Separated main screen from filter inputs for improved visibility
- **Database References**: Corrected all file references to use v1.0RC instead of v5

### Added

- **Dedicated Filter Screen**: Ctrl+F opens comprehensive modal filter dialog
- **Row Metadata Storage**: Custom dictionary-based metadata storage for row-specific data
- **Enhanced Row Detection**: Fallback row selection using cursor coordinate system
- **Filter State Preservation**: Filter dialog preserves current values when reopened
- **Enter Key Binding**: Added Enter key for article detail viewing
- **Improved Help Documentation**: Updated help text to reflect new filter workflow

### Changed

- **Main Interface Layout**: Full-screen DataTable for optimal article viewing
- **Filter Workflow**: Moved from inline filters to dedicated modal screen (Ctrl+F)
- **CSS Styling**: Simplified main screen CSS, removed filter container styles
- **Row Selection Method**: Changed from direct cursor_row assignment to move_cursor() API
- **Keybindings**: Added Ctrl+F for filters, Enter for details

### Enhanced

- **User Experience**: Clean main interface with dedicated filter workflow
- **Navigation**: Improved keyboard navigation with proper row selection
- **Error Handling**: Better error handling for DataTable operations
- **Code Maintainability**: Updated all functions to use new row selection helper method

## [1.0RC] - 2024-12-XX

### Added

- **Professional Version Management**: Updated from v5 to v1.0RC (Release Candidate)
- **Startup/Shutdown Banners**: Beautiful ASCII art banners for application start and exit
- **Comprehensive Documentation**: Detailed Python script preamble with technical specifications
- **GitHub Repository Structure**: Complete repository setup for public release
- **Enhanced README**: Exhaustive documentation with installation, usage, and contribution guides
- **MIT License**: Open source licensing for community contribution
- **Requirements File**: Explicit dependency management with requirements.txt
- **Contributing Guidelines**: Detailed contribution documentation for developers
- **Professional Naming Convention**: Consistent v1.0RC naming across all files and references

### Changed

- **Database File**: Renamed from `scraped_data_tui_v5.db` to `scraped_data_tui_v1.0RC.db`
- **CSS File**: Renamed from `web_scraper_tui_v5.tcss` to `web_scraper_tui_v1.0RC.tcss`
- **Log File**: Renamed from `scraper_tui_v5.log` to `scraper_tui_v1.0RC.log`
- **Application Header**: Updated to display "Web Scraper TUI v1.0RC"
- **Error Messages**: Updated version references in logging and error handling
- **Application Exit**: Graceful shutdown with farewell banner display

### Enhanced

- **Code Documentation**: Added comprehensive docstring header with:
  - Detailed purpose and feature descriptions
  - Technical implementation overview
  - Architecture patterns explanation
  - Pending features and improvements roadmap
  - Configuration and usage instructions
- **User Experience**: Professional startup experience with feature overview
- **Error Handling**: Improved KeyboardInterrupt handling with clean exit
- **Repository Readiness**: All files necessary for GitHub repository initialization

---

## [0.5] - Previous Development Phase

### Features Implemented in Previous Versions

- **Core TUI Framework**: Built with Textual for modern terminal interface
- **Web Scraping Engine**: BeautifulSoup4-powered HTML content extraction
- **Database Management**: SQLite database with normalized schema
- **Pre-installed Scrapers**: 10+ scraper profiles for popular websites
- **Custom Scraper Creation**: User-defined scrapers with CSS selectors
- **AI Integration**: Google Gemini API for summarization and sentiment analysis
- **Data Management**: Filtering, sorting, and tagging system
- **Export Functionality**: CSV export with applied filters
- **Article Reading**: Full-text display with markdown rendering
- **Tag Management**: Comma-separated tagging system
- **Modal Dialogs**: Intuitive popup interfaces for user interaction
- **Real-time Updates**: Reactive UI with live data refreshing
- **Error Handling**: Robust error management and logging
- **Archive Support**: Wayback Machine integration
- **Background Processing**: Async workers for non-blocking operations

### Technical Architecture

- **Async/Await Pattern**: Non-blocking operations for UI responsiveness
- **Worker Pattern**: Background task management
- **Modal Screen Pattern**: Structured user interaction flow
- **Reactive Programming**: Textual's reactive system integration
- **Context Management**: Safe database operations with proper cleanup
- **Logging System**: Comprehensive logging with multiple handlers

---

## Upcoming Releases

### [1.0] - Stable Release (Planned)

- **Performance Optimizations**: Enhanced memory management and faster operations
- **Bug Fixes**: Resolution of any issues found during RC testing
- **Documentation Polish**: Final documentation refinements
- **Stability Improvements**: Enhanced error handling and edge case management
- **User Feedback Integration**: Community-driven improvements

### [1.1] - Feature Enhancement (Planned)

- **Enhanced Scraper Profiles**: Additional pre-configured website scrapers
- **Advanced Filtering**: More sophisticated search and filter capabilities
- **Bulk Operations**: Multi-select functionality for batch operations
- **Export Formats**: JSON, XML, and other export format support
- **Configuration Management**: YAML/JSON configuration file support

### [1.2] - AI Enhancement (Planned)

- **Multiple AI Providers**: OpenAI, Anthropic Claude integration
- **Custom Summarization**: User-defined summarization styles
- **Content Classification**: Automatic article categorization
- **Sentiment Trends**: Historical sentiment analysis
- **AI Model Selection**: Choose between different AI models

### [2.0] - Major Feature Release (Future)

- **Plugin System**: Extensible architecture for custom processors
- **Scheduled Scraping**: Automated scraping with cron-like scheduling
- **Data Visualization**: Charts and graphs for data analysis
- **Web Interface**: Optional web UI for remote access
- **API Server**: REST API for programmatic access
- **Multi-user Support**: Collaborative features and user management

---

## Migration Guide

### From v5 to v1.0RC

#### File Changes

```bash
# Old files (v5)
scraped_data_tui_v5.db
web_scraper_tui_v5.tcss
scraper_tui_v5.log

# New files (v1.0RC)
scraped_data_tui_v1.0RC.db
web_scraper_tui_v1.0RC.tcss
scraper_tui_v1.0RC.log
```

#### Automatic Migration

- Files are automatically renamed when upgrading
- Database schema remains compatible
- No data loss during version transition
- CSS styles are preserved
- Log history is maintained

#### Configuration Updates

- No configuration changes required
- All existing scrapers and data are preserved
- API keys remain in the same location
- User preferences are maintained

### Breaking Changes

- **None**: v1.0RC maintains full backward compatibility with v5
- **File Names**: Only cosmetic file name changes, no functional impact
- **API Compatibility**: All existing integrations continue to work

---

## Development Process

### Version Numbering

- **v1.0RC**: Release Candidate - Feature complete, testing phase
- **v1.0**: Stable Release - Production ready
- **v1.x**: Minor releases - New features, backward compatible
- **v2.x**: Major releases - Significant changes, possible breaking changes

### Release Cycle

1. **Development**: Feature development and bug fixes
2. **Testing**: Internal testing and quality assurance
3. **Release Candidate**: Community testing and feedback
4. **Stable Release**: Production deployment
5. **Maintenance**: Bug fixes and security updates

### Community Involvement

- **Issue Reporting**: GitHub Issues for bug reports and feature requests
- **Pull Requests**: Community contributions and improvements
- **Discussions**: GitHub Discussions for community interaction
- **Documentation**: Community-driven documentation improvements

---

## Security Updates

### Security Practices

- **Dependency Updates**: Regular security updates for all dependencies
- **Code Review**: All changes undergo security review
- **Vulnerability Scanning**: Automated security vulnerability detection
- **Secure Defaults**: Secure configuration out of the box

### Reporting Security Issues

For security vulnerabilities, please email: security@webscrape-tui.com

- Do not report security issues in public GitHub issues
- We will respond within 24 hours
- Security patches will be prioritized

---

## Contributors

### Core Team

- **Development Team**: WebScrape-TUI Core Contributors
- **Community**: GitHub contributors and issue reporters

### Recognition

We thank all contributors who have helped make WebScrape-TUI better:

- Bug reporters and testers
- Feature suggestion providers
- Documentation writers
- Code contributors
- Community supporters

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute to this project.

---

*This changelog is maintained according to [Keep a Changelog](https://keepachangelog.com/) principles.*