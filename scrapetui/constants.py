"""Constants and enums for WebScrape-TUI."""

from enum import Enum


class Role(Enum):
    """User roles in hierarchical order."""
    GUEST = 0
    VIEWER = 1
    USER = 2
    ADMIN = 3


class SummaryStyle(Enum):
    """AI summarization styles."""
    BRIEF = "brief"
    DETAILED = "detailed"
    BULLETS = "bullets"
    TECHNICAL = "technical"
    EXECUTIVE = "executive"


class AIProvider(Enum):
    """Supported AI providers."""
    GEMINI = "gemini"
    OPENAI = "openai"
    CLAUDE = "claude"


class ExportFormat(Enum):
    """Supported export formats."""
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    PDF = "pdf"


class SortOption(Enum):
    """Article sorting options."""
    DATE_DESC = "date_desc"
    DATE_ASC = "date_asc"
    TITLE_ASC = "title_asc"
    TITLE_DESC = "title_desc"
    URL_ASC = "url_asc"
    URL_DESC = "url_desc"
    SENTIMENT_ASC = "sentiment_asc"
    SENTIMENT_DESC = "sentiment_desc"
    RELEVANCE = "relevance"


# Database schema version
SCHEMA_VERSION = "2.0.0"

# Default admin credentials
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "Ch4ng3M3"  # Should be changed on first login

# Session configuration
DEFAULT_SESSION_DURATION_HOURS = 24

# Scraper configuration
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Rate limiting
DEFAULT_RATE_LIMIT_SECONDS = 1.0
DEFAULT_MAX_REQUESTS_PER_MINUTE = 60

# UI Configuration
MAX_TABLE_ROWS = 1000
DEFAULT_MODAL_WIDTH = 80
DEFAULT_MODAL_HEIGHT = 20
