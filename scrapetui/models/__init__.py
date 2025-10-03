"""Data models for WebScrape-TUI."""

from .user import User, Role
from .article import Article
from .scraper import ScraperProfile
from .tag import Tag
from .session import Session

__all__ = [
    'User',
    'Role',
    'Article',
    'ScraperProfile',
    'Tag',
    'Session'
]
