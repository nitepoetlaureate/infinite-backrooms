"""State management module for AI Backroom application.

Provides secure session management and application state handling
with proper validation and thread safety.
"""

from .app_state import AppState, get_app_state, reset_app_state
from .session_manager import SecureSessionManager

__all__ = [
    "AppState",
    "get_app_state",
    "reset_app_state",
    "SecureSessionManager",
]