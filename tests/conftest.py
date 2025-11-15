"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_persona_data():
    """Sample persona data for testing."""
    return {
        "id": "test-123",
        "name": "TestBot",
        "model": "test-model",
        "role": "Scientist",
        "system_prompt": "You are a helpful AI assistant.",
        "color": "#1f77b4",
        "enabled": True,
    }


@pytest.fixture
def sample_message_data():
    """Sample message data for testing."""
    return {
        "role": "assistant",
        "content": "Hello, I'm a test message!",
        "persona_name": "TestBot",
        "model": "test-model",
    }
