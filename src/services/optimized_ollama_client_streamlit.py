"""Streamlit-safe wrapper for the optimized Ollama client.

This module provides a Streamlit-compatible wrapper for the new optimized
Ollama client that uses thread-based execution to avoid event loop corruption
while leveraging the advanced connection pooling capabilities.
"""

from __future__ import annotations

from typing import Any, Generator

from src.services.optimized_ollama_client import OptimizedOllamaClient
from src.utils.constants import DEFAULT_OLLAMA_URL, DEFAULT_RESPONSE_TIMEOUT
from src.utils.streamlit_async import safe_async_call, safe_stream_wrapper


class StreamlitOptimizedOllamaClient:
    """Streamlit-safe wrapper for the optimized Ollama client.

    This client wraps the new OptimizedOllamaClient with thread-based execution
    to ensure compatibility with Streamlit's event loop management while
    leveraging advanced connection pooling for optimal performance.

    Key improvements over the original:
    - Uses advanced connection pooling with health monitoring
    - Eliminates blocking sleep operations
    - Provides proper resource lifecycle management
    - Includes retry logic and error recovery
    - Supports concurrent operations safely

    Usage:
        client = StreamlitOptimizedOllamaClient()
        connected, models = client.test_connection()
        for chunk in client.generate_stream("llama2", "Hello"):
            print(chunk)
    """

    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_URL,
        pool_min_connections: int = 2,
        pool_max_connections: int = 10,
        enable_connection_pooling: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize Streamlit-safe optimized Ollama client.

        Args:
            base_url: Base URL for Ollama API
            pool_min_connections: Minimum connections in pool
            pool_max_connections: Maximum connections in pool
            enable_connection_pooling: Whether to use connection pooling
            **kwargs: Additional arguments for the optimized client
        """
        self.base_url = base_url
        self.pool_min_connections = pool_min_connections
        self.pool_max_connections = pool_max_connections
        self.enable_connection_pooling = enable_connection_pooling
        self.client_kwargs = kwargs

    def test_connection(self) -> tuple[bool, list[str]]:
        """Test Ollama connection safely in Streamlit.

        Returns:
            Tuple of (connected: bool, models: list of model names)

        Example:
            client = StreamlitOptimizedOllamaClient()
            connected, models = client.test_connection()
        """
        async def _test_connection() -> tuple[bool, list[str]]:
            async with OptimizedOllamaClient(
                base_url=self.base_url,
                pool_min_connections=self.pool_min_connections,
                pool_max_connections=self.pool_max_connections,
                enable_connection_pooling=self.enable_connection_pooling,
                **self.client_kwargs,
            ) as client:
                return await client.test_connection()

        return safe_async_call(_test_connection())

    def generate_stream(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
        think: bool = True,
        timeout: int = DEFAULT_RESPONSE_TIMEOUT,
    ) -> Generator[dict[str, str], None, None]:
        """Generate streaming response safely in Streamlit.

        Args:
            model: Model name to use
            prompt: User prompt
            system: Optional system prompt
            think: Enable thinking mode (if supported by model)
            timeout: Request timeout in seconds

        Yields:
            Chunks as dict with keys: type ("thinking", "response", "error", "info"), content

        Example:
            client = StreamlitOptimizedOllamaClient()
            for chunk in client.generate_stream("llama2", "Hello"):
                print(chunk)
        """
        async def _generate_stream():
            async with OptimizedOllamaClient(
                base_url=self.base_url,
                pool_min_connections=self.pool_min_connections,
                pool_max_connections=self.pool_max_connections,
                enable_connection_pooling=self.enable_connection_pooling,
                **self.client_kwargs,
            ) as client:
                async for chunk in client.generate_stream(
                    model, prompt, system, think, timeout
                ):
                    yield chunk

        # Use the stream-safe processor
        stream_processor = safe_stream_wrapper(_generate_stream)
        for chunk in stream_processor():
            yield chunk

    def generate_response(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
        think: bool = True,
        timeout: int = DEFAULT_RESPONSE_TIMEOUT,
    ) -> tuple[str, str, bool]:
        """Generate a complete response safely in Streamlit.

        Args:
            model: Model name to use
            prompt: User prompt
            system: Optional system prompt
            think: Enable thinking mode (if supported by model)
            timeout: Request timeout in seconds

        Returns:
            Tuple of (thinking_content, response_content, success)

        Example:
            client = StreamlitOptimizedOllamaClient()
            thinking, response, success = client.generate_response("llama2", "Hello")
        """
        thinking_content = ""
        response_content = ""
        success = False

        try:
            for chunk in self.generate_stream(model, prompt, system, think, timeout):
                if chunk["type"] == "error":
                    break
                elif chunk["type"] == "thinking":
                    thinking_content += chunk["content"]
                elif chunk["type"] == "response":
                    response_content += chunk["content"]
                    success = True
        except Exception:
            # Error handling is done in the chunks
            pass

        return thinking_content, response_content, success

    def get_connection_metrics(self) -> dict[str, Any]:
        """Get connection pool metrics safely in Streamlit.

        Returns:
            Dictionary with connection pool statistics
        """
        async def _get_metrics() -> dict[str, Any]:
            async with OptimizedOllamaClient(
                base_url=self.base_url,
                pool_min_connections=self.pool_min_connections,
                pool_max_connections=self.pool_max_connections,
                enable_connection_pooling=self.enable_connection_pooling,
                **self.client_kwargs,
            ) as client:
                return await client.get_connection_metrics()

        return safe_async_call(_get_metrics())

    def health_check(self) -> dict[str, Any]:
        """Perform comprehensive health check safely in Streamlit.

        Returns:
            Dictionary with health status information
        """
        async def _health_check() -> dict[str, Any]:
            async with OptimizedOllamaClient(
                base_url=self.base_url,
                pool_min_connections=self.pool_min_connections,
                pool_max_connections=self.pool_max_connections,
                enable_connection_pooling=self.enable_connection_pooling,
                **self.client_kwargs,
            ) as client:
                return await client.health_check()

        return safe_async_call(_health_check())


# Backward compatibility alias
StreamlitOllamaClient = StreamlitOptimizedOllamaClient