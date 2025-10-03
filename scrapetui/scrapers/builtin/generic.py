"""Generic HTML scraper for any website."""

from ..base import HTMLScraper, ScraperMetadata, ScraperResult, ScraperType


class GenericHTMLScraper(HTMLScraper):
    """Generic scraper that works with any HTML page."""

    metadata = ScraperMetadata(
        name="Generic HTML",
        description="Generic scraper for any HTML website",
        version="1.0.0",
        author="WebScrape-TUI",
        scraper_type=ScraperType.HTML,
        supported_domains=["*"],  # Matches any domain
        requires_javascript=False,
        rate_limit_seconds=1.0
    )

    def can_handle(self, url: str) -> bool:
        """Generic scraper can handle any URL."""
        return url.startswith('http://') or url.startswith('https://')

    def scrape(self, url: str, **kwargs) -> ScraperResult:
        """
        Scrape content from URL using provided selectors.

        Args:
            url: URL to scrape
            title_selector: CSS selector for title (default: 'h1, title')
            content_selector: CSS selector for content (default: 'article, main, .content, p')

        Returns:
            ScraperResult with scraped content
        """
        title_selector = kwargs.get('title_selector', 'h1, title')
        content_selector = kwargs.get('content_selector', 'article, main, .content, p')

        try:
            # Fetch HTML
            html = self.fetch_html(url)

            # Extract content
            title, content = self.extract_content(html, title_selector, content_selector)

            return ScraperResult(
                url=url,
                title=title,
                content=content,
                link=url,
                metadata={
                    'scraper': self.metadata.name,
                    'title_selector': title_selector,
                    'content_selector': content_selector
                },
                success=True
            )

        except Exception as e:
            return ScraperResult(
                url=url,
                title="",
                content="",
                link=url,
                success=False,
                error=str(e)
            )
