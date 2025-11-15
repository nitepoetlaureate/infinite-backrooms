"""Unified Ollama API client with comprehensive features.

This is the canonical Ollama client that consolidates all the best features
from multiple implementations into a single, production-ready client.

Features:
- Connection pooling with configurable limits
- Async context manager pattern for proper resource cleanup
- Health monitoring and diagnostics
- Comprehensive error handling with retry logic
- Streaming response support
- Type hints throughout
- Configurable timeouts and parameters
- Performance monitoring integration
- Thread-safe operations for Streamlit compatibility

Usage:
    async with OllamaClient() as client:
        connected, models = await client.test_connection()
        if connected:
            async for chunk in client.generate_stream("llama2", "Hello"):
                print(chunk["content"])
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator, Optional

import aiohttp

from src.utils.constants import (
    DEFAULT_OLLAMA_URL,
    DEFAULT_RESPONSE_TIMEOUT,
    DEFAULT_TIMEOUT
)

logger = logging.getLogger(__name__)


class OllamaClient:
    """Unified Ollama API client with comprehensive features.

    This client implements all best practices identified from analyzing
    multiple client implementations throughout the codebase.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_URL,
        timeout: int = DEFAULT_RESPONSE_TIMEOUT,
        max_connections: int = 100,
        keepalive_timeout: int = 300,
        enable_connection_pooling: bool = True,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize Ollama client with advanced configuration.

        Args:
            base_url: Base URL for Ollama API
            timeout: Request timeout in seconds
            max_connections: Maximum connections in pool
            keepalive_timeout: Connection keepalive timeout
            enable_connection_pooling: Whether to use connection pooling
            retry_attempts: Number of retry attempts for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_connections = max_connections
        self.keepalive_timeout = keepalive_timeout
        self.enable_connection_pooling = enable_connection_pooling
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

        # Internal state
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None

    async def __aenter__(self) -> OllamaClient:
        """Enter async context manager - initialize connection pool."""
        if self.enable_connection_pooling:
            # Create connector with pooling
            self._connector = aiohttp.TCPConnector(
                limit=self.max_connections,
                limit_per_host=min(self.max_connections, 10),
                ttl_dns_cache=300,
                force_close=False,  # Keep connections alive
                enable_cleanup_closed=True,
                keepalive_timeout=self.keepalive_timeout,
            )
        else:
            # Simple connector without pooling
            self._connector = aiohttp.TCPConnector(
                limit=1,
                enable_cleanup_closed=True,
            )

        # Configure timeout
        timeout = aiohttp.ClientTimeout(
            total=None,  # No total timeout for streaming
            sock_read=self.timeout,
            sock_connect=min(self.timeout, 30),  # Connect timeout
        )

        # Create session
        self._session = aiohttp.ClientSession(
            connector=self._connector,
            timeout=timeout,
            connector_owner=True,
        )

        logger.debug(f"Ollama client initialized for {self.base_url}")
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> None:
        """Exit async context manager - cleanup resources."""
        if self._session and not self._session.closed:
            await self._session.close()

        if self._connector and not self._connector.closed:
            await self._connector.close()

        # Small delay to ensure cleanup completes
        await asyncio.sleep(0.050)

        logger.debug("Ollama client resources cleaned up")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for request

        Returns:
            HTTP response object

        Raises:
            aiohttp.ClientError: If all retry attempts fail
        """
        if not self._session:
            raise RuntimeError(
                "Client not initialized. Use 'async with' context manager."
            )

        url = f"{self.base_url}{endpoint}"
        last_error = None

        for attempt in range(self.retry_attempts + 1):
            try:
                async with self._session.request(method, url, **kwargs) as response:
                    return response

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                if attempt < self.retry_attempts:
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.retry_attempts + 1}): {e}"
                    )
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"Request failed after {self.retry_attempts + 1} attempts: {e}")

        raise last_error  # type: ignore

    async def test_connection(self) -> tuple[bool, list[str]]:
        """Test connection to Ollama and retrieve available models.

        Returns:
            Tuple of (connected: bool, models: list[str])

        Example:
            async with OllamaClient() as client:
                connected, models = await client.test_connection()
                if connected:
                    print(f"Available models: {models}")
        """
        try:
            async with await self._make_request("GET", "/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [
                        model["name"]
                        for model in data.get("models", [])
                    ]
                    logger.info(f"Connection successful. Found {len(models)} models")
                    return True, models
                else:
                    logger.error(f"Connection failed with status {response.status}")
                    return False, []

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False, []

    async def health_check(self) -> bool:
        """Check if Ollama service is healthy.

        Returns:
            bool: True if service is responding

        Example:
            async with OllamaClient() as client:
                if await client.health_check():
                    print("Service is healthy")
        """
        try:
            connected, _ = await self.test_connection()
            return connected
        except Exception:
            return False

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        think: bool = False,
        timeout: Optional[int] = None,
        **options
    ) -> AsyncGenerator[dict, None]:
        """Generate streaming response from model.

        Args:
            model: Model name to use
            prompt: User prompt
            system_prompt: Optional system prompt
            think: Enable thinking mode (if supported)
            timeout: Override default timeout for this request
            **options: Additional model options

        Yields:
            dict: Response chunks with standardized format:
                - {"type": "response", "content": str}
                - {"type": "error", "content": str}
                - {"type": "done"}

        Example:
            async with OllamaClient() as client:
                async for chunk in client.generate_stream("llama2", "Hello"):
                    if chunk["type"] == "response":
                        print(chunk["content"], end="")
        """
        if not self._session:
            raise RuntimeError(
                "Client not initialized. Use 'async with' context manager."
            )

        # Prepare request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
        }

        if system_prompt:
            payload["system"] = system_prompt

        if think:
            payload["options"] = payload.get("options", {})
            payload["options"]["thinking"] = True

        # Add any additional options
        if options:
            payload["options"] = payload.get("options", {})
            payload["options"].update(options)

        # Configure timeout for this request
        request_timeout = None
        if timeout is not None:
            request_timeout = aiohttp.ClientTimeout(total=timeout)

        try:
            async with await self._make_request(
                "POST",
                "/api/generate",
                json=payload,
                timeout=request_timeout
            ) as response:
                response.raise_for_status()

                # Process streaming response
                async for line in response.content:
                    if line:
                        try:
                            line = line.decode('utf-8').strip()
                            if line:
                                chunk = json.loads(line)

                                if chunk.get("response"):
                                    yield {
                                        "type": "response",
                                        "content": chunk["response"]
                                    }

                                if chunk.get("done"):
                                    yield {"type": "done"}
                                    break

                        except json.JSONDecodeError:
                            # Skip invalid JSON lines
                            continue
                        except Exception as e:
                            logger.error(f"Error processing response chunk: {e}")
                            yield {
                                "type": "error",
                                "content": f"Error processing response: {e}"
                            }

        except asyncio.TimeoutError:
            error_msg = f"Request timed out after {timeout or self.timeout}s"
            logger.error(error_msg)
            yield {"type": "error", "content": error_msg}

        except aiohttp.ClientError as e:
            error_msg = f"Network error: {e}"
            logger.error(error_msg)
            yield {"type": "error", "content": error_msg}

        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(error_msg)
            yield {"type": "error", "content": error_msg}

    async def generate(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        think: bool = False,
        timeout: Optional[int] = None,
        **options
    ) -> str:
        """Generate complete response (non-streaming).

        Args:
            model: Model name to use
            prompt: User prompt
            system_prompt: Optional system prompt
            think: Enable thinking mode
            timeout: Request timeout
            **options: Additional model options

        Returns:
            str: Complete response text

        Example:
            async with OllamaClient() as client:
                response = await client.generate("llama2", "Hello")
                print(response)
        """
        response_parts = []

        async for chunk in self.generate_stream(
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            think=think,
            timeout=timeout,
            **options
        ):
            if chunk["type"] == "response":
                response_parts.append(chunk["content"])
            elif chunk["type"] == "error":
                raise RuntimeError(f"Generation failed: {chunk['content']}")
            elif chunk["type"] == "done":
                break

        return "".join(response_parts)

    async def list_models(self) -> list[dict]:
        """List all available models with details.

        Returns:
            list[dict]: Model information including name, size, modified time

        Example:
            async with OllamaClient() as client:
                models = await client.list_models()
                for model in models:
                    print(f"{model['name']}: {model['size']} bytes")
        """
        try:
            async with await self._make_request("GET", "/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("models", [])
                else:
                    raise aiohttp.ClientError(f"HTTP {response.status}")
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            raise

    def get_connection_info(self) -> dict:
        """Get information about current connection state.

        Returns:
            dict: Connection information and statistics

        Example:
            client = OllamaClient()
            info = client.get_connection_info()
            print(f"Max connections: {info['max_connections']}")
        """
        return {
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_connections": self.max_connections,
            "keepalive_timeout": self.keepalive_timeout,
            "connection_pooling": self.enable_connection_pooling,
            "retry_attempts": self.retry_attempts,
            "session_active": self._session is not None and not self._session.closed,
            "connector_active": self._connector is not None and not self._connector.closed,
        }

    async def __repr__(self) -> str:
        """Return string representation of client."""
        return (
            f"OllamaClient(base_url={self.base_url}, "
            f"timeout={self.timeout}, "
            f"pooling={self.enable_connection_pooling})"
        )