"""Unit tests for scraper system."""

import pytest
from unittest.mock import Mock, patch

from scrapetui.scrapers.base import (
    BaseScraper, HTMLScraper, ScraperMetadata, ScraperResult, ScraperType
)
from scrapetui.scrapers.manager import ScraperManager
from scrapetui.scrapers.builtin.generic import GenericHTMLScraper
from scrapetui.scrapers.builtin.news import TechCrunchScraper, BBCNewsScraper
from scrapetui.scrapers.builtin.tech import ArsTechnicaScraper

# Fixtures


@pytest.fixture
def sample_html():
    """Sample HTML for testing."""
    return """
    <html>
        <head><title>Test Article</title></head>
        <body>
            <h1>Test Title</h1>
            <article>
                <p>First paragraph.</p>
                <p>Second paragraph.</p>
            </article>
        </body>
    </html>
    """


@pytest.fixture
def mock_requests_get(sample_html):
    """Mock requests.get for testing."""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = sample_html
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        yield mock_get

# ScraperMetadata Tests


def test_scraper_metadata_creation():
    """Test ScraperMetadata creation."""
    metadata = ScraperMetadata(
        name="Test Scraper",
        description="A test scraper",
        version="1.0.0",
        author="Test Author",
        scraper_type=ScraperType.HTML,
        supported_domains=["example.com"]
    )

    assert metadata.name == "Test Scraper"
    assert metadata.scraper_type == ScraperType.HTML
    assert "example.com" in metadata.supported_domains


def test_scraper_metadata_to_dict():
    """Test ScraperMetadata to_dict."""
    metadata = ScraperMetadata(
        name="Test", description="Desc", version="1.0.0",
        author="Author", scraper_type=ScraperType.HTML,
        supported_domains=["test.com"]
    )

    data = metadata.to_dict()
    assert data['name'] == "Test"
    assert data['scraper_type'] == "html"
    assert data['supported_domains'] == ["test.com"]


def test_scraper_metadata_defaults():
    """Test ScraperMetadata default values."""
    metadata = ScraperMetadata(
        name="Test", description="Desc", version="1.0.0",
        author="Author", scraper_type=ScraperType.HTML,
        supported_domains=["test.com"]
    )

    assert metadata.requires_javascript is False
    assert metadata.rate_limit_seconds == 1.0
    assert metadata.max_retries == 3
    assert metadata.timeout_seconds == 30

# ScraperResult Tests


def test_scraper_result_success():
    """Test successful ScraperResult."""
    result = ScraperResult(
        url="https://example.com",
        title="Test Title",
        content="Test content",
        link="https://example.com/article",
        success=True
    )

    assert result.success
    assert result.error is None
    assert result.content_length == len("Test content")


def test_scraper_result_failure():
    """Test failed ScraperResult."""
    result = ScraperResult(
        url="https://example.com",
        title="",
        content="",
        link="https://example.com",
        success=False,
        error="Connection failed"
    )

    assert not result.success
    assert result.error == "Connection failed"


def test_scraper_result_to_dict():
    """Test ScraperResult to_dict."""
    result = ScraperResult(
        url="https://test.com", title="Title", content="Content",
        link="https://test.com", success=True
    )

    data = result.to_dict()
    assert data['url'] == "https://test.com"
    assert data['title'] == "Title"
    assert data['success'] is True


def test_scraper_result_content_length():
    """Test content_length property."""
    result = ScraperResult(
        url="https://test.com", title="Title",
        content="A" * 1000, link="https://test.com", success=True
    )

    assert result.content_length == 1000


def test_scraper_result_empty_content():
    """Test content_length with empty content."""
    result = ScraperResult(
        url="https://test.com", title="Title",
        content="", link="https://test.com", success=True
    )

    assert result.content_length == 0

# HTMLScraper Tests


def test_html_scraper_fetch_html(mock_requests_get, sample_html):
    """Test HTML fetching."""
    scraper = GenericHTMLScraper()
    html = scraper.fetch_html("https://example.com")

    assert html == sample_html
    mock_requests_get.assert_called_once()


def test_html_scraper_parse_html(sample_html):
    """Test HTML parsing with CSS selector."""
    scraper = GenericHTMLScraper()

    paragraphs = scraper.parse_html(sample_html, 'p')
    assert len(paragraphs) == 2
    assert paragraphs[0] == "First paragraph."
    assert paragraphs[1] == "Second paragraph."


def test_html_scraper_extract_content(sample_html):
    """Test content extraction."""
    scraper = GenericHTMLScraper()

    title, content = scraper.extract_content(sample_html, 'h1', 'article p')
    assert title == "Test Title"
    assert "First paragraph" in content
    assert "Second paragraph" in content


def test_html_scraper_matches_domain():
    """Test domain matching."""
    # Import ScraperMetadata to create a test scraper with specific domains
    from scrapetui.scrapers.base import ScraperMetadata, ScraperType

    # Create a test scraper class with specific metadata
    class TestDomainScraper(HTMLScraper):
        metadata = ScraperMetadata(
            name="Test Domain Scraper",
            description="Test",
            version="1.0.0",
            author="Test",
            scraper_type=ScraperType.HTML,
            supported_domains=["example.com", "*.test.com"]
        )

        def can_handle(self, url: str) -> bool:
            return self.matches_domain(url)

        def scrape(self, url: str, **kwargs) -> ScraperResult:
            pass  # Not used in this test

    scraper = TestDomainScraper()

    assert scraper.matches_domain("https://example.com/article")
    assert scraper.matches_domain("https://sub.test.com/page")
    assert not scraper.matches_domain("https://other.com")


def test_html_scraper_wildcard_domain():
    """Test wildcard domain matching."""
    from scrapetui.scrapers.base import ScraperMetadata, ScraperType

    class TestWildcardScraper(HTMLScraper):
        metadata = ScraperMetadata(
            name="Test Wildcard Scraper",
            description="Test",
            version="1.0.0",
            author="Test",
            scraper_type=ScraperType.HTML,
            supported_domains=["*.example.com"]
        )

        def can_handle(self, url: str) -> bool:
            return self.matches_domain(url)

        def scrape(self, url: str, **kwargs) -> ScraperResult:
            pass

    scraper = TestWildcardScraper()

    assert scraper.matches_domain("https://www.example.com")
    assert scraper.matches_domain("https://blog.example.com")
    assert not scraper.matches_domain("https://example.com")


def test_html_scraper_extract_no_title(sample_html):
    """Test extraction with no title found."""
    scraper = GenericHTMLScraper()

    title, content = scraper.extract_content(sample_html, 'h2', 'article p')
    assert title == "No title"
    assert "First paragraph" in content


def test_html_scraper_extract_no_content(sample_html):
    """Test extraction with no content found."""
    scraper = GenericHTMLScraper()

    title, content = scraper.extract_content(sample_html, 'h1', 'section p')
    assert title == "Test Title"
    assert content == "No content"

# GenericHTMLScraper Tests


def test_generic_scraper_can_handle():
    """Test GenericHTMLScraper can handle any HTTP(S) URL."""
    scraper = GenericHTMLScraper()

    assert scraper.can_handle("https://example.com")
    assert scraper.can_handle("http://test.com")
    assert not scraper.can_handle("ftp://file.com")


def test_generic_scraper_scrape(mock_requests_get, sample_html):
    """Test GenericHTMLScraper scraping."""
    scraper = GenericHTMLScraper()

    result = scraper.scrape("https://example.com")

    assert result.success
    # Default selector is 'h1, title' which finds <title> first
    assert result.title == "Test Article"
    assert "First paragraph" in result.content


def test_generic_scraper_custom_selectors(mock_requests_get, sample_html):
    """Test GenericHTMLScraper with custom selectors."""
    scraper = GenericHTMLScraper()

    result = scraper.scrape(
        "https://example.com",
        title_selector='title',
        content_selector='p'
    )

    assert result.success
    assert result.title == "Test Article"


def test_generic_scraper_metadata():
    """Test GenericHTMLScraper metadata."""
    scraper = GenericHTMLScraper()

    assert scraper.metadata.name == "Generic HTML"
    assert scraper.metadata.scraper_type == ScraperType.HTML
    assert "*" in scraper.metadata.supported_domains

# Built-in Scraper Tests


def test_techcrunch_scraper_can_handle():
    """Test TechCrunchScraper domain matching."""
    scraper = TechCrunchScraper()

    assert scraper.can_handle("https://techcrunch.com/article")
    assert scraper.can_handle("https://www.techcrunch.com/article")
    assert not scraper.can_handle("https://example.com")


def test_techcrunch_scraper_metadata():
    """Test TechCrunchScraper metadata."""
    scraper = TechCrunchScraper()

    assert scraper.metadata.name == "TechCrunch"
    assert "techcrunch.com" in scraper.metadata.supported_domains


def test_bbc_scraper_can_handle():
    """Test BBCNewsScraper domain and path matching."""
    scraper = BBCNewsScraper()

    assert scraper.can_handle("https://bbc.com/news/article")
    assert scraper.can_handle("https://www.bbc.co.uk/news/uk-12345")
    assert not scraper.can_handle("https://bbc.com/sport")  # Not /news/


def test_bbc_scraper_metadata():
    """Test BBCNewsScraper metadata."""
    scraper = BBCNewsScraper()

    assert scraper.metadata.name == "BBC News"
    assert "bbc.com" in scraper.metadata.supported_domains
    assert "bbc.co.uk" in scraper.metadata.supported_domains


def test_ars_technica_scraper():
    """Test ArsTechnicaScraper initialization."""
    scraper = ArsTechnicaScraper()

    assert scraper.metadata.name == "Ars Technica"
    assert scraper.metadata.scraper_type == ScraperType.HTML
    assert "arstechnica.com" in scraper.metadata.supported_domains


def test_ars_technica_can_handle():
    """Test ArsTechnicaScraper URL handling."""
    scraper = ArsTechnicaScraper()

    assert scraper.can_handle("https://arstechnica.com/article")
    assert not scraper.can_handle("https://example.com")

# ScraperManager Tests


def test_scraper_manager_initialization():
    """Test ScraperManager loads scrapers."""
    manager = ScraperManager()

    assert len(manager.scrapers) > 0
    assert "Generic HTML" in manager.scrapers


def test_scraper_manager_loads_builtin_scrapers():
    """Test ScraperManager loads all built-in scrapers."""
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
        assert name in manager.scrapers, f"{name} not loaded"


def test_scraper_manager_register_scraper():
    """Test registering a scraper."""
    manager = ScraperManager()
    initial_count = len(manager.scrapers)

    # Create mock scraper
    mock_scraper = Mock(spec=BaseScraper)
    mock_scraper.metadata = ScraperMetadata(
        name="Test Scraper", description="Test", version="1.0.0",
        author="Test", scraper_type=ScraperType.HTML,
        supported_domains=["test.com"]
    )

    manager.register_scraper(mock_scraper)

    assert len(manager.scrapers) == initial_count + 1
    assert "Test Scraper" in manager.scrapers


def test_scraper_manager_unregister_scraper():
    """Test unregistering a scraper."""
    manager = ScraperManager()

    # Register a test scraper
    mock_scraper = Mock(spec=BaseScraper)
    mock_scraper.metadata = ScraperMetadata(
        name="Test Scraper", description="Test", version="1.0.0",
        author="Test", scraper_type=ScraperType.HTML,
        supported_domains=["test.com"]
    )
    manager.register_scraper(mock_scraper)

    # Unregister it
    manager.unregister_scraper("Test Scraper")

    assert "Test Scraper" not in manager.scrapers


def test_scraper_manager_get_scraper():
    """Test getting scraper by name."""
    manager = ScraperManager()

    scraper = manager.get_scraper("Generic HTML")
    assert scraper is not None
    assert isinstance(scraper, GenericHTMLScraper)


def test_scraper_manager_get_nonexistent_scraper():
    """Test getting nonexistent scraper."""
    manager = ScraperManager()

    scraper = manager.get_scraper("Nonexistent Scraper")
    assert scraper is None


def test_scraper_manager_get_scraper_for_url():
    """Test getting appropriate scraper for URL."""
    manager = ScraperManager()

    # Should get TechCrunch scraper
    scraper = manager.get_scraper_for_url("https://techcrunch.com/article")
    assert scraper is not None
    assert scraper.metadata.name == "TechCrunch"

    # Should get generic scraper for unknown domain
    scraper = manager.get_scraper_for_url("https://random-site.com/page")
    assert scraper is not None
    assert scraper.metadata.name == "Generic HTML"


def test_scraper_manager_list_scrapers():
    """Test listing all scrapers."""
    manager = ScraperManager()

    scrapers = manager.list_scrapers()
    assert len(scrapers) > 0
    assert all('name' in s for s in scrapers)
    assert all('version' in s for s in scrapers)


def test_scraper_manager_scrape_url(mock_requests_get):
    """Test scraping URL through manager."""
    manager = ScraperManager()

    result = manager.scrape_url("https://techcrunch.com/article")

    assert isinstance(result, ScraperResult)


def test_scraper_manager_scrape_url_specific_scraper(mock_requests_get):
    """Test scraping with specific scraper name."""
    manager = ScraperManager()

    result = manager.scrape_url(
        "https://example.com",
        scraper_name="Generic HTML"
    )

    assert isinstance(result, ScraperResult)


def test_scraper_manager_scrape_url_invalid_scraper():
    """Test scraping with invalid scraper name."""
    manager = ScraperManager()

    result = manager.scrape_url(
        "https://example.com",
        scraper_name="Nonexistent Scraper"
    )

    assert not result.success
    assert "not found" in result.error.lower()


def test_scraper_manager_scrape_url_no_scraper():
    """Test scraping with no available scraper."""
    manager = ScraperManager()

    # Remove all scrapers
    manager.scrapers.clear()

    result = manager.scrape_url("https://example.com")

    assert not result.success
    assert "no scraper" in result.error.lower()

# Error Handling Tests


def test_scraper_http_error():
    """Test scraper handles HTTP errors."""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception("Connection failed")

        scraper = GenericHTMLScraper()
        result = scraper.scrape("https://example.com")

        assert not result.success
        assert "Connection failed" in result.error


def test_scraper_invalid_html():
    """Test scraper handles invalid HTML gracefully."""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = "Not valid HTML"
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        scraper = GenericHTMLScraper()
        result = scraper.scrape("https://example.com")

        # Should still succeed but with "No title" / "No content"
        assert result.success


def test_scraper_timeout():
    """Test scraper handles timeout."""
    with patch('requests.get') as mock_get:
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")

        scraper = GenericHTMLScraper()
        result = scraper.scrape("https://example.com")

        assert not result.success
        assert "timeout" in result.error.lower()


def test_scraper_manager_scrape_exception():
    """Test manager handles scraper exceptions."""
    manager = ScraperManager()

    with patch.object(GenericHTMLScraper, 'scrape', side_effect=Exception("Scraper error")):
        result = manager.scrape_url("https://example.com")

        assert not result.success
        assert "Scraper error" in result.error

# Integration Tests


def test_scraper_manager_singleton():
    """Test ScraperManager singleton pattern."""
    from scrapetui.scrapers.manager import get_scraper_manager

    manager1 = get_scraper_manager()
    manager2 = get_scraper_manager()

    assert manager1 is manager2


def test_scraper_get_metadata():
    """Test getting scraper metadata."""
    scraper = GenericHTMLScraper()

    metadata = scraper.get_metadata()

    assert isinstance(metadata, dict)
    assert metadata['name'] == "Generic HTML"
    assert metadata['scraper_type'] == "html"


def test_scraper_validate_config():
    """Test scraper config validation."""
    scraper = GenericHTMLScraper()

    # Default implementation returns True
    assert scraper.validate_config({})
    assert scraper.validate_config({'key': 'value'})
