"""Configuration management for WebScrape-TUI."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import os


@dataclass
class Config:
    """Application configuration."""

    # Database settings
    database_path: str = "scraped_data_tui_v1.0.db"

    # Logging settings
    log_file: str = "scraper_tui_v1.0.log"
    log_level: str = "INFO"

    # API keys for AI providers
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # Session settings
    session_timeout_hours: int = 24

    # API settings (v2.1.0)
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_jwt_secret: Optional[str] = None
    api_jwt_algorithm: str = "HS256"
    api_jwt_expiration_minutes: int = 30
    api_cors_origins: list = field(default_factory=lambda: ["*"])
    api_rate_limit_per_minute: int = 60

    # Cache settings (v2.1.0)
    cache_enabled: bool = True
    cache_type: str = "memory"  # memory or redis
    cache_ttl_seconds: int = 3600
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # Performance settings (v2.1.0)
    max_workers: int = 4
    items_per_page: int = 50
    scraper_timeout_seconds: int = 30
    scraper_max_retries: int = 3

    # Plugin settings (v2.1.0)
    plugins_dir: str = "plugins"
    enable_plugins: bool = True


def load_env_file(env_path: str = ".env") -> None:
    """
    Load environment variables from .env file (idempotent - loads only once).

    Args:
        env_path: Path to .env file
    """
    global _env_loaded

    # Only load once to avoid repeated file I/O during imports
    if _env_loaded:
        return

    env_file = Path(env_path)
    if not env_file.exists():
        _env_loaded = True
        return

    try:
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        _env_loaded = True
    except Exception:
        # Silently fail if .env can't be read (will use defaults)
        _env_loaded = True


def get_config() -> Config:
    """
    Get application configuration from environment.

    Returns:
        Config instance with values from environment variables
    """
    load_env_file()

    return Config(
        # Database (check both env vars for backwards compatibility)
        database_path=os.getenv('SCRAPETUI_DB_PATH') or os.getenv('DATABASE_PATH', 'scraped_data_tui_v1.0.db'),

        # Logging
        log_file=os.getenv('LOG_FILE_PATH', 'scraper_tui_v1.0.log'),
        log_level=os.getenv('LOG_LEVEL', 'INFO'),

        # AI API keys
        gemini_api_key=os.getenv('GEMINI_API_KEY'),
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),

        # Session
        session_timeout_hours=int(os.getenv('SESSION_TIMEOUT_HOURS', '24')),

        # API
        api_host=os.getenv('API_HOST', '127.0.0.1'),
        api_port=int(os.getenv('API_PORT', '8000')),
        api_jwt_secret=os.getenv('API_JWT_SECRET', 'dev-secret-key-change-in-production'),
        api_jwt_algorithm=os.getenv('API_JWT_ALGORITHM', 'HS256'),
        api_jwt_expiration_minutes=int(os.getenv('API_JWT_EXPIRATION_MINUTES', '30')),
        api_cors_origins=os.getenv('API_CORS_ORIGINS', '*').split(','),
        api_rate_limit_per_minute=int(os.getenv('API_RATE_LIMIT_PER_MINUTE', '60')),

        # Cache
        cache_enabled=os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
        cache_type=os.getenv('CACHE_TYPE', 'memory'),
        cache_ttl_seconds=int(os.getenv('CACHE_TTL_SECONDS', '3600')),
        redis_host=os.getenv('REDIS_HOST', 'localhost'),
        redis_port=int(os.getenv('REDIS_PORT', '6379')),
        redis_db=int(os.getenv('REDIS_DB', '0')),
        redis_password=os.getenv('REDIS_PASSWORD'),

        # Performance
        max_workers=int(os.getenv('MAX_WORKERS', '4')),
        items_per_page=int(os.getenv('ITEMS_PER_PAGE', '50')),
        scraper_timeout_seconds=int(os.getenv('SCRAPER_TIMEOUT_SECONDS', '30')),
        scraper_max_retries=int(os.getenv('SCRAPER_MAX_RETRIES', '3')),

        # Plugins
        plugins_dir=os.getenv('PLUGINS_DIR', 'plugins'),
        enable_plugins=os.getenv('ENABLE_PLUGINS', 'true').lower() == 'true',
    )


# Global config instance for singleton pattern
_config: Optional[Config] = None
_env_loaded: bool = False


def init_config() -> Config:
    """Initialize and return global config instance."""
    global _config
    if _config is None:
        _config = get_config()
    return _config


def reset_config() -> None:
    """Reset global config instance (useful for testing)."""
    global _config, _env_loaded
    _config = None
    _env_loaded = False
