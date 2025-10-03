"""Scrapers for popular news websites."""

from ..base import HTMLScraper, ScraperMetadata, ScraperResult, ScraperType


class TechCrunchScraper(HTMLScraper):
    """Scraper for TechCrunch articles."""

    metadata = ScraperMetadata(
        name="TechCrunch",
        description="Scraper for TechCrunch technology news",
        version="1.0.0",
        author="WebScrape-TUI",
        scraper_type=ScraperType.HTML,
        supported_domains=["techcrunch.com", "*.techcrunch.com"],
        requires_javascript=False
    )

    def can_handle(self, url: str) -> bool:
        """Check if URL is from TechCrunch."""
        return self.matches_domain(url)

    def scrape(self, url: str, **kwargs) -> ScraperResult:
        """Scrape TechCrunch article."""
        try:
            html = self.fetch_html(url)
            title, content = self.extract_content(
                html,
                'h1.article__title, h1',
                'article .article-content, .article__content, article p'
            )

            return ScraperResult(
                url=url,
                title=title,
                content=content,
                link=url,
                metadata={'scraper': self.metadata.name},
                success=True
            )
        except Exception as e:
            return ScraperResult(
                url=url, title="", content="", link=url,
                success=False, error=str(e)
            )


class BBCNewsScraper(HTMLScraper):
    """Scraper for BBC News articles."""

    metadata = ScraperMetadata(
        name="BBC News",
        description="Scraper for BBC News articles",
        version="1.0.0",
        author="WebScrape-TUI",
        scraper_type=ScraperType.HTML,
        supported_domains=["bbc.com", "*.bbc.com", "bbc.co.uk", "*.bbc.co.uk"],
        requires_javascript=False
    )

    def can_handle(self, url: str) -> bool:
        """Check if URL is from BBC."""
        return self.matches_domain(url) and '/news/' in url

    def scrape(self, url: str, **kwargs) -> ScraperResult:
        """Scrape BBC News article."""
        try:
            html = self.fetch_html(url)
            title, content = self.extract_content(
                html,
                'h1#main-heading, h1',
                'article .article__body-content, article p, [data-component="text-block"]'
            )

            return ScraperResult(
                url=url, title=title, content=content, link=url,
                metadata={'scraper': self.metadata.name}, success=True
            )
        except Exception as e:
            return ScraperResult(
                url=url, title="", content="", link=url,
                success=False, error=str(e)
            )


class TheGuardianScraper(HTMLScraper):
    """Scraper for The Guardian articles."""

    metadata = ScraperMetadata(
        name="The Guardian",
        description="Scraper for The Guardian news",
        version="1.0.0",
        author="WebScrape-TUI",
        scraper_type=ScraperType.HTML,
        supported_domains=["theguardian.com", "*.theguardian.com"],
        requires_javascript=False
    )

    def can_handle(self, url: str) -> bool:
        """Check if URL is from The Guardian."""
        return self.matches_domain(url)

    def scrape(self, url: str, **kwargs) -> ScraperResult:
        """Scrape The Guardian article."""
        try:
            html = self.fetch_html(url)
            title, content = self.extract_content(
                html,
                'h1[itemprop="headline"], h1',
                'article .article-body-commercial-selector, article p'
            )

            return ScraperResult(
                url=url, title=title, content=content, link=url,
                metadata={'scraper': self.metadata.name}, success=True
            )
        except Exception as e:
            return ScraperResult(
                url=url, title="", content="", link=url,
                success=False, error=str(e)
            )
