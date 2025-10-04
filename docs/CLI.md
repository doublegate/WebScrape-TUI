# WebScrape-TUI CLI Reference

Complete command-line interface documentation for WebScrape-TUI v2.1.0+

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
  - [Scraping Commands](#scraping-commands)
  - [Export Commands](#export-commands)
  - [AI Commands](#ai-commands)
  - [Article Management](#article-management)
  - [User Management](#user-management)
  - [Database Management](#database-management)
- [Common Workflows](#common-workflows)
- [Environment Variables](#environment-variables)
- [Exit Codes](#exit-codes)

---

## Installation

Install WebScrape-TUI with CLI support:

```bash
pip install webscrape-tui
# or from source
pip install -e .
```

Verify installation:

```bash
scrapetui-cli --version
```

**Alternative Usage:**
```bash
# If scrapetui-cli is not in PATH
python -m scrapetui.cli --help
```

---

## Quick Start

```bash
# Initialize database
scrapetui-cli db init

# Scrape a website
scrapetui-cli scrape url --url "https://news.ycombinator.com" --selector "a.titlelink" --limit 10

# Export to CSV
scrapetui-cli export csv --output articles.csv

# Summarize an article
scrapetui-cli ai summarize --article-id 1 --provider gemini

# List all articles
scrapetui-cli articles list --limit 20
```

---

## Command Reference

### Global Options

All commands support these global options:

```bash
--version    # Show version and exit
--help       # Show help message and exit
```

---

## Scraping Commands

### `scrape url`

Scrape a single URL with custom CSS selector.

**Usage:**
```bash
scrapetui-cli scrape url --url URL --selector SELECTOR [OPTIONS]
```

**Options:**
- `--url TEXT` - URL to scrape (required)
- `--selector TEXT` - CSS selector for links (default: 'a')
- `--limit INTEGER` - Maximum number of articles to scrape (default: 10)
- `--tags TEXT` - Comma-separated tags to apply to scraped articles
- `--user-id INTEGER` - User ID for ownership (default: 1 = admin)
- `--format [text|json]` - Output format (default: text)

**Examples:**

```bash
# Basic scraping
scrapetui-cli scrape url --url "https://techcrunch.com" --selector "h2 a" --limit 20

# Scrape with tags
scrapetui-cli scrape url \
  --url "https://example.com/tech" \
  --selector "article a" \
  --tags "technology,news" \
  --limit 50

# JSON output
scrapetui-cli scrape url \
  --url "https://news.ycombinator.com" \
  --selector "a.titlelink" \
  --format json
```

**Output:**
```
Fetching URL...     ████████████████████████████████ 100%
Parsing HTML...     ████████████████████████████████ 100%
Storing articles... ████████████████████████████████ 100%

✓ Scraped https://techcrunch.com
  Inserted: 18 new articles
  Skipped: 2 duplicates

New articles:
  1. Latest AI Breakthrough Shows Promise
  2. Tech Company Announces New Product
  ...
```

---

### `scrape profile`

Scrape using a saved scraper profile.

**Usage:**
```bash
scrapetui-cli scrape profile --profile NAME [OPTIONS]
```

**Options:**
- `--profile TEXT` - Scraper profile name (required)
- `--limit INTEGER` - Override default limit from profile
- `--user-id INTEGER` - User ID for ownership (default: 1)
- `--format [text|json]` - Output format (default: text)

**Examples:**

```bash
# Use saved profile
scrapetui-cli scrape profile --profile "TechCrunch"

# Override limit
scrapetui-cli scrape profile --profile "HackerNews" --limit 50

# JSON output
scrapetui-cli scrape profile --profile "ArsTechnica" --format json
```

**Note:** Profiles must be created first via the TUI application (Ctrl+Alt+S).

---

### `scrape bulk`

Scrape multiple profiles in bulk.

**Usage:**
```bash
scrapetui-cli scrape bulk --profiles NAMES [OPTIONS]
```

**Options:**
- `--profiles TEXT` - Comma-separated list of profile names (required)
- `--limit INTEGER` - Override default limit for all profiles
- `--user-id INTEGER` - User ID for ownership (default: 1)

**Examples:**

```bash
# Scrape multiple sources
scrapetui-cli scrape bulk --profiles "TechCrunch,HackerNews,ArsTechnica"

# With custom limit
scrapetui-cli scrape bulk \
  --profiles "TechNews,DevNews,AINews" \
  --limit 100
```

**Output:**
```
Bulk scraping 3 profiles...

TechCrunch: Fetching... ████████████████████████████ 100%
  ✓ TechCrunch: 25 new, 5 skipped

HackerNews: Fetching... ████████████████████████████ 100%
  ✓ HackerNews: 30 new, 0 skipped

============================================================
Bulk scraping complete:
  Total inserted: 55
  Total skipped: 5
  Profiles processed: 2/3
```

---

## Export Commands

### `export csv`

Export articles to CSV format with optional filtering.

**Usage:**
```bash
scrapetui-cli export csv --output FILE [OPTIONS]
```

**Options:**
- `-o, --output PATH` - Output CSV file path (required)
- `--search TEXT` - Search text in title/content
- `--tag TEXT` - Filter by tag
- `--date-from TEXT` - Articles after date (YYYY-MM-DD)
- `--date-to TEXT` - Articles before date (YYYY-MM-DD)
- `--user-id INTEGER` - Filter by user ID
- `--sentiment TEXT` - Filter by sentiment (Positive, Negative, Neutral)
- `--limit INTEGER` - Limit number of results

**Examples:**

```bash
# Export all articles
scrapetui-cli export csv --output all_articles.csv

# Export with filters
scrapetui-cli export csv \
  --output tech_news.csv \
  --tag "technology" \
  --limit 100

# Export date range
scrapetui-cli export csv \
  --output october_2025.csv \
  --date-from "2025-10-01" \
  --date-to "2025-10-31"

# Export by sentiment
scrapetui-cli export csv \
  --output positive_news.csv \
  --sentiment "Positive"
```

**CSV Format:**
```csv
ID,Title,Source URL,Article Link,Timestamp,Summary,Sentiment,User ID,Tags
1,"Example Article","https://example.com","https://example.com/article-1","2025-10-04 10:30:00","Brief summary...","Positive",1,"tech,news"
```

---

### `export json`

Export articles to JSON format.

**Usage:**
```bash
scrapetui-cli export json --output FILE [OPTIONS]
```

**Options:**
- `-o, --output PATH` - Output JSON file path (required)
- `--search TEXT` - Search text in title/content
- `--tag TEXT` - Filter by tag
- `--date-from TEXT` - Articles after date (YYYY-MM-DD)
- `--date-to TEXT` - Articles before date (YYYY-MM-DD)
- `--user-id INTEGER` - Filter by user ID
- `--sentiment TEXT` - Filter by sentiment
- `--limit INTEGER` - Limit number of results
- `--pretty` - Pretty-print JSON output

**Examples:**

```bash
# Export all (pretty-printed)
scrapetui-cli export json --output articles.json --pretty

# Export with search
scrapetui-cli export json \
  --output ai_articles.json \
  --search "artificial intelligence" \
  --pretty

# Compact JSON
scrapetui-cli export json --output data.json --limit 1000
```

**JSON Structure:**
```json
{
  "exported_at": "2025-10-04T12:30:45.123456",
  "total_articles": 150,
  "filters": {
    "search": null,
    "tag": "technology",
    "limit": 150
  },
  "articles": [
    {
      "id": 1,
      "title": "Article Title",
      "url": "https://example.com",
      "link": "https://example.com/article-1",
      "timestamp": "2025-10-04T10:30:00",
      "summary": "Article summary...",
      "sentiment": "Positive",
      "user_id": 1,
      "tags": "tech,news"
    }
  ]
}
```

---

### `export excel`

Export articles to Excel (XLSX) format with formatting.

**Requirements:** `pip install openpyxl`

**Usage:**
```bash
scrapetui-cli export excel --output FILE [OPTIONS]
```

**Options:**
- `-o, --output PATH` - Output Excel file path (required)
- `--search TEXT` - Search text in title/content
- `--tag TEXT` - Filter by tag
- `--date-from TEXT` - Articles after date (YYYY-MM-DD)
- `--date-to TEXT` - Articles before date (YYYY-MM-DD)
- `--user-id INTEGER` - Filter by user ID
- `--sentiment TEXT` - Filter by sentiment
- `--limit INTEGER` - Limit number of results
- `--include-charts` - Include charts and visualizations
- `--template [standard|executive|detailed]` - Export template style (default: standard)

**Examples:**

```bash
# Basic export
scrapetui-cli export excel --output articles.xlsx

# Executive report with charts
scrapetui-cli export excel \
  --output monthly_report.xlsx \
  --template executive \
  --include-charts

# Detailed export
scrapetui-cli export excel \
  --output detailed_analysis.xlsx \
  --template detailed \
  --tag "technology"
```

**Features:**
- Multiple sheets (Articles, Statistics, Timeline, Charts)
- Styled headers with auto-column sizing
- Embedded charts and graphs (with `--include-charts`)
- Professional formatting

---

### `export pdf`

Export articles to PDF report format.

**Requirements:** `pip install reportlab`

**Usage:**
```bash
scrapetui-cli export pdf --output FILE [OPTIONS]
```

**Options:**
- `-o, --output PATH` - Output PDF file path (required)
- `--search TEXT` - Search text in title/content
- `--tag TEXT` - Filter by tag
- `--date-from TEXT` - Articles after date (YYYY-MM-DD)
- `--date-to TEXT` - Articles before date (YYYY-MM-DD)
- `--user-id INTEGER` - Filter by user ID
- `--sentiment TEXT` - Filter by sentiment
- `--limit INTEGER` - Limit number of results
- `--include-charts` - Include charts and visualizations
- `--template [standard|executive|detailed]` - Report template style (default: standard)

**Examples:**

```bash
# Basic PDF report
scrapetui-cli export pdf --output articles.pdf

# Executive summary
scrapetui-cli export pdf \
  --output executive_summary.pdf \
  --template executive \
  --include-charts \
  --limit 50

# Filtered report
scrapetui-cli export pdf \
  --output tech_report.pdf \
  --tag "technology" \
  --sentiment "Positive"
```

**Features:**
- Executive summary sections
- Embedded charts and graphs
- Table of contents
- Professional layouts and styling

---

## AI Commands

### `ai summarize`

Generate AI-powered summary for an article.

**Usage:**
```bash
scrapetui-cli ai summarize --article-id ID [OPTIONS]
```

**Options:**
- `--article-id INTEGER` - Article ID to summarize (required)
- `--provider [gemini|openai|claude]` - AI provider (default: gemini)
- `--style [brief|detailed|executive]` - Summary style (default: brief)

**Examples:**

```bash
# Basic summarization
scrapetui-cli ai summarize --article-id 123

# Detailed summary with OpenAI
scrapetui-cli ai summarize \
  --article-id 123 \
  --provider openai \
  --style detailed
```

**Requirements:** API keys must be set in `.env` file.

---

### `ai keywords`

Extract keywords from an article.

**Usage:**
```bash
scrapetui-cli ai keywords --article-id ID [OPTIONS]
```

**Options:**
- `--article-id INTEGER` - Article ID (required)
- `--top INTEGER` - Number of top keywords (default: 10)

**Examples:**

```bash
scrapetui-cli ai keywords --article-id 123 --top 15
```

---

### `ai entities`

Extract named entities from an article.

**Usage:**
```bash
scrapetui-cli ai entities --article-id ID
```

**Examples:**

```bash
scrapetui-cli ai entities --article-id 123
```

**Output:** Lists people, organizations, locations, dates, etc.

---

### `ai topics`

Perform topic modeling on article collection.

**Usage:**
```bash
scrapetui-cli ai topics [OPTIONS]
```

**Options:**
- `--num-topics INTEGER` - Number of topics to extract (default: 5)
- `--tag TEXT` - Filter articles by tag
- `--limit INTEGER` - Limit number of articles to analyze

**Examples:**

```bash
scrapetui-cli ai topics --num-topics 10
scrapetui-cli ai topics --tag "technology" --num-topics 5
```

---

### `ai question`

Answer questions using article content.

**Usage:**
```bash
scrapetui-cli ai question --query TEXT
```

**Options:**
- `--query TEXT` - Question to answer (required)
- `--tag TEXT` - Filter articles by tag
- `--limit INTEGER` - Limit search to N articles

**Examples:**

```bash
scrapetui-cli ai question --query "What are the latest AI trends?"
scrapetui-cli ai question --query "Who won the championship?" --tag "sports"
```

---

### `ai similar`

Find similar articles using AI embeddings.

**Usage:**
```bash
scrapetui-cli ai similar --article-id ID [OPTIONS]
```

**Options:**
- `--article-id INTEGER` - Reference article ID (required)
- `--top INTEGER` - Number of similar articles (default: 5)

**Examples:**

```bash
scrapetui-cli ai similar --article-id 123 --top 10
```

---

## Article Management

### `articles list`

List articles with optional filtering.

**Usage:**
```bash
scrapetui-cli articles list [OPTIONS]
```

**Options:**
- `--search TEXT` - Search in title/content
- `--tag TEXT` - Filter by tag
- `--limit INTEGER` - Limit results (default: 20)
- `--format [table|json]` - Output format (default: table)

**Examples:**

```bash
# List recent articles
scrapetui-cli articles list --limit 50

# Search articles
scrapetui-cli articles list --search "AI" --limit 20

# JSON output
scrapetui-cli articles list --format json
```

---

### `articles show`

Display full article details.

**Usage:**
```bash
scrapetui-cli articles show --article-id ID
```

**Examples:**

```bash
scrapetui-cli articles show --article-id 123
```

---

### `articles delete`

Delete an article.

**Usage:**
```bash
scrapetui-cli articles delete --article-id ID
```

**Examples:**

```bash
scrapetui-cli articles delete --article-id 123
```

**Note:** Requires ownership or admin privileges.

---

## User Management

### `user create`

Create a new user account.

**Usage:**
```bash
scrapetui-cli user create --username NAME [OPTIONS]
```

**Options:**
- `--username TEXT` - Username (required, unique)
- `--email TEXT` - Email address
- `--role [admin|user|viewer]` - User role (default: user)

**Examples:**

```bash
# Create user (prompts for password)
scrapetui-cli user create --username alice --email alice@example.com --role user

# Create admin
scrapetui-cli user create --username admin2 --role admin
```

**Roles:**
- `admin` - Full system access, can manage users
- `user` - Can create/edit/delete own content, view all
- `viewer` - Read-only access to all content

---

### `user list`

List all users.

**Usage:**
```bash
scrapetui-cli user list
```

**Output:**
```
Users:
┌────┬──────────┬───────────────────┬────────┬────────────────────┐
│ ID │ Username │ Email             │ Role   │ Created            │
├────┼──────────┼───────────────────┼────────┼────────────────────┤
│  1 │ admin    │ admin@example.com │ admin  │ 2025-10-01 10:00   │
│  2 │ alice    │ alice@example.com │ user   │ 2025-10-04 14:30   │
└────┴──────────┴───────────────────┴────────┴────────────────────┘
```

---

### `user reset-password`

Reset user password.

**Usage:**
```bash
scrapetui-cli user reset-password --username NAME
```

**Examples:**

```bash
scrapetui-cli user reset-password --username alice
```

**Note:** Prompts for new password (hidden input).

---

## Database Management

### `db init`

Initialize database with schema.

**Usage:**
```bash
scrapetui-cli db init
```

**Examples:**

```bash
scrapetui-cli db init
```

**Note:** Safe to run on existing database (no data loss).

---

### `db backup`

Create database backup.

**Usage:**
```bash
scrapetui-cli db backup --output FILE
```

**Options:**
- `-o, --output PATH` - Backup file path (required)

**Examples:**

```bash
# Create timestamped backup
scrapetui-cli db backup --output backup_$(date +%Y%m%d).db

# Simple backup
scrapetui-cli db backup --output my_backup.db
```

---

### `db restore`

Restore database from backup.

**Usage:**
```bash
scrapetui-cli db restore --input FILE
```

**Options:**
- `-i, --input PATH` - Backup file path (required)

**Examples:**

```bash
scrapetui-cli db restore --input backup_20251004.db
```

**Warning:** This will overwrite current database. Confirmation required.

---

### `db migrate`

Run database migrations.

**Usage:**
```bash
scrapetui-cli db migrate
```

**Examples:**

```bash
scrapetui-cli db migrate
```

**Note:** Automatically detects and applies pending migrations.

---

## Common Workflows

### Daily News Aggregation

```bash
#!/bin/bash
# daily_scrape.sh - Run daily at 6 AM

# Scrape multiple sources
scrapetui-cli scrape bulk --profiles "TechCrunch,HackerNews,ArsTechnica" --limit 50

# Export daily summary
scrapetui-cli export csv --output "daily_$(date +%Y%m%d).csv" --date-from "$(date +%Y-%m-%d)"

# Generate topics
scrapetui-cli ai topics --num-topics 5 --tag "technology"
```

### Content Analysis Pipeline

```bash
#!/bin/bash
# analyze_content.sh

ARTICLE_ID=$1

# Summarize article
scrapetui-cli ai summarize --article-id $ARTICLE_ID

# Extract keywords
scrapetui-cli ai keywords --article-id $ARTICLE_ID --top 10

# Find related articles
scrapetui-cli ai similar --article-id $ARTICLE_ID --top 5

# Extract entities
scrapetui-cli ai entities --article-id $ARTICLE_ID
```

### Weekly Report Generation

```bash
#!/bin/bash
# weekly_report.sh - Run weekly

WEEK_START=$(date -d 'last Monday' +%Y-%m-%d)
WEEK_END=$(date -d 'next Sunday' +%Y-%m-%d)

# Export weekly data
scrapetui-cli export pdf \
  --output "weekly_report_$(date +%Y%m%d).pdf" \
  --date-from "$WEEK_START" \
  --date-to "$WEEK_END" \
  --template executive \
  --include-charts
```

### Backup and Maintenance

```bash
#!/bin/bash
# backup.sh - Run daily at midnight

# Create timestamped backup
BACKUP_FILE="backups/backup_$(date +%Y%m%d_%H%M%S).db"
scrapetui-cli db backup --output "$BACKUP_FILE"

# Keep only last 7 days of backups
find backups/ -name "backup_*.db" -mtime +7 -delete
```

---

## Environment Variables

The CLI respects these environment variables:

```bash
# Database path (optional, defaults to scraped_data_tui_v1.0.db)
export SCRAPETUI_DB_PATH="/path/to/custom.db"

# API keys for AI providers
export GEMINI_API_KEY="your_gemini_api_key"
export OPENAI_API_KEY="your_openai_api_key"
export ANTHROPIC_API_KEY="your_anthropic_api_key"

# Logging level
export SCRAPETUI_LOG_LEVEL="DEBUG"  # DEBUG, INFO, WARNING, ERROR
```

**Configuration File:**

Create `.env` file in project directory:
```env
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

---

## Exit Codes

The CLI uses standard exit codes:

- `0` - Success
- `1` - General error (HTTP error, invalid input, etc.)
- `2` - Command usage error (missing required arguments)

**Example:**
```bash
scrapetui-cli scrape url --url "https://example.com" && echo "Success!" || echo "Failed with code $?"
```

---

## Troubleshooting

### Common Issues

**Issue:** `scrapetui-cli: command not found`

**Solution:**
```bash
# Use Python module syntax
python -m scrapetui.cli --help

# Or add to PATH
export PATH="$PATH:~/.local/bin"
```

---

**Issue:** `No module named 'scrapetui'`

**Solution:**
```bash
pip install -e .
# or
pip install webscrape-tui
```

---

**Issue:** `openpyxl not found` or `reportlab not found`

**Solution:**
```bash
pip install openpyxl reportlab
# or install all optional dependencies
pip install webscrape-tui[all]
```

---

**Issue:** `API key not configured`

**Solution:**
```bash
# Create .env file
echo "GEMINI_API_KEY=your_key_here" >> .env
echo "OPENAI_API_KEY=your_key_here" >> .env
```

---

## Additional Resources

- **Main Documentation:** [README.md](../README.md)
- **API Documentation:** [API.md](./API.md)
- **Changelog:** [CHANGELOG.md](../CHANGELOG.md)
- **GitHub Repository:** https://github.com/doublegate/WebScrape-TUI

---

## Support

For issues, questions, or feature requests:

- **GitHub Issues:** https://github.com/doublegate/WebScrape-TUI/issues
- **Discussions:** https://github.com/doublegate/WebScrape-TUI/discussions

---

**Version:** 2.1.0 | **Last Updated:** 2025-10-04
