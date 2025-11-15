"""Pytest configuration and fixtures for Infinite AI Backrooms tests."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import tempfile
import shutil
import json
import asyncio
from typing import Dict, Any, Generator, AsyncGenerator

# Add parent directory to path so we can import from source
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from actual module locations based on codebase analysis
from src.models.persona import AIPersona
from src.services.ollama_client import OllamaClient
from src.services.logger import ConversationLogger
from src.utils.sanitization import sanitize_html
from src.utils.validation import validate_persona_name, validate_model_name

# Try to import optional modules, create mocks if they don't exist
try:
    from src.utils.rate_limiter import RateLimiter
except ImportError:
    RateLimiter = Mock()

try:
    from src.utils.performance import PerformanceMonitor
except ImportError:
    PerformanceMonitor = Mock()

# Try to import mock responses if they exist
try:
    from tests.fixtures.mock_responses import (
        get_mock_models_response,
        get_mock_generate_response,
        get_mock_streaming_chunks
    )
except ImportError:
    # Create fallback mock responses
    def get_mock_models_response():
        return {"models": [{"name": "llama2:latest"}, {"name": "mistral:latest"}]}

    def get_mock_generate_response(text):
        return {"response": text, "done": True}

    def get_mock_streaming_chunks(text):
        return [{"response": chunk, "done": False} for chunk in text.split()] + [{"response": "", "done": True}]


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
        enabled=True
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
            enabled=True
        ),
        AIPersona(
            id="bob-002",
            name="Bob",
            model="mistral:latest",
            role="critic",
            system_prompt="You are critical.",
            color="#33C3FF",
            enabled=True
        ),
        AIPersona(
            id="charlie-003",
            name="Charlie",
            model="llama2:latest",
            role="mediator",
            system_prompt="You mediate discussions.",
            color="#33FF57",
            enabled=True
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
async def mock_ollama_client():
    """Create a properly mocked OllamaClient for testing."""
    client = AsyncMock(spec=OllamaClient)
    client.base_url = "http://localhost:11434"

    # Mock async methods with proper return values
    client.test_connection = AsyncMock(
        return_value=(True, ["llama2:latest", "mistral:latest"])
    )

    # Mock async generator for streaming
    async def mock_stream(*args, **kwargs):
        yield {"response": "Hello ", "done": False}
        yield {"response": "from ", "done": False}
        yield {"response": "the ", "done": False}
        yield {"response": "AI", "done": False}
        yield {"response": "", "done": True}

    client.generate_stream = mock_stream

    # Mock context manager methods
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

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
            "timestamp": "10:00:00"
        },
        {
            "speaker": "Bob",
            "message": "@Alice I think AI has great potential.",
            "timestamp": "10:01:00"
        },
        {
            "speaker": "Charlie",
            "message": "I agree with both perspectives.",
            "timestamp": "10:02:00"
        }
    ]


@pytest.fixture
def mock_streamlit_session_state():
    """Mock Streamlit session state."""
    return {
        "personas": [],
        "conversation_history": [],
        "auto_mode": False,
        "initialized": False,
        "turn_count": 0,
        "ollama_url": "http://localhost:11434",
        "available_models": []
    }


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


# Security and validation fixtures
@pytest.fixture
def malicious_inputs():
    """Collection of malicious inputs for security testing."""
    return {
        "xss": "<script>alert('xss')</script>",
        "sql_injection": "'; DROP TABLE users; --",
        "command_injection": "; rm -rf /",
        "path_traversal": "../../../etc/passwd",
        "ldap_injection": "*)(uid=*",
        "html_injection": "<iframe src='javascript:alert(1)'></iframe>",
        "markdown_injection": "[xss](javascript:alert(1))",
        "json_injection": '{"__proto__":{"polluted":true}}',
        "null_byte": "test\x00.txt",
        "oversized": "A" * 100000,
        "unicode_homograph": "admin\u200b.com",
        "csrf_token": "<script>document.location='http://evil.com'</script>"
    }


@pytest.fixture
def valid_inputs():
    """Collection of valid inputs for positive testing."""
    return {
        "persona_name": "TestBot",
        "model_name": "llama2:latest",
        "system_prompt": "You are a helpful AI assistant.",
        "color": "#1f77b4",
        "url": "https://example.com",
        "email": "test@example.com",
        "filename": "test_file.txt",
        "html": "<strong>Bold text</strong>",
        "markdown": "## Heading\n\nThis is **bold** text.",
        "json": '{"key": "value", "number": 123}',
        "text": "Simple text content"
    }


# Performance testing fixtures
@pytest.fixture
def performance_monitor():
    """Create a performance monitor for testing."""
    return PerformanceMonitor()


@pytest.fixture
def rate_limiter():
    """Create a rate limiter for testing."""
    return RateLimiter(max_requests=10, window_seconds=60)


# Mock Streamlit components
@pytest.fixture
def mock_streamlit():
    """Mock Streamlit module for UI testing."""
    mock_st = MagicMock()

    # Mock common Streamlit functions
    mock_st.session_state = {}
    mock_st.sidebar = MagicMock()
    mock_st.columns = MagicMock(return_value=[MagicMock(), MagicMock()])
    mock_st.container = MagicMock()
    mock_st.empty = MagicMock()
    mock_st.info = MagicMock()
    mock_st.success = MagicMock()
    mock_st.error = MagicMock()
    mock_st.warning = MagicMock()
    mock_st.text_input = MagicMock(return_value="test")
    mock_st.text_area = MagicMock(return_value="test input")
    mock_st.selectbox = MagicMock(return_value="option1")
    mock_st.multiselect = MagicMock(return_value=["option1"])
    mock_st.checkbox = MagicMock(return_value=False)
    mock_st.slider = MagicMock(return_value=50)
    mock_st.button = MagicMock(return_value=False)
    mock_st.markdown = MagicMock()
    mock_st.write = MagicMock()
    mock_st.dataframe = MagicMock()
    mock_st.plotly_chart = MagicMock()
    mock_st.experimental_rerun = MagicMock()
    mock_st.set_page_config = MagicMock()

    return mock_st


# Async testing fixtures
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_context():
    """Provide async context for async tests."""
    yield
    # Cleanup can be added here if needed


# UI component fixtures
@pytest.fixture
def mock_session_state():
    """Enhanced mock Streamlit session state with all required keys."""
    return {
        "personas": [],
        "conversation_history": [],
        "auto_mode": False,
        "initialized": False,
        "turn_count": 0,
        "ollama_url": "http://localhost:11434",
        "available_models": [],
        "selected_personas": [],
        "user_input": "",
        "system_status": "connected",
        "last_response": "",
        "debug_mode": False,
        "theme": "light",
        "language": "en"
    }


# Test data fixtures
@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing."""
    return {
        "messages": [
            {
                "speaker": "Alice",
                "message": "Hello everyone!",
                "timestamp": datetime(2024, 1, 1, 12, 0, 0),
                "model": "llama2:latest"
            },
            {
                "speaker": "Bob",
                "message": "@Alice How are you?",
                "timestamp": datetime(2024, 1, 1, 12, 1, 0),
                "model": "mistral:latest"
            }
        ],
        "metadata": {
            "session_id": "test-session-123",
            "duration": 300,
            "total_messages": 2
        }
    }


@pytest.fixture
def mock_api_responses():
    """Collection of mock API responses for testing."""
    return {
        "success_response": {
            "status": "success",
            "data": {"result": "test result"}
        },
        "error_response": {
            "status": "error",
            "error": "Something went wrong"
        },
        "models_response": {
            "models": [
                {"name": "llama2:latest", "size": 4000000000},
                {"name": "mistral:latest", "size": 3500000000}
            ]
        },
        "generate_response": {
            "model": "llama2:latest",
            "created_at": datetime.now().isoformat(),
            "response": "This is a test response",
            "done": True
        }
    }


# Security testing fixtures
@pytest.fixture
def security_test_scenarios():
    """Security test scenarios for comprehensive testing."""
    return {
        "xss_prevention": [
            ("<script>alert('xss')</script>", "&lt;script&gt;alert('xss')&lt;/script&gt;"),
            ("javascript:alert(1)", ""),
            ("onload=alert(1)", "")
        ],
        "injection_prevention": [
            ("'; DROP TABLE users; --", " DROP TABLE users --"),
            ("../../../etc/passwd", "etc_passwd"),
            ("*|command", "command")
        ],
        "input_validation": [
            ("", ""),  # Empty string
            ("A" * 10000, "A" * 10000),  # Max length
            ("A" * 10001, "A" * 9997 + "...[truncated]")  # Oversized
        ]
    }


# Performance test fixtures
@pytest.fixture
def performance_benchmark_data():
    """Data for performance benchmarking tests."""
    return {
        "small_dataset": list(range(100)),
        "medium_dataset": list(range(1000)),
        "large_dataset": list(range(10000)),
        "text_samples": [
            "Short text",
            "Medium length text with more content and details about the topic being discussed",
            "Very long text " * 100  # Long repetitive text
        ]
    }


@pytest.fixture
def mock_file_system():
    """Mock file system operations for testing."""
    with patch("builtins.open", create=True) as mock_open:
        mock_file = MagicMock()
        mock_file.write = MagicMock()
        mock_file.read = MagicMock(return_value="test content")
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=None)
        mock_open.return_value = mock_file
        yield mock_open


@pytest.fixture
def temp_env_vars():
    """Temporary environment variables for testing."""
    original_env = {}
    test_env = {
        "OLLAMA_URL": "http://localhost:11434",
        "LOG_LEVEL": "INFO",
        "MAX_PERSONAS": "10",
        "RATE_LIMIT": "100"
    }

    # Set test environment variables
    for key, value in test_env.items():
        original_env[key] = pytest.monkeypatch.setenv(key, value)

    yield test_env

    # Restore original environment
    for key in test_env:
        if key in original_env:
            pytest.monkeypatch.setenv(key, original_env[key])
        else:
            pytest.monkeypatch.delenv(key, raising=False)