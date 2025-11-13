"""Comprehensive tests for streamlit_backroom module to achieve 80%+ coverage"""

import asyncio
import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import aiohttp
import pytest

from streamlit_backroom import (
    AIPersona,
    ConversationLogger,
    OllamaClient,
    StreamlitBackroomApp,
    sanitize_html,
)


class TestSanitizeHTML:
    """Test HTML sanitization"""

    def test_sanitize_html_basic(self):
        """Test basic HTML escaping"""
        text = "<script>alert('xss')</script>"
        result = sanitize_html(text)
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_sanitize_html_ampersand(self):
        """Test ampersand escaping"""
        text = "Tom & Jerry"
        result = sanitize_html(text)
        assert "&amp;" in result

    def test_sanitize_html_quotes(self):
        """Test quote escaping"""
        text = 'Say "hello"'
        result = sanitize_html(text)
        assert "&quot;" in result

    def test_sanitize_html_no_change(self):
        """Test that safe text is unchanged"""
        text = "This is safe text"
        result = sanitize_html(text)
        assert "This is safe text" in result


class TestOllamaClient:
    """Test OllamaClient"""

    @pytest.fixture
    def ollama_client(self):
        """Create an OllamaClient instance"""
        return OllamaClient(base_url="http://localhost:11434")

    @pytest.mark.asyncio
    async def test_test_connection_success(self, ollama_client):
        """Test successful connection to Ollama"""
        mock_response = {
            "models": [
                {"name": "llama2:7b"},
                {"name": "mistral:latest"}
            ]
        }

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 200
            mock_response_obj.json = AsyncMock(return_value=mock_response)

            mock_session.get = AsyncMock(return_value=mock_response_obj)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_response_obj.__aenter__ = AsyncMock(return_value=mock_response_obj)
            mock_response_obj.__aexit__ = AsyncMock()

            mock_session_class.return_value = mock_session

            connected, models = await ollama_client.test_connection()

            assert connected is True
            assert len(models) == 2
            assert "llama2:7b" in models

    @pytest.mark.asyncio
    async def test_test_connection_failure(self, ollama_client):
        """Test failed connection to Ollama"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 500

            mock_session.get = AsyncMock(return_value=mock_response_obj)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_response_obj.__aenter__ = AsyncMock(return_value=mock_response_obj)
            mock_response_obj.__aexit__ = AsyncMock()

            mock_session_class.return_value = mock_session

            connected, models = await ollama_client.test_connection()

            assert connected is False
            assert len(models) == 0

    @pytest.mark.asyncio
    async def test_test_connection_timeout(self, ollama_client):
        """Test connection timeout"""
        with patch('aiohttp.ClientSession') as mock_session_class, \
             patch('streamlit.error') as mock_error:

            mock_session = AsyncMock()
            mock_session.get = AsyncMock(side_effect=TimeoutError("Connection timeout"))
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()

            mock_session_class.return_value = mock_session

            connected, models = await ollama_client.test_connection()

            assert connected is False
            assert len(models) == 0
            mock_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_stream_success(self, ollama_client):
        """Test successful streaming generation"""
        mock_chunks = [
            b'{"response": "Hello", "done": false}\n',
            b'{"response": " world", "done": false}\n',
            b'{"done": true}\n'
        ]

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 200

            # Create async iterator for content
            class AsyncIterator:
                def __init__(self, items):
                    self.items = items
                    self.index = 0

                def __aiter__(self):
                    return self

                async def __anext__(self):
                    if self.index >= len(self.items):
                        raise StopAsyncIteration
                    item = self.items[self.index]
                    self.index += 1
                    return item

            mock_response_obj.content = AsyncIterator(mock_chunks)

            mock_connector = Mock()
            mock_session.post = AsyncMock(return_value=mock_response_obj)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session.close = AsyncMock()
            mock_session.closed = False
            mock_response_obj.__aenter__ = AsyncMock(return_value=mock_response_obj)
            mock_response_obj.__aexit__ = AsyncMock()

            mock_session_class.return_value = mock_session

            with patch('aiohttp.TCPConnector', return_value=mock_connector):
                chunks = []
                async for chunk in ollama_client.generate_stream("llama2:7b", "Hello"):
                    chunks.append(chunk)

                assert len(chunks) >= 2
                assert any(c["type"] == "response" and "Hello" in c["content"] for c in chunks)

    @pytest.mark.asyncio
    async def test_generate_stream_with_thinking(self, ollama_client):
        """Test streaming generation with thinking"""
        mock_chunks = [
            b'{"thinking": "Let me think...", "done": false}\n',
            b'{"response": "Answer", "done": false}\n',
            b'{"done": true}\n'
        ]

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 200

            class AsyncIterator:
                def __init__(self, items):
                    self.items = items
                    self.index = 0

                def __aiter__(self):
                    return self

                async def __anext__(self):
                    if self.index >= len(self.items):
                        raise StopAsyncIteration
                    item = self.items[self.index]
                    self.index += 1
                    return item

            mock_response_obj.content = AsyncIterator(mock_chunks)

            mock_connector = Mock()
            mock_session.post = AsyncMock(return_value=mock_response_obj)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session.close = AsyncMock()
            mock_session.closed = False
            mock_response_obj.__aenter__ = AsyncMock(return_value=mock_response_obj)
            mock_response_obj.__aexit__ = AsyncMock()

            mock_session_class.return_value = mock_session

            with patch('aiohttp.TCPConnector', return_value=mock_connector):
                chunks = []
                async for chunk in ollama_client.generate_stream("llama2:7b", "Hello", think=True):
                    chunks.append(chunk)

                # Should have both thinking and response chunks
                assert any(c["type"] == "thinking" for c in chunks)
                assert any(c["type"] == "response" for c in chunks)

    @pytest.mark.asyncio
    async def test_generate_stream_error_response(self, ollama_client):
        """Test streaming generation with error response"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 500
            mock_response_obj.text = AsyncMock(return_value="Internal server error")

            mock_connector = Mock()
            mock_session.post = AsyncMock(return_value=mock_response_obj)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session.close = AsyncMock()
            mock_session.closed = False
            mock_response_obj.__aenter__ = AsyncMock(return_value=mock_response_obj)
            mock_response_obj.__aexit__ = AsyncMock()

            mock_session_class.return_value = mock_session

            with patch('aiohttp.TCPConnector', return_value=mock_connector):
                chunks = []
                async for chunk in ollama_client.generate_stream("llama2:7b", "Hello"):
                    chunks.append(chunk)

                assert any(c["type"] == "error" for c in chunks)


class TestStreamlitBackroomApp:
    """Test StreamlitBackroomApp"""

    @pytest.fixture
    def app(self):
        """Create a StreamlitBackroomApp instance"""
        # Mock session_state as an object with attribute access
        mock_session_state = MagicMock()
        mock_session_state.personas = []
        mock_session_state.messages = []
        mock_session_state.is_running = False
        mock_session_state.available_models = []
        mock_session_state.last_speaker_index = None
        mock_session_state.settings = {
            'max_history': 100,
            'response_delay_min': 1,
            'response_delay_max': 5,
            'auto_advance': True,
            'context_messages': 10,
            'enable_thinking': True,
            'response_timeout': 300
        }
        mock_session_state.auto_run_count = 0
        mock_session_state.total_message_count = 0
        mock_session_state.non_thinking_models = set()
        mock_session_state.pending_manual_turn = False

        with patch('streamlit_backroom.st.session_state', mock_session_state):
            return StreamlitBackroomApp()

    def test_init_creates_logger_and_client(self, app):
        """Test that initialization creates logger and Ollama client"""
        assert app.logger is not None
        assert app.ollama is not None
        assert isinstance(app.role_templates, dict)

    def test_get_role_templates(self, app):
        """Test getting role templates"""
        templates = app.get_role_templates()
        assert isinstance(templates, dict)
        assert "" in templates
        assert "Moderator" in templates
        assert "Philosopher" in templates

    def test_get_persona_avatar_with_role(self, app):
        """Test getting avatar for persona with role"""
        persona = AIPersona(
            id="test",
            name="Test",
            model="llama2:7b",
            role="Moderator"
        )
        avatar = app.get_persona_avatar(persona)
        assert avatar == "🎯"  # Moderator emoji

    def test_get_persona_avatar_without_role(self, app):
        """Test getting avatar for persona without role"""
        persona = AIPersona(
            id="test",
            name="Test",
            model="llama2:7b"
        )
        avatar = app.get_persona_avatar(persona)
        assert avatar == "🤖"  # Default emoji

    def test_create_persona_display_html(self, app):
        """Test creating persona display HTML"""
        html = app._create_persona_display_html("TestBot", "#FF0000", "Moderator")
        assert "TestBot" in html
        assert "#FF0000" in html
        assert "Moderator" in html
        assert "🎯" in html  # Moderator emoji

    def test_create_persona_display_html_xss_protection(self, app):
        """Test XSS protection in persona display"""
        html = app._create_persona_display_html("<script>alert('xss')</script>", "#FF0000")
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_highlight_mentions(self, app):
        """Test highlighting @mentions"""
        personas = [
            AIPersona(id="1", name="Bot1", model="llama2", color="#FF0000"),
            AIPersona(id="2", name="Bot2", model="llama2", color="#00FF00")
        ]

        content = "Hey @Bot1, what do you think?"
        result, has_mentions = app._highlight_mentions(content, personas)

        assert has_mentions is True
        assert "@Bot1" in result
        assert "#FF0000" in result

    def test_highlight_mentions_no_mentions(self, app):
        """Test highlighting with no @mentions"""
        personas = [
            AIPersona(id="1", name="Bot1", model="llama2", color="#FF0000")
        ]

        content = "Just a regular message"
        result, has_mentions = app._highlight_mentions(content, personas)

        assert has_mentions is False

    def test_get_next_speaker(self, app):
        """Test getting next speaker in rotation"""
        mock_state = MagicMock()
        mock_state.personas = [
            AIPersona(id="1", name="Bot1", model="llama2", enabled=True),
            AIPersona(id="2", name="Bot2", model="llama2", enabled=True)
        ]
        mock_state.last_speaker_index = None

        with patch('streamlit_backroom.st.session_state', mock_state):
            app.get_next_speaker()

            # Should set last_speaker_index to 0 for first call
            assert mock_state.last_speaker_index == 0

    def test_get_next_speaker_rotation(self, app):
        """Test speaker rotation"""
        mock_state = MagicMock()
        mock_state.personas = [
            AIPersona(id="1", name="Bot1", model="llama2", enabled=True),
            AIPersona(id="2", name="Bot2", model="llama2", enabled=True)
        ]
        mock_state.last_speaker_index = 0

        with patch('streamlit_backroom.st.session_state', mock_state):
            app.get_next_speaker()

            # Should increment to 1
            assert mock_state.last_speaker_index == 1

    def test_get_next_speaker_no_enabled_personas(self, app):
        """Test getting next speaker with no enabled personas"""
        mock_state = MagicMock()
        mock_state.personas = []

        with patch('streamlit_backroom.st.session_state', mock_state):
            result = app.get_next_speaker()

            assert result is None

    def test_generate_system_prompt_basic(self, app):
        """Test generating system prompt"""
        persona = AIPersona(
            id="1",
            name="Bot1",
            model="llama2",
            role="Philosopher"
        )

        mock_state = MagicMock()
        mock_state.personas = [
            persona,
            AIPersona(id="2", name="Bot2", model="llama2", enabled=True)
        ]

        with patch('streamlit_backroom.st.session_state', mock_state):
            prompt = app.generate_system_prompt(persona)

            assert "Bot1" in prompt
            assert "Philosopher" in prompt
            assert "@mention" in prompt.lower()

    def test_generate_system_prompt_moderator_role(self, app):
        """Test system prompt for Moderator role"""
        persona = AIPersona(
            id="1",
            name="Moderator",
            model="llama2",
            role="Moderator"
        )

        mock_state = MagicMock()
        mock_state.personas = [persona]

        with patch('streamlit_backroom.st.session_state', mock_state):
            prompt = app.generate_system_prompt(persona)

            assert "follow-up questions" in prompt
            assert "Introducing new topics" in prompt

    def test_generate_system_prompt_note_taker_role(self, app):
        """Test system prompt for Note-Taker role"""
        persona = AIPersona(
            id="1",
            name="Notes",
            model="llama2",
            role="Note-Taker"
        )

        mock_state = MagicMock()
        mock_state.personas = [persona]

        with patch('streamlit_backroom.st.session_state', mock_state):
            prompt = app.generate_system_prompt(persona)

            assert "summarizing" in prompt
            assert "themes" in prompt

    def test_generate_system_prompt_custom_role(self, app):
        """Test system prompt with custom role"""
        persona = AIPersona(
            id="1",
            name="Custom",
            model="llama2",
            role="CustomRole",
            system_prompt="Be extra helpful"
        )

        mock_state = MagicMock()
        mock_state.personas = [persona]

        with patch('streamlit_backroom.st.session_state', mock_state):
            prompt = app.generate_system_prompt(persona)

            assert "CustomRole" in prompt
            assert "Be extra helpful" in prompt

    def test_generate_conversation_prompt_first_message(self, app):
        """Test generating prompt for first message"""
        persona = AIPersona(id="1", name="Bot1", model="llama2")

        mock_state = MagicMock()
        mock_state.messages = []
        mock_state.settings = {'context_messages': 10}
        mock_state.personas = [persona]

        with patch('streamlit_backroom.st.session_state', mock_state):
            prompt = app._generate_conversation_prompt(persona)

            assert "introduce yourself" in prompt.lower()

    def test_generate_conversation_prompt_with_history(self, app):
        """Test generating prompt with conversation history"""
        persona = AIPersona(id="1", name="Bot1", model="llama2")

        mock_state = MagicMock()
        mock_state.messages = [
            {
                "role": "assistant",
                "content": "Hello",
                "timestamp": datetime(2025, 1, 15, 10, 0, 0),
                "persona_name": "Bot2",
                "model": "llama2"
            }
        ]
        mock_state.settings = {'context_messages': 10}
        mock_state.personas = [persona, AIPersona(id="2", name="Bot2", model="llama2", enabled=True)]

        with patch('streamlit_backroom.st.session_state', mock_state):
            prompt = app._generate_conversation_prompt(persona)

            assert "CONVERSATION HISTORY" in prompt
            assert "Bot2" in prompt
            assert "Hello" in prompt

    def test_run_async_in_new_loop(self, app):
        """Test running async coroutine in new loop"""
        async def sample_coro():
            return "test result"

        result = app._run_async_in_new_loop(sample_coro())
        assert result == "test result"

    @pytest.mark.asyncio
    async def test_check_ollama_connection(self, app):
        """Test checking Ollama connection"""
        mock_state = MagicMock()
        mock_state.available_models = []

        with patch('streamlit_backroom.st.session_state', mock_state):
            with patch.object(app.ollama, 'test_connection', new=AsyncMock(return_value=(True, ["llama2"]))):
                result = await app.check_ollama_connection()

                assert result is True
                assert mock_state.available_models == ["llama2"]

    def test_save_message_to_history(self, app):
        """Test saving message to history"""
        persona = AIPersona(id="1", name="Bot1", model="llama2")
        timestamp = datetime.now()

        mock_state = MagicMock()
        mock_state.messages = []
        mock_state.total_message_count = 0
        mock_state.settings = {'max_history': 100}

        with patch('streamlit_backroom.st.session_state', mock_state):
            app._save_message_to_history(persona, "Test response", "thinking", timestamp)

            assert len(mock_state.messages) == 1
            assert mock_state.messages[0]["content"] == "Test response"
            assert mock_state.total_message_count == 1

    def test_save_message_to_history_max_limit(self, app):
        """Test saving message respects max history limit"""
        persona = AIPersona(id="1", name="Bot1", model="llama2")
        timestamp = datetime.now()

        mock_state = MagicMock()
        # Create a history at max capacity
        mock_state.messages = [{"role": "assistant", "content": f"Msg {i}",
                               "timestamp": timestamp, "persona_name": "Bot",
                               "model": "llama2", "thinking": ""}
                              for i in range(10)]
        mock_state.total_message_count = 10
        mock_state.settings = {'max_history': 10}

        with patch('streamlit_backroom.st.session_state', mock_state):
            app._save_message_to_history(persona, "New message", "", timestamp)

            # Should maintain max_history limit
            assert len(mock_state.messages) == 10
            assert mock_state.messages[-1]["content"] == "New message"

    def test_save_message_skips_errors(self, app):
        """Test that error messages are not saved"""
        persona = AIPersona(id="1", name="Bot1", model="llama2")
        timestamp = datetime.now()

        mock_state = MagicMock()
        mock_state.messages = []
        mock_state.total_message_count = 0
        mock_state.settings = {'max_history': 100}

        with patch('streamlit_backroom.st.session_state', mock_state):
            app._save_message_to_history(persona, "Error: Connection failed", "", timestamp)

            # Error messages should not be saved
            assert len(mock_state.messages) == 0


class TestAIPersona:
    """Test AIPersona dataclass"""

    def test_persona_creation(self):
        """Test creating a persona"""
        persona = AIPersona(
            id="test-id",
            name="TestBot",
            model="llama2:7b",
            role="Philosopher",
            system_prompt="Be thoughtful",
            color="#FF0000",
            enabled=True
        )

        assert persona.id == "test-id"
        assert persona.name == "TestBot"
        assert persona.model == "llama2:7b"
        assert persona.role == "Philosopher"
        assert persona.system_prompt == "Be thoughtful"
        assert persona.color == "#FF0000"
        assert persona.enabled is True

    def test_persona_defaults(self):
        """Test persona default values"""
        persona = AIPersona(
            id="test",
            name="Test",
            model="llama2"
        )

        assert persona.role == ""
        assert persona.system_prompt == ""
        assert persona.color == "#1f77b4"
        assert persona.enabled is True
