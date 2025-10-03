# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Version**: v2.0.0 (Multi-User Foundation Release)

This is a Python-based Text User Interface (TUI) application for web scraping built with the Textual framework. The application provides secure multi-user authentication, role-based access control (RBAC), and comprehensive web scraping capabilities. Users can scrape websites, store articles in a SQLite database, apply AI-powered summarization and sentiment analysis using multiple AI providers (Gemini, OpenAI, Claude), and manage scraped data through an interactive terminal interface.

**Test Suite**: 345/345 tests passing (100% pass rate) across Python 3.11 and 3.12
**CI/CD**: Fully operational with GitHub Actions workflow

## Architecture

### Core Components

- **Main Application**: `scrapetui.py` - Single-file application (9,715 lines) containing the entire TUI app
- **Database**: SQLite database (`scraped_data_tui_v1.0.db`) with tables for articles, tags, scraper profiles, users, and sessions
- **Styling**: `web_scraper_tui_v1.0.tcss` - Textual CSS styling file
- **Configuration**: `.env` file for API keys (GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY)
- **Test Suite**: `tests/test_v2_auth_phase1.py` (456 lines), `tests/test_v2_ui_phase2.py` (575 lines)

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

**Default Login Credentials**:
- Username: `admin`
- Password: `Ch4ng3M3` (CHANGE IMMEDIATELY after first login)

### Dependencies

The application requires these Python packages:
- `textual` - TUI framework
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `lxml` - XML/HTML parser (used by BeautifulSoup)
- `bcrypt` - Password hashing (v2.0.0)

Install with:
```bash
pip install textual requests beautifulsoup4 lxml bcrypt
```

### Database Management
- Database is auto-created on first run
- Schema v2.0.0 includes: `users`, `user_sessions`, `schema_version`, `scraped_data`, `tags`, `article_tags`, `saved_scrapers`
- Database file: `scraped_data_tui_v1.0.db`
- Automatic migration from v1.x with backup creation
- Default admin user created on first run

### API Configuration
- Multiple AI providers supported: Google Gemini, OpenAI GPT, Anthropic Claude
- API keys should be set in the `.env` file:
  - `GEMINI_API_KEY` - For Google Gemini
  - `OPENAI_API_KEY` - For OpenAI GPT
  - `ANTHROPIC_API_KEY` - For Anthropic Claude
- Environment variables are loaded via `load_env_file()` function
- Uses proper environment variable management for security

### Testing

Run the comprehensive test suite (345 tests):
```bash
pytest tests/ -v
```

Expected output:
```
============================= 345 passed in X.XXs ==============================
```

CI/CD pipeline tests on Python 3.11 and 3.12.

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
- **Advanced AI Features**: Named entity recognition, keyword extraction, topic modeling, question answering, duplicate detection
- **Improved Error Handling**: Fixed Textual API compatibility issues
- **Robust Confirmation Dialogs**: Fixed button display issues with proper CSS layout
- **Code Optimization**: Comprehensive formatting improvements and performance enhancements
- **Memory Efficiency**: Removed unused imports and optimized resource usage
- **Database Performance**: Enhanced SQL query formatting and connection management
- **Enhanced Stability**: Better exception handling and resource cleanup
- **100% Test Pass Rate**: 345/345 tests passing across Python 3.11 and 3.12

## File Locations

### Main Files
- **Main application**: `scrapetui.py` (9,715 lines)
  - Lines 297-677: v2.0.0 Authentication & session management functions
  - Lines 978-1304: Database initialization with v2.0.0 schema
  - Lines 4643-5280: v2.0.0 User interface modals (Login, Profile, User Management)
  - Lines 7373-7506: Main application class with login flow
  - Lines 7451-7455: Reactive user state variables
- **CSS styling**: `web_scraper_tui_v1.0.tcss`
- **Database**: `scraped_data_tui_v1.0.db` (v2.0.0 schema)
- **Database backup**: `scraped_data_tui_v1.0.db.backup-v1` (created on migration)
- **Logs**: `scraper_tui_v1.0.log`
- **Config**: `.env` (API keys for Gemini, OpenAI, Claude)

### Test Files
- **Phase 1 Auth Tests**: `tests/test_v2_auth_phase1.py` (456 lines)
  - Tests for password hashing, session management, authentication, database migration
- **Phase 2 UI Tests**: `tests/test_v2_ui_phase2.py` (575 lines)
  - Tests for user interface components, modals, RBAC, user management
- **Total Test Count**: 345 tests (100% passing)

### Documentation
- **README**: `README.md` - Comprehensive feature documentation and setup guide
- **CHANGELOG**: `CHANGELOG.md` - Detailed version history with v2.0.0 changes
- **CONTRIBUTING**: `CONTRIBUTING.md` - Development guidelines
- **INSTALL**: `INSTALL-ARCH.md` - Arch Linux installation guide