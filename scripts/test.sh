#!/bin/bash
# Test runner script for Infinite Backrooms
# Ensures tests run in the correct virtual environment

set -e  # Exit on error

echo "🧪 Running Infinite Backrooms Test Suite"
echo "========================================"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: 'uv' is not installed"
    echo "Please install uv: pip install uv"
    exit 1
fi

# Sync dependencies
echo "📦 Syncing dependencies..."
uv sync --dev

# Run tests based on arguments
if [ "$1" == "all" ]; then
    echo ""
    echo "🔬 Running ALL tests (including integration tests)..."
    echo "⚠️  Note: Integration tests require Ollama running on localhost:11434"
    echo ""
    uv run pytest tests/ --cov --cov-report=html --cov-report=term-missing -v
elif [ "$1" == "unit" ]; then
    echo ""
    echo "🔬 Running unit tests only (skipping integration tests)..."
    echo ""
    uv run pytest tests/ --cov --cov-report=html --cov-report=term-missing -v -k "not real and not Real"
elif [ "$1" == "fast" ]; then
    echo ""
    echo "⚡ Running fast unit tests (no coverage)..."
    echo ""
    uv run pytest tests/ -v -k "not real and not Real"
elif [ "$1" == "coverage" ]; then
    echo ""
    echo "📊 Running tests with detailed coverage report..."
    echo ""
    uv run pytest tests/ --cov --cov-report=html --cov-report=term-missing -v -k "not real and not Real"
    echo ""
    echo "📈 Coverage report generated at: htmlcov/index.html"
else
    echo ""
    echo "🔬 Running default test suite (unit tests with coverage)..."
    echo ""
    uv run pytest tests/ --cov --cov-report=html --cov-report=term-missing -v -k "not real and not Real"
fi

echo ""
echo "✅ Test run complete!"
