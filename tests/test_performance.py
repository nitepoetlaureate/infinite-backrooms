"""Performance benchmarks for Infinite Backrooms.

These tests establish performance baselines for critical operations.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.persona import AIPersona
from src.services.logger import ConversationLogger


class MockSessionState:
    """Mock Streamlit session state for testing."""

    def __init__(self) -> None:
        self._state: dict[str, Any] = {}

    def __contains__(self, key: str) -> bool:
        return key in self._state

    def __getitem__(self, key: str) -> Any:
        return self._state[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._state[key] = value

    def __getattr__(self, key: str) -> Any:
        if key.startswith("_state"):
            return object.__getattribute__(self, key)
        return self._state.get(key)

    def __setattr__(self, key: str, value: Any) -> None:
        if key.startswith("_state"):
            object.__setattr__(self, key, value)
        else:
            self._state[key] = value


class TestPerformance:
    """Performance benchmarks for key operations."""

    def test_persona_creation_performance(self) -> None:
        """Benchmark persona creation time."""
        import time

        start = time.time()
        personas = [
            AIPersona(
                id=f"persona-{i}",
                name=f"Persona{i}",
                model="llama2",
                role="Explorer",
                system_prompt="Test prompt",
            )
            for i in range(100)
        ]
        elapsed = time.time() - start

        assert len(personas) == 100
        # Should create 100 personas in less than 100ms
        assert elapsed < 0.1, f"Persona creation took {elapsed:.3f}s (expected <0.1s)"

    def test_logger_message_write_performance(self, tmp_path) -> None:
        """Benchmark conversation logging performance."""
        import time

        logger = ConversationLogger(log_dir=str(tmp_path))

        start = time.time()
        for i in range(100):
            logger.log_message(f"Persona{i % 10}", f"Message {i}")
        elapsed = time.time() - start

        # Should log 100 messages in less than 1 second
        assert elapsed < 1.0, f"Logging 100 messages took {elapsed:.3f}s (expected <1.0s)"

    def test_logger_parse_performance(self, tmp_path) -> None:
        """Benchmark log file parsing performance."""
        import time

        logger = ConversationLogger(log_dir=str(tmp_path))

        # Create log with 1000 messages
        for i in range(1000):
            logger.log_message(f"Persona{i % 10}", f"Message {i}")

        log_file = logger.get_daily_log_file()

        start = time.time()
        messages = logger.parse_log_file(log_file)
        elapsed = time.time() - start

        assert len(messages) == 1000
        # Should parse 1000 messages in less than 500ms
        assert elapsed < 0.5, f"Parsing 1000 messages took {elapsed:.3f}s (expected <0.5s)"

    def test_persona_lookup_performance(self) -> None:
        """Benchmark persona lookup from list vs dict."""
        import time

        # Create 100 personas
        personas = [
            AIPersona(id=f"p{i}", name=f"Persona{i}", model="llama2") for i in range(100)
        ]

        # Test list lookup (O(n))
        start = time.time()
        for _ in range(1000):
            for persona in personas:
                if persona.name == "Persona99":
                    found = persona
                    break
        list_time = time.time() - start

        # Test dict lookup (O(1))
        persona_dict = {p.name: p for p in personas}
        start = time.time()
        for _ in range(1000):
            found = persona_dict.get("Persona99")
        dict_time = time.time() - start

        # Dict should be significantly faster for large lists
        assert dict_time < list_time, "Dict lookup should be faster than list search"
        # Dict lookup should be at least 2x faster
        speedup = list_time / dict_time
        assert speedup > 2, f"Dict lookup only {speedup:.1f}x faster (expected >2x)"

    @pytest.mark.asyncio
    async def test_session_client_cache_performance(self) -> None:
        """Benchmark session caching vs creating new clients."""
        from src.utils.session import get_ollama_client

        session_state = MockSessionState()
        base_url = "http://localhost:11434"

        with patch("src.services.ollama_client.OllamaClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            import time

            # First call - creates client
            start = time.time()
            client1 = await get_ollama_client(session_state, base_url)
            first_call_time = time.time() - start

            # Subsequent calls - returns cached client
            start = time.time()
            for _ in range(100):
                client = await get_ollama_client(session_state, base_url)
            cached_calls_time = time.time() - start

            # Cached calls should be much faster (no __aenter__ calls)
            avg_cached_time = cached_calls_time / 100
            # Each cached call should be <1ms
            assert avg_cached_time < 0.001, (
                f"Cached client retrieval took {avg_cached_time*1000:.3f}ms (expected <1ms)"
            )

    def test_validation_performance(self) -> None:
        """Benchmark input validation performance."""
        from src.utils.validation import validate_persona_name

        import time

        # Test 10,000 validations
        start = time.time()
        for i in range(10000):
            validate_persona_name(f"Persona{i}")
        elapsed = time.time() - start

        # Should validate 10,000 names in less than 100ms
        assert elapsed < 0.1, f"10,000 validations took {elapsed:.3f}s (expected <0.1s)"

    def test_message_cleaning_performance(self, tmp_path) -> None:
        """Benchmark thinking tag removal performance."""
        from src.services.logger import ConversationLogger

        import time

        logger = ConversationLogger(log_dir=str(tmp_path))

        # Create message with thinking tags
        message_with_tags = (
            "Here is my response <think>This is internal thought</think> "
            "and more text <think>Another thought</think> end."
        )

        start = time.time()
        for _ in range(10000):
            cleaned = logger.clean_message(message_with_tags)
        elapsed = time.time() - start

        # Should clean 10,000 messages in less than 500ms
        assert elapsed < 0.5, f"Cleaning 10,000 messages took {elapsed:.3f}s (expected <0.5s)"


class TestMemoryUsage:
    """Memory usage tests for key operations."""

    def test_large_conversation_memory(self) -> None:
        """Test memory usage with large conversation history."""
        import sys

        # Create 1000 messages
        messages = [
            {"persona_name": f"Persona{i % 10}", "content": f"Message {i}" * 10}
            for i in range(1000)
        ]

        # Rough estimate: each message should be <1KB
        message_size = sys.getsizeof(messages) / len(messages)
        assert message_size < 1024, f"Average message size is {message_size:.0f} bytes (expected <1KB)"

    def test_persona_list_memory(self) -> None:
        """Test memory usage of persona list."""
        import sys

        personas = [
            AIPersona(
                id=f"p{i}",
                name=f"Persona{i}",
                model="llama2",
                role="Explorer",
                system_prompt="Test prompt" * 10,
            )
            for i in range(100)
        ]

        # 100 personas should use <100KB
        total_size = sys.getsizeof(personas)
        assert total_size < 100 * 1024, f"100 personas use {total_size/1024:.1f}KB (expected <100KB)"
