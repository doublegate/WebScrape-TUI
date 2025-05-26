#!/usr/bin/env python3
"""Basic tests for WebScrape-TUI application."""

import sys
import os

def test_import_main_application():
    """Test that the main application module can be imported."""
    try:
        import scrapetui
        assert hasattr(scrapetui, 'WebScraperApp')
        print("✓ Main application imports successfully")
    except ImportError as e:
        print(f"✗ Failed to import main application: {e}")
        sys.exit(1)

def test_dependencies_available():
    """Test that required dependencies are available."""
    required_modules = ['textual', 'requests', 'bs4', 'sqlite3']
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module} is available")
        except ImportError:
            missing.append(module)
            print(f"✗ {module} is missing")
    
    if missing:
        print(f"Missing dependencies: {missing}")
        sys.exit(1)

if __name__ == "__main__":
    test_dependencies_available()
    test_import_main_application()
    print("All basic tests passed!")