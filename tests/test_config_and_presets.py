#!/usr/bin/env python3
"""Tests for v1.4.0 features: Configuration Management and Filter Presets."""

import pytest
import tempfile
from pathlib import Path
import yaml
import json


class TestConfigManager:
    """Test configuration management with YAML/JSON persistence."""

    def test_config_manager_load_default(self):
        """Test loading default configuration."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scrapetui import ConfigManager

        config = ConfigManager.load_config()

        assert 'ai' in config
        assert 'export' in config
        assert 'ui' in config
        assert 'database' in config
        assert 'logging' in config

    def test_config_manager_save_load(self, tmp_path):
        """Test saving and loading configuration."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scrapetui import ConfigManager

        # Override config path for testing
        original_path = ConfigManager.CONFIG_PATH
        test_config_path = tmp_path / "test_config.yaml"
        ConfigManager.CONFIG_PATH = test_config_path

        try:
            # Create custom config
            custom_config = ConfigManager.DEFAULT_CONFIG.copy()
            custom_config['ai']['default_provider'] = 'openai'
            custom_config['export']['default_format'] = 'json'

            # Save config
            assert ConfigManager.save_config(custom_config) is True
            assert test_config_path.exists()

            # Load config
            loaded_config = ConfigManager.load_config()
            assert loaded_config['ai']['default_provider'] == 'openai'
            assert loaded_config['export']['default_format'] == 'json'
        finally:
            ConfigManager.CONFIG_PATH = original_path

    def test_config_manager_merge_config(self):
        """Test configuration merging."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scrapetui import ConfigManager

        base = {
            'ai': {'default_provider': 'gemini', 'default_model': None},
            'export': {'default_format': 'csv'}
        }
        override = {
            'ai': {'default_provider': 'openai'},
            'logging': {'level': 'DEBUG'}
        }

        result = ConfigManager._merge_config(base, override)

        assert result['ai']['default_provider'] == 'openai'
        assert result['ai']['default_model'] is None  # Preserved from base
        assert result['export']['default_format'] == 'csv'  # Preserved from base
        assert result['logging']['level'] == 'DEBUG'  # Added from override

    def test_config_manager_save_as_json(self, tmp_path):
        """Test saving configuration as JSON."""
        import sys
        import copy
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scrapetui import ConfigManager

        test_json_path = tmp_path / "test_config.json"
        config = copy.deepcopy(ConfigManager.DEFAULT_CONFIG)

        assert ConfigManager.save_as_json(config, test_json_path) is True
        assert test_json_path.exists()

        # Verify JSON can be loaded
        with open(test_json_path, 'r') as f:
            loaded = json.load(f)
        # Just verify structure, don't check specific values
        assert 'ai' in loaded
        assert 'export' in loaded
        assert 'default_provider' in loaded['ai']


class TestFilterPresetManager:
    """Test filter preset management."""

    @pytest.fixture
    def temp_db(self, monkeypatch):
        """Create a temporary database with proper schema."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import scrapetui
        import sqlite3

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)

        monkeypatch.setattr(scrapetui, 'DB_PATH', db_path)
        scrapetui.init_db()

        yield db_path

        if db_path.exists():
            db_path.unlink()

    def test_save_preset(self, temp_db):
        """Test saving a filter preset."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scrapetui import FilterPresetManager

        result = FilterPresetManager.save_preset(
            name="Test Preset",
            title_filter="Python",
            url_filter="example.com",
            date_from="2024-01-01",
            date_to="2024-12-31",
            tags_filter="tech,programming",
            sentiment_filter="Positive",
            use_regex=True,
            tags_logic="AND"
        )

        assert result is True

    def test_load_preset(self, temp_db):
        """Test loading a filter preset."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scrapetui import FilterPresetManager

        # Save preset first
        FilterPresetManager.save_preset(
            name="Test Preset",
            title_filter="Python",
            url_filter="example.com",
            date_from="2024-01-01",
            date_to="2024-12-31",
            tags_filter="tech",
            sentiment_filter="Positive",
            use_regex=True,
            tags_logic="OR"
        )

        # Load preset
        preset = FilterPresetManager.load_preset("Test Preset")

        assert preset is not None
        assert preset['title_filter'] == "Python"
        assert preset['url_filter'] == "example.com"
        assert preset['date_from'] == "2024-01-01"
        assert preset['date_to'] == "2024-12-31"
        assert preset['tags_filter'] == "tech"
        assert preset['sentiment_filter'] == "Positive"
        assert preset['use_regex'] is True
        assert preset['tags_logic'] == "OR"

    def test_load_nonexistent_preset(self, temp_db):
        """Test loading a preset that doesn't exist."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scrapetui import FilterPresetManager

        preset = FilterPresetManager.load_preset("Nonexistent")
        assert preset is None

    def test_list_presets(self, temp_db):
        """Test listing all presets."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scrapetui import FilterPresetManager

        # Save multiple presets
        for i in range(3):
            FilterPresetManager.save_preset(
                name=f"Preset {i}",
                title_filter="",
                url_filter="",
                date_from="",
                date_to="",
                tags_filter="",
                sentiment_filter="",
                use_regex=False,
                tags_logic="AND"
            )

        presets = FilterPresetManager.list_presets()
        assert len(presets) == 3
        assert "Preset 0" in presets
        assert "Preset 1" in presets
        assert "Preset 2" in presets

    def test_delete_preset(self, temp_db):
        """Test deleting a preset."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scrapetui import FilterPresetManager

        # Save preset
        FilterPresetManager.save_preset(
            name="To Delete",
            title_filter="",
            url_filter="",
            date_from="",
            date_to="",
            tags_filter="",
            sentiment_filter="",
            use_regex=False,
            tags_logic="AND"
        )

        # Verify it exists
        assert "To Delete" in FilterPresetManager.list_presets()

        # Delete it
        result = FilterPresetManager.delete_preset("To Delete")
        assert result is True

        # Verify it's gone
        assert "To Delete" not in FilterPresetManager.list_presets()

    def test_update_existing_preset(self, temp_db):
        """Test updating an existing preset."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scrapetui import FilterPresetManager

        # Save initial preset
        FilterPresetManager.save_preset(
            name="Update Test",
            title_filter="Old Title",
            url_filter="",
            date_from="",
            date_to="",
            tags_filter="",
            sentiment_filter="",
            use_regex=False,
            tags_logic="AND"
        )

        # Update it
        FilterPresetManager.save_preset(
            name="Update Test",
            title_filter="New Title",
            url_filter="new.com",
            date_from="2025-01-01",
            date_to="",
            tags_filter="updated",
            sentiment_filter="",
            use_regex=True,
            tags_logic="OR"
        )

        # Load and verify
        preset = FilterPresetManager.load_preset("Update Test")
        assert preset['title_filter'] == "New Title"
        assert preset['url_filter'] == "new.com"
        assert preset['date_from'] == "2025-01-01"
        assert preset['tags_filter'] == "updated"
        assert preset['use_regex'] is True
        assert preset['tags_logic'] == "OR"

    def test_preset_with_empty_values(self, temp_db):
        """Test preset with empty/None values."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scrapetui import FilterPresetManager

        FilterPresetManager.save_preset(
            name="Empty Preset",
            title_filter="",
            url_filter="",
            date_from="",
            date_to="",
            tags_filter="",
            sentiment_filter="",
            use_regex=False,
            tags_logic="AND"
        )

        preset = FilterPresetManager.load_preset("Empty Preset")
        assert preset is not None
        assert preset['title_filter'] == ""
        assert preset['url_filter'] == ""
        assert preset['use_regex'] is False
        assert preset['tags_logic'] == "AND"


class TestYAMLHandling:
    """Test YAML-specific functionality."""

    def test_yaml_structure(self, tmp_path):
        """Test YAML configuration structure."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scrapetui import ConfigManager

        test_yaml = tmp_path / "test.yaml"
        config = {
            'ai': {'default_provider': 'gemini'},
            'export': {'default_format': 'csv', 'output_directory': '.'},
            'ui': {'theme': 'default'}
        }

        with open(test_yaml, 'w') as f:
            yaml.safe_dump(config, f, default_flow_style=False)

        # Verify it can be loaded
        with open(test_yaml, 'r') as f:
            loaded = yaml.safe_load(f)

        assert loaded['ai']['default_provider'] == 'gemini'
        assert loaded['export']['output_directory'] == '.'

    def test_yaml_unicode_support(self, tmp_path):
        """Test YAML handles Unicode properly."""
        test_yaml = tmp_path / "unicode.yaml"
        config = {
            'test': '你好世界',
            'emoji': '🎉✨'
        }

        with open(test_yaml, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config, f, allow_unicode=True)

        with open(test_yaml, 'r', encoding='utf-8') as f:
            loaded = yaml.safe_load(f)

        assert loaded['test'] == '你好世界'
        assert loaded['emoji'] == '🎉✨'


class TestDatabaseSchema:
    """Test database schema updates for v1.4.0."""

    def test_filter_presets_table_exists(self, monkeypatch):
        """Test that filter_presets table has all required columns."""
        import sys
        import sqlite3
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import scrapetui

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)

        monkeypatch.setattr(scrapetui, 'DB_PATH', db_path)
        scrapetui.init_db()

        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("PRAGMA table_info(filter_presets)")
                columns = {row[1]: row[2] for row in cursor.fetchall()}

                assert 'id' in columns
                assert 'name' in columns
                assert 'title_filter' in columns
                assert 'url_filter' in columns
                assert 'date_from' in columns
                assert 'date_to' in columns
                assert 'tags_filter' in columns
                assert 'sentiment_filter' in columns
                assert 'use_regex' in columns
                assert 'tags_logic' in columns
                assert 'created_at' in columns
        finally:
            if db_path.exists():
                db_path.unlink()
