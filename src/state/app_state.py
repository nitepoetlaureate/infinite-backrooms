"""Application State Management.

Centralized state management for the Streamlit application with
proper initialization and synchronization with session state.
"""

from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from src.services.logger import ConversationLogger
from src.state.session_manager import SecureSessionManager


class AppState:
    """Centralized application state manager.

    Manages application-wide state and ensures proper initialization
    of all components with Streamlit session state integration.

    Attributes:
        session_manager: Secure session state manager
        conversation_orchestrator: Business logic orchestrator
        conversation_logger: Conversation logging service
    """

    def __init__(self) -> None:
        """Initialize application state."""
        self._initialize_session_state()
        self.session_manager = SecureSessionManager()
        self.conversation_logger = ConversationLogger()
        self.conversation_orchestrator = ConversationOrchestrator(
            self.session_manager,
            self.conversation_logger,
        )

    def _initialize_session_state(self) -> None:
        """Initialize Streamlit session state with default values."""
        from src.utils.constants import (
            AUTO_ADVANCE_DEFAULT,
            AUTO_RUN_DELAY_MAX,
            AUTO_RUN_DELAY_MIN,
            DEFAULT_CONTEXT_MESSAGES,
            DEFAULT_HISTORY_MESSAGES,
            DEFAULT_PERSONA_COLOR,
            DEFAULT_RESPONSE_TIMEOUT,
            ENABLE_THINKING,
        )

        # Initialize session state if not already done
        if "personas" not in st.session_state:
            st.session_state.personas = []
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "is_running" not in st.session_state:
            st.session_state.is_running = False
        if "available_models" not in st.session_state:
            st.session_state.available_models = []
        if "last_speaker_index" not in st.session_state:
            st.session_state.last_speaker_index = None
        if "settings" not in st.session_state:
            st.session_state.settings = {
                "max_history": DEFAULT_HISTORY_MESSAGES,
                "response_delay_min": AUTO_RUN_DELAY_MIN,
                "response_delay_max": AUTO_RUN_DELAY_MAX,
                "auto_advance": AUTO_ADVANCE_DEFAULT,
                "context_messages": DEFAULT_CONTEXT_MESSAGES,
                "enable_thinking": ENABLE_THINKING,
                "response_timeout": DEFAULT_RESPONSE_TIMEOUT,
            }
        if "auto_run_count" not in st.session_state:
            st.session_state.auto_run_count = 0
        if "total_message_count" not in st.session_state:
            st.session_state.total_message_count = 0
        if "non_thinking_models" not in st.session_state:
            st.session_state.non_thinking_models = set()
        if "pending_manual_turn" not in st.session_state:
            st.session_state.pending_manual_turn = False

    def sync_with_session_state(self) -> None:
        """Synchronize app state with Streamlit session state.

        This method ensures that the application state is properly
        synchronized with Streamlit's session state after any changes.
        """
        # Sync personas
        self.session_manager._personas = st.session_state.personas

        # Sync messages
        self.session_manager._messages = st.session_state.messages

        # Sync conversation state
        self.session_manager._is_running = st.session_state.is_running
        self.session_manager._last_speaker_index = st.session_state.last_speaker_index
        self.session_manager._auto_run_count = st.session_state.auto_run_count
        self.session_manager._total_message_count = st.session_state.total_message_count
        self.session_manager._pending_manual_turn = st.session_state.pending_manual_turn

        # Sync settings
        self.session_manager._settings = st.session_state.settings

        # Sync models
        self.session_manager._available_models = st.session_state.available_models
        self.session_manager._non_thinking_models = st.session_state.non_thinking_models

    def sync_to_session_state(self) -> None:
        """Synchronize from app state to Streamlit session state.

        This method updates Streamlit's session state with any
        changes made through the application state.
        """
        st.session_state.personas = self.session_manager._personas
        st.session_state.messages = self.session_manager._messages
        st.session_state.is_running = self.session_manager._is_running
        st.session_state.last_speaker_index = self.session_manager._last_speaker_index
        st.session_state.auto_run_count = self.session_manager._auto_run_count
        st.session_state.total_message_count = self.session_manager._total_message_count
        st.session_state.pending_manual_turn = self.session_manager._pending_manual_turn
        st.session_state.settings = self.session_manager._settings
        st.session_state.available_models = self.session_manager._available_models
        st.session_state.non_thinking_models = self.session_manager._non_thinking_models

    def get_session_manager(self) -> SecureSessionManager:
        """Get the session manager instance.

        Returns:
            SecureSessionManager instance
        """
        return self.session_manager

    def get_conversation_orchestrator(self) -> ConversationOrchestrator:
        """Get the conversation orchestrator instance.

        Returns:
            ConversationOrchestrator instance
        """
        return self.conversation_orchestrator

    def get_conversation_logger(self) -> ConversationLogger:
        """Get the conversation logger instance.

        Returns:
            ConversationLogger instance
        """
        return self.conversation_logger

    def initialize_from_session_state(self) -> None:
        """Initialize app state from existing Streamlit session state."""
        # This is called after _initialize_session_state to ensure
        # we're not overwriting existing session state

        # Copy existing session state to app state
        self.sync_with_session_state()

    def add_persona(self, persona) -> None:
        """Add a persona and update session state.

        Args:
            persona: Persona to add
        """
        self.session_manager.add_persona(persona)
        self.sync_to_session_state()

    def remove_persona(self, persona_id: str) -> bool:
        """Remove a persona and update session state.

        Args:
            persona_id: ID of persona to remove

        Returns:
            True if persona was removed
        """
        result = self.session_manager.remove_persona(persona_id)
        self.sync_to_session_state()
        return result

    def update_persona(self, persona_id: str, **kwargs) -> bool:
        """Update a persona and sync session state.

        Args:
            persona_id: ID of persona to update
            **kwargs: Attributes to update

        Returns:
            True if persona was updated
        """
        result = self.session_manager.update_persona(persona_id, **kwargs)
        self.sync_to_session_state()
        return result

    def start_conversation(self) -> None:
        """Start conversation and update session state."""
        self.session_manager.start_conversation()
        self.sync_to_session_state()

    def stop_conversation(self) -> None:
        """Stop conversation and update session state."""
        self.session_manager.stop_conversation()
        self.sync_to_session_state()

    def clear_messages(self) -> None:
        """Clear messages and update session state."""
        self.session_manager.clear_messages()
        self.sync_to_session_state()

    def add_message(self, message: Dict[str, Any]) -> None:
        """Add a message and update session state.

        Args:
            message: Message to add
        """
        self.session_manager.add_message(message)
        self.sync_to_session_state()

    def update_settings(self, **kwargs) -> None:
        """Update settings and sync to session state.

        Args:
            **kwargs: Settings to update
        """
        self.session_manager.update_settings(**kwargs)
        self.sync_to_session_state()

    def set_available_models(self, models: list) -> None:
        """Set available models and update session state.

        Args:
            models: List of available model names
        """
        self.session_manager.set_available_models(models)
        self.sync_to_session_state()

    def set_pending_manual_turn(self, pending: bool) -> None:
        """Set pending manual turn and update session state.

        Args:
            pending: Whether manual turn is pending
        """
        self.session_manager.set_pending_manual_turn(pending)
        self.sync_to_session_state()

    def get_app_statistics(self) -> Dict[str, Any]:
        """Get comprehensive application statistics.

        Returns:
            Dictionary of application statistics
        """
        return {
            "session_stats": self.session_manager.get_stats(),
            "conversation_stats": self.conversation_orchestrator.get_conversation_stats(),
            "streamlit_state": {
                "session_state_keys": list(st.session_state.keys()),
                "has_personas": bool(st.session_state.get("personas")),
                "has_messages": bool(st.session_state.get("messages")),
                "is_running": st.session_state.get("is_running", False),
            },
        }


# Global app state instance
_app_state: AppState | None = None


def get_app_state() -> AppState:
    """Get the global application state instance.

    Returns:
        AppState singleton instance
    """
    global _app_state
    if _app_state is None:
        _app_state = AppState()
        _app_state.initialize_from_session_state()
    return _app_state


def reset_app_state() -> None:
    """Reset the global application state instance."""
    global _app_state
    _app_state = None