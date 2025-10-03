# WebScrape-TUI Installation Guide

Complete installation instructions for all platforms and Python versions.

## Table of Contents

- [Quick Start](#quick-start)
- [Platform-Specific Instructions](#platform-specific-instructions)
- [Python Version Compatibility](#python-version-compatibility)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Standard Installation (Python 3.8-3.12)

```bash
# Clone repository
git clone https://github.com/doublegate/WebScrape-TUI.git
cd WebScrape-TUI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Run application
python scrapetui.py
```

### Python 3.13 Installation

See [Python 3.13 Compatibility](#python-313-compatibility) section below.

## Platform-Specific Instructions

### Arch Linux + Fish Shell

See [INSTALL-ARCH.md](../INSTALL-ARCH.md) for comprehensive Arch Linux installation guide.

Quick commands:
```fish
yay -S python312
python3.12 -m venv venv-312
source venv-312/bin/activate.fish
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Ubuntu/Debian

```bash
# Install Python 3.12 (if needed)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv

# Create venv
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### macOS

```bash
# Install Python 3.12 (if needed)
brew install python@3.12

# Create venv
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Windows

```powershell
# Download Python 3.12 from python.org
# Install to C:\Python312

# Create venv
C:\Python312\python.exe -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Python Version Compatibility

### Supported Versions

- **Python 3.8-3.12**: ✅ Fully supported (all features work)
- **Python 3.13**: ⚠️ Partial support (99% features, no topic modeling)

### Python 3.13 Compatibility

**Issue**: The gensim library (used for topic modeling in v1.9.0) is not yet compatible with Python 3.13.

**Solutions**:

#### Option 1: Use Python 3.12 (Recommended)

Install Python 3.12 alongside Python 3.13 and create a separate virtual environment. See platform-specific instructions above.

#### Option 2: Use Python 3.13 Without Topic Modeling

Run the automated installation script:
```bash
./install-python313.sh
```

Or install manually:
```bash
grep -v "^gensim" requirements.txt | pip install -r /dev/stdin
python -m spacy download en_core_web_sm
```

**What works**: All features except topic modeling (Ctrl+Alt+T)
**What doesn't work**: Topic modeling (LDA/NMF algorithms)

#### Option 3: Wait for gensim Update

Monitor https://pypi.org/project/gensim/ for Python 3.13 compatibility updates.

### Verifying Installation

```bash
# Check Python version
python --version

# Verify key dependencies
python -c "import textual; print('textual:', textual.__version__)"
python -c "import bcrypt; print('bcrypt:', bcrypt.__version__)"  # v2.0.0+
python -c "import gensim; print('gensim:', gensim.__version__)"  # Will fail on Python 3.13
python -c "import spacy; print('spacy:', spacy.__version__)"

# Run application (v2.0.0+: login required)
python scrapetui.py
# Default credentials: admin / Ch4ng3M3 (change immediately!)
```

## Troubleshooting

### gensim Installation Fails

**Error**:
```
error: command '/usr/bin/gcc' failed with exit code 1
ERROR: Failed building wheel for gensim
```

**Solution**: You're using Python 3.13. See [Python 3.13 Compatibility](#python-313-compatibility) above.

### spaCy Model Not Found

**Error**: "Can't find model 'en_core_web_sm'"

**Solution**:
```bash
python -m spacy download en_core_web_sm
```

### Virtual Environment Activation Issues

**Fish Shell** (Arch Linux, etc.):
```fish
source venv/bin/activate.fish  # NOT activate
```

**Bash/Zsh** (Most Linux/macOS):
```bash
source venv/bin/activate
```

**Windows PowerShell**:
```powershell
venv\Scripts\Activate.ps1
```

**Windows CMD**:
```cmd
venv\Scripts\activate.bat
```

### For More Help

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for comprehensive troubleshooting guide.

## Additional Resources

- [README.md](../README.md) - Main documentation
- [INSTALL-ARCH.md](../INSTALL-ARCH.md) - Arch Linux specific guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development environment setup
