# Migration Guide: v2.0.0 → v2.1.0

This guide helps users migrate from WebScrape-TUI v2.0.0 to v2.1.0.

## Overview

**v2.1.0** is a major feature release that adds:
- Advanced AI features (8 new AI capabilities)
- Command-line interface (CLI)
- Async database layer
- Zero deprecation warnings

**Migration Effort**: Low to Medium
- **Database**: Automatic (no schema changes)
- **Code**: Backward compatible (no breaking changes)
- **Configuration**: Minor updates for new features

---

## What's New in v2.1.0

### Sprint 1: Database & Core AI Features

**New AI Capabilities**:
- Named Entity Recognition (NER) - Extract people, organizations, locations
- Keyword Extraction - TF-IDF based keyword extraction
- Topic Modeling - LDA/NMF algorithms for content themes

**Keyboard Shortcuts**:
- `Ctrl+Shift+E` - Extract named entities
- `Ctrl+Shift+K` - Extract keywords
- `Ctrl+Alt+T` - Topic modeling

**Database Enhancements**:
- Improved query performance
- Better connection management
- Enhanced error handling

### Sprint 2: Advanced AI Features

**New AI Capabilities**:
- Question Answering - TF-IDF based Q&A with multi-article synthesis
- Entity Relationships - Knowledge graph construction from dependencies
- Summary Quality Metrics - ROUGE scores and coherence analysis
- Content Similarity - Embedding-based similarity search
- Duplicate Detection - Fuzzy matching for similar/duplicate articles

**Keyboard Shortcuts**:
- `Ctrl+Alt+Q` - Question answering
- `Ctrl+Alt+L` - Entity relationships
- `Ctrl+Alt+M` - Summary quality metrics
- `Ctrl+Shift+R` - Content similarity search
- `Ctrl+Alt+D` - Duplicate detection

### Sprint 3: Command-Line Interface

**New CLI Commands**:
- `scrapetui-cli users create/list/reset-password` - User management
- `scrapetui-cli database init/backup/restore` - Database operations
- `scrapetui-cli scrape url/profile/bulk` - Web scraping
- `scrapetui-cli export csv/json/excel/pdf` - Data export
- `scrapetui-cli ai summarize/keywords/entities/qa` - AI analysis

**Installation**:
```bash
pip install -e .
scrapetui-cli --help
```

**Use Cases**:
- Automation and scripting
- Cron jobs for scheduled scraping
- Batch processing of articles
- Headless server environments

### Sprint 4: Async & Performance

**Async Database Layer**:
- New `scrapetui/core/database_async.py` with aiosqlite
- Async CRUD operations for articles, users, sessions
- Better performance for concurrent operations
- FastAPI native async support

**Code Quality**:
- Zero deprecation warnings (future-proof)
- Modern async/await patterns
- Pydantic v2 best practices
- FastAPI latest patterns

---

## Migration Steps

### Step 1: Backup Your Data

**IMPORTANT**: Always backup before upgrading.

```bash
# Backup database
cp scraped_data_tui_v1.0.db scraped_data_tui_v1.0.db.backup

# Backup configuration
cp .env .env.backup
```

### Step 2: Update Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Update WebScrape-TUI
git pull origin main

# Install new dependencies
pip install -r requirements.txt

# Download spaCy model (for NER)
python -m spacy download en_core_web_sm
```

**New Dependencies**:
- `aiosqlite>=0.19.0` - Async database operations
- `pytest-asyncio` - Async test support (dev only)
- `spacy` - Named entity recognition
- `scikit-learn` - TF-IDF and topic modeling
- `gensim` - Topic modeling algorithms
- `sentence-transformers` - Embedding-based similarity
- `click` - CLI framework

### Step 3: Install CLI (Optional)

If you want to use the CLI:

```bash
pip install -e .
scrapetui-cli --help
```

### Step 4: Configure API Keys (Optional)

For AI features, add API keys to `.env`:

```bash
# Google Gemini (for summarization, sentiment)
GEMINI_API_KEY=your_gemini_api_key_here

# OpenAI GPT (alternative)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic Claude (alternative)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### Step 5: Test the Upgrade

```bash
# Run the TUI
python scrapetui.py

# Try new features
# - Press Ctrl+Shift+E on an article to extract entities
# - Press Ctrl+Shift+K to extract keywords
# - Press Ctrl+Alt+Q for question answering

# Test CLI (if installed)
scrapetui-cli --help
scrapetui-cli users list
```

---

## Database Migration

**Good News**: No database schema changes between v2.0.0 and v2.1.0!

Your existing database will work without migration. The application will:
- Continue using your existing `scraped_data_tui_v1.0.db`
- Preserve all users, articles, tags, and sessions
- No data loss or conversion needed

**Database Compatibility**:
- v2.0.0 schema → v2.1.0 schema: ✅ Compatible (no changes)
- Async layer uses same database: ✅ Compatible
- CLI uses same database: ✅ Compatible

---

## Configuration Changes

### Environment Variables

**New (Optional)**:
- `SCRAPETUI_DB_PATH` - Alternative to `DATABASE_PATH` (CLI compatibility)
- Both env vars are supported, use whichever you prefer

**Example `.env`**:
```bash
# Database path (choose one)
DATABASE_PATH=scraped_data_tui_v1.0.db
# OR
SCRAPETUI_DB_PATH=scraped_data_tui_v1.0.db

# AI API Keys (optional - for AI features)
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

---

## Breaking Changes

**None!** v2.1.0 is fully backward compatible with v2.0.0.

All existing functionality continues to work:
- ✅ User authentication and sessions
- ✅ Web scraping with profiles
- ✅ Article storage and management
- ✅ Tag system
- ✅ Existing AI features (summarization, sentiment)
- ✅ REST API endpoints
- ✅ TUI interface and keyboard shortcuts

---

## New Features Usage

### Using Advanced AI Features

**Named Entity Recognition**:
```bash
# Via TUI
1. Select an article
2. Press Ctrl+Shift+E
3. View extracted entities (people, organizations, locations)

# Via CLI
scrapetui-cli ai entities --article-id 123
```

**Keyword Extraction**:
```bash
# Via TUI
1. Select an article
2. Press Ctrl+Shift+K
3. View top keywords

# Via CLI
scrapetui-cli ai keywords --article-id 123
```

**Question Answering**:
```bash
# Via TUI
1. Press Ctrl+Alt+Q
2. Enter your question
3. Select articles to search
4. View answer with confidence score

# Via CLI
scrapetui-cli ai qa --question "What are the main topics?" --article-ids 1,2,3
```

### Using the CLI

**Daily Automation Example**:
```bash
#!/bin/bash
# daily_scrape.sh - Run this with cron

# Scrape news sources
scrapetui-cli scrape bulk --profiles "TechCrunch,HackerNews,ArsTechnica" --limit 100

# Export to CSV
scrapetui-cli export csv --output "articles_$(date +%Y%m%d).csv" --limit 100

# Generate summaries for recent articles
for id in $(seq 1 20); do
    scrapetui-cli ai summarize --article-id $id --provider gemini
done
```

**Cron Setup**:
```bash
# Edit crontab
crontab -e

# Add daily scrape at 6 AM
0 6 * * * /path/to/daily_scrape.sh
```

### Using Async Database (Advanced)

**For FastAPI Integration**:
```python
from scrapetui.core.database_async import get_async_db_manager

async def get_articles():
    db = get_async_db_manager()
    articles = await db.fetch_articles(limit=100)
    return articles
```

---

## Troubleshooting

### Issue: "Cannot login after CLI user creation"

**Solution**: Fixed in latest version. If you created users before the fix:
```bash
# Verify both CLI and TUI use same database
python -c "from scrapetui.config import get_config; print(get_config().database_path)"
python scrapetui.py  # Should show same database file

# If different, set env var:
export DATABASE_PATH=scraped_data_tui_v1.0.db
```

### Issue: "spaCy model not found"

**Solution**: Download the English model:
```bash
python -m spacy download en_core_web_sm
```

### Issue: "CLI command not found"

**Solution**: Install in editable mode:
```bash
pip install -e .
```

### Issue: "No module named 'aiosqlite'"

**Solution**: Install missing dependency:
```bash
pip install aiosqlite>=0.19.0
```

### Issue: "Deprecation warnings in output"

**Solution**: Our code has zero deprecation warnings. External library warnings are normal:
- spaCy, click, pydantic, httpx may show warnings
- These are from dependencies, not our code
- Safe to ignore

---

## Performance Improvements

**v2.1.0 Performance Enhancements**:

1. **Async Database** - Non-blocking operations for better concurrency
2. **CLI Efficiency** - Faster batch operations and export
3. **Test Suite** - Improved test isolation and speed
4. **Code Quality** - Reduced technical debt

**Expected Performance**:
- TUI startup: ~2 seconds (unchanged)
- Article queries: <100ms for 1000+ articles
- Session validation: <10ms
- Export operations: Faster with CLI batch mode

---

## Rollback Procedure

If you need to rollback to v2.0.0:

```bash
# Restore database backup
cp scraped_data_tui_v1.0.db.backup scraped_data_tui_v1.0.db

# Restore configuration
cp .env.backup .env

# Checkout v2.0.0
git checkout v2.0.0

# Reinstall dependencies
pip install -r requirements.txt
```

**Note**: No database migration needed, so rollback is safe and easy.

---

## Getting Help

**Documentation**:
- [Project Status](PROJECT-STATUS.md) - Current state and test results
- [Roadmap](ROADMAP.md) - Development roadmap
- [API Reference](API.md) - REST API documentation
- [CLI Reference](CLI.md) - Command-line interface
- [Architecture](ARCHITECTURE.md) - System design

**Issues**:
- GitHub Issues: https://github.com/doublegate/WebScrape-TUI/issues
- Create issue with `[v2.1.0]` tag for version-specific issues

**Support**:
- Check TROUBLESHOOTING.md for common issues
- Review CHANGELOG.md for detailed changes
- Search closed issues for similar problems

---

## Summary

**Migration Complexity**: ✅ Low
**Breaking Changes**: ✅ None
**Database Migration**: ✅ Not Required
**Estimated Time**: 15-30 minutes
**Rollback**: ✅ Easy and Safe

v2.1.0 is a **backward-compatible feature release** with significant new capabilities. All existing functionality is preserved while adding powerful new AI features, CLI automation, and async performance improvements.

**Recommended for all users** - upgrade process is straightforward with minimal risk.
