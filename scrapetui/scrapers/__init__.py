"""Scraper plugin system for WebScrape-TUI."""

from .base import (
    BaseScraper,
    HTMLScraper,
    ScraperMetadata,
    ScraperResult,
    ScraperType
)
from .manager import ScraperManager, get_scraper_manager

__all__ = [
    'BaseScraper',
    'HTMLScraper',
    'ScraperMetadata',
    'ScraperResult',
    'ScraperType',
    'ScraperManager',
    'get_scraper_manager'
]
