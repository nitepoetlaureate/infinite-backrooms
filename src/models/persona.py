"""AI Persona data model."""

from __future__ import annotations

from dataclasses import dataclass

from src.utils.validation import (
    validate_persona_name,
    validate_model_name,
    validate_system_prompt,
    validate_role,
    validate_color,
)


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

    Security:
        - All attributes validated in __post_init__
        - Prevents injection attacks via input validation
    """

    id: str
    name: str
    model: str
    role: str = ""
    system_prompt: str = ""
    color: str = "#1f77b4"
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate persona attributes after initialization.

        Raises:
            ValueError: If any attribute fails validation

        Security:
            - Validates all inputs to prevent injection attacks
            - Ensures data integrity
        """
        if not self.id:
            raise ValueError("Persona id cannot be empty")

        # Validate name
        is_valid, error = validate_persona_name(self.name)
        if not is_valid:
            raise ValueError(f"Invalid persona name: {error}")

        # Validate model
        is_valid, error = validate_model_name(self.model)
        if not is_valid:
            raise ValueError(f"Invalid model name: {error}")

        # Validate role
        is_valid, error = validate_role(self.role)
        if not is_valid:
            raise ValueError(f"Invalid role: {error}")

        # Validate system prompt
        is_valid, error = validate_system_prompt(self.system_prompt)
        if not is_valid:
            raise ValueError(f"Invalid system prompt: {error}")

        # Validate color
        is_valid, error = validate_color(self.color)
        if not is_valid:
            raise ValueError(f"Invalid color: {error}")
