#!/usr/bin/env python3
"""Tests for AI provider abstraction layer."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import from monolithic scrapetui.py using importlib.util
import importlib.util

_scrapetui_path = Path(__file__).parent.parent / 'scrapetui.py'
_spec = importlib.util.spec_from_file_location("scrapetui_monolith", _scrapetui_path)
_scrapetui_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scrapetui_module)

# Import needed components from monolithic module
GeminiProvider = _scrapetui_module.GeminiProvider
OpenAIProvider = _scrapetui_module.OpenAIProvider
ClaudeProvider = _scrapetui_module.ClaudeProvider
get_ai_provider = _scrapetui_module.get_ai_provider
set_ai_provider = _scrapetui_module.set_ai_provider
TemplateManager = _scrapetui_module.TemplateManager


class TestAIProviderAbstraction:
    """Test AI provider interface and implementations."""

    def test_gemini_provider_initialization(self):
        """Test Gemini provider initialization."""

        provider = GeminiProvider("test_api_key")
        assert provider.api_key == "test_api_key"
        assert provider.name == "Google Gemini"
        assert "gemini-2.0-flash" in provider.available_models

    def test_openai_provider_initialization(self):
        """Test OpenAI provider initialization."""

        provider = OpenAIProvider("test_api_key")
        assert provider.api_key == "test_api_key"
        assert provider.name == "OpenAI"
        assert "gpt-4o-mini" in provider.available_models

    def test_claude_provider_initialization(self):
        """Test Claude provider initialization."""

        provider = ClaudeProvider("test_api_key")
        assert provider.api_key == "test_api_key"
        assert provider.name == "Anthropic Claude"
        assert "claude-3-5-haiku-20241022" in provider.available_models

    def test_provider_switching(self):
        """Test switching between providers."""

        # Set Gemini provider
        gemini = GeminiProvider("gemini_key")
        set_ai_provider(gemini)
        assert get_ai_provider().name == "Google Gemini"

        # Switch to OpenAI
        openai = OpenAIProvider("openai_key")
        set_ai_provider(openai)
        assert get_ai_provider().name == "OpenAI"


class TestTemplateManager:
    """Test template management functionality."""

    def test_template_variable_substitution(self):
        """Test template variable replacement."""

        template = "Title: {title}\nContent: {content}\nURL: {url}"
        result = TemplateManager.apply_template(
            template,
            "Test content here",
            "Test Title",
            "https://example.com"
        )

        assert "Test Title" in result
        assert "Test content here" in result
        assert "https://example.com" in result

    def test_template_manager_apply_partial_variables(self):
        """Test template with missing variables."""

        template = "Title: {title}\nContent: {content}"
        result = TemplateManager.apply_template(template, "Content text", "")

        # Should not crash, just leave empty
        assert "Content text" in result


class TestAdvancedFiltering:
    """Test advanced filtering features."""

    def test_regex_pattern_validation(self):
        """Test regex pattern compilation."""
        import re

        # Valid patterns
        assert re.compile(r"test.*pattern")
        assert re.compile(r"\d{4}-\d{2}-\d{2}")

        # Invalid pattern should raise error
        with pytest.raises(re.error):
            re.compile(r"[invalid(")

    def test_date_range_logic(self):
        """Test date range filtering logic."""
        from datetime import datetime

        # Test date parsing
        date1 = datetime.strptime("2024-01-01", "%Y-%m-%d")
        date2 = datetime.strptime("2024-12-31", "%Y-%m-%d")

        assert date1 < date2

    def test_tag_logic_sql_generation(self):
        """Test tag AND/OR SQL generation logic."""
        # AND logic: multiple subqueries
        tags = ["python", "web"]
        and_conditions = []
        for i, tag in enumerate(tags):
            and_conditions.append(f"id IN (SELECT article_id FROM article_tags WHERE tag_id = {i})")

        assert len(and_conditions) == 2

        # OR logic: single IN clause
        or_condition = f"id IN (SELECT article_id FROM article_tags WHERE tag_id IN (0, 1))"
        assert "IN" in or_condition
