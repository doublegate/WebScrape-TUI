#!/usr/bin/env python3
"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
