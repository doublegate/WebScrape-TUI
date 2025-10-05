"""Custom exceptions for WebScrape-TUI."""


class WebScrapeTUIError(Exception):
    """Base exception for WebScrape-TUI."""


class AuthenticationError(WebScrapeTUIError):
    """Authentication failed."""


class PermissionError(WebScrapeTUIError):
    """User lacks required permissions."""


class DatabaseError(WebScrapeTUIError):
    """Database operation failed."""


class ScraperError(WebScrapeTUIError):
    """Scraping operation failed."""


class AIProviderError(WebScrapeTUIError):
    """AI provider operation failed."""


class ConfigurationError(WebScrapeTUIError):
    """Configuration error."""


class ValidationError(WebScrapeTUIError):
    """Validation failed."""


class PluginError(WebScrapeTUIError):
    """Plugin loading or execution failed."""


class CacheError(WebScrapeTUIError):
    """Cache operation failed."""
