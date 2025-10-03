"""WebScrape-TUI - Modern web scraping application with TUI and REST API.

This package provides both a Terminal User Interface (TUI) application
and a REST API for web scraping, article management, and AI-powered analysis.

Version: 2.1.0-alpha.3
"""

# Import from legacy single-file application (backward compatibility)
# These imports ensure that existing tests continue to work while we
# gradually migrate to the new modular structure.
# The scrapetui.py file at the root contains the full TUI application.

import sys
import importlib.util
from pathlib import Path

# Load the root-level scrapetui.py module directly
_root_file = Path(__file__).parent.parent / "scrapetui.py"
_spec = importlib.util.spec_from_file_location("_scrapetui_legacy", _root_file)
_legacy = importlib.util.module_from_spec(_spec)
sys.modules["_scrapetui_legacy"] = _legacy
_spec.loader.exec_module(_legacy)

# Re-export everything needed by tests for backward compatibility
get_db_connection = _legacy.get_db_connection
init_db = _legacy.init_db
DB_PATH = _legacy.DB_PATH

# Authentication functions
hash_password = _legacy.hash_password
verify_password = _legacy.verify_password
create_session_token = _legacy.create_session_token
create_user_session = _legacy.create_user_session
validate_session = _legacy.validate_session
logout_session = _legacy.logout_session
authenticate_user = _legacy.authenticate_user
initialize_admin_user = _legacy.initialize_admin_user
migrate_database_to_v2 = _legacy.migrate_database_to_v2

# Database utilities
db_datetime_now = _legacy.db_datetime_now
db_datetime_future = _legacy.db_datetime_future

# Configuration
load_env_file = _legacy.load_env_file
ConfigManager = _legacy.ConfigManager

# AI Providers
AIProvider = _legacy.AIProvider
GeminiProvider = _legacy.GeminiProvider
OpenAIProvider = _legacy.OpenAIProvider
ClaudeProvider = _legacy.ClaudeProvider
get_ai_provider = _legacy.get_ai_provider
set_ai_provider = _legacy.set_ai_provider

# Managers
TemplateManager = _legacy.TemplateManager
FilterPresetManager = _legacy.FilterPresetManager
ScheduleManager = _legacy.ScheduleManager
AnalyticsManager = _legacy.AnalyticsManager
ExcelExportManager = _legacy.ExcelExportManager
PDFExportManager = _legacy.PDFExportManager
EnhancedVisualizationManager = _legacy.EnhancedVisualizationManager
AITaggingManager = _legacy.AITaggingManager
EntityRecognitionManager = _legacy.EntityRecognitionManager
ContentSimilarityManager = _legacy.ContentSimilarityManager
KeywordExtractionManager = _legacy.KeywordExtractionManager
MultiLevelSummarizationManager = _legacy.MultiLevelSummarizationManager
TopicModelingManager = _legacy.TopicModelingManager
EntityRelationshipManager = _legacy.EntityRelationshipManager
DuplicateDetectionManager = _legacy.DuplicateDetectionManager
SummaryQualityManager = _legacy.SummaryQualityManager
QuestionAnsweringManager = _legacy.QuestionAnsweringManager

# Constants
PREINSTALLED_SCRAPERS = _legacy.PREINSTALLED_SCRAPERS

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
