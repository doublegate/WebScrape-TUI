"""Scraper plugin manager for dynamic loading and management."""

import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Type
import sys

from .base import BaseScraper, ScraperResult, ScraperMetadata
from ..utils.logging import get_logger
from ..config import get_config

# Lazy initialization - do not create logger/config at module level
_logger = None
_config = None

def _get_lazy_logger():
    """Get logger lazily."""
    global _logger
    if _logger is None:
        _logger = get_logger(__name__)
    return _logger

def _get_lazy_config():
    """Get config lazily."""
    global _config
    if _config is None:
        _config = get_config()
    return _config


class ScraperManager:
    """Manage scraper plugins."""

    def __init__(self):
        """Initialize scraper manager."""
        self.scrapers: Dict[str, BaseScraper] = {}
        self._loaded_modules: List[str] = []

        # Load scrapers
        self.load_builtin_scrapers()
        self.load_plugin_scrapers()

        _get_lazy_logger().info(f"Loaded {len(self.scrapers)} scrapers")

    def load_builtin_scrapers(self):
        """Load built-in scrapers from scrapetui/scrapers/builtin/."""
        from . import builtin

        builtin_path = Path(builtin.__file__).parent

        # Find all Python files in builtin directory
        for module_file in builtin_path.glob("*.py"):
            if module_file.name.startswith('_'):
                continue

            module_name = f"scrapetui.scrapers.builtin.{module_file.stem}"

            try:
                module = importlib.import_module(module_name)
                self._load_scrapers_from_module(module, is_builtin=True)
            except Exception as e:
                _get_lazy_logger().error(f"Failed to load builtin scraper {module_name}: {e}")

    def load_plugin_scrapers(self):
        """Load user plugin scrapers from plugins/scrapers/."""
        plugin_dir = Path("plugins/scrapers")

        if not plugin_dir.exists():
            _get_lazy_logger().info("No plugins directory found")
            return

        # Add plugins directory to Python path
        if str(plugin_dir.parent) not in sys.path:
            sys.path.insert(0, str(plugin_dir.parent))

        for plugin_file in plugin_dir.glob("*.py"):
            if plugin_file.name.startswith('_'):
                continue

            try:
                spec = importlib.util.spec_from_file_location(
                    f"scrapers.{plugin_file.stem}",
                    plugin_file
                )

                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self._load_scrapers_from_module(module, is_builtin=False)

            except Exception as e:
                _get_lazy_logger().error(f"Failed to load plugin {plugin_file.name}: {e}")

    def _load_scrapers_from_module(self, module, is_builtin: bool = False):
        """
        Load scraper classes from a module.

        Args:
            module: Python module to load from
            is_builtin: Whether this is a built-in scraper
        """
        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            # Check if it's a scraper class
            if (isinstance(attr, type) and
                issubclass(attr, BaseScraper) and
                attr != BaseScraper and
                not attr_name.startswith('_')):

                try:
                    scraper = attr()
                    self.register_scraper(scraper)

                    source = "built-in" if is_builtin else "plugin"
                    _get_lazy_logger().info(f"Loaded {source} scraper: {scraper.metadata.name}")

                except Exception as e:
                    _get_lazy_logger().error(f"Failed to instantiate scraper {attr_name}: {e}")

    def register_scraper(self, scraper: BaseScraper):
        """
        Register a scraper instance.

        Args:
            scraper: Scraper instance to register
        """
        name = scraper.metadata.name

        if name in self.scrapers:
            _get_lazy_logger().warning(f"Scraper {name} already registered, replacing")

        self.scrapers[name] = scraper

    def unregister_scraper(self, name: str):
        """
        Unregister a scraper by name.

        Args:
            name: Scraper name to unregister
        """
        if name in self.scrapers:
            del self.scrapers[name]
            _get_lazy_logger().info(f"Unregistered scraper: {name}")

    def get_scraper(self, name: str) -> Optional[BaseScraper]:
        """
        Get scraper by name.

        Args:
            name: Scraper name

        Returns:
            Scraper instance or None
        """
        return self.scrapers.get(name)

    def get_scraper_for_url(self, url: str) -> Optional[BaseScraper]:
        """
        Get appropriate scraper for URL.
        Prioritizes specific scrapers over generic ones.

        Args:
            url: URL to scrape

        Returns:
            Scraper instance that can handle URL, or None
        """
        # First try specific scrapers (non-generic)
        for scraper in self.scrapers.values():
            if scraper.metadata.name != "Generic HTML" and scraper.can_handle(url):
                return scraper

        # Fall back to generic scraper
        generic = self.scrapers.get("Generic HTML")
        if generic and generic.can_handle(url):
            return generic

        return None

    def list_scrapers(self) -> List[Dict]:
        """
        List all available scrapers.

        Returns:
            List of scraper metadata dictionaries
        """
        return [scraper.get_metadata() for scraper in self.scrapers.values()]

    def scrape_url(self, url: str, scraper_name: Optional[str] = None, **kwargs) -> ScraperResult:
        """
        Scrape URL using appropriate scraper.

        Args:
            url: URL to scrape
            scraper_name: Specific scraper to use (optional)
            **kwargs: Additional scraper options

        Returns:
            ScraperResult with scraped content
        """
        # Get scraper
        if scraper_name:
            scraper = self.get_scraper(scraper_name)
            if not scraper:
                return ScraperResult(
                    url=url,
                    title="",
                    content="",
                    link=url,
                    success=False,
                    error=f"Scraper '{scraper_name}' not found"
                )
        else:
            scraper = self.get_scraper_for_url(url)
            if not scraper:
                return ScraperResult(
                    url=url,
                    title="",
                    content="",
                    link=url,
                    success=False,
                    error="No scraper available for this URL"
                )

        # Scrape with error handling
        try:
            _get_lazy_logger().info(f"Scraping {url} with {scraper.metadata.name}")
            result = scraper.scrape(url, **kwargs)

            if result.success:
                _get_lazy_logger().info(f"Successfully scraped {url} ({result.content_length} chars)")
            else:
                _get_lazy_logger().warning(f"Scraping failed for {url}: {result.error}")

            return result

        except Exception as e:
            _get_lazy_logger().error(f"Scraping error for {url}: {e}")
            return ScraperResult(
                url=url,
                title="",
                content="",
                link=url,
                success=False,
                error=str(e)
            )


# Global manager instance
_manager_instance: Optional[ScraperManager] = None


def get_scraper_manager() -> ScraperManager:
    """Get global scraper manager instance (singleton)."""
    global _manager_instance

    if _manager_instance is None:
        _manager_instance = ScraperManager()

    return _manager_instance
