#!/usr/bin/env python3
"""
Test suite for v1.7.0 enhanced export features.

Tests cover:
- Excel (XLSX) export with formatting and multiple sheets
- PDF report generation with professional layouts
- Word cloud visualization generation
- Sentiment scatter plot generation
- Export template system
"""

import pytest
import sqlite3
from pathlib import Path
import sys
from datetime import datetime
import tempfile
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapetui import (
    ExcelExportManager,
    PDFExportManager,
    EnhancedVisualizationManager,
    init_db,
    get_db_connection
)


@pytest.fixture
def test_db():
    """Create a test database with sample data."""
    # Use temporary database
    db_path = tempfile.mktemp(suffix='.db')

    # Initialize database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scraped_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            link TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            summary TEXT,
            sentiment TEXT,
            content TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS article_tags (
            article_id INTEGER,
            tag_id INTEGER,
            FOREIGN KEY (article_id) REFERENCES scraped_data(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (article_id, tag_id)
        )
    """)

    # Insert test data
    test_articles = [
        ('Test Article 1', 'https://example.com/1', 'https://example.com/article/1',
         '2025-01-01 10:00:00', 'Summary 1', 'Positive', 'Full content 1'),
        ('Test Article 2', 'https://example.com/2', 'https://example.com/article/2',
         '2025-01-02 11:00:00', 'Summary 2', 'Negative', 'Full content 2'),
        ('Test Article 3', 'https://example.com/3', 'https://example.com/article/3',
         '2025-01-03 12:00:00', 'Summary 3', 'Neutral', 'Full content 3'),
        ('Test Article 4', 'https://example.com/4', 'https://example.com/article/4',
         '2025-01-04 13:00:00', 'Summary 4', 'Positive', 'Full content 4'),
        ('Test Article 5', 'https://example.com/5', 'https://example.com/article/5',
         '2025-01-05 14:00:00', 'Summary 5', 'Neutral', 'Full content 5'),
    ]

    cursor.executemany(
        "INSERT INTO scraped_data (title, url, link, timestamp, summary, sentiment, content) VALUES (?, ?, ?, ?, ?, ?, ?)",
        test_articles
    )

    # Insert test tags
    test_tags = ['python', 'testing', 'export', 'excel', 'pdf']
    cursor.executemany("INSERT INTO tags (name) VALUES (?)", [(tag,) for tag in test_tags])

    # Link tags to articles
    article_tag_links = [
        (1, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 1), (5, 3)
    ]
    cursor.executemany("INSERT INTO article_tags (article_id, tag_id) VALUES (?, ?)", article_tag_links)

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def sample_articles():
    """Provide sample article data for export tests."""
    return [
        {
            'id': 1,
            'title': 'Test Article 1',
            'source_url': 'https://example.com/1',
            'article_link': 'https://example.com/article/1',
            'date_scraped': '2025-01-01',
            'timestamp': '2025-01-01 10:00:00',
            'summary': 'This is a test summary for article 1',
            'sentiment': 'Positive',
            'full_text': 'Full content of article 1 for testing purposes.',
            'tags': 'python, testing'
        },
        {
            'id': 2,
            'title': 'Test Article 2',
            'source_url': 'https://example.com/2',
            'article_link': 'https://example.com/article/2',
            'date_scraped': '2025-01-02',
            'timestamp': '2025-01-02 11:00:00',
            'summary': 'This is a test summary for article 2',
            'sentiment': 'Negative',
            'full_text': 'Full content of article 2 for testing purposes.',
            'tags': 'export'
        },
        {
            'id': 3,
            'title': 'Test Article 3',
            'source_url': 'https://example.com/3',
            'article_link': 'https://example.com/article/3',
            'date_scraped': '2025-01-03',
            'timestamp': '2025-01-03 12:00:00',
            'summary': 'This is a test summary for article 3',
            'sentiment': 'Neutral',
            'full_text': 'Full content of article 3 for testing purposes.',
            'tags': 'excel, testing'
        }
    ]


class TestExcelExport:
    """Test Excel export functionality."""

    def test_excel_export_standard_template(self, sample_articles, tmp_path):
        """Test Excel export with standard template."""
        output_file = tmp_path / "test_export.xlsx"

        success = ExcelExportManager.export_to_excel(
            sample_articles,
            str(output_file),
            include_charts=True,
            template="standard"
        )

        assert success is True
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_excel_export_executive_template(self, sample_articles, tmp_path):
        """Test Excel export with executive template."""
        output_file = tmp_path / "test_export_executive.xlsx"

        success = ExcelExportManager.export_to_excel(
            sample_articles,
            str(output_file),
            include_charts=True,
            template="executive"
        )

        assert success is True
        assert output_file.exists()

    def test_excel_export_detailed_template(self, sample_articles, tmp_path):
        """Test Excel export with detailed template."""
        output_file = tmp_path / "test_export_detailed.xlsx"

        success = ExcelExportManager.export_to_excel(
            sample_articles,
            str(output_file),
            include_charts=True,
            template="detailed"
        )

        assert success is True
        assert output_file.exists()

    def test_excel_export_without_charts(self, sample_articles, tmp_path):
        """Test Excel export without charts."""
        output_file = tmp_path / "test_export_no_charts.xlsx"

        success = ExcelExportManager.export_to_excel(
            sample_articles,
            str(output_file),
            include_charts=False,
            template="standard"
        )

        assert success is True
        assert output_file.exists()

    def test_excel_export_empty_data(self, tmp_path):
        """Test Excel export with empty article list."""
        output_file = tmp_path / "test_export_empty.xlsx"

        success = ExcelExportManager.export_to_excel(
            [],
            str(output_file),
            include_charts=False,
            template="standard"
        )

        # Should still create file with headers
        assert success is True
        assert output_file.exists()

    def test_excel_export_invalid_path(self, sample_articles):
        """Test Excel export with invalid output path."""
        output_file = "/invalid/path/test.xlsx"

        success = ExcelExportManager.export_to_excel(
            sample_articles,
            output_file,
            template="standard"
        )

        assert success is False


class TestPDFExport:
    """Test PDF export functionality."""

    def test_pdf_export_standard_template(self, sample_articles, tmp_path):
        """Test PDF export with standard template."""
        output_file = tmp_path / "test_report.pdf"

        success = PDFExportManager.export_to_pdf(
            sample_articles,
            str(output_file),
            include_charts=True,
            template="standard"
        )

        assert success is True
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_pdf_export_executive_template(self, sample_articles, tmp_path):
        """Test PDF export with executive template."""
        output_file = tmp_path / "test_report_executive.pdf"

        success = PDFExportManager.export_to_pdf(
            sample_articles,
            str(output_file),
            include_charts=True,
            template="executive"
        )

        assert success is True
        assert output_file.exists()

    def test_pdf_export_detailed_template(self, sample_articles, tmp_path):
        """Test PDF export with detailed template."""
        output_file = tmp_path / "test_report_detailed.pdf"

        success = PDFExportManager.export_to_pdf(
            sample_articles,
            str(output_file),
            include_charts=True,
            template="detailed"
        )

        assert success is True
        assert output_file.exists()

    def test_pdf_export_without_charts(self, sample_articles, tmp_path):
        """Test PDF export without charts."""
        output_file = tmp_path / "test_report_no_charts.pdf"

        success = PDFExportManager.export_to_pdf(
            sample_articles,
            str(output_file),
            include_charts=False,
            template="standard"
        )

        assert success is True
        assert output_file.exists()

    def test_pdf_export_empty_data(self, tmp_path):
        """Test PDF export with empty article list."""
        output_file = tmp_path / "test_report_empty.pdf"

        success = PDFExportManager.export_to_pdf(
            [],
            str(output_file),
            include_charts=False,
            template="standard"
        )

        # Should still create file with title page
        assert success is True
        assert output_file.exists()

    def test_pdf_export_invalid_path(self, sample_articles):
        """Test PDF export with invalid output path."""
        output_file = "/invalid/path/test.pdf"

        success = PDFExportManager.export_to_pdf(
            sample_articles,
            output_file,
            template="standard"
        )

        assert success is False


class TestEnhancedVisualizations:
    """Test enhanced visualization features."""

    def test_word_cloud_generation(self, tmp_path):
        """Test word cloud generation from tag data."""
        output_file = tmp_path / "test_wordcloud.png"

        tags_data = [
            ('python', 10),
            ('testing', 8),
            ('export', 6),
            ('excel', 5),
            ('pdf', 4),
            ('visualization', 3),
            ('data', 2),
            ('analytics', 1)
        ]

        success = EnhancedVisualizationManager.generate_word_cloud(
            tags_data,
            str(output_file),
            width=800,
            height=400
        )

        assert success is True
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_word_cloud_empty_data(self, tmp_path):
        """Test word cloud with empty tag data."""
        output_file = tmp_path / "test_wordcloud_empty.png"

        success = EnhancedVisualizationManager.generate_word_cloud(
            [],
            str(output_file)
        )

        assert success is False

    def test_word_cloud_invalid_path(self):
        """Test word cloud with invalid output path."""
        output_file = "/invalid/path/wordcloud.png"

        tags_data = [('python', 10), ('testing', 5)]

        success = EnhancedVisualizationManager.generate_word_cloud(
            tags_data,
            output_file
        )

        assert success is False

    def test_sentiment_scatter_plot(self, sample_articles, tmp_path):
        """Test sentiment scatter plot generation."""
        output_file = tmp_path / "test_sentiment_scatter.png"

        success = EnhancedVisualizationManager.generate_sentiment_scatter(
            sample_articles,
            str(output_file)
        )

        assert success is True
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_sentiment_scatter_empty_data(self, tmp_path):
        """Test sentiment scatter plot with empty data."""
        output_file = tmp_path / "test_sentiment_scatter_empty.png"

        success = EnhancedVisualizationManager.generate_sentiment_scatter(
            [],
            str(output_file)
        )

        assert success is False

    def test_sentiment_scatter_invalid_path(self, sample_articles):
        """Test sentiment scatter plot with invalid path."""
        output_file = "/invalid/path/scatter.png"

        success = EnhancedVisualizationManager.generate_sentiment_scatter(
            sample_articles,
            output_file
        )

        assert success is False


class TestExportTemplates:
    """Test export template system."""

    def test_all_excel_templates(self, sample_articles, tmp_path):
        """Test all Excel templates are accessible."""
        templates = ['standard', 'executive', 'detailed']

        for template in templates:
            output_file = tmp_path / f"test_excel_{template}.xlsx"
            success = ExcelExportManager.export_to_excel(
                sample_articles,
                str(output_file),
                template=template
            )
            assert success is True
            assert output_file.exists()

    def test_all_pdf_templates(self, sample_articles, tmp_path):
        """Test all PDF templates are accessible."""
        templates = ['standard', 'executive', 'detailed']

        for template in templates:
            output_file = tmp_path / f"test_pdf_{template}.pdf"
            success = PDFExportManager.export_to_pdf(
                sample_articles,
                str(output_file),
                template=template
            )
            assert success is True
            assert output_file.exists()


class TestIntegration:
    """Integration tests for export workflow."""

    def test_full_export_workflow(self, sample_articles, tmp_path):
        """Test complete export workflow with all formats."""
        # Excel export
        excel_file = tmp_path / "full_export.xlsx"
        excel_success = ExcelExportManager.export_to_excel(
            sample_articles,
            str(excel_file),
            template="detailed"
        )

        # PDF export
        pdf_file = tmp_path / "full_report.pdf"
        pdf_success = PDFExportManager.export_to_pdf(
            sample_articles,
            str(pdf_file),
            template="executive"
        )

        # Word cloud
        wordcloud_file = tmp_path / "tags_wordcloud.png"
        tags_data = [('python', 10), ('testing', 8), ('export', 6)]
        wordcloud_success = EnhancedVisualizationManager.generate_word_cloud(
            tags_data,
            str(wordcloud_file)
        )

        # Sentiment scatter
        scatter_file = tmp_path / "sentiment_scatter.png"
        scatter_success = EnhancedVisualizationManager.generate_sentiment_scatter(
            sample_articles,
            str(scatter_file)
        )

        assert excel_success is True
        assert pdf_success is True
        assert wordcloud_success is True
        assert scatter_success is True

        assert excel_file.exists()
        assert pdf_file.exists()
        assert wordcloud_file.exists()
        assert scatter_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
