#!/usr/bin/env fish
# WebScrape-TUI - Arch Linux + Fish Shell Installation Script

echo "🔧 Installing Python 3.12 on Arch Linux..."
echo ""

# Check if python312 is already installed
if command -v python3.12 &> /dev/null
    echo "✅ Python 3.12 is already installed"
    python3.12 --version
else
    echo "📦 Installing Python 3.12 from AUR..."
    echo "Run one of these commands:"
    echo "  yay -S python312        # If you use yay"
    echo "  paru -S python312       # If you use paru"
    echo ""
    echo "After installation, run this script again."
    exit 1
end

# Create venv with Python 3.12
echo ""
echo "📦 Creating virtual environment with Python 3.12..."
python3.12 -m venv venv-312

# Fish shell venv activation
echo ""
echo "🐟 Activating virtual environment (fish shell)..."
source venv-312/bin/activate.fish

# Install dependencies
echo ""
echo "📦 Installing all dependencies (including gensim)..."
pip install -r requirements.txt

# Download spaCy model
echo ""
echo "📥 Downloading spaCy English language model..."
python -m spacy download en_core_web_sm

echo ""
echo "✅ Installation complete!"
echo ""
echo "To use this environment in the future:"
echo "  source venv-312/bin/activate.fish"
echo ""
echo "Then run:"
echo "  python scrapetui.py"
