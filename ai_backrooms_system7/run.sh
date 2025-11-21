#!/bin/bash
# AI Backrooms - System 7 Edition
# Startup script with Ollama health check

echo "🖥️  AI Backrooms - System 7 Edition"
echo "===================================="
echo ""

# Check Python version
PYTHON_CMD="python3"
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION found"

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
