"""Tests for AIPersona dataclass."""

import pytest

from src.models.persona import AIPersona


class TestAIPersona:
    """Test AIPersona dataclass functionality."""

    def test_persona_creation(self, sample_persona):
        """Test creating a persona with all fields."""
        assert sample_persona.id == "test-123"
        assert sample_persona.name == "TestBot"
        assert sample_persona.model == "llama2:latest"
        assert sample_persona.role == "analyst"
        assert sample_persona.system_prompt == "You are a test analyst."
        assert sample_persona.color == "#FF5733"
        assert sample_persona.enabled is True

    def test_persona_minimal_creation(self):
        """Test creating a persona with minimal required fields."""
        persona = AIPersona(id="min-001", name="MinimalBot", model="llama2:latest")
        assert persona.id == "min-001"
        assert persona.name == "MinimalBot"
        assert persona.model == "llama2:latest"
        assert persona.role == ""
        assert persona.system_prompt == ""
        assert persona.enabled is True

    def test_persona_equality(self):
        """Test persona equality comparison."""
        p1 = AIPersona(
            id="test-1", name="Bot", model="llama2:latest", role="analyst", system_prompt="Prompt"
        )
        p2 = AIPersona(
            id="test-1", name="Bot", model="llama2:latest", role="analyst", system_prompt="Prompt"
        )
        p3 = AIPersona(
            id="test-2", name="Bot2", model="llama2:latest", role="analyst", system_prompt="Prompt"
        )

        assert p1 == p2
        assert p1 != p3

    def test_persona_disabled(self):
        """Test creating a disabled persona."""
        persona = AIPersona(
            id="disabled-001", name="DisabledBot", model="llama2:latest", enabled=False
        )
        assert persona.enabled is False

    def test_persona_with_custom_color(self):
        """Test persona with custom color."""
        persona = AIPersona(
            id="colored-001", name="ColorBot", model="llama2:latest", color="#AABBCC"
        )
        assert persona.color == "#AABBCC"

    def test_persona_with_long_system_prompt(self):
        """Test persona with a long system prompt."""
        long_prompt = "You are a highly specialized AI " * 50
        persona = AIPersona(
            id="long-001", name="LongPromptBot", model="llama2:latest", system_prompt=long_prompt
        )
        assert len(persona.system_prompt) > 100
        assert persona.system_prompt == long_prompt

    def test_persona_with_special_characters_in_name(self):
        """Test persona name can contain special characters."""
        persona = AIPersona(id="special-001", name="Bot-2000_v1", model="llama2:latest")
        assert persona.name == "Bot-2000_v1"

    def test_multiple_personas_different_ids(self, sample_personas):
        """Test multiple personas have unique IDs."""
        ids = [p.id for p in sample_personas]
        assert len(ids) == len(set(ids))  # All IDs should be unique

    def test_persona_fields_are_mutable(self, sample_persona):
        """Test that persona fields can be modified."""
        sample_persona.name = "NewName"
        sample_persona.enabled = False
        sample_persona.color = "#000000"

        assert sample_persona.name == "NewName"
        assert sample_persona.enabled is False
        assert sample_persona.color == "#000000"

    def test_persona_empty_name_raises_error(self) -> None:
        """Test that creating persona with empty name raises ValueError."""
        with pytest.raises(ValueError, match="Persona name cannot be empty"):
            AIPersona(id="test-id", name="", model="llama2")

    def test_persona_empty_model_raises_error(self) -> None:
        """Test that creating persona with empty model raises ValueError."""
        with pytest.raises(ValueError, match="Persona model cannot be empty"):
            AIPersona(id="test-id", name="TestBot", model="")

    def test_persona_empty_id_raises_error(self) -> None:
        """Test that creating persona with empty id raises ValueError."""
        with pytest.raises(ValueError, match="Persona id cannot be empty"):
            AIPersona(id="", name="TestBot", model="llama2")
