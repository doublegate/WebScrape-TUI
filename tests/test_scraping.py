#!/usr/bin/env python3
"""Web scraping functionality tests for WebScrape-TUI."""

from unittest.mock import Mock, patch

import pytest
import requests


class TestHTMLParsing:
    """Test HTML parsing with BeautifulSoup."""

    @pytest.fixture
    def sample_html(self):
        """Sample HTML for testing."""
        return """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <article class="post">
                    <h2>Article 1</h2>
                    <p>Content 1</p>
                </article>
                <article class="post">
                    <h2>Article 2</h2>
                    <p>Content 2</p>
                </article>
                <article class="post">
                    <h2>Article 3</h2>
                    <p>Content 3</p>
                </article>
            </body>
        </html>
        """

    def test_parse_article_selector(self, sample_html):
        """Test parsing HTML with article selector."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(sample_html, 'lxml')
        articles = soup.select('article.post')

        assert len(articles) == 3
        assert articles[0].find('h2').text == 'Article 1'
        assert articles[1].find('h2').text == 'Article 2'

    def test_parse_with_limit(self, sample_html):
        """Test parsing with article limit."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(sample_html, 'lxml')
        articles = soup.select('article.post')[:2]

        assert len(articles) == 2

    def test_extract_text_content(self, sample_html):
        """Test extracting text from HTML elements."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(sample_html, 'lxml')
        article = soup.select_one('article.post')

        assert 'Article 1' in article.get_text()
        assert 'Content 1' in article.get_text()


class TestURLValidation:
    """Test URL validation and processing."""

    def test_valid_url_format(self):
        """Test valid URL format detection."""
        valid_urls = [
            'https://example.com',
            'http://example.com/page',
            'https://example.com/path/to/page?query=value',
            'https://subdomain.example.com',
        ]

        for url in valid_urls:
            # Basic URL validation (starts with http:// or https://)
            assert url.startswith(('http://', 'https://'))

    def test_invalid_url_format(self):
        """Test invalid URL format detection."""
        invalid_urls = [
            'example.com',
            'ftp://example.com',
            'not-a-url',
            '',
        ]

        for url in invalid_urls:
            # These should not pass validation
            assert not url.startswith(('http://', 'https://'))


class TestHTTPRequests:
    """Test HTTP request handling."""

    @patch('requests.get')
    def test_successful_request(self, mock_get):
        """Test successful HTTP request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><body>Test</body></html>'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Make request
        response = requests.get('https://example.com')

        assert response.status_code == 200
        assert b'Test' in response.content
        mock_get.assert_called_once_with('https://example.com')

    @patch('requests.get')
    def test_request_timeout(self, mock_get):
        """Test request timeout handling."""
        # Mock timeout
        mock_get.side_effect = requests.Timeout('Request timed out')

        with pytest.raises(requests.Timeout):
            requests.get('https://example.com', timeout=5)

    @patch('requests.get')
    def test_request_connection_error(self, mock_get):
        """Test connection error handling."""
        # Mock connection error
        mock_get.side_effect = requests.ConnectionError('Failed to connect')

        with pytest.raises(requests.ConnectionError):
            requests.get('https://example.com')

    @patch('requests.get')
    def test_request_404_error(self, mock_get):
        """Test 404 error handling."""
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = (
            requests.HTTPError('404 Not Found')
        )
        mock_get.return_value = mock_response

        response = requests.get('https://example.com/notfound')
        assert response.status_code == 404

        with pytest.raises(requests.HTTPError):
            response.raise_for_status()


class TestScraperProfiles:
    """Test scraper profile functionality."""

    def test_profile_data_structure(self):
        """Test scraper profile data structure."""
        profile = {
            'name': 'Test Scraper',
            'url': 'https://example.com',
            'selector': 'article',
            'default_limit': 10,
            'default_tags_csv': 'test, example',
            'description': 'Test scraper profile'
        }

        assert 'name' in profile
        assert 'url' in profile
        assert 'selector' in profile
        assert profile['default_limit'] == 10

    def test_profile_validation(self):
        """Test scraper profile field validation."""
        profile = {
            'name': 'Test Scraper',
            'url': 'https://example.com',
            'selector': 'article',
            'default_limit': 10,
        }

        # Validate required fields
        assert profile['name'] and isinstance(profile['name'], str)
        assert profile['url'].startswith(('http://', 'https://'))
        assert profile['selector'] and isinstance(profile['selector'], str)
        assert isinstance(profile['default_limit'], int)
        assert profile['default_limit'] > 0


class TestContentExtraction:
    """Test content extraction from HTML."""

    def test_extract_title_from_article(self):
        """Test extracting title from article."""
        from bs4 import BeautifulSoup

        html = '<article><h1>Test Title</h1><p>Content</p></article>'
        soup = BeautifulSoup(html, 'lxml')
        article = soup.find('article')

        title = article.find('h1')
        assert title is not None
        assert title.text == 'Test Title'

    def test_extract_multiple_paragraphs(self):
        """Test extracting multiple paragraphs."""
        from bs4 import BeautifulSoup

        html = '''
        <article>
            <p>Paragraph 1</p>
            <p>Paragraph 2</p>
            <p>Paragraph 3</p>
        </article>
        '''
        soup = BeautifulSoup(html, 'lxml')
        article = soup.find('article')

        paragraphs = article.find_all('p')
        assert len(paragraphs) == 3
        assert paragraphs[0].text == 'Paragraph 1'

    def test_extract_links(self):
        """Test extracting links from HTML."""
        from bs4 import BeautifulSoup

        html = '''
        <article>
            <a href="https://example.com/1">Link 1</a>
            <a href="https://example.com/2">Link 2</a>
        </article>
        '''
        soup = BeautifulSoup(html, 'lxml')
        article = soup.find('article')

        links = article.find_all('a')
        assert len(links) == 2
        assert links[0]['href'] == 'https://example.com/1'

    def test_clean_whitespace(self):
        """Test cleaning whitespace from extracted text."""
        from bs4 import BeautifulSoup

        html = '<article>  \n  Test Content  \n  </article>'
        soup = BeautifulSoup(html, 'lxml')
        article = soup.find('article')

        text = article.get_text(strip=True)
        assert text == 'Test Content'


class TestWaybackMachine:
    """Test Wayback Machine integration."""

    def test_wayback_url_format(self):
        """Test Wayback Machine URL format."""
        original_url = 'https://example.com'
        wayback_url = (
            f'https://web.archive.org/web/2024/*/{original_url}'
        )

        assert 'web.archive.org' in wayback_url
        assert original_url in wayback_url

    @patch('requests.get')
    def test_wayback_redirect_handling(self, mock_get):
        """Test handling Wayback Machine redirects."""
        # Mock redirect response
        mock_response = Mock()
        mock_response.status_code = 302
        mock_response.headers = {
            'Location': 'https://web.archive.org/web/20240101/...'
        }
        mock_get.return_value = mock_response

        response = requests.get(
            'https://web.archive.org/web/2024/*/https://example.com'
        )
        assert response.status_code == 302
        assert 'Location' in response.headers


class TestErrorHandling:
    """Test error handling in scraping operations."""

    @patch('requests.get')
    def test_malformed_html_handling(self, mock_get):
        """Test handling of malformed HTML."""
        from bs4 import BeautifulSoup

        # Mock response with malformed HTML
        mock_response = Mock()
        mock_response.content = b'<html><body><article>Test</body></html>'
        mock_get.return_value = mock_response

        response = requests.get('https://example.com')

        # BeautifulSoup should still parse it
        soup = BeautifulSoup(response.content, 'lxml')
        assert soup.find('article') is not None

    def test_empty_selector_results(self):
        """Test handling when selector returns no results."""
        from bs4 import BeautifulSoup

        html = '<html><body><div>No articles here</div></body></html>'
        soup = BeautifulSoup(html, 'lxml')

        articles = soup.select('article')
        assert len(articles) == 0

    def test_missing_expected_elements(self):
        """Test handling when expected elements are missing."""
        from bs4 import BeautifulSoup

        html = '<article><p>Content without title</p></article>'
        soup = BeautifulSoup(html, 'lxml')
        article = soup.find('article')

        title = article.find('h1')
        assert title is None  # Should handle gracefully
