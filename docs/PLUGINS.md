# Plugin Development Guide - WebScrape-TUI v2.1.0

This guide explains how to create custom scraper plugins for WebScrape-TUI.

## Overview

WebScrape-TUI v2.1.0 features a plugin system that allows you to create custom scrapers for any website. Plugins are Python modules that implement the `BaseScraper` interface.

## Quick Start

### 1. Create Plugin Directory

```bash
mkdir -p plugins/scrapers
```

### 2. Create Your Scraper

Create `plugins/scrapers/my_scraper.py`:

```python
from scrapetui.scrapers.base import HTMLScraper, ScraperMetadata, ScraperResult, ScraperType

class MyScraper(HTMLScraper):
    """Scraper for my favorite website."""

    metadata = ScraperMetadata(
        name="My Scraper",
        description="Scraper for example.com",
        version="1.0.0",
        author="Your Name",
        scraper_type=ScraperType.HTML,
        supported_domains=["example.com", "*.example.com"]
    )

    def can_handle(self, url: str) -> bool:
        """Check if this scraper can handle the URL."""
        return self.matches_domain(url)

    def scrape(self, url: str, **kwargs) -> ScraperResult:
        """Scrape content from URL."""
        try:
            html = self.fetch_html(url)
            title, content = self.extract_content(
                html,
                'h1',  # Title selector
                'article p'  # Content selector
            )

            return ScraperResult(
                url=url,
                title=title,
                content=content,
                link=url,
                success=True
            )
        except Exception as e:
            return ScraperResult(
                url=url, title="", content="", link=url,
                success=False, error=str(e)
            )
```

### 3. Use Your Plugin

Your plugin is automatically loaded when WebScrape-TUI starts. Just scrape URLs from your target domain!

## Base Classes

### BaseScraper

Abstract base class for all scrapers.

**Required:**
- `metadata: ScraperMetadata` - Scraper information
- `can_handle(url: str) -> bool` - URL compatibility check
- `scrape(url: str, **kwargs) -> ScraperResult` - Scraping logic

**Optional:**
- `validate_config(config: dict) -> bool` - Configuration validation

### HTMLScraper

Specialized base class for HTML scraping (most common).

**Provides:**
- `fetch_html(url: str) -> str` - Fetch HTML content
- `parse_html(html: str, selector: str) -> List[str]` - CSS selector parsing
- `extract_content(html, title_sel, content_sel) -> (str, str)` - Title/content extraction
- `matches_domain(url: str) -> bool` - Domain matching with wildcards

## ScraperMetadata

Configuration for your scraper:

```python
metadata = ScraperMetadata(
    name="Scraper Name",              # Display name
    description="Description",         # What it scrapes
    version="1.0.0",                  # Semantic version
    author="Your Name",               # Author name
    scraper_type=ScraperType.HTML,    # HTML, API, RSS, DYNAMIC
    supported_domains=["example.com"], # Domain list (supports *)
    requires_javascript=False,         # JS required?
    rate_limit_seconds=1.0,           # Delay between requests
    max_retries=3,                    # Retry failed requests
    timeout_seconds=30                # Request timeout
)
```

## ScraperResult

Return value from `scrape()`:

```python
ScraperResult(
    url="https://example.com",        # Original URL
    title="Article Title",            # Extracted title
    content="Article content...",     # Extracted content
    link="https://example.com/article", # Canonical link
    metadata={'key': 'value'},        # Optional metadata
    success=True,                     # Success flag
    error=None                        # Error message if failed
)
```

## Advanced Examples

### Custom CSS Selectors

```python
def scrape(self, url: str, **kwargs) -> ScraperResult:
    html = self.fetch_html(url)

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'lxml')

    # Custom extraction logic
    title_elem = soup.select_one('meta[property="og:title"]')
    title = title_elem['content'] if title_elem else "No title"

    article = soup.select_one('article.main-content')
    content = article.get_text(strip=True) if article else ""

    return ScraperResult(
        url=url, title=title, content=content, link=url, success=True
    )
```

### Handling Pagination

```python
def scrape(self, url: str, **kwargs) -> ScraperResult:
    all_content = []
    current_url = url

    while current_url:
        html = self.fetch_html(current_url)
        soup = BeautifulSoup(html, 'lxml')

        # Extract page content
        page_content = soup.select('article p')
        all_content.extend([p.get_text() for p in page_content])

        # Find next page
        next_link = soup.select_one('a.next-page')
        current_url = next_link['href'] if next_link else None

    return ScraperResult(
        url=url,
        title="Multi-page Article",
        content='\n\n'.join(all_content),
        link=url,
        success=True
    )
```

### Error Handling

```python
def scrape(self, url: str, **kwargs) -> ScraperResult:
    try:
        html = self.fetch_html(url)
        title, content = self.extract_content(html, 'h1', 'article')

        # Validate extracted content
        if not content or len(content) < 100:
            raise ValueError("Content too short or empty")

        return ScraperResult(
            url=url, title=title, content=content, link=url, success=True
        )

    except requests.HTTPError as e:
        return ScraperResult(
            url=url, title="", content="", link=url,
            success=False, error=f"HTTP error: {e}"
        )
    except Exception as e:
        return ScraperResult(
            url=url, title="", content="", link=url,
            success=False, error=f"Scraping failed: {e}"
        )
```

### Extracting Metadata

```python
def scrape(self, url: str, **kwargs) -> ScraperResult:
    html = self.fetch_html(url)
    soup = BeautifulSoup(html, 'lxml')

    # Extract title and content
    title = soup.select_one('h1').get_text(strip=True)
    content = '\n\n'.join([p.get_text(strip=True) for p in soup.select('article p')])

    # Extract metadata
    metadata = {}

    # Author
    author_elem = soup.select_one('meta[name="author"]')
    if author_elem:
        metadata['author'] = author_elem.get('content', '')

    # Publication date
    date_elem = soup.select_one('meta[property="article:published_time"]')
    if date_elem:
        metadata['published_date'] = date_elem.get('content', '')

    # Tags
    tag_elems = soup.select('meta[property="article:tag"]')
    if tag_elems:
        metadata['tags'] = [tag.get('content', '') for tag in tag_elems]

    return ScraperResult(
        url=url, title=title, content=content, link=url,
        metadata=metadata, success=True
    )
```

### API-Based Scraper

```python
from scrapetui.scrapers.base import BaseScraper, ScraperMetadata, ScraperResult, ScraperType
import requests
import json

class MyAPIScraper(BaseScraper):
    """Scraper for API-based content."""

    metadata = ScraperMetadata(
        name="My API Scraper",
        description="Scraper using REST API",
        version="1.0.0",
        author="Your Name",
        scraper_type=ScraperType.API,
        supported_domains=["api.example.com"]
    )

    def can_handle(self, url: str) -> bool:
        return self.matches_domain(url)

    def scrape(self, url: str, **kwargs) -> ScraperResult:
        try:
            response = requests.get(url, timeout=self.metadata.timeout_seconds)
            response.raise_for_status()

            data = response.json()

            return ScraperResult(
                url=url,
                title=data.get('title', 'No title'),
                content=data.get('body', ''),
                link=data.get('url', url),
                metadata={'source': 'api'},
                success=True
            )
        except Exception as e:
            return ScraperResult(
                url=url, title="", content="", link=url,
                success=False, error=str(e)
            )
```

### RSS Feed Scraper

```python
from scrapetui.scrapers.base import BaseScraper, ScraperMetadata, ScraperResult, ScraperType
import feedparser

class MyRSSScraper(BaseScraper):
    """Scraper for RSS feeds."""

    metadata = ScraperMetadata(
        name="My RSS Scraper",
        description="RSS feed scraper",
        version="1.0.0",
        author="Your Name",
        scraper_type=ScraperType.RSS,
        supported_domains=["example.com/feed"]
    )

    def can_handle(self, url: str) -> bool:
        return 'feed' in url.lower() or url.endswith('.xml')

    def scrape(self, url: str, **kwargs) -> ScraperResult:
        try:
            feed = feedparser.parse(url)

            if not feed.entries:
                raise ValueError("No entries found in feed")

            # Get the first entry (or all entries)
            entry = feed.entries[0]

            return ScraperResult(
                url=url,
                title=entry.get('title', 'No title'),
                content=entry.get('summary', entry.get('description', '')),
                link=entry.get('link', url),
                metadata={'feed_title': feed.feed.get('title', '')},
                success=True
            )
        except Exception as e:
            return ScraperResult(
                url=url, title="", content="", link=url,
                success=False, error=str(e)
            )
```

## Testing Your Plugin

Create `tests/test_my_plugin.py`:

```python
import pytest
from plugins.scrapers.my_scraper import MyScraper

def test_can_handle():
    scraper = MyScraper()
    assert scraper.can_handle("https://example.com/article")
    assert not scraper.can_handle("https://other.com/article")

def test_metadata():
    scraper = MyScraper()
    assert scraper.metadata.name == "My Scraper"
    assert scraper.metadata.version == "1.0.0"

def test_scrape_mock():
    from unittest.mock import patch, Mock

    scraper = MyScraper()

    # Mock HTML response
    mock_html = """
    <html>
        <body>
            <h1>Test Title</h1>
            <article>
                <p>Test content paragraph 1.</p>
                <p>Test content paragraph 2.</p>
            </article>
        </body>
    </html>
    """

    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = scraper.scrape("https://example.com/test")

        assert result.success
        assert result.title == "Test Title"
        assert "Test content" in result.content
```

Run tests:
```bash
pytest tests/test_my_plugin.py -v
```

## Best Practices

1. **Be Respectful**: Follow rate limits, check robots.txt
2. **Handle Errors**: Always catch exceptions and return proper errors
3. **Validate Content**: Check that extracted content makes sense
4. **Document Selectors**: Comment why you chose specific CSS selectors
5. **Test Thoroughly**: Test with multiple URLs from target site
6. **Version Control**: Use semantic versioning for your plugins
7. **Minimal Dependencies**: Only import what you need

## Plugin Distribution

### Packaging Your Plugin

Create a `setup.py` for your plugin:

```python
from setuptools import setup

setup(
    name='webscrape-tui-plugin-example',
    version='1.0.0',
    author='Your Name',
    description='Example scraper plugin for WebScrape-TUI',
    py_modules=['my_scraper'],
    install_requires=[
        'beautifulsoup4>=4.9.0',
        'lxml>=4.6.0',
        'requests>=2.25.0'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)
```

### Sharing Your Plugin

1. **GitHub**: Create a repository with your plugin code
2. **PyPI**: Publish to Python Package Index
3. **Documentation**: Include README with installation and usage
4. **Examples**: Provide example URLs that work with your scraper
5. **License**: Include appropriate open-source license

## Plugin Examples

See built-in scrapers for examples:
- `scrapetui/scrapers/builtin/generic.py` - Generic HTML scraper
- `scrapetui/scrapers/builtin/news.py` - News site scrapers
- `scrapetui/scrapers/builtin/tech.py` - Tech site scrapers

## Troubleshooting

**Plugin not loading:**
- Check file is in `plugins/scrapers/`
- Ensure class inherits from `BaseScraper` or `HTMLScraper`
- Check for syntax errors
- Look at logs for error messages

**Scraping fails:**
- Verify CSS selectors with browser DevTools
- Check if site requires JavaScript (use ScraperType.DYNAMIC)
- Ensure site is accessible (check robots.txt)
- Add better error handling

**Content extraction issues:**
- Inspect HTML structure of target site
- Try different CSS selectors
- Use BeautifulSoup directly for complex extraction
- Check for dynamic content loading

**Domain matching not working:**
- Verify domain in `supported_domains` list
- Use wildcards for subdomains: `*.example.com`
- Check URL format (http:// vs https://)
- Test with `matches_domain()` method

## Advanced Topics

### Rate Limiting

Respect rate limits by configuring `rate_limit_seconds`:

```python
metadata = ScraperMetadata(
    name="Polite Scraper",
    # ... other fields ...
    rate_limit_seconds=2.0  # Wait 2 seconds between requests
)
```

### User Agents

Customize user agent for requests:

```python
def fetch_html(self, url: str) -> str:
    response = requests.get(
        url,
        timeout=self.metadata.timeout_seconds,
        headers={
            'User-Agent': 'MyBot/1.0 (contact@example.com)',
            'Accept': 'text/html,application/xhtml+xml'
        }
    )
    return response.text
```

### Authentication

Handle authenticated scraping:

```python
def scrape(self, url: str, **kwargs) -> ScraperResult:
    # Get credentials from kwargs
    api_key = kwargs.get('api_key')

    if not api_key:
        return ScraperResult(
            url=url, title="", content="", link=url,
            success=False, error="API key required"
        )

    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get(url, headers=headers)
    # ... rest of scraping logic
```

### Caching

Use the built-in cache system:

```python
from scrapetui.core.cache import get_cache

def scrape(self, url: str, **kwargs) -> ScraperResult:
    cache = get_cache()
    cache_key = f"scraper:{url}"

    # Check cache
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    # Scrape and cache
    result = self._do_scrape(url)
    cache.set(cache_key, result, ttl=3600)  # Cache for 1 hour

    return result
```

## Support

For help with plugin development:
- GitHub Issues: https://github.com/doublegate/WebScrape-TUI/issues
- Documentation: https://github.com/doublegate/WebScrape-TUI/tree/main/docs
- Examples: `scrapetui/scrapers/builtin/`
