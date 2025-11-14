"""Pytest configuration and fixtures for Infinite AI Backrooms tests."""

import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

# Add parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.persona import AIPersona
from src.services.logger import ConversationLogger
from src.services.ollama_client import OllamaClient
from tests.fixtures.mock_responses import (
    get_mock_generate_response,
    get_mock_models_response,
    get_mock_streaming_chunks,
)


@pytest.fixture
def sample_persona():
    """Create a sample AIPersona for testing."""
    return AIPersona(
        id="test-123",
        name="TestBot",
        model="llama2:latest",
        role="analyst",
        system_prompt="You are a test analyst.",
        color="#FF5733",
        enabled=True,
    )


@pytest.fixture
def sample_personas():
    """Create multiple sample personas for testing."""
    return [
        AIPersona(
            id="alice-001",
            name="Alice",
            model="llama2:latest",
            role="creative",
            system_prompt="You are creative.",
            color="#FF5733",
            enabled=True,
        ),
        AIPersona(
            id="bob-002",
            name="Bob",
            model="mistral:latest",
            role="critic",
            system_prompt="You are critical.",
            color="#33C3FF",
            enabled=True,
        ),
        AIPersona(
            id="charlie-003",
            name="Charlie",
            model="llama2:latest",
            role="mediator",
            system_prompt="You mediate discussions.",
            color="#33FF57",
            enabled=True,
        ),
    ]


@pytest.fixture
def mock_ollama_response():
    """Mock successful Ollama generate response."""
    return get_mock_generate_response("This is a test response.")


@pytest.fixture
def mock_models_response():
    """Mock successful Ollama models list response."""
    return get_mock_models_response()


@pytest.fixture
def mock_streaming_chunks():
    """Mock streaming response chunks."""
    return get_mock_streaming_chunks("Hello from the AI")


@pytest.fixture
async def mock_ollama_client(mock_ollama_response, mock_models_response):
    """Create a mock OllamaClient for testing."""
    client = Mock(spec=OllamaClient)
    client.base_url = "http://localhost:11434"
    client.test_connection = AsyncMock(return_value=(True, ["llama2:latest", "mistral:latest"]))

    async def mock_generate_stream(*args, **kwargs):
        """Mock async generator for streaming."""
        chunks = ["Hello ", "from ", "the ", "AI"]
        for chunk in chunks:
            yield {"response": chunk, "done": False}
        yield {"response": "", "done": True}

    client.generate_stream = mock_generate_stream
    return client


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def conversation_logger(temp_log_dir):
    """Create a ConversationLogger with temporary directory."""
    return ConversationLogger(log_dir=str(temp_log_dir))


@pytest.fixture
def sample_conversation_history():
    """Create sample conversation history."""
    return [
        {
            "speaker": "Alice",
            "message": "Hello everyone! Let's discuss AI.",
            "timestamp": "10:00:00",
        },
        {
            "speaker": "Bob",
            "message": "@Alice I think AI has great potential.",
            "timestamp": "10:01:00",
        },
        {
            "speaker": "Charlie",
            "message": "I agree with both perspectives.",
            "timestamp": "10:02:00",
        },
    ]


class MockSessionState(dict):
    """Mock Streamlit session state that supports both dict and attribute access."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'MockSessionState' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise AttributeError(f"'MockSessionState' object has no attribute '{name}'")


@pytest.fixture
def mock_streamlit_session_state():
    """Mock Streamlit session state."""
    return MockSessionState({
        "personas": [],
        "conversation_history": [],
        "auto_mode": False,
        "initialized": False,
        "turn_count": 0,
        "ollama_url": "http://localhost:11434",
        "available_models": [],
    })


# Pytest configuration
@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset mocks before each test."""
    yield
    # Cleanup happens automatically


@pytest.fixture
def fixed_datetime():
    """Provide a fixed datetime for testing."""
    return datetime(2024, 1, 1, 12, 0, 0)
