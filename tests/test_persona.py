"""Tests for AIPersona dataclass."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from streamlit_backroom import AIPersona


class TestAIPersona:
    """Test AIPersona dataclass."""

    def test_persona_creation(self, sample_persona_data):
        """Test creating a persona with valid data."""
        persona = AIPersona(**sample_persona_data)

        assert persona.id == sample_persona_data["id"]
        assert persona.name == sample_persona_data["name"]
        assert persona.model == sample_persona_data["model"]
        assert persona.role == sample_persona_data["role"]
        assert persona.enabled is True

    def test_persona_defaults(self):
        """Test persona with default values."""
        persona = AIPersona(id="test", name="Test", model="test-model")

        assert persona.role == ""
        assert persona.system_prompt == ""
        assert persona.color == "#1f77b4"
        assert persona.enabled is True

    def test_persona_custom_role(self):
        """Test persona with custom role."""
        persona = AIPersona(
            id="test",
            name="Test",
            model="test-model",
            role="CustomRole",
            enabled=False,
        )

        assert persona.role == "CustomRole"
        assert persona.enabled is False
