"""AI Persona data model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AIPersona:
    """Represents an AI instance with detailed configuration.

    Attributes:
        id: Unique identifier for the persona
        name: Display name of the persona
        model: Ollama model to use (e.g., "llama2:latest")
        role: Optional role for personality/behavior (e.g., "Philosopher", "Scientist")
        system_prompt: Custom system prompt instructions
        color: Color for UI display (hex format)
        enabled: Whether this persona is active in conversations
    """

    id: str
    name: str
    model: str
    role: str = ""
    system_prompt: str = ""
    color: str = "#1f77b4"
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate persona attributes after initialization."""
        if not self.name:
            raise ValueError("Persona name cannot be empty")
        if not self.model:
            raise ValueError("Persona model cannot be empty")
        if not self.id:
            raise ValueError("Persona id cannot be empty")
