# Development Guide

## Getting Started with Development

This guide covers setting up your development environment, understanding the codebase structure, testing procedures, and contribution guidelines for WebScrape-TUI.

## Table of Contents

- [Environment Setup](#environment-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Style](#code-style)
- [Adding Features](#adding-features)
- [Debugging](#debugging)
- [Release Process](#release-process)

## Environment Setup

### Python Version Requirements

WebScrape-TUI development currently requires **Python 3.8 to 3.12**. Python 3.13 is not yet supported due to gensim dependency incompatibility.

**Recommended for Development**: Python 3.10, 3.11, or 3.12

### Prerequisites

- **Python 3.8 to 3.12** (Python 3.10-3.12 recommended for best compatibility)
  - **Python 3.13**: Not yet supported (gensim incompatibility)
- **Git** for version control
- **Virtual environment** tool (venv, virtualenv, or conda)
- **Terminal with Unicode support** for TUI testing

### Setting Up Development Environment

#### Step 1: Install Python 3.12 (if using Python 3.13)

See [INSTALL-ARCH.md](../INSTALL-ARCH.md) or [TROUBLESHOOTING.md](TROUBLESHOOTING.md#python-version-compatibility-issues) for platform-specific Python 3.12 installation instructions.

#### Step 2: Create Virtual Environment

```bash
# With Python 3.12
python3.12 -m venv venv-dev
source venv-dev/bin/activate  # Linux/macOS
# or
venv-dev\Scripts\activate     # Windows

# Verify Python version
python --version  # Should show Python 3.12.x
```

#### Step 3: Install Dependencies

```bash
# Install all production dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install pytest pytest-cov black flake8 mypy isort

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Troubleshooting Development Setup

**Issue**: gensim installation fails

**Solution**: You're likely using Python 3.13. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#python-version-compatibility-issues) for solutions.

**Issue**: Tests fail due to missing dependencies

**Solution**: Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Development Tools (Optional)

```bash
# Code formatting
pip install black isort

# Linting
pip install flake8 pylint

# Type checking
pip install mypy
```

## Project Structure

```
WebScrape-TUI/
├── scrapetui.py              # Main application (4600+ lines)
│   ├── Database functions    # Lines 1-700
│   ├── Manager classes       # Lines 700-2000
│   ├── Modal screens         # Lines 2000-3500
│   └── Main App class        # Lines 3500-4600
│
├── web_scraper_tui_v1.0.tcss # Textual CSS styling
├── config.yaml               # User configuration (auto-created)
├── requirements.txt          # Python dependencies
│
├── tests/                    # Test suite (142 tests)
│   ├── test_database.py      # 13 tests
│   ├── test_scraping.py      # 15 tests
│   ├── test_utils.py         # 21 tests
│   ├── test_ai_providers.py  # 9 tests
│   ├── test_bulk_operations.py # 8 tests
│   ├── test_json_export.py   # 14 tests
│   ├── test_config_and_presets.py # 12 tests
│   ├── test_scheduling.py    # 16 tests
│   └── test_analytics.py     # 16 tests
│
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md       # System architecture
│   ├── DEVELOPMENT.md        # This file
│   ├── ROADMAP.md            # Future plans
│   └── API.md                # API documentation
│
├── README.md                 # User documentation
├── CHANGELOG.md              # Version history
└── LICENSE                   # MIT License
```

### Code Organization (scrapetui.py)

The main file is organized into logical sections:

1. **Imports** (lines 1-130)
2. **Constants & Configuration** (lines 130-200)
3. **Database Layer** (lines 200-800)
4. **AI Providers** (lines 850-1035)
5. **Manager Classes** (lines 1036-1960)
6. **Utility Functions** (lines 1960-2100)
7. **Modal Screens** (lines 2100-3500)
8. **Main Application** (lines 3500-4600)

## Development Workflow

### 1. Feature Branch Strategy

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes
# ... edit code ...

# Run tests
pytest tests/

# Commit with conventional commits
git commit -m "feat: add new feature description"

# Push to GitHub
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

### 2. Conventional Commits

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
feat: add new feature (new functionality)
fix: fix bug (bug fixes)
docs: update documentation (documentation only)
style: format code (no functional changes)
refactor: refactor code (no functional changes)
test: add tests (test additions/changes)
chore: update dependencies (maintenance)
```

Examples:
```bash
git commit -m "feat: add export to Excel functionality"
git commit -m "fix: resolve database connection leak"
git commit -m "docs: update API documentation for v1.7.0"
git commit -m "test: add tests for analytics edge cases"
```

### 3. Development Cycle

```
1. Read existing code/docs
2. Plan implementation
3. Write tests (TDD approach)
4. Implement feature
5. Run tests
6. Update documentation
7. Commit & push
8. Create PR
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_analytics.py

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test class
pytest tests/test_analytics.py::TestAnalyticsManager

# Run specific test method
pytest tests/test_analytics.py::TestAnalyticsManager::test_get_statistics
```

### Writing Tests

#### 1. Test File Structure

```python
#!/usr/bin/env python3
"""Tests for feature X."""

import pytest
from pathlib import Path
import sys

# Import application components
sys.path.insert(0, str(Path(__file__).parent.parent))
from scrapetui import YourClass, init_db, get_db_connection

@pytest.fixture
def temp_db(monkeypatch):
    """Create temporary database for testing."""
    # Setup
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db_path = f.name

    monkeypatch.setattr('scrapetui.DB_PATH', Path(temp_db_path))
    init_db()

    yield temp_db_path

    # Teardown
    Path(temp_db_path).unlink(missing_ok=True)

class TestYourFeature:
    """Test your feature functionality."""

    def test_basic_operation(self, temp_db):
        """Test basic operation."""
        result = YourClass.method()
        assert result == expected_value
```

#### 2. Test Categories

**Unit Tests:**
```python
def test_individual_function():
    """Test single function in isolation."""
    result = my_function(input)
    assert result == expected
```

**Integration Tests:**
```python
def test_component_interaction(temp_db):
    """Test multiple components working together."""
    # Setup
    manager = YourManager()

    # Execute
    result = manager.complex_operation()

    # Verify
    assert result is not None
    assert database_state_is_correct()
```

**Edge Case Tests:**
```python
def test_edge_case_empty_input():
    """Test behavior with empty input."""
    result = function([])
    assert result == []

def test_edge_case_null_value():
    """Test behavior with None."""
    result = function(None)
    assert result is None
```

#### 3. Mocking External Services

```python
from unittest.mock import Mock, patch

@patch('requests.get')
def test_http_request(mock_get):
    """Test HTTP request with mocking."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "<html>Test</html>"
    mock_get.return_value = mock_response

    result = scrape_url("http://example.com")
    assert result is not None
```

### Test Coverage Goals

- **Overall**: 80%+ coverage
- **Critical paths**: 95%+ coverage (database, AI, scraping)
- **New features**: 100% coverage requirement

## Code Style

### PEP 8 Compliance

Follow [PEP 8](https://pep8.org/) style guide:

```python
# Good: 4-space indentation
def function_name(parameter_one, parameter_two):
    """Docstring explaining function."""
    result = parameter_one + parameter_two
    return result

# Good: Line length <= 88 characters (Black default)
def long_function_name(
    parameter_one,
    parameter_two,
    parameter_three
):
    """Break long signatures across multiple lines."""
    pass

# Good: Clear variable names
article_count = 10
user_input_text = "example"

# Bad: Unclear abbreviations
ac = 10
uit = "example"
```

### Documentation Standards

**Module Docstrings:**
```python
"""
Brief description of module.

Longer description with details about what this module contains
and how it should be used.
"""
```

**Class Docstrings:**
```python
class AnalyticsManager:
    """
    Manages data analytics and visualization.

    Provides methods for generating statistics, charts, and reports
    from scraped article data.
    """
```

**Function Docstrings:**
```python
def get_statistics() -> Dict[str, Any]:
    """
    Get comprehensive statistics about scraped data.

    Returns:
        Dictionary containing:
        - total_articles: Total article count
        - sentiment_distribution: Dict of sentiment counts
        - top_sources: List of (url, count) tuples

    Raises:
        DatabaseError: If database connection fails
    """
```

### Type Hints

Use type hints for clarity:

```python
from typing import List, Dict, Optional, Tuple, Any

def process_articles(
    articles: List[Dict[str, str]],
    limit: Optional[int] = None
) -> Tuple[int, List[str]]:
    """Process articles with type hints."""
    processed_count = 0
    results: List[str] = []

    # Implementation

    return processed_count, results
```

### Code Formatting

Use **Black** for automatic formatting:

```bash
# Format all Python files
black scrapetui.py tests/

# Check formatting without changes
black --check scrapetui.py

# Format with line length 88 (default)
black --line-length 88 scrapetui.py
```

Use **isort** for import organization:

```bash
# Sort imports
isort scrapetui.py tests/

# Check import order
isort --check-only scrapetui.py
```

### Import Organization

```python
# 1. Standard library imports
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional

# 2. Third-party imports
import requests
from textual.app import App
from textual.widgets import DataTable

# 3. Local imports
from .utils import helper_function
from .database import get_connection
```

## Adding Features

### 1. Adding a New Manager Class

```python
class NewFeatureManager:
    """
    Manages new feature functionality.

    Example usage:
        manager = NewFeatureManager()
        result = manager.do_something()
    """

    @staticmethod
    def create_item(name: str, value: str) -> bool:
        """
        Create a new item.

        Args:
            name: Item name
            value: Item value

        Returns:
            True if successful, False otherwise
        """
        try:
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO items (name, value) VALUES (?, ?)",
                    (name, value)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to create item: {e}")
            return False

    @staticmethod
    def list_items() -> List[Dict[str, Any]]:
        """Get all items."""
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM items")
            return [dict(row) for row in cursor.fetchall()]
```

### 2. Adding a New Modal Screen

```python
class NewFeatureModal(ModalScreen[Optional[str]]):
    """Modal for new feature input."""

    DEFAULT_CSS = """
    NewFeatureModal > Vertical {
        width: 60;
        height: auto;
        padding: 2;
        border: thick $primary;
        background: $panel;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose modal widgets."""
        with Vertical():
            yield Label("Enter Details")
            yield Input(placeholder="Name", id="name_input")
            yield Input(placeholder="Value", id="value_input")
            with Horizontal(classes="modal-buttons"):
                yield Button("Submit", variant="primary", id="submit")
                yield Button("Cancel", id="cancel")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "submit":
            name = self.query_one("#name_input", Input).value
            value = self.query_one("#value_input", Input).value

            if name and value:
                self.dismiss(f"{name}:{value}")
            else:
                self.notify("All fields required", severity="error")
        else:
            self.dismiss(None)
```

### 3. Adding a New Keyboard Shortcut

**Step 1:** Add binding to `WebScraperApp.BINDINGS`:

```python
BINDINGS = [
    # ... existing bindings ...
    Binding("ctrl+x", "new_feature", "New Feature"),
]
```

**Step 2:** Add action handler:

```python
async def action_new_feature(self) -> None:
    """Open new feature modal (Ctrl+X)."""
    def handle_result(result: Optional[str]) -> None:
        if result:
            # Process result
            self.notify(f"Created: {result}", severity="success")

    self.push_screen(NewFeatureModal(), handle_result)
```

### 4. Adding Database Tables

```python
def init_db():
    """Initialize database with all tables."""
    # ... existing table creation ...

    # New table
    conn.execute(
        "CREATE TABLE IF NOT EXISTS new_items ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "name TEXT NOT NULL UNIQUE, "
        "value TEXT NOT NULL, "
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )

    # Index for performance
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_new_items_name "
        "ON new_items(name)"
    )
```

### 5. Writing Tests for New Features

```python
class TestNewFeature:
    """Test new feature functionality."""

    def test_create_item(self, temp_db):
        """Test creating an item."""
        success = NewFeatureManager.create_item("test", "value")
        assert success is True

        items = NewFeatureManager.list_items()
        assert len(items) == 1
        assert items[0]['name'] == "test"
        assert items[0]['value'] == "value"

    def test_create_duplicate_item(self, temp_db):
        """Test duplicate item prevention."""
        NewFeatureManager.create_item("test", "value1")
        success = NewFeatureManager.create_item("test", "value2")
        assert success is False
```

## Debugging

### Logging

The application uses Python's `logging` module:

```python
import logging

logger = logging.getLogger(__name__)

# Log levels
logger.debug("Detailed information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical error")
```

**View logs:**
```bash
tail -f scraper_tui_v1.0.log
```

### Textual DevTools

Use Textual's built-in developer tools:

```bash
# Run with console for debugging
textual console

# In another terminal, run app
python scrapetui.py
```

### Python Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use Python 3.7+
breakpoint()
```

**PDB Commands:**
- `n`: Next line
- `s`: Step into function
- `c`: Continue execution
- `l`: List source code
- `p variable`: Print variable value
- `q`: Quit debugger

### Common Issues

**Issue:** Tests fail with "No module named 'scrapetui'"

**Solution:**
```bash
# Ensure you're in virtual environment
source .venv/bin/activate

# Ensure tests import correctly
cd WebScrape-TUI
pytest tests/
```

**Issue:** "ModuleNotFoundError: No module named 'matplotlib'"

**Solution:**
```bash
pip install matplotlib pandas
```

**Issue:** Database locked errors

**Solution:**
```python
# Ensure proper connection closing
with get_db_connection() as conn:
    # ... operations ...
    conn.commit()
# Connection auto-closed here
```

## Release Process

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., 1.6.0)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. **Update version numbers:**
   - `README.md` (title and badges)
   - `CHANGELOG.md` (add new version section)
   - `scrapetui.py` (if version constant exists)

2. **Run full test suite:**
```bash
pytest tests/ -v
```

3. **Update documentation:**
   - `CHANGELOG.md`: Complete feature list
   - `README.md`: New features in highlights
   - `docs/ROADMAP.md`: Mark completed items

4. **Commit changes:**
```bash
git add .
git commit -m "feat: release v1.X.0 with [feature description]"
```

5. **Create and push tag:**
```bash
git tag -a v1.X.0 -m "Release v1.X.0: [Feature Name]"
git push origin main
git push --tags
```

6. **Create GitHub Release:**
   - Go to GitHub repository
   - Click "Releases" → "Draft a new release"
   - Select tag v1.X.0
   - Title: "v1.X.0 - [Feature Name]"
   - Description: Copy from CHANGELOG.md
   - Attach any binaries/assets
   - Publish release

7. **Announce:**
   - Update project README
   - Post to relevant communities
   - Update documentation site (if applicable)

## Contributing

### Pull Request Process

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes with tests
4. Ensure all tests pass (`pytest tests/`)
5. Update documentation
6. Commit changes (follow conventional commits)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open Pull Request on GitHub

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] Added tests for new functionality
- [ ] All existing tests pass
- [ ] Test coverage >= 80%

## Checklist
- [ ] Code follows PEP 8 style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

### Code Review Guidelines

**For Reviewers:**
- Check code quality and style
- Verify tests are comprehensive
- Ensure documentation is updated
- Test functionality locally
- Provide constructive feedback

**For Contributors:**
- Respond to feedback promptly
- Make requested changes
- Keep PRs focused and small
- Write clear commit messages

## Resources

### External Documentation

- [Textual Documentation](https://textual.textualize.io/)
- [BeautifulSoup4 Docs](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [APScheduler Docs](https://apscheduler.readthedocs.io/)
- [Matplotlib Docs](https://matplotlib.org/stable/contents.html)
- [pytest Documentation](https://docs.pytest.org/)

### Learning Resources

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Async/Await in Python](https://docs.python.org/3/library/asyncio.html)
- [SQLite Tutorial](https://www.sqlitetutorial.net/)

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/doublegate/WebScrape-TUI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/doublegate/WebScrape-TUI/discussions)
- **Documentation**: This docs/ directory

---

Happy coding! 🚀
