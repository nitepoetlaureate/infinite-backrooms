"""Tests for session management utilities."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.session import cleanup_ollama_client, get_ollama_client


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


class TestGetOllamaClient:
    """Tests for get_ollama_client function."""

    @pytest.mark.asyncio
    async def test_get_ollama_client_creates_new_client(self) -> None:
        """Test that get_ollama_client creates a new client when none exists."""
        session_state = MockSessionState()
        base_url = "http://localhost:11434"

        with patch("src.services.ollama_client.OllamaClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value = mock_client

            result = await get_ollama_client(session_state, base_url)

            assert result == mock_client
            assert session_state._ollama_client == mock_client
            assert session_state._ollama_client_url == base_url
            mock_client.__aenter__.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_ollama_client_returns_cached_client(self) -> None:
        """Test that get_ollama_client returns cached client if URL matches."""
        session_state = MockSessionState()
        base_url = "http://localhost:11434"

        # Create mock client
        mock_client = AsyncMock()
        session_state._ollama_client = mock_client
        session_state._ollama_client_url = base_url

        with patch("src.services.ollama_client.OllamaClient") as mock_client_class:
            result = await get_ollama_client(session_state, base_url)

            # Should return cached client without creating new one
            assert result == mock_client
            mock_client_class.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_ollama_client_recreates_on_url_change(self) -> None:
        """Test that get_ollama_client creates new client when URL changes."""
        session_state = MockSessionState()
        old_url = "http://localhost:11434"
        new_url = "http://localhost:11435"

        # Set up old client
        old_client = AsyncMock()
        old_client.__aexit__ = AsyncMock()
        session_state._ollama_client = old_client
        session_state._ollama_client_url = old_url

        with patch("src.services.ollama_client.OllamaClient") as mock_client_class:
            new_client = AsyncMock()
            new_client.__aenter__ = AsyncMock(return_value=new_client)
            mock_client_class.return_value = new_client

            result = await get_ollama_client(session_state, new_url)

            # Should clean up old client
            old_client.__aexit__.assert_called_once_with(None, None, None)

            # Should create and return new client
            assert result == new_client
            assert session_state._ollama_client == new_client
            assert session_state._ollama_client_url == new_url
            new_client.__aenter__.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_ollama_client_handles_cleanup_error(self) -> None:
        """Test that get_ollama_client handles errors during old client cleanup."""
        session_state = MockSessionState()
        old_url = "http://localhost:11434"
        new_url = "http://localhost:11435"

        # Set up old client that raises error on exit
        old_client = AsyncMock()
        old_client.__aexit__ = AsyncMock(side_effect=Exception("Cleanup error"))
        session_state._ollama_client = old_client
        session_state._ollama_client_url = old_url

        with patch("src.services.ollama_client.OllamaClient") as mock_client_class:
            new_client = AsyncMock()
            new_client.__aenter__ = AsyncMock(return_value=new_client)
            mock_client_class.return_value = new_client

            # Should not raise exception, just log warning
            result = await get_ollama_client(session_state, new_url)

            # Should still create new client despite cleanup error
            assert result == new_client
            assert session_state._ollama_client == new_client
            assert session_state._ollama_client_url == new_url

    @pytest.mark.asyncio
    async def test_get_ollama_client_initializes_cache(self) -> None:
        """Test that get_ollama_client initializes cache attributes."""
        session_state = MockSessionState()
        base_url = "http://localhost:11434"

        # Ensure cache attributes don't exist initially
        assert "_ollama_client" not in session_state

        with patch("src.services.ollama_client.OllamaClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value = mock_client

            await get_ollama_client(session_state, base_url)

            # Cache attributes should be initialized
            assert "_ollama_client" in session_state
            assert "_ollama_client_url" in session_state

    @pytest.mark.asyncio
    async def test_get_ollama_client_with_none_cached_client(self) -> None:
        """Test get_ollama_client when cached client is None."""
        session_state = MockSessionState()
        session_state._ollama_client = None
        session_state._ollama_client_url = None
        base_url = "http://localhost:11434"

        with patch("src.services.ollama_client.OllamaClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value = mock_client

            result = await get_ollama_client(session_state, base_url)

            # Should create new client
            assert result == mock_client
            mock_client_class.assert_called_once_with(base_url=base_url)


class TestCleanupOllamaClient:
    """Tests for cleanup_ollama_client function."""

    @pytest.mark.asyncio
    async def test_cleanup_ollama_client_cleans_up_existing_client(self) -> None:
        """Test that cleanup_ollama_client cleans up existing client."""
        session_state = MockSessionState()

        mock_client = AsyncMock()
        mock_client.__aexit__ = AsyncMock()
        session_state._ollama_client = mock_client
        session_state._ollama_client_url = "http://localhost:11434"

        await cleanup_ollama_client(session_state)

        mock_client.__aexit__.assert_called_once_with(None, None, None)
        assert session_state._ollama_client is None
        assert session_state._ollama_client_url is None

    @pytest.mark.asyncio
    async def test_cleanup_ollama_client_handles_no_client(self) -> None:
        """Test that cleanup_ollama_client handles missing client gracefully."""
        session_state = MockSessionState()

        # Should not raise exception
        await cleanup_ollama_client(session_state)

    @pytest.mark.asyncio
    async def test_cleanup_ollama_client_handles_none_client(self) -> None:
        """Test that cleanup_ollama_client handles None client."""
        session_state = MockSessionState()
        session_state._ollama_client = None

        # Should not raise exception
        await cleanup_ollama_client(session_state)

    @pytest.mark.asyncio
    async def test_cleanup_ollama_client_handles_cleanup_error(self) -> None:
        """Test that cleanup_ollama_client handles errors during cleanup."""
        session_state = MockSessionState()

        mock_client = AsyncMock()
        mock_client.__aexit__ = AsyncMock(side_effect=Exception("Cleanup error"))
        session_state._ollama_client = mock_client
        session_state._ollama_client_url = "http://localhost:11434"

        # Should not raise exception, just log warning
        await cleanup_ollama_client(session_state)

        # Client should still be set to None even after error
        assert session_state._ollama_client is None
        assert session_state._ollama_client_url is None

    @pytest.mark.asyncio
    async def test_cleanup_ollama_client_clears_state_even_on_error(self) -> None:
        """Test that cleanup always clears state even if __aexit__ raises."""
        session_state = MockSessionState()

        mock_client = AsyncMock()
        mock_client.__aexit__ = AsyncMock(side_effect=RuntimeError("Test error"))
        session_state._ollama_client = mock_client
        session_state._ollama_client_url = "http://test:1234"

        await cleanup_ollama_client(session_state)

        # State should be cleared despite error
        assert session_state._ollama_client is None
        assert session_state._ollama_client_url is None
