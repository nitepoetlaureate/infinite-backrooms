"""Tests for error message templates and constants."""

from __future__ import annotations

from src.utils.constants import ERROR_MESSAGES, PRESET_DIVERSE_PERSONAS, PRESET_STRUCTURED_PERSONAS, ROLE_TEMPLATES


class TestErrorMessages:
    """Tests for error message templates."""

    def test_error_messages_exist(self) -> None:
        """Test that all expected error messages are defined."""
        required_keys = [
            "ollama_connection_failed",
            "model_not_found",
            "timeout_error",
            "generation_error",
        ]

        for key in required_keys:
            assert key in ERROR_MESSAGES, f"Missing error message: {key}"
            assert isinstance(ERROR_MESSAGES[key], str)
            assert len(ERROR_MESSAGES[key]) > 0

    def test_ollama_connection_failed_message(self) -> None:
        """Test ollama connection failed message formatting."""
        message = ERROR_MESSAGES["ollama_connection_failed"]

        assert "Cannot connect to Ollama" in message
        assert "{url}" in message
        assert "ollama serve" in message

    def test_model_not_found_message(self) -> None:
        """Test model not found message formatting."""
        message = ERROR_MESSAGES["model_not_found"]

        assert "Model not found" in message
        assert "{model}" in message
        assert "ollama pull" in message

    def test_timeout_error_message(self) -> None:
        """Test timeout error message formatting."""
        message = ERROR_MESSAGES["timeout_error"]

        assert "timed out" in message.lower()
        assert "{timeout}" in message

    def test_generation_error_message(self) -> None:
        """Test generation error message formatting."""
        message = ERROR_MESSAGES["generation_error"]

        assert "Error generating response" in message
        assert "{error}" in message or "{model}" in message


class TestPresetPersonas:
    """Tests for preset persona configurations."""

    def test_diverse_personas_exist(self) -> None:
        """Test that diverse persona presets are defined."""
        assert isinstance(PRESET_DIVERSE_PERSONAS, list)
        assert len(PRESET_DIVERSE_PERSONAS) > 0

    def test_diverse_personas_structure(self) -> None:
        """Test structure of diverse persona presets."""
        for persona in PRESET_DIVERSE_PERSONAS:
            assert "name" in persona
            assert "role" in persona
            assert "model" in persona
            assert "system_prompt" in persona
            assert isinstance(persona["name"], str)
            assert len(persona["name"]) > 0

    def test_structured_personas_exist(self) -> None:
        """Test that structured persona presets are defined."""
        assert isinstance(PRESET_STRUCTURED_PERSONAS, list)
        assert len(PRESET_STRUCTURED_PERSONAS) > 0

    def test_structured_personas_structure(self) -> None:
        """Test structure of structured persona presets."""
        for persona in PRESET_STRUCTURED_PERSONAS:
            assert "name" in persona
            assert "role" in persona
            assert "model" in persona
            assert "system_prompt" in persona
            assert isinstance(persona["name"], str)
            assert len(persona["name"]) > 0

    def test_preset_personas_have_unique_names(self) -> None:
        """Test that preset personas have unique names."""
        all_personas = PRESET_DIVERSE_PERSONAS + PRESET_STRUCTURED_PERSONAS
        names = [p["name"] for p in all_personas]
        assert len(names) == len(set(names)), "Preset personas should have unique names"


class TestRoleTemplates:
    """Tests for role template configurations."""

    def test_role_templates_exist(self) -> None:
        """Test that role templates are defined."""
        assert isinstance(ROLE_TEMPLATES, dict)
        assert len(ROLE_TEMPLATES) > 0

    def test_role_templates_have_descriptions(self) -> None:
        """Test that all role templates have descriptions."""
        for role, description in ROLE_TEMPLATES.items():
            assert isinstance(description, str), f"Role {role} description must be string"
            if role != "":  # Empty role has minimal description
                assert len(description) > 10, f"Role {role} description too short"

    def test_empty_role_exists(self) -> None:
        """Test that empty role template exists for custom personas."""
        assert "" in ROLE_TEMPLATES
        assert ROLE_TEMPLATES[""] == "No specific role"

    def test_common_roles_exist(self) -> None:
        """Test that common roles are defined."""
        common_roles = [
            "Moderator",
            "Note-Taker",
            "Philosopher",
            "Scientist",
            "Explorer",
            "Analyst",
        ]

        for role in common_roles:
            assert role in ROLE_TEMPLATES, f"Missing common role: {role}"
            assert len(ROLE_TEMPLATES[role]) > 20, f"Role {role} needs better description"

    def test_role_templates_match_preset_personas(self) -> None:
        """Test that preset personas use valid role templates."""
        all_personas = PRESET_DIVERSE_PERSONAS + PRESET_STRUCTURED_PERSONAS

        for persona in all_personas:
            role = persona["role"]
            assert role in ROLE_TEMPLATES, (
                f"Persona {persona['name']} uses undefined role: {role}"
            )


class TestConstantsConfiguration:
    """Tests for configuration constants."""

    def test_timeout_bounds(self) -> None:
        """Test that timeout bounds are reasonable."""
        from src.utils.constants import (
            DEFAULT_TIMEOUT,
            MAX_RESPONSE_TIMEOUT,
            MIN_RESPONSE_TIMEOUT,
        )

        assert MIN_RESPONSE_TIMEOUT > 0
        assert MAX_RESPONSE_TIMEOUT > MIN_RESPONSE_TIMEOUT
        assert DEFAULT_TIMEOUT >= MIN_RESPONSE_TIMEOUT
        assert DEFAULT_TIMEOUT <= MAX_RESPONSE_TIMEOUT

    def test_context_message_bounds(self) -> None:
        """Test that context message bounds are reasonable."""
        from src.utils.constants import (
            DEFAULT_CONTEXT_MESSAGES,
            MAX_CONTEXT_MESSAGES,
            MIN_CONTEXT_MESSAGES,
        )

        assert MIN_CONTEXT_MESSAGES > 0
        assert MAX_CONTEXT_MESSAGES > MIN_CONTEXT_MESSAGES
        assert DEFAULT_CONTEXT_MESSAGES >= MIN_CONTEXT_MESSAGES
        assert DEFAULT_CONTEXT_MESSAGES <= MAX_CONTEXT_MESSAGES

    def test_temperature_bounds(self) -> None:
        """Test that temperature bounds are valid."""
        from src.utils.constants import DEFAULT_TEMPERATURE, MAX_TEMPERATURE, MIN_TEMPERATURE

        assert MIN_TEMPERATURE >= 0.0
        assert MAX_TEMPERATURE >= MIN_TEMPERATURE
        assert DEFAULT_TEMPERATURE >= MIN_TEMPERATURE
        assert DEFAULT_TEMPERATURE <= MAX_TEMPERATURE

    def test_security_limits(self) -> None:
        """Test that security limits are defined."""
        from src.utils.constants import MAX_PERSONA_NAME_LENGTH, MAX_SYSTEM_PROMPT_LENGTH, REGEX_TIMEOUT

        assert MAX_PERSONA_NAME_LENGTH > 0
        assert MAX_PERSONA_NAME_LENGTH <= 1000  # Reasonable upper bound
        assert MAX_SYSTEM_PROMPT_LENGTH > 0
        assert MAX_SYSTEM_PROMPT_LENGTH >= 1000  # Must allow substantial prompts
        assert REGEX_TIMEOUT > 0
        assert REGEX_TIMEOUT <= 60  # Reasonable timeout
