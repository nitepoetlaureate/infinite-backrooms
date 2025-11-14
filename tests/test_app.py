"""Tests for main application module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.app import StreamlitBackroomApp, run_async
from src.models.persona import AIPersona
from tests.conftest import MockSessionState


class TestRunAsync:
    """Test run_async utility function."""

    def test_run_async_successful_execution(self):
        """Test successful execution of async function."""

        async def sample_coro():
            return "success"

        result = run_async(sample_coro())
        assert result == "success"

    def test_run_async_with_return_value(self):
        """Test async function with return value."""

        async def add_numbers(a, b):
            await asyncio.sleep(0.001)  # Simulate async work
            return a + b

        result = run_async(add_numbers(5, 3))
        assert result == 8

    def test_run_async_with_exception(self):
        """Test async function that raises exception."""

        async def failing_coro():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            run_async(failing_coro())

    @patch("src.app.asyncio.run")
    def test_run_async_fallback_on_runtime_error(self, mock_asyncio_run):
        """Test fallback to new event loop when asyncio.run fails."""
        # Simulate asyncio.run() failing with RuntimeError
        mock_asyncio_run.side_effect = RuntimeError("Event loop is closed")

        async def sample_coro():
            return "fallback_success"

        with patch("src.app.asyncio.new_event_loop") as mock_new_loop:
            with patch("src.app.asyncio.set_event_loop") as mock_set_loop:
                mock_loop = Mock()
                mock_loop.run_until_complete = Mock(return_value="fallback_success")
                mock_loop.close = Mock()
                mock_new_loop.return_value = mock_loop

                result = run_async(sample_coro())

                # Verify fallback was used
                mock_new_loop.assert_called_once()
                mock_set_loop.assert_called_once_with(mock_loop)
                mock_loop.run_until_complete.assert_called_once()
                assert result == "fallback_success"

    def test_run_async_with_complex_return_type(self):
        """Test async function with complex return type."""

        async def get_dict():
            return {"key": "value", "number": 42, "list": [1, 2, 3]}

        result = run_async(get_dict())
        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["number"] == 42
        assert result["list"] == [1, 2, 3]


class TestStreamlitBackroomAppInit:
    """Test StreamlitBackroomApp initialization."""

    @patch("src.app.st")
    def test_app_initialization(self, mock_st):
        """Test basic app initialization."""
        # Setup mock session_state
        mock_st.session_state = MockSessionState()

        app = StreamlitBackroomApp()

        # Verify services are initialized
        assert app.logger is not None
        assert app.ollama is not None

    @patch("src.app.st")
    def test_initialize_session_state_creates_all_keys(self, mock_st):
        """Test that session state initialization creates all required keys."""
        mock_st.session_state = MockSessionState()

        app = StreamlitBackroomApp()
        app.initialize_session_state()

        # Check all required keys are present
        assert "personas" in mock_st.session_state
        assert "messages" in mock_st.session_state
        assert "is_running" in mock_st.session_state
        assert "available_models" in mock_st.session_state
        assert "last_speaker_index" in mock_st.session_state
        assert "settings" in mock_st.session_state
        assert "auto_run_count" in mock_st.session_state
        assert "total_message_count" in mock_st.session_state
        assert "non_thinking_models" in mock_st.session_state
        assert "pending_manual_turn" in mock_st.session_state

    @patch("src.app.st")
    def test_initialize_session_state_default_values(self, mock_st):
        """Test that session state has correct default values."""
        mock_st.session_state = MockSessionState()

        app = StreamlitBackroomApp()
        app.initialize_session_state()

        # Check default values
        assert mock_st.session_state["personas"] == []
        assert mock_st.session_state["messages"] == []
        assert mock_st.session_state["is_running"] is False
        assert mock_st.session_state["last_speaker_index"] is None
        assert mock_st.session_state["auto_run_count"] == 0
        assert mock_st.session_state["total_message_count"] == 0

    @patch("src.app.st")
    def test_initialize_session_state_preserves_existing(self, mock_st):
        """Test that existing session state values are not overwritten."""
        mock_st.session_state = MockSessionState({
            "personas": ["existing"],
            "messages": ["existing"],
            "custom_key": "custom_value",
        })

        app = StreamlitBackroomApp()
        app.initialize_session_state()

        # Existing values should not be overwritten
        assert mock_st.session_state["personas"] == ["existing"]
        assert mock_st.session_state["messages"] == ["existing"]
        assert mock_st.session_state["custom_key"] == "custom_value"


class TestGetNextSpeaker:
    """Test get_next_speaker method."""

    @patch("src.app.st")
    def test_get_next_speaker_with_enabled_personas(self, mock_st):
        """Test getting next speaker with enabled personas."""
        personas = [
            AIPersona(
                id="1",
                name="Alice",
                model="llama2:latest",
                role="creative",
                system_prompt="",
                color="#FF5733",
                enabled=True,
            ),
            AIPersona(
                id="2",
                name="Bob",
                model="mistral:latest",
                role="analyst",
                system_prompt="",
                color="#33C3FF",
                enabled=True,
            ),
        ]

        mock_st.session_state = MockSessionState({
            "personas": personas,
            "last_speaker_index": None,
        })

        app = StreamlitBackroomApp()
        app.initialize_session_state()
        mock_st.session_state["personas"] = personas

        # First call should return first persona
        speaker = app.get_next_speaker()
        assert speaker.name == "Alice"
        assert mock_st.session_state["last_speaker_index"] == 0

        # Second call should return second persona
        speaker = app.get_next_speaker()
        assert speaker.name == "Bob"
        assert mock_st.session_state["last_speaker_index"] == 1

        # Third call should wrap around to first persona
        speaker = app.get_next_speaker()
        assert speaker.name == "Alice"
        assert mock_st.session_state["last_speaker_index"] == 0

    @patch("src.app.st")
    def test_get_next_speaker_skips_disabled_personas(self, mock_st):
        """Test that disabled personas are skipped."""
        personas = [
            AIPersona(
                id="1",
                name="Alice",
                model="llama2:latest",
                role="creative",
                system_prompt="",
                color="#FF5733",
                enabled=True,
            ),
            AIPersona(
                id="2",
                name="Bob",
                model="mistral:latest",
                role="analyst",
                system_prompt="",
                color="#33C3FF",
                enabled=False,  # Disabled
            ),
            AIPersona(
                id="3",
                name="Charlie",
                model="llama2:latest",
                role="moderator",
                system_prompt="",
                color="#33FF57",
                enabled=True,
            ),
        ]

        mock_st.session_state = MockSessionState({
            "personas": personas,
            "last_speaker_index": None,
        })

        app = StreamlitBackroomApp()
        app.initialize_session_state()
        mock_st.session_state["personas"] = personas

        # Should get Alice, then Charlie (skipping disabled Bob)
        speaker1 = app.get_next_speaker()
        assert speaker1.name == "Alice"

        speaker2 = app.get_next_speaker()
        assert speaker2.name == "Charlie"

        # Should wrap back to Alice
        speaker3 = app.get_next_speaker()
        assert speaker3.name == "Alice"

    @patch("src.app.st")
    def test_get_next_speaker_no_enabled_personas(self, mock_st):
        """Test behavior when no personas are enabled."""
        personas = [
            AIPersona(
                id="1",
                name="Alice",
                model="llama2:latest",
                role="creative",
                system_prompt="",
                color="#FF5733",
                enabled=False,
            ),
        ]

        mock_st.session_state = MockSessionState({
            "personas": personas,
            "last_speaker_index": None,
        })

        app = StreamlitBackroomApp()
        app.initialize_session_state()
        mock_st.session_state["personas"] = personas

        speaker = app.get_next_speaker()
        assert speaker is None

    @patch("src.app.st")
    def test_get_next_speaker_empty_personas_list(self, mock_st):
        """Test behavior with empty personas list."""
        mock_st.session_state = MockSessionState({
            "personas": [],
            "last_speaker_index": None,
        })

        app = StreamlitBackroomApp()
        app.initialize_session_state()
        mock_st.session_state["personas"] = []

        speaker = app.get_next_speaker()
        assert speaker is None


class TestGenerateSystemPrompt:
    """Test generate_system_prompt method."""

    @patch("src.app.st")
    def test_generate_system_prompt_basic(self, mock_st):
        """Test basic system prompt generation."""
        persona = AIPersona(
            id="1",
            name="Alice",
            model="llama2:latest",
            role="creative",
            system_prompt="",
            color="#FF5733",
            enabled=True,
        )

        other_persona = AIPersona(
            id="2",
            name="Bob",
            model="mistral:latest",
            role="analyst",
            system_prompt="",
            color="#33C3FF",
            enabled=True,
        )

        mock_st.session_state = MockSessionState({
            "personas": [persona, other_persona],
        })

        app = StreamlitBackroomApp()
        prompt = app.generate_system_prompt(persona)

        # Check that prompt contains persona name
        assert "Alice" in prompt
        # Check that prompt mentions the other persona
        assert "Bob" in prompt
        # Check that it mentions conversation
        assert "conversation" in prompt.lower()

    @patch("src.app.st")
    def test_generate_system_prompt_with_role(self, mock_st):
        """Test system prompt generation with role."""
        persona = AIPersona(
            id="1",
            name="Alice",
            model="llama2:latest",
            role="Moderator",
            system_prompt="",
            color="#FF5733",
            enabled=True,
        )

        mock_st.session_state = MockSessionState({
            "personas": [persona],
        })

        app = StreamlitBackroomApp()
        prompt = app.generate_system_prompt(persona)

        # Check that prompt includes role-specific instructions
        assert "Moderator" in prompt or "moderator" in prompt.lower()
        assert "questions" in prompt.lower()

    @patch("src.app.st")
    def test_generate_system_prompt_with_custom_prompt(self, mock_st):
        """Test system prompt includes custom prompt."""
        persona = AIPersona(
            id="1",
            name="Alice",
            model="llama2:latest",
            role="creative",
            system_prompt="Always be cheerful and optimistic!",
            color="#FF5733",
            enabled=True,
        )

        mock_st.session_state = MockSessionState({
            "personas": [persona],
        })

        app = StreamlitBackroomApp()
        prompt = app.generate_system_prompt(persona)

        # Check that custom prompt is included
        assert "Always be cheerful and optimistic!" in prompt

    @patch("src.app.st")
    def test_generate_system_prompt_mentions_feature(self, mock_st):
        """Test that system prompt mentions @mention feature."""
        persona = AIPersona(
            id="1",
            name="Alice",
            model="llama2:latest",
            role="creative",
            system_prompt="",
            color="#FF5733",
            enabled=True,
        )

        other = AIPersona(
            id="2",
            name="Bob",
            model="mistral:latest",
            role="analyst",
            system_prompt="",
            color="#33C3FF",
            enabled=True,
        )

        mock_st.session_state = MockSessionState({
            "personas": [persona, other],
        })

        app = StreamlitBackroomApp()
        prompt = app.generate_system_prompt(persona)

        # Check that @mention feature is explained
        assert "@" in prompt
        assert "Mention" in prompt or "mention" in prompt

    @patch("src.app.st")
    def test_generate_system_prompt_note_taker_role(self, mock_st):
        """Test system prompt for Note-Taker role includes specific instructions."""
        persona = AIPersona(
            id="1",
            name="Scribe",
            model="llama2:latest",
            role="Note-Taker",
            system_prompt="",
            color="#FF5733",
            enabled=True,
        )

        mock_st.session_state = MockSessionState({
            "personas": [persona],
        })

        app = StreamlitBackroomApp()
        prompt = app.generate_system_prompt(persona)

        # Check for Note-Taker specific instructions
        assert "Note-Taker" in prompt or "summarizing" in prompt.lower()

    @patch("src.app.st")
    def test_generate_system_prompt_single_persona(self, mock_st):
        """Test system prompt when only one persona exists."""
        persona = AIPersona(
            id="1",
            name="Alice",
            model="llama2:latest",
            role="creative",
            system_prompt="",
            color="#FF5733",
            enabled=True,
        )

        mock_st.session_state = MockSessionState({
            "personas": [persona],
        })

        app = StreamlitBackroomApp()
        prompt = app.generate_system_prompt(persona)

        # Should still generate valid prompt
        assert "Alice" in prompt
        # Should mention 0 other AIs
        assert "0" in prompt

    @patch("src.app.st")
    def test_generate_system_prompt_excludes_disabled_personas(self, mock_st):
        """Test that disabled personas are not mentioned in system prompt."""
        persona = AIPersona(
            id="1",
            name="Alice",
            model="llama2:latest",
            role="creative",
            system_prompt="",
            color="#FF5733",
            enabled=True,
        )

        disabled = AIPersona(
            id="2",
            name="Disabled",
            model="mistral:latest",
            role="analyst",
            system_prompt="",
            color="#33C3FF",
            enabled=False,
        )

        enabled = AIPersona(
            id="3",
            name="Bob",
            model="llama2:latest",
            role="analyst",
            system_prompt="",
            color="#33FF57",
            enabled=True,
        )

        mock_st.session_state = MockSessionState({
            "personas": [persona, disabled, enabled],
        })

        app = StreamlitBackroomApp()
        prompt = app.generate_system_prompt(persona)

        # Should mention Bob but not Disabled
        assert "Bob" in prompt
        assert "Disabled" not in prompt


class TestCheckOllamaConnection:
    """Test check_ollama_connection method."""

    @pytest.mark.asyncio
    @patch("src.app.st")
    @patch("src.app.OllamaClient")
    async def test_check_ollama_connection_success(self, mock_ollama_class, mock_st):
        """Test successful Ollama connection."""
        mock_st.session_state = MockSessionState()

        # Mock the OllamaClient context manager
        mock_client = AsyncMock()
        mock_client.test_connection = AsyncMock(
            return_value=(True, ["llama2:latest", "mistral:latest"])
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_ollama_class.return_value = mock_client

        app = StreamlitBackroomApp()
        connected = await app.check_ollama_connection()

        assert connected is True
        assert mock_st.session_state["available_models"] == ["llama2:latest", "mistral:latest"]

    @pytest.mark.asyncio
    @patch("src.app.st")
    @patch("src.app.OllamaClient")
    async def test_check_ollama_connection_failure(self, mock_ollama_class, mock_st):
        """Test failed Ollama connection."""
        mock_st.session_state = MockSessionState()

        # Mock the OllamaClient context manager
        mock_client = AsyncMock()
        mock_client.test_connection = AsyncMock(return_value=(False, []))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_ollama_class.return_value = mock_client

        app = StreamlitBackroomApp()
        connected = await app.check_ollama_connection()

        assert connected is False
        assert mock_st.session_state["available_models"] == []
