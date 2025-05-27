# Contributing to WebScrape-TUI

🎉 Thank you for your interest in contributing to WebScrape-TUI! We welcome contributions from developers of all skill levels and backgrounds.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Ways to Contribute](#ways-to-contribute)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to [conduct@webscrape-tui.com](mailto:conduct@webscrape-tui.com).

### Our Standards

**Examples of behavior that contributes to creating a positive environment include:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Examples of unacceptable behavior include:**
- The use of sexualized language or imagery and unwelcome sexual attention or advances
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

## Getting Started

### Prerequisites

- **Python 3.8+** (Python 3.9+ recommended)
- **Git** for version control
- **Terminal** with Unicode support
- **Text Editor/IDE** (VS Code, PyCharm, Vim, etc.)

### First Contribution

1. **Star the repository** ⭐ to show your support
2. **Fork the repository** to your GitHub account
3. **Clone your fork** locally
4. **Set up the development environment** (see below)
5. **Find a good first issue** labeled `good first issue`
6. **Make your changes** following our guidelines
7. **Submit a pull request** with a clear description

## Ways to Contribute

### 🐛 Bug Reports
Help us improve by reporting bugs you encounter:
- Use the bug report template
- Include clear reproduction steps
- Provide environment details (OS, Python version, terminal)
- Attach relevant log files and screenshots

### 💡 Feature Requests
Suggest new features or improvements:
- Check if the feature already exists or is planned
- Use the feature request template
- Describe the use case and expected behavior
- Consider implementation complexity

### 🛠️ Code Contributions
Contribute code improvements:
- **Bug fixes** for reported issues
- **New features** from the roadmap
- **Performance improvements** and optimizations
- **Code quality** enhancements and refactoring
- **Test coverage** improvements

### 📚 Documentation
Help improve our documentation:
- **README** improvements and corrections
- **Code comments** and docstrings
- **API documentation** for developers
- **User guides** and tutorials
- **Translation** into other languages

### 🧪 Testing
Improve test coverage and quality:
- **Unit tests** for new features
- **Integration tests** for workflows
- **Performance tests** for optimization
- **Manual testing** on different platforms
- **Accessibility testing** for UI components

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/doublegate/WebScrape-TUI.git
cd WebScrape-TUI

# Add the original repository as upstream
git remote add upstream https://github.com/doublegate/WebScrape-TUI.git
```

### 2. Create Development Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (if available)
pip install -r requirements-dev.txt

# Set up environment configuration
cp .env.example .env
# Edit .env file and add your API keys
```

### 3. Verify Installation

```bash
# Run the application to ensure it works
python scrapetui.py

# Run tests (if available)
python -m pytest tests/

# Check code style (if linting is set up)
flake8 scrapetui.py
black --check scrapetui.py
```

### 4. Create Feature Branch

```bash
# Create and switch to a new branch for your feature
git checkout -b feature/your-feature-name

# Or for bug fixes:
git checkout -b fix/bug-description
```

## Code Style Guidelines

### Python Code Style

We follow **PEP 8** with some project-specific conventions:

#### General Guidelines
- **Line length**: Maximum 88 characters (Black formatter default)
- **Indentation**: 4 spaces (no tabs)
- **Imports**: Group imports (standard library, third-party, local) and remove unused imports
- **Docstrings**: Use Google-style docstrings
- **Type hints**: Use type hints for function parameters and return values
- **Code Quality**: Follow PEP 8 standards (run flake8 before submitting)
- **Multi-line Strings**: Break long strings across multiple lines for readability
- **Error Handling**: Use proper exception handling with multi-line formatting
- **Database Operations**: Use context managers for safe resource management

#### Example Code Style

```python
#!/usr/bin/env python3
\"\"\"
Module docstring describing the module's purpose.

This module handles web scraping functionality for the TUI application.
\"\"\"

import sqlite3
from typing import Optional, List, Dict, Any
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from textual.app import App


class WebScraperClass:
    \"\"\"
    Class for handling web scraping operations.
    
    This class provides methods for scraping websites, parsing HTML content,
    and storing the results in a database.
    
    Attributes:
        database_path: Path to the SQLite database file.
        session: Requests session for HTTP operations.
    \"\"\"
    
    def __init__(self, database_path: Path) -> None:
        \"\"\"
        Initialize the web scraper.
        
        Args:
            database_path: Path to the SQLite database file.
        \"\"\"
        self.database_path = database_path
        self.session = requests.Session()
    
    def scrape_url(
        self, 
        url: str, 
        selector: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        \"\"\"
        Scrape articles from a given URL.
        
        Args:
            url: The target URL to scrape.
            selector: CSS selector for article elements.
            limit: Maximum number of articles to scrape.
            
        Returns:
            List of dictionaries containing article data.
            
        Raises:
            requests.RequestException: If the HTTP request fails.
            ValueError: If the selector is invalid.
        \"\"\"
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            articles = soup.select(selector)[:limit]
            
            return [self._extract_article_data(article) for article in articles]
        
        except requests.RequestException as e:
            logger.error(f\"Failed to scrape URL {url}: {e}\")
            raise
    
    def _extract_article_data(self, article_element) -> Dict[str, Any]:
        \"\"\"Extract data from an article element (private method).\"\"\"
        # Implementation details...
        pass
```

#### Naming Conventions
- **Variables**: `snake_case`
- **Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `SCREAMING_SNAKE_CASE`
- **Private methods**: `_leading_underscore`
- **Database tables**: `snake_case`

#### Error Handling
```python
try:
    # Risky operation
    result = perform_operation()
except SpecificException as e:
    logger.error(f\"Specific error occurred: {e}\")
    # Handle specific case
except Exception as e:
    logger.error(f\"Unexpected error: {e}\", exc_info=True)
    # Handle general case
finally:
    # Cleanup if needed
    cleanup_resources()
```

### Textual UI Guidelines

#### Widget Organization
```python
class MyScreen(Screen):
    \"\"\"Screen for displaying specific functionality.\"\"\"
    
    def compose(self) -> ComposeResult:
        \"\"\"Create child widgets for the screen.\"\"\"
        with Vertical():
            yield Header(show_clock=True)
            with Horizontal():
                yield SidebarWidget()
                yield MainContentWidget()
            yield Footer()
    
    def on_mount(self) -> None:
        \"\"\"Called when the screen is mounted.\"\"\"
        self.setup_initial_state()
    
    @on(Button.Pressed, \"#my-button\")
    def handle_button_press(self, event: Button.Pressed) -> None:
        \"\"\"Handle button press events.\"\"\"
        self.notify(\"Button pressed!\")
```

#### CSS Styling Guidelines
```css
/* Use semantic class names */
.article-list {
    height: 1fr;
    border: panel $primary;
}

/* Follow consistent spacing */
.modal-dialog {
    padding: 1 2;
    margin: 1;
    border: thick $accent;
}

/* Use CSS variables for theming */
.status-bar {
    background: $surface;
    color: $text;
    dock: bottom;
}
```

### Database Guidelines

#### Schema Design
- Use descriptive table and column names
- Include proper foreign key constraints
- Add indexes for frequently queried columns
- Use appropriate data types

#### Query Patterns
```python
def get_articles_by_tag(tag_name: str) -> List[sqlite3.Row]:
    \"\"\"Get all articles with a specific tag.\"\"\"
    with get_db_connection() as conn:
        return conn.execute(
            \"\"\"
            SELECT a.* FROM scraped_data a
            JOIN article_tags at ON a.id = at.article_id
            JOIN tags t ON at.tag_id = t.id
            WHERE t.name = ?
            ORDER BY a.timestamp DESC
            \"\"\",
            (tag_name,)
        ).fetchall()
```

## Testing

### Test Structure

We use **pytest** for testing. Tests are organized as follows:

```
tests/
├── test_database.py      # Database operation tests
├── test_scraping.py      # Web scraping tests
├── test_ui.py           # UI component tests
├── test_ai.py           # AI integration tests
└── fixtures/            # Test data and fixtures
    ├── sample_html/
    └── test_data.json
```

### Writing Tests

#### Unit Tests
```python
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from scrapetui import WebScraperClass


class TestWebScraper:
    \"\"\"Test cases for WebScraperClass.\"\"\"
    
    @pytest.fixture
    def scraper(self, tmp_path):
        \"\"\"Create a scraper instance for testing.\"\"\"
        db_path = tmp_path / \"test.db\"
        return WebScraperClass(db_path)
    
    def test_scrape_url_success(self, scraper):
        \"\"\"Test successful URL scraping.\"\"\"
        with patch('requests.Session.get') as mock_get:
            # Set up mock response
            mock_response = Mock()
            mock_response.content = \"<html><article>Test</article></html>\"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Test the method
            result = scraper.scrape_url(
                \"https://example.com\", 
                \"article\", 
                limit=1
            )
            
            # Assertions
            assert len(result) == 1
            mock_get.assert_called_once()
    
    def test_scrape_url_network_error(self, scraper):
        \"\"\"Test network error handling.\"\"\"
        with patch('requests.Session.get') as mock_get:
            mock_get.side_effect = requests.RequestException(\"Network error\")
            
            with pytest.raises(requests.RequestException):
                scraper.scrape_url(\"https://example.com\", \"article\")
```

#### Integration Tests
```python
def test_full_scraping_workflow(tmp_path):
    \"\"\"Test complete scraping workflow from URL to database.\"\"\"
    # Set up test environment
    db_path = tmp_path / \"test.db\"
    initialize_database(db_path)
    
    # Perform scraping operation
    scraper = WebScraperClass(db_path)
    # ... test implementation
    
    # Verify results in database
    with sqlite3.connect(db_path) as conn:
        articles = conn.execute(\"SELECT * FROM scraped_data\").fetchall()
        assert len(articles) > 0
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=scrapetui

# Run specific test file
python -m pytest tests/test_scraping.py

# Run with verbose output
python -m pytest -v

# Run only tests matching a pattern
python -m pytest -k \"test_scraping\"
```

## Pull Request Process

### Before Submitting

1. **Update your branch** with the latest changes from upstream:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   git checkout your-feature-branch
   git rebase main
   ```

2. **Test your changes** thoroughly:
   ```bash
   python -m pytest
   python scrapetui.py  # Manual testing
   ```

3. **Check code style**:
   ```bash
   flake8 scrapetui.py
   black --check scrapetui.py
   ```

4. **Update documentation** if needed:
   - Update README.md for new features
   - Add/update docstrings
   - Update CHANGELOG.md

### Pull Request Template

When creating a pull request, use this template:

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] I have tested this change thoroughly
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes

## Screenshots (if applicable)
Add screenshots to help explain your changes.

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have checked my code and corrected any misspellings
```

### Review Process

1. **Automated checks** will run (if configured)
2. **Maintainer review** will be requested
3. **Address feedback** if any changes are requested
4. **Approval and merge** once all requirements are met

## Issue Guidelines

### Bug Reports

Use the bug report template and include:

- **Environment details**: OS, Python version, terminal type
- **Steps to reproduce**: Clear, numbered steps
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Screenshots/logs**: Visual evidence if applicable
- **Additional context**: Any other relevant information

### Feature Requests

Use the feature request template and include:

- **Problem description**: What problem does this solve?
- **Proposed solution**: How should it work?
- **Alternatives considered**: Other approaches you've thought of
- **Implementation ideas**: Technical suggestions if any
- **Use cases**: Who would benefit and how?

### Good Issue Practices

- **Search existing issues** before creating new ones
- **Use descriptive titles** that summarize the issue
- **Provide complete information** to help maintainers understand
- **Label appropriately** if you have permission
- **Follow up** on questions from maintainers

## Documentation

### Types of Documentation

1. **Code Documentation**
   - Inline comments for complex logic
   - Docstrings for all public functions and classes
   - Type hints for better code understanding

2. **User Documentation**
   - README.md for general usage
   - Installation and setup guides
   - Feature documentation and tutorials

3. **Developer Documentation**
   - Architecture decisions and patterns
   - API documentation
   - Contribution guidelines (this file)

### Documentation Standards

- **Clear and concise** language
- **Step-by-step instructions** for procedures
- **Examples and code snippets** for clarity
- **Up-to-date information** that reflects current state
- **Proper formatting** with markdown

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General discussions and questions
- **Pull Requests**: Code review and collaboration
- **Email**: [support@webscrape-tui.com](mailto:support@webscrape-tui.com) for private matters

### Getting Help

- **Check existing documentation** first
- **Search issues and discussions** for similar questions
- **Provide complete context** when asking for help
- **Be patient and respectful** in interactions

### Community Values

- **Inclusivity**: Welcome contributors from all backgrounds
- **Respect**: Treat everyone with kindness and respect
- **Collaboration**: Work together towards common goals
- **Learning**: Help others learn and grow
- **Quality**: Strive for high-quality contributions

## Recognition

We appreciate all contributions to WebScrape-TUI:

- **Contributors** are listed in our GitHub repository
- **Significant contributions** may be highlighted in release notes
- **Community helpers** are recognized for their support
- **Maintainers** work hard to keep the project running smoothly

### Ways to Show Appreciation

- ⭐ **Star the repository** to show support
- 🐛 **Report bugs** to help improve quality
- 💡 **Suggest features** for future development
- 🛠️ **Contribute code** to add functionality
- 📚 **Improve documentation** for better user experience
- 🗣️ **Share the project** with others who might benefit

---

**Thank you for contributing to WebScrape-TUI!** 🚀

Your contributions help make this project better for everyone. Whether you're fixing a typo, adding a feature, or helping other users, every contribution matters.

*Happy coding!* 💻