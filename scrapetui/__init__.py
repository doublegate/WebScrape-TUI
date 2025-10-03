"""WebScrape-TUI - Modern web scraping application with TUI and REST API.

This package provides both a Terminal User Interface (TUI) application
and a REST API for web scraping, article management, and AI-powered analysis.

Version: 2.1.0-alpha.3
"""

# NOTE: Legacy imports commented out to prevent loading monolithic TUI application
# The full TUI (scrapetui.py) should only be loaded when explicitly run as main
# New modular code in scrapetui/ package operates independently

# Import from legacy single-file application (backward compatibility)
# These imports ensure that existing tests continue to work while we
# gradually migrate to the new modular structure.
# TEMPORARILY DISABLED: Loading causes test hangs due to Textual initialization
#
# import sys
# import importlib.util
# from pathlib import Path
#
# # Load the root-level scrapetui.py module directly
# _root_file = Path(__file__).parent.parent / "scrapetui.py"
# _spec = importlib.util.spec_from_file_location("_scrapetui_legacy", _root_file)
# _legacy = importlib.util.module_from_spec(_spec)
# sys.modules["_scrapetui_legacy"] = _legacy
# _spec.loader.exec_module(_legacy)  # THIS HANGS TESTS - executes entire TUI app

# Provide imports from new modular structure where available
# For backward compatibility, tests should migrate to import from scrapetui.core.* directly
from .core.database import get_db_connection, check_database_exists, init_db
from .core.auth import (
    hash_password,
    verify_password,
    create_session_token,
    create_user_session,
    validate_session,
    logout_session,
    authenticate_user,
    initialize_admin_user,
    db_datetime_now,
    db_datetime_future
)
from .database.migrations import run_migrations as migrate_database_to_v2
from .config import Config, get_config

# Placeholder exports for items not yet migrated - tests may need updates
# These will return None/empty to avoid breaking imports while we complete migration
def load_env_file(): pass
ConfigManager = None
AIProvider = None
GeminiProvider = None
OpenAIProvider = None
ClaudeProvider = None
get_ai_provider = None
set_ai_provider = None
TemplateManager = None
FilterPresetManager = None
ScheduleManager = None
AnalyticsManager = None
ExcelExportManager = None
PDFExportManager = None
EnhancedVisualizationManager = None
AITaggingManager = None
EntityRecognitionManager = None
ContentSimilarityManager = None
KeywordExtractionManager = None
MultiLevelSummarizationManager = None
TopicModelingManager = None
EntityRelationshipManager = None
DuplicateDetectionManager = None
SummaryQualityManager = None
QuestionAnsweringManager = None
PREINSTALLED_SCRAPERS = []

# Note: DB_PATH is initialized from config - tests should override via get_config()
# To avoid hangs, we set a safe default here
DB_PATH = "scraped_data_tui_v1.0.db"  # Default, can be overridden by config

__version__ = "2.1.0-alpha.3"
__all__ = [
    # Database
    "get_db_connection",
    "init_db",
    "DB_PATH",
    "db_datetime_now",
    "db_datetime_future",

    # Authentication
    "hash_password",
    "verify_password",
    "create_session_token",
    "create_user_session",
    "validate_session",
    "logout_session",
    "authenticate_user",
    "initialize_admin_user",
    "migrate_database_to_v2",

    # Configuration
    "load_env_file",
    "ConfigManager",

    # AI Providers
    "AIProvider",
    "GeminiProvider",
    "OpenAIProvider",
    "ClaudeProvider",
    "get_ai_provider",
    "set_ai_provider",

    # Managers
    "TemplateManager",
    "FilterPresetManager",
    "ScheduleManager",
    "AnalyticsManager",
    "ExcelExportManager",
    "PDFExportManager",
    "EnhancedVisualizationManager",
    "AITaggingManager",
    "EntityRecognitionManager",
    "ContentSimilarityManager",
    "KeywordExtractionManager",
    "MultiLevelSummarizationManager",
    "TopicModelingManager",
    "EntityRelationshipManager",
    "DuplicateDetectionManager",
    "SummaryQualityManager",
    "QuestionAnsweringManager",

    # Constants
    "PREINSTALLED_SCRAPERS",
]
