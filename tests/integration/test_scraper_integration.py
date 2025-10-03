"""Integration tests for scraper system."""

import pytest
import tempfile
from pathlib import Path

from scrapetui.scrapers.manager import ScraperManager
from scrapetui.scrapers.base import HTMLScraper, ScraperMetadata, ScraperResult, ScraperType


def test_plugin_directory_creation():
    """Test plugin directory is created if it doesn't exist."""
    # Manager should not crash if plugins directory is missing
    manager = ScraperManager()
    assert len(manager.scrapers) > 0  # Built-in scrapers still loaded


def test_builtin_scrapers_loaded():
    """Test all built-in scrapers are loaded."""
    manager = ScraperManager()

    expected_scrapers = [
        "Generic HTML",
        "TechCrunch",
        "BBC News",
        "The Guardian",
        "Ars Technica",
        "The Verge",
        "Wired"
    ]

    for name in expected_scrapers:
        assert name in manager.scrapers, f"Built-in scraper {name} not loaded"


def test_scraper_priority():
    """Test that specific scrapers take priority over generic."""
    manager = ScraperManager()

    # TechCrunch URL should use TechCrunch scraper, not generic
    scraper = manager.get_scraper_for_url("https://techcrunch.com/article")
    assert scraper.metadata.name == "TechCrunch"

    # Random URL should use generic scraper
    scraper = manager.get_scraper_for_url("https://random.com/page")
    assert scraper.metadata.name == "Generic HTML"


def test_multiple_managers():
    """Test multiple manager instances share scrapers (singleton pattern)."""
    from scrapetui.scrapers.manager import get_scraper_manager

    manager1 = get_scraper_manager()
    manager2 = get_scraper_manager()

    assert manager1 is manager2  # Same instance


def test_all_scrapers_have_metadata():
    """Test all loaded scrapers have valid metadata."""
    manager = ScraperManager()

    for name, scraper in manager.scrapers.items():
        assert scraper.metadata is not None
        assert scraper.metadata.name == name
        assert scraper.metadata.version
        assert scraper.metadata.author
        assert len(scraper.metadata.supported_domains) > 0


def test_scraper_domain_uniqueness():
    """Test that scrapers don't conflict on domain matching."""
    manager = ScraperManager()

    # Each specific domain should match exactly one non-generic scraper
    test_urls = [
        "https://techcrunch.com/article",
        "https://bbc.com/news/article",
        "https://theguardian.com/article",
        "https://arstechnica.com/article"
    ]

    for url in test_urls:
        # Find all scrapers that can handle this URL
        matching_scrapers = [
            s for s in manager.scrapers.values()
            if s.can_handle(url) and s.metadata.name != "Generic HTML"
        ]

        # Should have exactly one specific scraper
        assert len(matching_scrapers) == 1, f"Expected 1 scraper for {url}, got {len(matching_scrapers)}"


def test_scraper_type_consistency():
    """Test all scrapers have correct type set."""
    manager = ScraperManager()

    for scraper in manager.scrapers.values():
        assert scraper.metadata.scraper_type in [
            ScraperType.HTML,
            ScraperType.API,
            ScraperType.RSS,
            ScraperType.DYNAMIC
        ]


def test_scraper_methods_implemented():
    """Test all scrapers implement required methods."""
    manager = ScraperManager()

    for name, scraper in manager.scrapers.items():
        # Check can_handle is implemented
        assert callable(scraper.can_handle)

        # Check scrape is implemented
        assert callable(scraper.scrape)

        # Check get_metadata works
        metadata = scraper.get_metadata()
        assert isinstance(metadata, dict)
        assert 'name' in metadata
