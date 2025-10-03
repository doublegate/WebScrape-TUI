"""Custom exceptions for WebScrape-TUI."""


class WebScrapeTUIError(Exception):
    """Base exception for WebScrape-TUI."""
    pass


class AuthenticationError(WebScrapeTUIError):
    """Authentication failed."""
    pass


class PermissionError(WebScrapeTUIError):
    """User lacks required permissions."""
    pass


class DatabaseError(WebScrapeTUIError):
    """Database operation failed."""
    pass


class ScraperError(WebScrapeTUIError):
    """Scraping operation failed."""
    pass


class AIProviderError(WebScrapeTUIError):
    """AI provider operation failed."""
    pass


class ConfigurationError(WebScrapeTUIError):
    """Configuration error."""
    pass


class ValidationError(WebScrapeTUIError):
    """Validation failed."""
    pass


class PluginError(WebScrapeTUIError):
    """Plugin loading or execution failed."""
    pass


class CacheError(WebScrapeTUIError):
    """Cache operation failed."""
    pass
