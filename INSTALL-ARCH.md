# WebScrape-TUI Installation Guide for Arch Linux

## Current Situation

You're running:
- **OS**: Arch Linux (CachyOS)
- **Shell**: Fish shell
- **Python**: 3.13.7 (system)
- **Issue**: gensim is incompatible with Python 3.13

## Solution: Install Python 3.12

### Step 1: Install Python 3.12 from AUR

Choose your AUR helper:

```fish
# If you use yay (most common)
yay -S python312

# If you use paru
paru -S python312

# If you use another AUR helper or want to build manually
git clone https://aur.archlinux.org/python312.git
cd python312
makepkg -si
```

### Step 2: Verify Python 3.12 Installation

```fish
python3.12 --version
# Should show: Python 3.12.x
```

### Step 3: Create Virtual Environment with Python 3.12

```fish
# Navigate to project directory
cd ~/Code/WebScrape-TUI

# Create venv with Python 3.12
python3.12 -m venv venv-312

# Activate venv (Fish shell syntax)
source venv-312/bin/activate.fish
```

### Step 4: Install Dependencies

```fish
# Install all dependencies (including gensim)
pip install -r requirements.txt

# This should work without errors now!
```

### Step 5: Download spaCy Language Model

```fish
# Download English language model for entity recognition
python -m spacy download en_core_web_sm
```

### Step 6: Run the Application

```fish
python scrapetui.py
```

## Alternative: Continue with Python 3.13 (Without Topic Modeling)

If you don't want to install Python 3.12, you can continue using your current setup:

```fish
# Activate your Python 3.13 venv
source .venv/bin/activate.fish

# You already have 20/21 dependencies installed
# Everything works except topic modeling (Ctrl+Alt+T)

# Run the app
python scrapetui.py
```

**What works without gensim**:
- ✅ All v1.0-v1.8 features (scraping, AI, export, analytics)
- ✅ 16/17 v1.9.0 features (Q&A, entity recognition, duplicates, clustering, etc.)

**What doesn't work**:
- ❌ Topic Modeling (Ctrl+Alt+T)

## Fish Shell Tips

### Activating Virtual Environments

```fish
# Fish shell uses .fish extension
source venv-312/bin/activate.fish   # NOT activate (that's for bash/zsh)

# Deactivate
deactivate
```

### Setting Environment Variables (for API keys)

```fish
# Edit .env file
nano .env

# Add your API keys:
# GEMINI_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here
# CLAUDE_API_KEY=your_key_here
```

## Troubleshooting

### "externally-managed-environment" Error

This is Arch's PEP 668 protection. You're doing it correctly by using a virtual environment!

**✅ Correct** (you're already doing this):
```fish
source venv-312/bin/activate.fish   # Use venv
pip install -r requirements.txt     # Install in venv
```

**❌ Wrong** (don't do this):
```fish
pip install -r requirements.txt     # Without venv - will fail
```

### Fish Shell Command Errors

If you see "Unknown command" errors, make sure you're using Fish syntax:

```fish
# Fish uses 'and' instead of '&&'
command1; and command2

# Fish uses different variable syntax
set MY_VAR "value"
echo $MY_VAR
```

### Python Version Conflicts

To ensure you're using the right Python:

```fish
# Check which Python is active
which python
python --version

# Inside venv-312, should show Python 3.12.x
# Outside venv, shows Python 3.13.7
```

## Quick Start Commands (Copy-Paste for Fish)

```fish
# Install Python 3.12
yay -S python312

# Create and activate venv
cd ~/Code/WebScrape-TUI
python3.12 -m venv venv-312
source venv-312/bin/activate.fish

# Install everything
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Run
python scrapetui.py
```

## Future Sessions

To use the app after installation:

```fish
cd ~/Code/WebScrape-TUI
source venv-312/bin/activate.fish
python scrapetui.py
```

## Summary

**Best Option for You**: Install Python 3.12 from AUR
- Takes 5-10 minutes
- One-time setup
- All features work (100%)
- No compromises

**Quick Option**: Use Python 3.13 with 20/21 dependencies
- Already set up
- 99% of features work
- Missing only topic modeling
- Can upgrade later
