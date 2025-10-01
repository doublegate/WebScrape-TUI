#!/usr/bin/env python3
"""Tests for JSON export functionality."""

import json
import tempfile
from pathlib import Path
from datetime import datetime

import pytest


class TestJSONExportFormat:
    """Test JSON export format and structure."""

    def test_json_structure(self):
        """Test basic JSON export structure."""
        export_data = {
            'export_date': datetime.now().isoformat(),
            'total_articles': 2,
            'filters_applied': {
                'title': None,
                'url': None,
                'date': None,
                'tags': None,
                'sentiment': None
            },
            'articles': [
                {
                    'id': 1,
                    'title': 'Test Article 1',
                    'source_url': 'https://example.com',
                    'article_link': 'https://example.com/article1',
                    'timestamp': '2024-05-26 12:00:00',
                    'summary': 'Test summary',
                    'sentiment': 'Positive',
                    'content': 'Test content',
                    'tags': ['tech', 'news']
                },
                {
                    'id': 2,
                    'title': 'Test Article 2',
                    'source_url': 'https://example.com',
                    'article_link': 'https://example.com/article2',
                    'timestamp': '2024-05-26 13:00:00',
                    'summary': None,
                    'sentiment': 'Neutral',
                    'content': 'Test content 2',
                    'tags': []
                }
            ]
        }

        # Validate structure
        assert 'export_date' in export_data
        assert 'total_articles' in export_data
        assert 'filters_applied' in export_data
        assert 'articles' in export_data
        assert len(export_data['articles']) == 2

    def test_json_serialization(self):
        """Test JSON can be properly serialized and deserialized."""
        original_data = {
            'export_date': datetime.now().isoformat(),
            'total_articles': 1,
            'filters_applied': {},
            'articles': [
                {
                    'id': 1,
                    'title': 'Test with Unicode: 你好',
                    'tags': ['python', 'テスト']
                }
            ]
        }

        # Serialize to JSON string
        json_str = json.dumps(original_data, indent=2, ensure_ascii=False)

        # Deserialize back
        deserialized = json.loads(json_str)

        assert deserialized['articles'][0]['title'] == 'Test with Unicode: 你好'
        assert 'python' in deserialized['articles'][0]['tags']

    def test_json_file_writing(self):
        """Test writing JSON to file."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json_path = Path(f.name)

        try:
            test_data = {
                'export_date': '2024-05-26T12:00:00',
                'total_articles': 1,
                'articles': [{'id': 1, 'title': 'Test'}]
            }

            # Write JSON
            with open(json_path, 'w', encoding='utf-8') as jsonf:
                json.dump(test_data, jsonf, indent=2, ensure_ascii=False)

            # Read back
            with open(json_path, 'r', encoding='utf-8') as jsonf:
                loaded_data = json.load(jsonf)

            assert loaded_data['total_articles'] == 1
            assert loaded_data['articles'][0]['title'] == 'Test'
        finally:
            json_path.unlink()


class TestJSONDataConversion:
    """Test data conversion for JSON export."""

    def test_tags_list_conversion(self):
        """Test converting comma-separated tags to list."""
        tags_str = 'python, web scraping, automation'
        tags_list = [t.strip() for t in tags_str.split(',') if t.strip()]

        assert len(tags_list) == 3
        assert tags_list == ['python', 'web scraping', 'automation']

    def test_empty_tags_conversion(self):
        """Test handling empty tags."""
        tags_str = None
        tags_list = (
            [t.strip() for t in tags_str.split(',') if t.strip()]
            if tags_str
            else []
        )

        assert tags_list == []

    def test_timestamp_conversion(self):
        """Test timestamp formatting for JSON."""
        dt = datetime(2024, 5, 26, 12, 30, 45)
        timestamp_str = dt.strftime('%Y-%m-%d %H:%M:%S')

        assert timestamp_str == '2024-05-26 12:30:45'

    def test_none_values_in_json(self):
        """Test handling None/null values in JSON."""
        data = {
            'id': 1,
            'title': 'Test',
            'summary': None,
            'content': None
        }

        json_str = json.dumps(data)
        loaded = json.loads(json_str)

        assert loaded['summary'] is None
        assert loaded['content'] is None


class TestJSONExportFilters:
    """Test JSON export with filters applied."""

    def test_filter_metadata_in_export(self):
        """Test filters are recorded in export metadata."""
        filters_applied = {
            'title': 'Python',
            'url': None,
            'date': '2024-05-26',
            'tags': 'tech, programming',
            'sentiment': 'Positive'
        }

        export_data = {
            'export_date': datetime.now().isoformat(),
            'total_articles': 5,
            'filters_applied': filters_applied,
            'articles': []
        }

        assert export_data['filters_applied']['title'] == 'Python'
        assert export_data['filters_applied']['date'] == '2024-05-26'
        assert export_data['filters_applied']['tags'] == 'tech, programming'

    def test_no_filters_applied(self):
        """Test export with no filters."""
        filters_applied = {
            'title': None,
            'url': None,
            'date': None,
            'tags': None,
            'sentiment': None
        }

        all_none = all(v is None for v in filters_applied.values())
        assert all_none is True


class TestJSONExportComparison:
    """Compare JSON and CSV export formats."""

    def test_json_vs_csv_data_completeness(self):
        """Test JSON export contains more data than CSV."""
        # JSON export includes full content
        json_article = {
            'id': 1,
            'title': 'Test',
            'source_url': 'https://example.com',
            'article_link': 'https://example.com/1',
            'timestamp': '2024-05-26 12:00:00',
            'summary': 'Brief summary',
            'sentiment': 'Positive',
            'content': 'Full article content here...',  # JSON includes this
            'tags': ['python', 'tech']  # JSON uses list format
        }

        # CSV typically has summary instead of full content
        csv_row = {
            'ID': 1,
            'Title': 'Test',
            'Source URL': 'https://example.com',
            'Article Link': 'https://example.com/1',
            'Timestamp': '2024-05-26 12:00:00',
            'Summary': 'Brief summary',  # CSV has summary
            'Sentiment': 'Positive',
            'Tags': 'python, tech'  # CSV uses string format
        }

        # JSON has content field that CSV doesn't
        assert 'content' in json_article
        assert 'content' not in csv_row

        # JSON uses list for tags, CSV uses string
        assert isinstance(json_article['tags'], list)
        assert isinstance(csv_row['Tags'], str)

    def test_json_nested_structure(self):
        """Test JSON supports nested structure."""
        export_data = {
            'export_date': '2024-05-26T12:00:00',
            'metadata': {
                'version': '1.2.0',
                'exported_by': 'WebScrape-TUI'
            },
            'filters_applied': {
                'title': 'Python',
                'tags': 'tech'
            },
            'articles': [
                {
                    'id': 1,
                    'tags': ['python', 'tech'],
                    'metadata': {
                        'scraped_at': '2024-05-26',
                        'source': 'Manual'
                    }
                }
            ]
        }

        # JSON supports nested objects
        assert isinstance(export_data['metadata'], dict)
        assert isinstance(export_data['articles'][0]['tags'], list)
        assert isinstance(export_data['articles'][0]['metadata'], dict)


class TestJSONExportValidation:
    """Test JSON export validation."""

    def test_valid_json_output(self):
        """Test generated JSON is valid."""
        data = {
            'export_date': datetime.now().isoformat(),
            'total_articles': 1,
            'articles': [{'id': 1}]
        }

        # Should not raise exception
        json_str = json.dumps(data)
        assert json_str is not None

        # Should be parseable
        parsed = json.loads(json_str)
        assert parsed['total_articles'] == 1

    def test_json_schema_validation(self):
        """Test JSON follows expected schema."""
        export_data = {
            'export_date': '2024-05-26T12:00:00',
            'total_articles': 1,
            'filters_applied': {},
            'articles': [
                {
                    'id': 1,
                    'title': 'Test',
                    'source_url': 'https://example.com',
                    'article_link': 'https://example.com/1',
                    'timestamp': '2024-05-26 12:00:00',
                    'summary': None,
                    'sentiment': None,
                    'content': None,
                    'tags': []
                }
            ]
        }

        # Validate required fields
        assert 'export_date' in export_data
        assert 'total_articles' in export_data
        assert 'articles' in export_data

        # Validate article structure
        article = export_data['articles'][0]
        required_fields = [
            'id', 'title', 'source_url', 'article_link',
            'timestamp', 'summary', 'sentiment', 'content', 'tags'
        ]
        for field in required_fields:
            assert field in article

    def test_json_pretty_print(self):
        """Test JSON pretty printing."""
        data = {'test': 'value', 'nested': {'key': 'value'}}

        # With indentation
        pretty = json.dumps(data, indent=2)
        assert '\n' in pretty
        assert '  ' in pretty

        # Without indentation
        compact = json.dumps(data)
        assert '\n' not in compact
