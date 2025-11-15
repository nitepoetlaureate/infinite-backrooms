"""Secure Session Manager for managing application state.

Handles secure state management with proper validation and cleanup.
Ensures thread-safe operations and maintains conversation integrity.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from src.models.persona import AIPersona
from src.utils.validation import validate_model_name


class SecureSessionManager:
    """Manages secure session state for the AI Backroom application.

    Provides thread-safe state management with proper validation,
    cleanup, and security measures for conversation data.

    Attributes:
        personas: List of AI personas in the session
        messages: Conversation history
        is_running: Whether conversation is auto-running
        available_models: List of available Ollama models
        last_speaker_index: Index of last speaker for rotation
        settings: Application settings
        auto_run_count: Count of auto-run turns
        total_message_count: Total messages in session
        non_thinking_models: Set of models that don't support thinking
        pending_manual_turn: Flag for pending manual turns
    """

    def __init__(self) -> None:
        """Initialize a new secure session manager."""
        self._personas: List[AIPersona] = []
        self._messages: List[Dict[str, Any]] = []
        self._is_running: bool = False
        self._available_models: List[str] = []
        self._last_speaker_index: Optional[int] = None
        self._settings: Dict[str, Any] = self._get_default_settings()
        self._auto_run_count: int = 0
        self._total_message_count: int = 0
        self._non_thinking_models: Set[str] = set()
        self._pending_manual_turn: bool = False
        self._session_id: str = str(uuid.uuid4())
        self._created_at: datetime = datetime.now()

    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default application settings.

        Returns:
            Default settings dictionary
        """
        from src.utils.constants import (
            AUTO_ADVANCE_DEFAULT,
            AUTO_RUN_DELAY_MAX,
            AUTO_RUN_DELAY_MIN,
            DEFAULT_CONTEXT_MESSAGES,
            DEFAULT_HISTORY_MESSAGES,
            DEFAULT_RESPONSE_TIMEOUT,
            ENABLE_THINKING,
        )

        return {
            "max_history": DEFAULT_HISTORY_MESSAGES,
            "response_delay_min": AUTO_RUN_DELAY_MIN,
            "response_delay_max": AUTO_RUN_DELAY_MAX,
            "auto_advance": AUTO_ADVANCE_DEFAULT,
            "context_messages": DEFAULT_CONTEXT_MESSAGES,
            "enable_thinking": ENABLE_THINKING,
            "response_timeout": DEFAULT_RESPONSE_TIMEOUT,
        }

    def get_session_id(self) -> str:
        """Get the unique session identifier.

        Returns:
            Session UUID
        """
        return self._session_id

    def get_session_age(self) -> float:
        """Get session age in seconds.

        Returns:
            Age of session in seconds
        """
        return (datetime.now() - self._created_at).total_seconds()

    # Persona management
    def add_persona(self, persona: AIPersona) -> None:
        """Add a persona to the session.

        Args:
            persona: Persona to add
        """
        self._personas.append(persona)

    def remove_persona(self, persona_id: str) -> bool:
        """Remove a persona by ID.

        Args:
            persona_id: ID of persona to remove

        Returns:
            True if persona was removed, False if not found
        """
        original_count = len(self._personas)
        self._personas = [p for p in self._personas if p.id != persona_id]
        return len(self._personas) < original_count

    def get_personas(self) -> List[AIPersona]:
        """Get all personas.

        Returns:
            List of personas
        """
        return self._personas.copy()

    def get_enabled_personas(self) -> List[AIPersona]:
        """Get only enabled personas.

        Returns:
            List of enabled personas
        """
        return [p for p in self._personas if p.enabled]

    def find_persona_by_name(self, name: str) -> Optional[AIPersona]:
        """Find a persona by name.

        Args:
            name: Persona name to find

        Returns:
            Persona if found, None otherwise
        """
        for persona in self._personas:
            if persona.name == name:
                return persona
        return None

    def update_persona(self, persona_id: str, **kwargs) -> bool:
        """Update persona attributes.

        Args:
            persona_id: ID of persona to update
            **kwargs: Attributes to update

        Returns:
            True if updated, False if not found
        """
        for persona in self._personas:
            if persona.id == persona_id:
                for key, value in kwargs.items():
                    if hasattr(persona, key):
                        setattr(persona, key, value)
                return True
        return False

    # Message management
    def add_message(self, message: Dict[str, Any]) -> None:
        """Add a message to conversation history.

        Args:
            message: Message dictionary to add
        """
        # Validate message structure
        required_fields = ["role", "content", "timestamp"]
        for field in required_fields:
            if field not in message:
                raise ValueError(f"Message missing required field: {field}")

        self._messages.append(message)
        self._total_message_count += 1

        # Enforce history limit
        max_history = self._settings.get("max_history", 100)
        if len(self._messages) > max_history:
            self._messages = self._messages[-max_history:]

    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation messages.

        Args:
            limit: Optional limit on number of messages

        Returns:
            List of messages
        """
        if limit:
            return self._messages[-limit:]
        return self._messages.copy()

    def get_context_messages(self) -> List[Dict[str, Any]]:
        """Get messages for AI context based on settings.

        Returns:
            List of context messages
        """
        context_limit = min(
            self._settings.get("context_messages", 20),
            len(self._messages)
        )
        return self._messages[-context_limit:]

    def clear_messages(self) -> None:
        """Clear all messages from conversation history."""
        self._messages.clear()
        self._total_message_count = 0
        self._last_speaker_index = None

    # Model management
    def set_available_models(self, models: List[str]) -> None:
        """Set the list of available models.

        Args:
            models: List of available model names
        """
        self._available_models = []
        for model in models:
            is_valid, _ = validate_model_name(model)
            if is_valid:
                self._available_models.append(model)

    def get_available_models(self) -> List[str]:
        """Get available models.

        Returns:
            List of available model names
        """
        return self._available_models.copy()

    def add_non_thinking_model(self, model: str) -> None:
        """Add a model to the non-thinking set.

        Args:
            model: Model name that doesn't support thinking
        """
        self._non_thinking_models.add(model)

    def is_non_thinking_model(self, model: str) -> bool:
        """Check if a model supports thinking.

        Args:
            model: Model name to check

        Returns:
            True if model doesn't support thinking
        """
        return model in self._non_thinking_models

    def clear_model_cache(self) -> None:
        """Clear the model compatibility cache."""
        self._non_thinking_models.clear()

    # Settings management
    def update_settings(self, **kwargs) -> None:
        """Update application settings.

        Args:
            **kwargs: Settings to update
        """
        self._settings.update(kwargs)

    def get_settings(self) -> Dict[str, Any]:
        """Get current settings.

        Returns:
            Settings dictionary
        """
        return self._settings.copy()

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value.

        Args:
            key: Setting key
            default: Default value if not found

        Returns:
            Setting value
        """
        return self._settings.get(key, default)

    # Conversation state management
    def start_conversation(self) -> None:
        """Start the conversation auto-runner."""
        self._is_running = True
        self._auto_run_count = 0

    def stop_conversation(self) -> None:
        """Stop the conversation auto-runner."""
        self._is_running = False

    def is_conversation_running(self) -> bool:
        """Check if conversation is running.

        Returns:
            True if conversation is auto-running
        """
        return self._is_running

    def increment_auto_run_count(self) -> int:
        """Increment the auto-run counter.

        Returns:
            New auto-run count
        """
        self._auto_run_count += 1
        return self._auto_run_count

    def get_auto_run_count(self) -> int:
        """Get current auto-run count.

        Returns:
            Auto-run count
        """
        return self._auto_run_count

    # Speaker rotation
    def get_next_speaker(self) -> Optional[AIPersona]:
        """Get the next speaker in rotation.

        Returns:
            Next persona or None if no enabled personas
        """
        enabled_personas = self.get_enabled_personas()
        if not enabled_personas:
            return None

        if self._last_speaker_index is None:
            self._last_speaker_index = 0
        else:
            self._last_speaker_index = (
                self._last_speaker_index + 1
            ) % len(enabled_personas)

        return enabled_personas[self._last_speaker_index]

    def reset_speaker_rotation(self) -> None:
        """Reset the speaker rotation to start from first enabled persona."""
        self._last_speaker_index = None

    # Manual turn management
    def set_pending_manual_turn(self, pending: bool) -> None:
        """Set pending manual turn flag.

        Args:
            pending: Whether a manual turn is pending
        """
        self._pending_manual_turn = pending

    def is_pending_manual_turn(self) -> bool:
        """Check if manual turn is pending.

        Returns:
            True if manual turn is pending
        """
        return self._pending_manual_turn

    # Session statistics
    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics.

        Returns:
            Dictionary of session statistics
        """
        enabled_personas = self.get_enabled_personas()

        return {
            "session_id": self._session_id,
            "session_age_seconds": self.get_session_age(),
            "total_personas": len(self._personas),
            "enabled_personas": len(enabled_personas),
            "total_messages": self._total_message_count,
            "displayed_messages": len(self._messages),
            "auto_run_count": self._auto_run_count,
            "is_running": self._is_running,
            "available_models": len(self._available_models),
            "non_thinking_models": len(self._non_thinking_models),
        }

    # Session cleanup
    def cleanup(self) -> None:
        """Clean up session resources and reset state."""
        self._personas.clear()
        self._messages.clear()
        self._available_models.clear()
        self._non_thinking_models.clear()
        self._is_running = False
        self._auto_run_count = 0
        self._total_message_count = 0
        self._last_speaker_index = None
        self._pending_manual_turn = False
        self._settings = self._get_default_settings()