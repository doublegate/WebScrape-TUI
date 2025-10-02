# Troubleshooting Guide

This guide covers common issues, error messages, and solutions for WebScrape-TUI.

## Table of Contents

- [Python Version Compatibility Issues](#python-version-compatibility-issues)
- [Installation Issues](#installation-issues)
- [Runtime Errors](#runtime-errors)
- [Database Issues](#database-issues)
- [Scraping Problems](#scraping-problems)
- [AI Integration Issues](#ai-integration-issues)
- [Scheduling Issues](#scheduling-issues)
- [Analytics & Export Issues](#analytics--export-issues)
- [Performance Issues](#performance-issues)
- [UI Display Issues](#ui-display-issues)

---

## Python Version Compatibility Issues

### Python 3.13 Incompatibility with gensim

**Symptom**: Installation fails with compilation errors when running `pip install -r requirements.txt` on Python 3.13.

**Error Messages**:
```
gensim/models/word2vec_inner.c:9378:39: error: 'PyArray_Descr' has no member named 'subarray'
error: command '/usr/bin/gcc' failed with exit code 1
ERROR: Failed building wheel for gensim
```

**Root Cause**:
- gensim 4.3.x uses Cython code compiled for Python 3.12 and earlier
- Python 3.13 introduced breaking changes to the C API
- `PyArray_Descr` structure changed, `_PyLong_AsByteArray` signature changed
- gensim maintainers have not yet released a Python 3.13-compatible version

**Solutions**:

#### Solution 1: Use Python 3.12 (Recommended - 100% Feature Compatibility)

**For Arch Linux + Fish Shell**:
```fish
# Install Python 3.12 from AUR
yay -S python312

# Create venv with Python 3.12
cd ~/Code/WebScrape-TUI
python3.12 -m venv venv-312
source venv-312/bin/activate.fish

# Install all dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# See INSTALL-ARCH.md for detailed instructions
```

**For Ubuntu/Debian**:
```bash
# Install Python 3.12
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv

# Create venv with Python 3.12
python3.12 -m venv venv-312
source venv-312/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

**For macOS**:
```bash
# Install Python 3.12
brew install python@3.12

# Create venv with Python 3.12
python3.12 -m venv venv-312
source venv-312/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

**For Windows**:
```powershell
# Download Python 3.12 from python.org
# Install to C:\Python312

# Create venv with Python 3.12
C:\Python312\python.exe -m venv venv-312
venv-312\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

#### Solution 2: Use Python 3.13 Without Topic Modeling (99% Features)

**Automated Installation** (Linux/macOS):
```bash
# Run the provided script
./install-python313.sh
```

**Manual Installation**:
```bash
# Activate your Python 3.13 venv
source .venv/bin/activate

# Install all dependencies except gensim
grep -v "^gensim" requirements.txt | pip install -r /dev/stdin

# Download spaCy model
python -m spacy download en_core_web_sm
```

**What Works**:
- ✅ All v1.0-v1.8 features
- ✅ 16/17 v1.9.0 features

**What Doesn't Work**:
- ❌ Topic Modeling (Ctrl+Alt+T)

If you try to use topic modeling, you'll see an error message in the UI.

#### Solution 3: Wait for gensim Update

Monitor the gensim PyPI page for Python 3.13 support:
- https://pypi.org/project/gensim/
- GitHub issue tracker: https://github.com/RaRe-Technologies/gensim

Once gensim 4.4.0 or later with Python 3.13 support is released:
```bash
pip install --upgrade gensim
```

### Verifying Your Python Version

Check which Python version you're using:
```bash
python --version
# or
python3 --version
```

Inside a virtual environment, this should show the Python version the venv was created with.

### Platform-Specific Installation Guides

- **Arch Linux + Fish Shell**: See [INSTALL-ARCH.md](../INSTALL-ARCH.md)
- **General Linux/macOS/Windows**: See [README.md Installation section](../README.md#-installation)

---

## Installation Issues

### Issue: `ModuleNotFoundError: No module named 'textual'`

**Problem:** Dependencies not installed

**Solution:**
```bash
# Ensure you're in virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install all dependencies
pip install -r requirements.txt
```

---

### Issue: `pip install` fails with permission errors

**Problem:** Attempting to install system-wide without permissions

**Solution:**
```bash
# Option 1: Use virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Option 2: User install (not recommended)
pip install --user -r requirements.txt
```

---

### Issue: `ModuleNotFoundError: No module named 'matplotlib'` (v1.6.0+)

**Problem:** Missing v1.6.0 dependencies

**Solution:**
```bash
pip install matplotlib pandas

# Or reinstall all dependencies
pip install -r requirements.txt
```

---

## Runtime Errors

### Issue: `sqlite3.OperationalError: database is locked`

**Problem:** Multiple processes accessing database or improper connection closing

**Solution:**
```bash
# Option 1: Close other instances
# Ensure only one instance of scrapetui.py is running

# Option 2: Check for zombie processes
ps aux | grep scrapetui.py
kill <PID>

# Option 3: Remove lock file (if exists)
rm scraped_data_tui_v1.0.db-journal
```

**Prevention:**
```python
# Always use context managers
with get_db_connection() as conn:
    # ... operations ...
    conn.commit()
# Connection auto-closed
```

---

### Issue: `UnicodeDecodeError` when scraping

**Problem:** Non-UTF-8 encoded content

**Solution:**
This is handled internally, but if you see this error:

```python
# The application already handles this with:
response.encoding = response.apparent_encoding
```

If the issue persists:
1. Check the website's character encoding
2. Try a different scraper profile
3. Report as bug with URL

---

### Issue: `textual.app.AppError: Screen not found`

**Problem:** Modal screen dismissed improperly

**Solution:**
```bash
# Restart the application
# This is usually a transient error

# If persistent:
rm -rf ~/.textual/  # Clear Textual cache
```

---

## Database Issues

### Issue: Database file corrupted

**Problem:** Unexpected shutdown or disk full

**Symptoms:**
- `database disk image is malformed`
- Application crashes on startup

**Solution:**
```bash
# Option 1: Restore from backup (if you have one)
cp scraped_data_tui_v1.0.db.backup scraped_data_tui_v1.0.db

# Option 2: Export and rebuild
sqlite3 scraped_data_tui_v1.0.db .dump > backup.sql
rm scraped_data_tui_v1.0.db
python scrapetui.py  # Will create new DB
# Then manually import from backup.sql

# Option 3: Start fresh (loses data)
rm scraped_data_tui_v1.0.db
python scrapetui.py
```

**Prevention:**
```bash
# Regular backups
cp scraped_data_tui_v1.0.db "backup_$(date +%Y%m%d).db"

# Or use cron for automatic backups
# Add to crontab:
# 0 0 * * * cp /path/to/scraped_data_tui_v1.0.db /path/to/backups/backup_$(date +\%Y\%m\%d).db
```

---

### Issue: Missing tables or columns

**Problem:** Database from older version

**Symptoms:**
- `no such table: scheduled_scrapes`
- `no such column: summary`

**Solution:**
```bash
# The application should auto-migrate, but if not:

# Check current schema
sqlite3 scraped_data_tui_v1.0.db ".schema"

# Manual migration (example for v1.5.0 scheduled_scrapes table)
sqlite3 scraped_data_tui_v1.0.db << EOF
CREATE TABLE IF NOT EXISTS scheduled_scrapes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    scraper_profile_id INTEGER NOT NULL,
    schedule_type TEXT NOT NULL,
    schedule_value TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT 1,
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    run_count INTEGER DEFAULT 0,
    last_status TEXT,
    last_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scraper_profile_id) REFERENCES saved_scrapers(id)
);
EOF

# Restart application
python scrapetui.py
```

---

## Scraping Problems

### Issue: "No articles found" despite visible content

**Problem:** Incorrect CSS selector

**Solution:**
1. **Inspect the webpage:**
   ```bash
   # Use browser DevTools (F12)
   # Right-click article → Inspect
   # Find the selector (e.g., "article h2 a")
   ```

2. **Test selector:**
   ```python
   # In Python console:
   from bs4 import BeautifulSoup
   import requests

   response = requests.get("URL")
   soup = BeautifulSoup(response.text, 'lxml')
   articles = soup.select("YOUR_SELECTOR")
   print(f"Found {len(articles)} articles")
   ```

3. **Common selectors:**
   - `h2 a` - Headlines with links
   - `article a` - Articles with links
   - `.post-title a` - Class-based
   - `#content h3 a` - ID-based

---

### Issue: HTTP timeout errors

**Problem:** Slow website or network issues

**Symptoms:**
- `requests.exceptions.Timeout`
- Scraping hangs

**Solution:**
```bash
# Check network connection
ping google.com

# Try different timeout in code (default: 30s)
# The application has retry logic, but you can increase timeout

# If persistent:
# 1. Check if website is accessible in browser
# 2. Try VPN if region-blocked
# 3. Check robots.txt compliance
```

---

### Issue: 403 Forbidden errors

**Problem:** Website blocking automated requests

**Symptoms:**
- `403 Forbidden`
- Empty content

**Solution:**
The application includes a User-Agent header, but some sites block anyway.

**Workarounds:**
1. Use Wayback Machine integration (Archive.org)
2. Try different scraper profile
3. Manual data entry
4. Wait and retry (rate limiting)

**Not Recommended:**
- Aggressive scraping (respects robots.txt)
- Bypassing security measures
- Commercial use of scraped data without permission

---

## AI Integration Issues

### Issue: `API key not found` or `Invalid API key`

**Problem:** Missing or incorrect API key configuration

**Solution:**
```bash
# Option 1: Via Settings Modal (Ctrl+G)
# 1. Press Ctrl+G
# 2. Navigate to AI section
# 3. Enter API key
# 4. Save

# Option 2: Via config.yaml
# Edit config.yaml:
ai:
  gemini_api_key: "YOUR_KEY_HERE"
  openai_api_key: "YOUR_KEY_HERE"
  claude_api_key: "YOUR_KEY_HERE"

# Option 3: Via .env file (legacy)
# Create .env:
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
CLAUDE_API_KEY=your_key_here
```

---

### Issue: AI summarization fails with rate limit errors

**Problem:** API quota exceeded

**Symptoms:**
- `429 Too Many Requests`
- "Quota exceeded" message

**Solution:**
```bash
# 1. Check API usage dashboard
# Google: https://console.cloud.google.com/
# OpenAI: https://platform.openai.com/usage
# Claude: https://console.anthropic.com/

# 2. Reduce usage
# - Summarize fewer articles
# - Use lower-tier API (Gemini Flash instead of Pro)
# - Increase interval between summaries

# 3. Switch providers
# Press Ctrl+P to select different AI provider
```

---

### Issue: AI responses are poor quality

**Problem:** Wrong template or provider for content type

**Solution:**
1. **Try different templates:**
   - "overview" - General summary
   - "bullets" - Key points
   - "academic" - Technical content
   - "news" - News articles
   - "executive" - Business reports

2. **Switch AI providers:**
   ```bash
   # Press Ctrl+P
   # Try: Gemini → OpenAI → Claude
   # Different models excel at different tasks
   ```

3. **Create custom template:**
   ```bash
   # In Settings (Ctrl+G)
   # Add custom template with specific instructions
   ```

---

## Scheduling Issues

### Issue: Scheduled scrapes not executing

**Problem:** Schedule disabled or incorrect configuration

**Solution:**
```bash
# 1. Check schedule is enabled
# Press Ctrl+Shift+A
# Verify "Enabled" column shows True

# 2. Check next_run time
# Ensure next_run is in the future

# 3. Check logs
tail -f scraper_tui_v1.0.log
# Look for schedule execution messages

# 4. Verify scraper profile exists
# The profile_id must be valid

# 5. Restart application
# Schedules load on startup
```

---

### Issue: Schedule runs but fails

**Problem:** Network error, invalid selector, or website change

**Solution:**
```bash
# 1. Check last_error in schedule management
# Press Ctrl+Shift+A
# View "Last Error" column

# 2. Test scraper profile manually
# Press Ctrl+M
# Run the same profile interactively

# 3. Common errors:
# - Network timeout: Increase timeout, check connection
# - Invalid selector: Website changed, update selector
# - Rate limiting: Increase interval between runs
```

---

### Issue: Next run time incorrect

**Problem:** Timezone confusion or calculation error

**Solution:**
```bash
# The application uses local system time

# 1. Verify system time
date

# 2. Check timezone
timedatectl  # Linux
# or
date +%Z     # macOS

# 3. Update schedule
# Press Ctrl+Shift+A
# Edit schedule with correct time
# Format: "HH:MM" (24-hour format)
```

---

## Analytics & Export Issues

### Issue: Charts not generating (v1.6.0+)

**Problem:** Matplotlib installation issue

**Solution:**
```bash
# 1. Verify matplotlib installed
pip list | grep matplotlib

# 2. Reinstall if missing
pip install matplotlib

# 3. Check for backend errors
# In logs:
tail -f scraper_tui_v1.0.log

# 4. Try manual chart generation
python -c "import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt; print('OK')"
```

---

### Issue: "No sentiment data available for chart"

**Problem:** No articles have sentiment analysis

**Solution:**
```bash
# 1. Check if any articles have sentiment
# In DataTable, look for sentiment column

# 2. Run sentiment analysis
# Select article → Press 's' → Analyze sentiment

# 3. For bulk sentiment analysis:
# This feature is planned for v1.8.0
# Currently: manual one-by-one
```

---

### Issue: CSV export is slow or fails

**Problem:** Large dataset (10,000+ articles)

**Solution:**
```bash
# 1. Use filters to reduce size
# Press Ctrl+F
# Filter by date range, tags, etc.

# 2. Export in batches
# Filter by year/month
# Export each batch separately

# 3. Increase system resources
# Close other applications
# Export might use significant memory

# 4. Use JSON export (faster for large datasets)
# Press Ctrl+J instead of Ctrl+E
```

---

## Performance Issues

### Issue: Application is slow or laggy

**Problem:** Large database, memory leak, or resource contention

**Symptoms:**
- UI unresponsive
- High CPU/memory usage
- Slow table refresh

**Solution:**
```bash
# 1. Check database size
ls -lh scraped_data_tui_v1.0.db

# 2. Optimize database
sqlite3 scraped_data_tui_v1.0.db "VACUUM;"
sqlite3 scraped_data_tui_v1.0.db "ANALYZE;"

# 3. Archive old data
# Export articles older than X months
# Delete from database
# Keep export for records

# 4. Restart application
# Clears any memory leaks

# 5. Check system resources
top  # or htop
# Look for python process
```

---

### Issue: Scraping is very slow

**Problem:** Network latency, rate limiting, or large pages

**Solution:**
```bash
# 1. Check network speed
# Run speed test

# 2. Reduce limit parameter
# Don't scrape 100+ articles at once
# Use limit of 10-20

# 3. Check website responsiveness
# Try opening in browser
# If slow there, it's the website

# 4. Use scheduled scraping for large jobs
# Set up hourly/daily schedule
# Scrape incrementally
```

---

## UI Display Issues

### Issue: Garbled text or weird characters

**Problem:** Terminal doesn't support Unicode

**Symptoms:**
- � characters
- Boxes instead of text
- Missing special characters

**Solution:**
```bash
# 1. Use UTF-8 compatible terminal
# Recommended:
# - Windows: Windows Terminal
# - macOS: iTerm2 or Terminal.app
# - Linux: gnome-terminal, konsole

# 2. Set locale
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# 3. Check terminal settings
# Ensure "UTF-8" encoding enabled
```

---

### Issue: Dark mode colors are hard to read

**Problem:** Terminal color scheme conflict

**Solution:**
```bash
# 1. Toggle light/dark mode
# Press Ctrl+L

# 2. Adjust terminal color scheme
# Use built-in themes that work well

# 3. Modify CSS (advanced)
# Edit web_scraper_tui_v1.0.tcss
# Adjust color values
```

---

### Issue: Table doesn't fit terminal window

**Problem:** Terminal too small or table too wide

**Solution:**
```bash
# 1. Resize terminal
# Maximize window
# Minimum recommended: 80x24

# 2. Use smaller font
# Zoom out in terminal
# Ctrl+Minus (usually)

# 3. Hide columns (not currently supported)
# Future feature for v1.7.0
```

---

## General Debugging

### Enable Detailed Logging

```bash
# Logs are automatically written to:
scraper_tui_v1.0.log

# Watch logs in real-time:
tail -f scraper_tui_v1.0.log

# Search for errors:
grep ERROR scraper_tui_v1.0.log
grep WARNING scraper_tui_v1.0.log
```

### Use Python Debugger

```python
# Add to scrapetui.py at problem location:
import pdb; pdb.set_trace()

# Or use built-in breakpoint (Python 3.7+):
breakpoint()

# Commands:
# n - next line
# s - step into
# c - continue
# p variable - print variable
# q - quit
```

### Textual DevTools

```bash
# Terminal 1: Start console
textual console

# Terminal 2: Run application
python scrapetui.py

# View debug output in Terminal 1
```

---

## Getting Help

If your issue isn't covered here:

1. **Check Documentation:**
   - README.md
   - docs/ARCHITECTURE.md
   - docs/API.md

2. **Search Issues:**
   - [GitHub Issues](https://github.com/doublegate/WebScrape-TUI/issues)

3. **Ask Community:**
   - [GitHub Discussions](https://github.com/doublegate/WebScrape-TUI/discussions)

4. **Report Bug:**
   - Create GitHub Issue with:
     - Error message (full traceback)
     - Steps to reproduce
     - Environment (OS, Python version)
     - Log file excerpt

---

## Emergency Recovery

### Complete Reset (LOSES ALL DATA)

```bash
# Backup first (if possible)
cp scraped_data_tui_v1.0.db backup.db
cp config.yaml config.yaml.backup

# Remove all application data
rm scraped_data_tui_v1.0.db
rm config.yaml
rm scraper_tui_v1.0.log

# Reinstall dependencies
pip uninstall -y textual requests beautifulsoup4 lxml PyYAML APScheduler matplotlib pandas
pip install -r requirements.txt

# Start fresh
python scrapetui.py
```

---

**Last Updated:** October 2025 (v1.6.0)
**Contributions:** Please submit issues or PRs for additional troubleshooting topics!
