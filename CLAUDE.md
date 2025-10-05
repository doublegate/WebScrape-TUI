# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Version**: v2.1.0 (RELEASED - 2025-10-05)

This is a Python-based Text User Interface (TUI) application for web scraping built with the Textual framework. The application provides secure multi-user authentication, role-based access control (RBAC), comprehensive web scraping capabilities, and advanced AI-powered content analysis. Users can scrape websites, store articles in a SQLite database, apply AI-powered summarization and sentiment analysis using multiple AI providers (Gemini, OpenAI, Claude), perform question answering, analyze entity relationships, evaluate summary quality, and detect duplicate content through an interactive terminal interface.

**Test Suite**: 680+/680+ tests passing (100% pass rate, 1 skipped) across Python 3.11 and 3.12
**CI/CD**: Fully operational with GitHub Actions workflow
**Release**: v2.1.0 officially released with all 5 sprints complete

**Achievements**:
- ✅ All 5 sprints complete (v2.1.0 released)
- ✅ 8 advanced AI features implemented
- ✅ Complete CLI with 18+ commands
- ✅ Async database layer with aiosqlite
- ✅ Zero deprecation warnings (future-proof)
- ✅ 97% flake8 compliance (2,380→75 violations)
- ✅ Comprehensive documentation with migration guide

## Architecture

### Core Components

- **Main Application**: `scrapetui.py` - Monolithic TUI application (9,715 lines)
- **Modular Package**: `scrapetui/` - Modular architecture (~5,000 lines)
  - `scrapetui/core/` - Core functionality (database, config)
  - `scrapetui/ai/` - Advanced AI features (8 modules)
  - `scrapetui/cli/` - Command-line interface (18+ commands)
  - `scrapetui/api/` - FastAPI REST API
- **Async Database**: `scrapetui/core/database_async.py` (434 lines) - AsyncDatabaseManager with aiosqlite
- **Database**: SQLite database (`scraped_data_tui_v1.0.db`) with tables for articles, tags, scraper profiles, users, and sessions
- **Styling**: `web_scraper_tui_v2.tcss` - Textual CSS styling file (updated for v2.x)
- **Configuration**: `.env` file for API keys (GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY), `.flake8` for code style
- **Test Suite**: 15+ test files with 680+ comprehensive tests

### v2.0.0 Multi-User System

#### Authentication & Session Management (Lines 297-677)

The application implements secure authentication using bcrypt password hashing and session-based access control:

```python
# Password Security (Lines 312-344)
def hash_password(password: str) -> str:
    """Hash password using bcrypt with cost factor 12 (2^12 = 4096 rounds)."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against stored hash."""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

# Session Token Generation (Lines 347-385)
def create_session_token() -> str:
    """Generate cryptographically secure session token (32 bytes = 256 bits)."""
    return secrets.token_hex(32)

# Session Validation (Lines 387-438)
def validate_session(session_token: str) -> Optional[int]:
    """Validate session token and return user_id if valid, None otherwise."""
    # Returns user_id if session valid and not expired
    # Automatically cleans up expired sessions

# User Authentication (Lines 440-506)
def authenticate_user(username: str, password: str) -> Optional[int]:
    """Authenticate user and return user_id if successful."""
    # Creates new session with 24-hour expiration
    # Updates last_login timestamp
    # Returns user_id on success, None on failure
```

#### Role-Based Access Control (RBAC)

The application implements a hierarchical permission system with three roles:

- **Admin**: Full system access, can manage users, access all data
- **User**: Can create/edit/delete own content, view others' content
- **Viewer**: Read-only access to all content

**Permission Functions** (Throughout codebase):
```python
def check_permission(required_role: str) -> bool:
    """Check if current user has required role (hierarchical)."""
    # Admin > User > Viewer > Guest

def is_admin() -> bool:
    """Quick check if current user is admin."""

def can_edit(owner_user_id: int) -> bool:
    """Check if user can edit resource (admin or owner)."""

def can_delete(owner_user_id: int) -> bool:
    """Check if user can delete resource (admin or owner)."""
```

#### Database Schema v2.0.0 (Lines 978-1304)

New tables for multi-user support:

```sql
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email TEXT,
    role TEXT NOT NULL DEFAULT 'user',  -- admin, user, viewer
    created_at TEXT NOT NULL,
    last_login TEXT,
    is_active INTEGER NOT NULL DEFAULT 1
)

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_token TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
)

-- Existing tables updated with user_id columns:
-- scraped_data: user_id column for ownership tracking
-- saved_scrapers: user_id and is_shared columns
```

**Database Migration** (Lines 508-677):
- Automatic detection of v1.x databases
- Backup creation (`.db.backup-v1`) before migration
- All existing data assigned to admin user (id=1)
- Schema version tracking for future migrations

#### User Interface Components (Lines 4643-5280)

**LoginModal** (Lines 4643-4747):
- Application startup authentication
- Username/password input with keyboard shortcuts
- Password masking for security
- Clear error messaging
- Auto-focus on username field

**UserProfileModal** (Lines 4749-4850) - Ctrl+U:
- Display username, email, role, created date, last login, status
- Edit email address
- Launch password change modal
- Read-only display of sensitive fields

**ChangePasswordModal** (Lines 4852-4969):
- Current password verification
- New password confirmation
- Minimum 8-character validation
- Password matching validation

**UserManagementModal** (Lines 4971-5096) - Ctrl+Alt+U (Admin only):
- DataTable showing all users
- Create new users with role selection
- Edit existing users (email, role)
- Toggle user active/inactive status
- Real-time table refresh after operations

**CreateUserModal** (Lines 5098-5216):
- Username input with uniqueness check
- Optional email field
- Password input with validation
- Role selection via RadioButtons

**EditUserModal** (Lines 5218-5280):
- Email address update
- Role modification
- Pre-populated with existing data

#### Application State (Lines 7451-7455)

Reactive variables for user session management:

```python
# v2.0.0 User state
current_user_id: reactive[Optional[int]] = reactive(None)
current_username: reactive[str] = reactive("Not logged in")
current_user_role: reactive[str] = reactive("guest")
session_token: reactive[Optional[str]] = reactive(None)
```

#### Login Flow (Lines 7476-7506)

Fixed NoActiveWorker error by using worker-based login:

```python
async def on_mount(self) -> None:
    # v2.0.0: Show login modal before initializing app (use worker to avoid NoActiveWorker error)
    self.run_worker(self._handle_login_and_init(), exclusive=True)

async def _handle_login_and_init(self) -> None:
    """Handle login flow and app initialization in a worker context."""
    user_id = await self.push_screen_wait(LoginModal())
    if user_id is None:
        # User cancelled login - exit app
        self.notify("Login required. Exiting...", severity="warning")
        self.exit()
        return
    # Login successful - initialize user session
    await self._initialize_user_session(user_id)
```

### Async Database Layer (Sprint 4)

**Location**: `scrapetui/core/database_async.py` (434 lines)

The application includes a complete async database implementation using aiosqlite:

```python
from scrapetui.core.database_async import get_async_db_manager

async def example():
    db = get_async_db_manager()
    articles = await db.fetch_articles(limit=100)
    return articles
```

**Features**:
- AsyncDatabaseManager with context manager support
- Async CRUD operations (articles, users, sessions, scrapers, tags)
- Advanced filtering (search, tags, dates, user_id, sentiment)
- Singleton pattern with connection pooling
- 25 comprehensive async tests (100% passing)
- Full compatibility with synchronous database operations

**Key Methods**:
- `fetch_articles()` - Retrieve articles with filtering/pagination
- `create_article()` - Insert new article records
- `update_article()` - Modify existing articles
- `delete_article()` - Remove articles by ID
- `fetch_users()` - User management operations
- `validate_session()` - Async session validation

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

**TUI Mode** (Text User Interface):
```bash
python3 scrapetui.py
```

**CLI Mode** (Command-Line Interface):
```bash
# Install in editable mode first
pip install -e .

# Then use CLI commands
scrapetui-cli --help                    # Show all commands
scrapetui-cli users list                # List all users
scrapetui-cli scrape url https://...    # Scrape a URL
scrapetui-cli export csv --output data.csv  # Export to CSV
scrapetui-cli ai summarize --article-id 1   # Summarize article
```

**API Mode** (REST API):
```bash
uvicorn scrapetui.api.app:app --reload --port 8000
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

**Default Login Credentials**:
- Username: `admin`
- Password: `Ch4ng3M3` (CHANGE IMMEDIATELY after first login)

### Dependencies

The application requires these Python packages:

**Core Dependencies**:
- `textual` - TUI framework
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `lxml` - XML/HTML parser (used by BeautifulSoup)
- `bcrypt` - Password hashing (v2.0.0)

**AI/NLP Dependencies**:
- `google-generativeai` - Google Gemini API
- `openai` - OpenAI GPT API
- `anthropic` - Anthropic Claude API
- `spacy` - Named Entity Recognition
- `scikit-learn` - TF-IDF, clustering
- `gensim` - Topic modeling (LDA/NMF)
- `sentence-transformers` - Text embeddings

**Async & CLI Dependencies** (v2.1.0):
- `aiosqlite` - Async database operations
- `click` - CLI framework

**API Dependencies**:
- `fastapi` - REST API framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation (v2+)

Install all dependencies:
```bash
pip install -r requirements.txt
```

Or install in editable mode (includes CLI):
```bash
pip install -e .
```

### Database Management
- Database is auto-created on first run
- **Schema v2.0.1** (current): Includes all v2.0.0 tables with improved indexes
- **Tables**: `users`, `user_sessions`, `schema_version`, `scraped_data`, `tags`, `article_tags`, `saved_scrapers`
- **Database file**: `scraped_data_tui_v1.0.db`
- **Automatic migration**: From v1.x and v2.0.0 with backup creation
- **Default admin user**: Created on first run (username: admin, password: Ch4ng3M3)
- **Async support**: Available via `scrapetui.core.database_async.get_async_db_manager()`
- **Backup**: `.db.backup-v1` created automatically during migration

### API Configuration
- Multiple AI providers supported: Google Gemini, OpenAI GPT, Anthropic Claude
- API keys should be set in the `.env` file:
  - `GEMINI_API_KEY` - For Google Gemini
  - `OPENAI_API_KEY` - For OpenAI GPT
  - `ANTHROPIC_API_KEY` - For Anthropic Claude
- Environment variables are loaded via `load_env_file()` function
- Uses proper environment variable management for security

### Testing

Run the comprehensive test suite (680+ tests):
```bash
pytest tests/ -v
```

Expected output:
```
============================= 680+ passed, 1 skipped in X.XXs ==============================
```

Run specific test categories:
```bash
pytest tests/unit/ -v                    # Unit tests (135 tests)
pytest tests/api/ -v                     # API tests (64 tests)
pytest tests/cli/ -v                     # CLI tests (33 tests)
pytest tests/unit/test_database_async.py # Async database tests (25 tests)
```

CI/CD pipeline tests on Python 3.11 and 3.12.

### Test Infrastructure Pattern (v2.1.0)

For test files that need to import from monolithic scrapetui.py:

```python
import importlib.util
from pathlib import Path

_scrapetui_path = Path(__file__).parent.parent / 'scrapetui.py'
_spec = importlib.util.spec_from_file_location("scrapetui_monolith", _scrapetui_path)
_scrapetui_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scrapetui_module)

# Import components
ManagerName = _scrapetui_module.ManagerName
```

This pattern avoids package import issues where managers are set to None. All legacy tests migrated to this pattern achieve 100% pass rate.

## Code Structure Guidelines

### Code Quality Standards (Updated v2.1.0)
- **PEP 8 Compliance**: Follow Python coding standards for readability
- **Flake8 Configuration**: Use `.flake8` config file (max-line-length=120)
- **Import Optimization**: Remove unused imports to reduce memory footprint
- **Error Handling**: Use proper exception handling with multi-line formatting
- **Database Connections**: Use context managers for safe resource management
- **Multi-line Strings**: Format long strings for better readability
- **Function Signatures**: Break long parameter lists across multiple lines
- **Async Patterns**: Use async/await for database operations where appropriate
- **No Deprecation Warnings**: Use modern APIs (datetime.now(timezone.utc), Pydantic v2)

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

### v2.0.0 Multi-User Features
- **Secure Authentication**: bcrypt password hashing (cost factor 12) with 24-hour session tokens
- **Role-Based Access Control (RBAC)**: Admin, User, and Viewer roles with hierarchical permissions
- **User Management**: Admin-only user administration interface (Ctrl+Alt+U)
- **User Profiles**: View and edit profile, change password (Ctrl+U)
- **Data Ownership**: All articles and scrapers tagged with creator user_id
- **Session Security**: Cryptographically secure 256-bit session tokens
- **Database Migration**: Automatic v1.x to v2.0.0 migration with backup
- **Login Required**: Exit on login cancel (no anonymous access)
- **User Status Bar**: Current user and role always displayed
- **Keyboard Shortcuts**: Ctrl+U (profile), Ctrl+Alt+U (users), Ctrl+Shift+L (logout)

### v2.1.0 Advanced Features (All Sprints Complete)

**Sprint 1: Database & Core AI** (Lines 5xxx-6xxx in scrapetui.py):
- **Named Entity Recognition (NER)** - Extract people, organizations, locations using spaCy (Ctrl+Shift+E)
- **Keyword Extraction** - TF-IDF based keyword and topic extraction (Ctrl+Shift+K)
- **Topic Modeling** - LDA/NMF algorithms for content theme discovery (Ctrl+Alt+T)
- Database schema v2.0.1 with improved indexes and constraints
- Enhanced error handling and validation

**Sprint 2: Advanced AI** (scrapetui/ai/ modules):
- **Question Answering** - TF-IDF based Q&A system with multi-article synthesis (Ctrl+Alt+Q)
- **Entity Relationships** - Knowledge graph construction from dependency parsing (Ctrl+Alt+L)
- **Summary Quality Metrics** - ROUGE scores and coherence analysis (Ctrl+Alt+M)
- **Content Similarity** - Embedding-based similarity search and clustering (Ctrl+Shift+R, Ctrl+Alt+C)
- **Duplicate Detection** - Fuzzy matching for finding similar/duplicate articles (Ctrl+Alt+D)
- Legacy test migration to monolithic import pattern (621/622 tests passing)

**Sprint 3: CLI Implementation** (scrapetui/cli/):
- **18+ CLI Commands** for automation and scripting
- **User Management**: `scrapetui-cli users create/list/reset-password/deactivate`
- **Web Scraping**: `scrapetui-cli scrape url/profile/bulk --output json/csv`
- **Data Export**: `scrapetui-cli export csv/json/excel/pdf --filters applied`
- **AI Analysis**: `scrapetui-cli ai summarize/keywords/entities/qa --article-id ID`
- **Tag Operations**: `scrapetui-cli tags list/add/remove --article-id ID`
- **Entry Point**: `pip install -e .` → `scrapetui-cli` command available
- 33/33 CLI tests passing (100%)

**Sprint 4: Async & Deprecation Fixes**:
- **Async Database Layer** - Complete async implementation with aiosqlite (434 lines)
- **Zero Deprecation Warnings** - Fixed datetime.utcnow(), Pydantic v2 migration, FastAPI warnings
- **25 Async Tests** - Comprehensive async database test suite (100% passing)
- **Performance Improvements** - Async operations for better concurrency
- **Future-Proof Codebase** - All deprecated APIs replaced with modern alternatives

**Sprint 5: Documentation & Release**:
- **Migration Guide** - docs/MIGRATION.md (570+ lines) for v2.0.0 → v2.1.0 upgrade
- **Complete Documentation** - Updated README, CHANGELOG, API docs, DEVELOPMENT guide
- **GitHub Release** - Official v2.1.0 release published
- **Version Sync** - All files updated to v2.1.0
- **F1 Help** - Updated internal help with all features and shortcuts

**Post-Release: Code Quality** (2025-10-05):
- **97% Flake8 Compliance** - Reduced violations from 2,380 to 75
- **Modern Standards** - max-line-length=120, proper formatting
- **Zero Regressions** - All 680+ tests still passing

### Core Features
- **Pre-installed Scrapers**: 10 built-in scraper profiles for common sites
- **Custom Scrapers**: User-defined scraper profiles with URL patterns and selectors
- **AI Integration**: Multiple providers (Gemini, OpenAI, Claude) for summarization and sentiment analysis
- **Dedicated Filter Screen**: Ctrl+F opens modal dialog with all filter options
- **Clean Main Interface**: Full-screen DataTable for optimal article viewing
- **Advanced Row Selection**: Keyboard and mouse click selection with visual indicators and intelligent fallback
- **Visual Selection Feedback**: Selected rows display asterisk prefix (*ID) for clear identification
- **Scraper Profile Context**: Visual indicators in status bar and modals showing current active profile
- **Sequential Modal Workflows**: Callback-based dialog chains for complex user interactions
- **Worker Context Compatibility**: Fixed Textual API push_screen_wait issues with callback patterns
- **Sorting**: 9 different sort options with proper table alias prefixes
- **Export**: CSV, JSON, Excel, PDF export with current filters applied
- **Article Reading**: Full-text article fetching and display
- **Tag Management**: Comma-separated tagging system with AND/OR logic
- **Improved Error Handling**: Fixed Textual API compatibility issues
- **Robust Confirmation Dialogs**: Fixed button display issues with proper CSS layout
- **Code Optimization**: Comprehensive formatting improvements and performance enhancements
- **Memory Efficiency**: Removed unused imports and optimized resource usage
- **Database Performance**: Enhanced SQL query formatting and connection management
- **Enhanced Stability**: Better exception handling and resource cleanup
- **100% Test Pass Rate**: 680+/680+ tests passing (1 skipped) across Python 3.11 and 3.12
- **97% Flake8 Compliance**: Modern code style with max-line-length=120

## File Locations

### Main Files

**Core Application**:
- **scrapetui.py** (9,715 lines) - Monolithic TUI application
  - Lines 297-677: v2.0.0 Authentication & session management functions
  - Lines 978-1304: Database initialization with v2.0.1 schema
  - Lines 4643-5280: v2.0.0 User interface modals (Login, Profile, User Management)
  - Lines 7373-7506: Main application class with login flow
  - Lines 7451-7455: Reactive user state variables
- **scrapetui/** - Modular package (~5,000 lines)
  - `scrapetui/core/database_async.py` (434 lines) - Async database layer
  - `scrapetui/cli/` - CLI commands (18+ commands)
  - `scrapetui/ai/` - Advanced AI features (8 modules)
  - `scrapetui/api/` - FastAPI REST API
- **CSS styling**: `web_scraper_tui_v2.tcss` - Textual styling (updated for v2.x)
- **Database**: `scraped_data_tui_v1.0.db` (schema v2.0.1)
- **Database backup**: `scraped_data_tui_v1.0.db.backup-v1` (created on migration)
- **Logs**: `scraper_tui_v1.0.log`
- **Config**: `.env` (API keys), `.flake8` (code style), `pyproject.toml` (CLI entry point)

### Test Files

**Total**: 680+/680+ tests passing (100%, 1 skipped)

**Breakdown**:
- **Unit Tests**: `tests/unit/` - 135/135 tests (includes 25 async database tests)
- **API Tests**: `tests/api/` - 64/64 tests (REST endpoints, middleware)
- **CLI Tests**: `tests/cli/test_cli_integration.py` - 33/33 tests (command-line interface)
- **Advanced AI Tests**: `tests/test_advanced_ai.py` - 30/30 tests (NER, keywords, topic modeling)
- **Duplicate Detection**: `tests/test_duplicate_detection.py` - 23/23 tests (fuzzy matching)
- **Phase 3 Isolation**: `tests/test_v2_phase3_isolation.py` - 23/23 tests (data isolation)
- **Enhanced Export**: `tests/test_enhanced_export.py` - 21/21 tests (Excel, PDF)
- **Database Tests**: `tests/test_database.py` - 14/14 tests (operations, migrations)
- **Config/Presets**: `tests/test_config_and_presets.py` - 14/14 tests (YAML, filters)
- **AI Providers**: `tests/test_ai_providers.py` - 9/9 tests (Gemini, OpenAI, Claude)
- **Auth Phase 1**: `tests/test_v2_auth_phase1.py` - 14/15 tests (1 skipped)

### Documentation

- **README.md** - Comprehensive feature documentation and setup guide
- **CHANGELOG.md** - Detailed version history with all releases
- **CONTRIBUTING.md** - Development guidelines
- **INSTALL-ARCH.md** - Arch Linux installation guide
- **docs/MIGRATION.md** (570+ lines) - v2.0.0 → v2.1.0 upgrade guide
- **docs/PROJECT-STATUS.md** - Current state (100% complete)
- **docs/ROADMAP.md** - Development roadmap (all sprints complete)
- **docs/TECHNICAL_DEBT.md** - Minimal technical debt
- **docs/CLI.md** (984 lines) - Complete CLI reference
- **docs/API.md** - REST API documentation
- **docs/ARCHITECTURE.md** - System design
- **docs/DEVELOPMENT.md** - Developer setup

## Recent Changes (v2.1.0 Release - 2025-10-05)

### All 5 Sprints Complete

**Sprint 1: Database & Core AI** (Complete):
- Named Entity Recognition (NER) with spaCy
- Keyword Extraction with TF-IDF
- Topic Modeling with LDA/NMF
- Database schema v2.0.1 improvements
- 135 unit tests passing

**Sprint 2: Advanced AI & Legacy Tests** (Complete):
- Question Answering system
- Entity Relationships & Knowledge Graphs
- Summary Quality Metrics (ROUGE scores)
- Content Similarity (embedding-based)
- Duplicate Detection (fuzzy matching)
- Legacy test migration to monolithic import pattern
- 621/622 tests passing

**Sprint 3: CLI Implementation** (Complete):
- 18+ commands for automation
- User management (create, list, reset-password, deactivate)
- Web scraping (url, profile, bulk)
- Data export (CSV, JSON, Excel, PDF)
- AI analysis (summarize, keywords, entities, qa)
- Tag operations (list, add, remove)
- Real web scraping with BeautifulSoup
- Entry point: `pip install -e .` → `scrapetui-cli`
- 33/33 CLI tests passing

**Sprint 4: Async & Deprecation Fixes** (Complete):
- Async database layer with aiosqlite (434 lines)
- Zero deprecation warnings:
  - Fixed datetime.utcnow() → datetime.now(timezone.utc)
  - Fixed Pydantic v1 → v2 migration
  - Fixed FastAPI deprecated warnings
- 25 async tests passing
- Performance improvements with async operations

**Sprint 5: Documentation & Release** (Complete):
- Migration guide created (docs/MIGRATION.md - 570+ lines)
- All documentation updated (README, CHANGELOG, API, CLI)
- GitHub release published: https://github.com/doublegate/WebScrape-TUI/releases/tag/v2.1.0
- v2.1.0 officially released
- F1 help updated with all features

### Post-Release Code Quality (2025-10-05)

**Flake8 Cleanup - 97% Violation Reduction**:
- Reduced violations from 2,380 to 75 (97% cleanup)
- Created `.flake8` configuration file
- Set max-line-length to 120 characters (modern standard)
- Applied automated fixes:
  - 1,650+ line length violations fixed
  - 118+ unused imports removed
  - 50+ blank line spacing issues fixed
  - 190+ whitespace issues fixed
  - 5+ import formatting issues fixed
- Manual fixes:
  - Fixed ambiguous variable names (E741)
  - Fixed boolean comparisons (E712)
  - Removed unused variables (F841)
  - Fixed extra blank lines (E303)
- All 680+ tests still passing (100%)
- Zero regressions

**Remaining Non-Critical Issues** (75 total):
- 53 E501: Lines exceeding 120 chars (mostly test data strings)
- 9 F541: F-strings without placeholders (cosmetic only)
- 7 F841: Unused cursor variables (database operation pattern)
- 5 E702/E704: Multiple statements on one line (compact helper functions)
- 1 E302: Minor blank line spacing issue

**Code Quality Metrics**:
- **Total Lines**: 9,715 (monolithic) + ~5,000 (modular) + 434 (async)
- **Functions**: ~300+
- **Classes**: ~70+
- **Test Lines**: 4,000+
- **Documentation**: 7+ comprehensive docs (5,000+ lines total)

**Release Status**: Production-ready, all goals achieved