"""Built-in scrapers for WebScrape-TUI."""

# Import all built-in scrapers to make them discoverable
from . import generic
from . import news
from . import tech

__all__ = ['generic', 'news', 'tech']
