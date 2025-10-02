#!/bin/bash
# WebScrape-TUI - Python 3.13 Installation Script
# This script installs all dependencies except gensim (which is incompatible with Python 3.13)

echo "🔧 Installing WebScrape-TUI dependencies for Python 3.13..."
echo "⚠️  Note: Topic modeling features (v1.9.0) will not be available without gensim"
echo ""

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Activate virtual environment if not already active
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d ".venv" ]; then
        echo "Activating virtual environment..."
        source .venv/bin/activate
    else
        echo "❌ Error: No virtual environment found. Please create one first:"
        echo "   python -m venv .venv"
        echo "   source .venv/bin/activate"
        exit 1
    fi
fi

# Install all dependencies except gensim
echo "📦 Installing dependencies (excluding gensim)..."
grep -v "^gensim" requirements.txt | pip install -r /dev/stdin

echo ""
echo "✅ Installation complete!"
echo ""
echo "📌 What works:"
echo "   ✓ All v1.0-v1.8 features (scraping, AI, export, analytics, etc.)"
echo "   ✓ 16 out of 17 v1.9.0 features"
echo ""
echo "⚠️  What doesn't work:"
echo "   ✗ Topic Modeling (Ctrl+Alt+T) - requires gensim"
echo ""
echo "💡 To use ALL features, use Python 3.12:"
echo "   pyenv install 3.12.8"
echo "   pyenv local 3.12.8"
echo "   python -m venv venv-312"
echo "   source venv-312/bin/activate"
echo "   pip install -r requirements.txt"
