"""Scrapers for technology news websites."""

from ..base import HTMLScraper, ScraperMetadata, ScraperResult, ScraperType


class ArsTechnicaScraper(HTMLScraper):
    """Scraper for Ars Technica articles."""

    metadata = ScraperMetadata(
        name="Ars Technica",
        description="Scraper for Ars Technica technology news",
        version="1.0.0",
        author="WebScrape-TUI",
        scraper_type=ScraperType.HTML,
        supported_domains=["arstechnica.com", "*.arstechnica.com"]
    )

    def can_handle(self, url: str) -> bool:
        return self.matches_domain(url)

    def scrape(self, url: str, **kwargs) -> ScraperResult:
        try:
            html = self.fetch_html(url)
            title, content = self.extract_content(
                html,
                'h1.heading, h1',
                'article .article-content, article p'
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


class TheVergeScraper(HTMLScraper):
    """Scraper for The Verge articles."""

    metadata = ScraperMetadata(
        name="The Verge",
        description="Scraper for The Verge technology news",
        version="1.0.0",
        author="WebScrape-TUI",
        scraper_type=ScraperType.HTML,
        supported_domains=["theverge.com", "*.theverge.com"]
    )

    def can_handle(self, url: str) -> bool:
        return self.matches_domain(url)

    def scrape(self, url: str, **kwargs) -> ScraperResult:
        try:
            html = self.fetch_html(url)
            title, content = self.extract_content(
                html,
                'h1.duet--article--article-title, h1',
                'article .duet--article--article-body, article p'
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


class WiredScraper(HTMLScraper):
    """Scraper for Wired articles."""

    metadata = ScraperMetadata(
        name="Wired",
        description="Scraper for Wired technology magazine",
        version="1.0.0",
        author="WebScrape-TUI",
        scraper_type=ScraperType.HTML,
        supported_domains=["wired.com", "*.wired.com"]
    )

    def can_handle(self, url: str) -> bool:
        return self.matches_domain(url)

    def scrape(self, url: str, **kwargs) -> ScraperResult:
        try:
            html = self.fetch_html(url)
            title, content = self.extract_content(
                html,
                'h1[data-testid="ContentHeaderHed"], h1',
                'article .body__inner-container, article p'
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
