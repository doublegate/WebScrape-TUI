"""Logging configuration for WebScrape-TUI."""

import logging
import sys
from pathlib import Path
from typing import Optional

from ..config import init_config


_loggers = {}
_configured = False


def setup_logging() -> None:
    """Configure application-wide logging."""
    global _configured
    if _configured:
        return

    config = init_config()

    # Create logs directory if needed
    log_file = Path(config.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger instance.

    Args:
        name: Logger name (typically __name__ of calling module)

    Returns:
        Logger instance
    """
    if name not in _loggers:
        if not _configured:
            setup_logging()
        _loggers[name] = logging.getLogger(name)

    return _loggers[name]


def reset_logging():
    """Reset logging state (for testing)."""
    global _loggers, _configured
    _loggers.clear()
    _configured = False
