#!/usr/bin/env python3
"""
Application constants and configuration values
Eliminates magic numbers and provides centralized configuration
"""

from pathlib import Path

# ============================================================================
# OLLAMA CONFIGURATION
# ============================================================================

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_TIMEOUT = 10  # seconds

# ============================================================================
# MESSAGE LIMITS
# ============================================================================

# History limits
MIN_HISTORY_MESSAGES = 10
MAX_HISTORY_MESSAGES = 200
DEFAULT_HISTORY_MESSAGES = 50

# Context limits (messages sent to AI)
MIN_CONTEXT_MESSAGES = 1
MAX_CONTEXT_MESSAGES = 25
DEFAULT_CONTEXT_MESSAGES = 10

# ============================================================================
# TIMEOUTS
# ============================================================================

# Response timeouts (seconds)
MIN_RESPONSE_TIMEOUT = 30
MAX_RESPONSE_TIMEOUT = 600
DEFAULT_RESPONSE_TIMEOUT = 300  # 5 minutes

# ============================================================================
# DELAYS
# ============================================================================

# Response delays (seconds)
MIN_RESPONSE_DELAY = 1
MAX_RESPONSE_DELAY = 60
DEFAULT_RESPONSE_DELAY_MIN = 2
DEFAULT_RESPONSE_DELAY_MAX = 8

# ============================================================================
# LOGGING
# ============================================================================

# Directory and file configuration
LOG_DIR = "conversations"
LOG_FILE_PREFIX = "streamlit_backroom"
LOG_TIMESTAMP_FORMAT = "%H:%M:%S"
LOG_DATE_FORMAT = "%Y-%m-%d"

# Application logging
APP_LOG_DIR = "logs"
APP_LOG_FILE = "app.log"
APP_LOG_MAX_BYTES = 10_000_000  # 10MB
APP_LOG_BACKUP_COUNT = 5

# ============================================================================
# UI COLORS
# ============================================================================

DEFAULT_PERSONA_COLOR = "#1f77b4"

# Predefined persona colors for quick setup
PRESET_COLORS = {
    "purple": "#9b59b6",
    "blue": "#3498db",
    "red": "#e74c3c",
    "orange": "#f39c12",
    "gray": "#95a5a6",
    "dark_blue": "#2c3e50",
    "dark_gray": "#34495e",
}

# ============================================================================
# VALIDATION LIMITS
# ============================================================================

MAX_PERSONA_NAME_LENGTH = 50
MAX_SYSTEM_PROMPT_LENGTH = 5000
MAX_MESSAGE_LENGTH = 10000

# ============================================================================
# RATE LIMITING
# ============================================================================

# Ollama API rate limits
OLLAMA_MAX_REQUESTS_PER_MINUTE = 10
OLLAMA_RATE_LIMIT_WINDOW_SECONDS = 60

# ============================================================================
# STREAMLIT CONFIGURATION
# ============================================================================

PAGE_TITLE = "AI Backroom"
PAGE_ICON = "🤖"
LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

# ============================================================================
# FILE PATTERNS
# ============================================================================

# Log file patterns for discovery
LOG_FILE_PATTERNS = [
    "backroom_*.txt",
    "ai_conversation_*.txt",
    "streamlit_backroom_*.txt"
]
