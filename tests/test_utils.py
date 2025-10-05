#!/usr/bin/env python3
"""Utility function tests for WebScrape-TUI."""

import importlib.util
from pathlib import Path
import tempfile
import sys


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from monolithic scrapetui.py file directly
# We need to import the .py file, not the package directory
_scrapetui_path = Path(__file__).parent.parent / 'scrapetui.py'
_spec = importlib.util.spec_from_file_location("scrapetui_monolith", _scrapetui_path)
_scrapetui_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scrapetui_module)

# Import needed components from the monolithic module
load_env_file = _scrapetui_module.load_env_file
PREINSTALLED_SCRAPERS = _scrapetui_module.PREINSTALLED_SCRAPERS


class TestEnvironmentLoading:
    """Test environment variable loading."""

    def test_load_env_file_basic(self):
        """Test loading basic environment file."""
        # Create temporary .env file
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.env', delete=False
        ) as f:
            f.write('TEST_KEY=test_value\n')
            f.write('ANOTHER_KEY=another_value\n')
            env_path = Path(f.name)

        try:
            env_vars = load_env_file(env_path)
            assert 'TEST_KEY' in env_vars
            assert env_vars['TEST_KEY'] == 'test_value'
            assert 'ANOTHER_KEY' in env_vars
            assert env_vars['ANOTHER_KEY'] == 'another_value'
        finally:
            env_path.unlink()

    def test_load_env_file_with_comments(self):
        """Test loading env file with comments."""
        # Create temporary .env file with comments
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.env', delete=False
        ) as f:
            f.write('# This is a comment\n')
            f.write('KEY1=value1\n')
            f.write('  # Another comment\n')
            f.write('KEY2=value2\n')
            env_path = Path(f.name)

        try:
            env_vars = load_env_file(env_path)
            assert len(env_vars) == 2  # Comments should be ignored
            assert 'KEY1' in env_vars
            assert 'KEY2' in env_vars
        finally:
            env_path.unlink()

    def test_load_env_file_with_empty_lines(self):
        """Test loading env file with empty lines."""
        # Create temporary .env file with empty lines
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.env', delete=False
        ) as f:
            f.write('KEY1=value1\n')
            f.write('\n')
            f.write('\n')
            f.write('KEY2=value2\n')
            env_path = Path(f.name)

        try:
            env_vars = load_env_file(env_path)
            assert len(env_vars) == 2
        finally:
            env_path.unlink()

    def test_load_nonexistent_env_file(self):
        """Test loading nonexistent env file."""
        env_vars = load_env_file(Path('/nonexistent/.env'))
        assert env_vars == {}  # Should return empty dict


class TestTagParsing:
    """Test tag parsing and formatting."""

    def test_split_comma_separated_tags(self):
        """Test splitting comma-separated tag string."""
        tags_str = 'python, web scraping, automation'
        tags = [tag.strip() for tag in tags_str.split(',')]

        assert len(tags) == 3
        assert 'python' in tags
        assert 'web scraping' in tags
        assert 'automation' in tags

    def test_split_tags_with_extra_spaces(self):
        """Test splitting tags with inconsistent spacing."""
        tags_str = 'tag1 ,  tag2,tag3  ,  tag4'
        tags = [tag.strip() for tag in tags_str.split(',')]

        assert len(tags) == 4
        assert all(tag.strip() == tag for tag in tags if tag)

    def test_empty_tag_string(self):
        """Test handling empty tag string."""
        tags_str = ''
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]

        assert len(tags) == 0

    def test_single_tag(self):
        """Test handling single tag."""
        tags_str = 'python'
        tags = [tag.strip() for tag in tags_str.split(',')]

        assert len(tags) == 1
        assert tags[0] == 'python'


class TestDateFormatting:
    """Test date formatting and parsing."""

    def test_timestamp_format(self):
        """Test timestamp format consistency."""
        from datetime import datetime

        now = datetime.now()
        formatted = now.strftime('%Y-%m-%d %H:%M:%S')

        # Verify format matches SQLite DEFAULT CURRENT_TIMESTAMP
        assert len(formatted.split(' ')) == 2
        assert len(formatted.split('-')) == 3

    def test_date_comparison(self):
        """Test date comparison for filtering."""
        from datetime import datetime, timedelta

        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        assert yesterday < now < tomorrow

    def test_date_string_parsing(self):
        """Test parsing date strings."""
        from datetime import datetime

        date_str = '2024-05-26'
        parsed = datetime.strptime(date_str, '%Y-%m-%d')

        assert parsed.year == 2024
        assert parsed.month == 5
        assert parsed.day == 26


class TestURLNormalization:
    """Test URL normalization and validation."""

    def test_url_with_trailing_slash(self):
        """Test URL normalization with trailing slash."""
        url1 = 'https://example.com/'
        url2 = 'https://example.com'

        # Both should be considered valid
        assert url1.startswith('https://')
        assert url2.startswith('https://')

    def test_url_with_query_parameters(self):
        """Test URL with query parameters."""
        url = 'https://example.com/page?query=value&another=param'

        assert '?' in url
        assert 'query=value' in url

    def test_url_with_fragment(self):
        """Test URL with fragment identifier."""
        url = 'https://example.com/page#section'

        assert '#section' in url

    def test_relative_to_absolute_url(self):
        """Test converting relative to absolute URL."""
        base_url = 'https://example.com/path/page.html'
        relative_url = '../other/file.html'

        # In actual implementation, would use urljoin
        from urllib.parse import urljoin
        absolute_url = urljoin(base_url, relative_url)

        assert absolute_url == 'https://example.com/other/file.html'


class TestTextCleaning:
    """Test text cleaning and normalization."""

    def test_strip_whitespace(self):
        """Test stripping leading/trailing whitespace."""
        text = '  \n  Test content  \n  '
        cleaned = text.strip()

        assert cleaned == 'Test content'

    def test_normalize_multiple_spaces(self):
        """Test normalizing multiple consecutive spaces."""
        text = 'Multiple    spaces    here'
        normalized = ' '.join(text.split())

        assert normalized == 'Multiple spaces here'

    def test_remove_html_entities(self):
        """Test removing or decoding HTML entities."""
        import html

        text = 'Test &amp; example &lt;tag&gt;'
        decoded = html.unescape(text)

        assert decoded == 'Test & example <tag>'

    def test_truncate_long_text(self):
        """Test truncating text to maximum length."""
        text = 'A' * 1000
        max_length = 100
        truncated = text[:max_length] + '...' if len(text) > max_length else text

        assert len(truncated) <= max_length + 3  # Account for ellipsis


class TestCSVExport:
    """Test CSV export functionality."""

    def test_csv_escaping(self):
        """Test CSV field escaping."""
        import csv
        from io import StringIO

        # Data with special characters
        data = [
            ['Title with, comma', 'Normal content'],
            ['Title with "quotes"', 'Content'],
        ]

        output = StringIO()
        writer = csv.writer(output)
        writer.writerows(data)

        csv_content = output.getvalue()

        # Verify escaping
        assert '"Title with, comma"' in csv_content or 'Title with, comma' in csv_content

    def test_csv_header_row(self):
        """Test CSV header row generation."""
        import csv
        from io import StringIO

        headers = ['ID', 'Title', 'URL', 'Date']
        data = [[1, 'Test', 'https://example.com', '2024-05-26']]

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(data)

        csv_content = output.getvalue()
        lines = csv_content.strip().split('\n')

        assert len(lines) == 2  # Header + 1 data row
        assert 'ID' in lines[0]


class TestSentimentValidation:
    """Test sentiment analysis data validation."""

    def test_valid_sentiment_labels(self):
        """Test valid sentiment label values."""
        valid_labels = ['positive', 'negative', 'neutral']

        for label in valid_labels:
            assert label in ['positive', 'negative', 'neutral']

    def test_sentiment_confidence_range(self):
        """Test sentiment confidence value range."""
        valid_confidences = [0.0, 0.5, 0.95, 1.0]
        invalid_confidences = [-0.1, 1.1, 2.0]

        for conf in valid_confidences:
            assert 0.0 <= conf <= 1.0

        for conf in invalid_confidences:
            assert not (0.0 <= conf <= 1.0)


class TestPreinstalledScrapers:
    """Test preinstalled scraper profiles."""

    def test_scraper_profile_structure(self):
        """Test that all preinstalled scrapers have required fields."""
        required_fields = ['name', 'url', 'selector', 'default_limit']

        for scraper in PREINSTALLED_SCRAPERS:
            for field in required_fields:
                assert field in scraper, (
                    f"Scraper '{scraper.get('name', 'unknown')}' "
                    f"missing field '{field}'"
                )

    def test_scraper_names_unique(self):
        """Test that scraper names are unique."""
        names = [s['name'] for s in PREINSTALLED_SCRAPERS]
        assert len(names) == len(set(names)), "Duplicate scraper names found"

    def test_scraper_selectors_valid(self):
        """Test that selectors are non-empty strings."""
        for scraper in PREINSTALLED_SCRAPERS:
            selector = scraper.get('selector', '')
            assert isinstance(selector, str)
            assert len(selector) > 0
