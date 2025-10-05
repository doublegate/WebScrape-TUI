"""Base scraper class for plugin system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import re


class ScraperType(Enum):
    """Types of scrapers."""
    HTML = "html"
    API = "api"
    RSS = "rss"
    DYNAMIC = "dynamic"  # JavaScript-heavy sites


@dataclass
class ScraperMetadata:
    """Metadata for a scraper plugin."""
    name: str
    description: str
    version: str
    author: str
    scraper_type: ScraperType
    supported_domains: List[str]
    requires_javascript: bool = False
    rate_limit_seconds: float = 1.0
    max_retries: int = 3
    timeout_seconds: int = 30

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'author': self.author,
            'scraper_type': self.scraper_type.value,
            'supported_domains': self.supported_domains,
            'requires_javascript': self.requires_javascript,
            'rate_limit_seconds': self.rate_limit_seconds,
            'max_retries': self.max_retries,
            'timeout_seconds': self.timeout_seconds
        }


@dataclass
class ScraperResult:
    """Result from a scraper operation."""
    url: str
    title: str
    content: str
    link: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None

    @property
    def content_length(self) -> int:
        """Get content length."""
        return len(self.content) if self.content else 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'url': self.url,
            'title': self.title,
            'content': self.content,
            'link': self.link,
            'metadata': self.metadata,
            'success': self.success,
            'error': self.error,
            'content_length': self.content_length
        }


class BaseScraper(ABC):
    """Base class for all scrapers."""

    # Scraper metadata (override in subclasses)
    metadata: ScraperMetadata

    def __init__(self):
        """Initialize scraper."""
        if not hasattr(self, 'metadata'):
            raise NotImplementedError("Scraper must define metadata attribute")

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """
        Check if this scraper can handle the given URL.

        Args:
            url: URL to check

        Returns:
            True if this scraper can handle the URL
        """

    @abstractmethod
    def scrape(self, url: str, **kwargs) -> ScraperResult:
        """
        Scrape content from URL.

        Args:
            url: URL to scrape
            **kwargs: Additional scraper-specific options

        Returns:
            ScraperResult with scraped content
        """

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate scraper configuration.

        Args:
            config: Configuration dictionary

        Returns:
            True if configuration is valid
        """
        return True

    def get_metadata(self) -> Dict[str, Any]:
        """Get scraper metadata as dictionary."""
        return self.metadata.to_dict()

    def matches_domain(self, url: str) -> bool:
        """
        Check if URL matches supported domains.

        Args:
            url: URL to check

        Returns:
            True if URL domain is supported
        """
        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        for supported in self.metadata.supported_domains:
            # Support wildcards like *.example.com
            pattern = supported.replace('.', r'\.').replace('*', '.*')
            if re.match(f"^{pattern}$", domain):
                return True

        return False


class HTMLScraper(BaseScraper):
    """Base class for HTML-based scrapers."""

    def __init__(self):
        """Initialize HTML scraper."""
        super().__init__()
        if self.metadata.scraper_type != ScraperType.HTML:
            raise ValueError("HTMLScraper must have scraper_type=ScraperType.HTML")

    def fetch_html(self, url: str) -> str:
        """
        Fetch HTML content from URL.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string
        """
        import requests
        from ..utils.logging import get_logger

        logger = get_logger(__name__)

        try:
            response = requests.get(
                url,
                timeout=self.metadata.timeout_seconds,
                headers={'User-Agent': 'WebScrape-TUI/2.1.0'}
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            raise

    def parse_html(self, html: str, selector: str) -> List[str]:
        """
        Parse HTML using CSS selector.

        Args:
            html: HTML content
            selector: CSS selector

        Returns:
            List of extracted text content
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'lxml')
        elements = soup.select(selector)

        return [elem.get_text(strip=True) for elem in elements]

    def extract_content(self, html: str, title_selector: str, content_selector: str) -> tuple[str, str]:
        """
        Extract title and content from HTML.

        Args:
            html: HTML content
            title_selector: CSS selector for title
            content_selector: CSS selector for content

        Returns:
            Tuple of (title, content)
        """
        titles = self.parse_html(html, title_selector)
        contents = self.parse_html(html, content_selector)

        title = titles[0] if titles else "No title"
        content = '\n\n'.join(contents) if contents else "No content"

        return title, content
