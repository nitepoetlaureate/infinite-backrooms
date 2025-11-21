#!/bin/bash
# AI Backrooms - System 7 Edition
# Startup script with Ollama health check and Tkinter detection

echo "🖥️  AI Backrooms - System 7 Edition"
echo "===================================="
echo ""

# Function to test if Python has Tkinter
has_tkinter() {
    $1 -c "import tkinter" 2>/dev/null
    return $?
}

# Try to find Python with Tkinter support
# Priority order: Homebrew versions, system Python, generic python3
PYTHON_CANDIDATES=(
    "python3.12"
    "python3.11"
    "python3.10"
    "python3.9"
    "python3.8"
    "/usr/bin/python3"
    "python3"
)

PYTHON_CMD=""
echo "🔍 Searching for Python with Tkinter support..."

for candidate in "${PYTHON_CANDIDATES[@]}"; do
    if command -v $candidate &> /dev/null; then
        if has_tkinter $candidate; then
            PYTHON_CMD=$candidate
            PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
            echo "✅ Found Python $PYTHON_VERSION with Tkinter at: $PYTHON_CMD"
            break
        fi
    fi
done

# If no Python with Tkinter found, show helpful error
if [ -z "$PYTHON_CMD" ]; then
    echo "❌ No Python installation with Tkinter support found!"
    echo ""
    echo "Tkinter is required for the System 7 UI."
    echo ""
    echo "📋 Solutions for macOS:"
    echo "  1. Install python-tk via Homebrew:"
    echo "     brew install python-tk@3.12"
    echo ""
    echo "  2. Install Python from python.org (includes Tkinter):"
    echo "     https://www.python.org/downloads/macos/"
    echo ""
    echo "  3. Install via pyenv:"
    echo "     brew install pyenv"
    echo "     pyenv install 3.12.7"
    echo ""
    echo "📋 Solutions for Linux:"
    echo "  Ubuntu/Debian: sudo apt-get install python3-tk"
    echo "  Fedora: sudo dnf install python3-tkinter"
    echo ""
    exit 1
fi

# Check if Ollama is running
echo ""
echo "Checking Ollama connection..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    MODEL_COUNT=$(curl -s http://localhost:11434/api/tags | grep -o '"name"' | wc -l)
    echo "✅ Ollama is running ($MODEL_COUNT models available)"
else
    echo "⚠️  Ollama not detected at localhost:11434"
    echo ""
    echo "The app will still run, but AI features require Ollama."
    echo "To install Ollama:"
    echo "  1. Visit: https://ollama.ai/"
    echo "  2. Run: ollama serve"
    echo "  3. Pull a model: ollama pull llama3"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Launch application
echo ""
echo "🚀 Launching AI Backrooms..."
echo ""

cd "$(dirname "$0")"
$PYTHON_CMD main.py

echo ""
echo "👋 Thanks for using AI Backrooms!"
