#!/bin/bash
# Fix system.css styling by clearing all caches and forcing reload

echo "🧹 Clearing Python caches..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name "*.pyo" -delete 2>/dev/null

echo "🧹 Clearing Streamlit caches..."
rm -rf ~/.streamlit/cache 2>/dev/null
rm -rf .streamlit/cache 2>/dev/null

echo "🧹 Clearing uv caches..."
rm -rf .venv 2>/dev/null

echo "✅ All caches cleared!"
echo ""
echo "Now run:"
echo "  uv sync"
echo "  export PYTHONDONTWRITEBYTECODE=1"
echo "  uv run streamlit run streamlit_backroom.py --server.runOnSave false"
