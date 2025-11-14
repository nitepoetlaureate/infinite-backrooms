"""Ollama API client with proper async resource management."""

from __future__ import annotations

import asyncio
import json
import logging
import ssl
from collections.abc import AsyncGenerator

import aiohttp

from src.utils.constants import (
    CONNECTION_CLEANUP_DELAY,
    CONNECTION_TEST_TIMEOUT,
    DEFAULT_CONNECTION_POOL_SIZE,
    DEFAULT_OLLAMA_URL,
    DEFAULT_RESPONSE_TIMEOUT,
    DNS_CACHE_TTL,
)
from src.utils.retry import async_retry, async_retry_generator

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API with proper async context management.

    This client implements proper resource cleanup to prevent memory leaks and
    unclosed session warnings.

    Usage:
        async with OllamaClient() as client:
            success, models = await client.test_connection()
            async for chunk in client.generate_stream("llama2", "Hello"):
                print(chunk)
    """

    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_URL,
        verify_ssl: bool = True,
        ssl_context: ssl.SSLContext | None = None,
    ) -> None:
        """Initialize Ollama client.

        Args:
            base_url: Base URL for Ollama API (default: http://localhost:11434)
            verify_ssl: Whether to verify SSL certificates for HTTPS connections (default: True)
            ssl_context: Custom SSL context for HTTPS connections (optional)
        """
        self.base_url = base_url
        self.verify_ssl = verify_ssl
        self._session: aiohttp.ClientSession | None = None
        self._connector: aiohttp.TCPConnector | None = None

        # Create SSL context for HTTPS connections
        if ssl_context is not None:
            self.ssl_context = ssl_context
        elif self.verify_ssl:
            # Use default context with certificate verification
            self.ssl_context = ssl.create_default_context()
        else:
            # Create context without certificate verification (for self-signed certs)
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
            logger.warning(
                "SSL verification disabled. This should only be used with trusted servers."
            )

    async def __aenter__(self) -> OllamaClient:
        """Enter async context manager - create session and connector."""
        # Determine SSL setting based on URL scheme
        ssl_setting: ssl.SSLContext | bool
        if self.base_url.startswith("https://"):
            # HTTPS connection - use SSL context
            ssl_setting = self.ssl_context
        else:
            # HTTP connection - no SSL needed
            ssl_setting = False

        self._connector = aiohttp.TCPConnector(
            limit=DEFAULT_CONNECTION_POOL_SIZE,
            ttl_dns_cache=DNS_CACHE_TTL,
            force_close=True,
            enable_cleanup_closed=True,
            ssl=ssl_setting,
        )
        timeout = aiohttp.ClientTimeout(total=None, sock_read=DEFAULT_RESPONSE_TIMEOUT)
        self._session = aiohttp.ClientSession(connector=self._connector, timeout=timeout)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit async context manager - cleanup session and connector."""
        if self._session and not self._session.closed:
            await self._session.close()
        if self._connector:
            await self._connector.close()
        # Give time for cleanup
        await asyncio.sleep(CONNECTION_CLEANUP_DELAY)

    @async_retry(max_attempts=3, base_delay=1.0, max_delay=5.0)
    async def test_connection(self) -> tuple[bool, list[str]]:
        """Test if Ollama API is accessible and return available models.

        Returns:
            Tuple of (success: bool, models: list of model names)

        Raises:
            RuntimeError: If client not used within async context manager
            aiohttp.ClientError: If connection fails after retries
        """
        if not self._session:
            raise RuntimeError("Client must be used within async context manager")

        try:
            async with self._session.get(
                f"{self.base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=CONNECTION_TEST_TIMEOUT),
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    models = [model["name"] for model in result.get("models", [])]
                    return True, models
                else:
                    logger.warning(f"Ollama API returned status {response.status}")
                    return False, []
        except (TimeoutError, aiohttp.ClientError, ConnectionError) as e:
            logger.error(f"Connection test failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during connection test: {str(e)}")
            return False, []

    @async_retry_generator(max_attempts=3, base_delay=1.0, max_delay=5.0)
    async def generate_stream(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
        think: bool = True,
        timeout: float = DEFAULT_RESPONSE_TIMEOUT,
    ) -> AsyncGenerator[dict[str, str], None]:
        """Generate streaming response from Ollama model with automatic retry.

        Args:
            model: Model name to use
            prompt: User prompt
            system: Optional system prompt
            think: Enable thinking mode (if supported by model)
            timeout: Request timeout in seconds

        Yields:
            Chunks as dict with keys: type ("thinking", "response", "error", "info"), content

        Note:
            Automatically retries on transient network errors with exponential backoff.
            Connection issues will be reported via info chunks before retry.
        """
        if not self._session:
            raise RuntimeError("Client must be used within async context manager")

        payload: dict[str, str | bool] = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "think": think,
        }

        if system and system.strip():
            payload["system"] = system.strip()

        try:
            async with self._session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                if response.status == 200:
                    try:
                        async for line in response.content:
                            if line:
                                try:
                                    chunk = json.loads(line.decode("utf-8"))

                                    # Yield thinking content if available
                                    if "thinking" in chunk and chunk["thinking"]:
                                        yield {"type": "thinking", "content": chunk["thinking"]}

                                    # Yield response content if available
                                    if "response" in chunk and chunk["response"]:
                                        yield {"type": "response", "content": chunk["response"]}

                                    if chunk.get("done", False):
                                        break
                                except json.JSONDecodeError as e:
                                    logger.warning(f"Failed to decode JSON chunk: {str(e)}")
                                    continue
                    except asyncio.CancelledError:
                        yield {"type": "info", "content": "Response cancelled by user"}
                        return

                elif response.status == 400 and think:
                    # Check if the error is about thinking not being supported
                    error_text = await response.text()
                    if "does not support thinking" in error_text:
                        yield {
                            "type": "info",
                            "content": f"Model {model} doesn't support thinking mode",
                        }
                        # Retry without thinking (without retry decorator)
                        async for chunk in self._generate_stream_no_retry(
                            model, prompt, system, think=False, timeout=timeout
                        ):
                            yield chunk
                        return
                    else:
                        logger.error(f"API error {response.status}: {error_text}")
                        yield {
                            "type": "error",
                            "content": f"API error {response.status}: {error_text}",
                        }
                else:
                    error_text = await response.text()
                    logger.error(f"API error {response.status}: {error_text}")
                    yield {"type": "error", "content": f"API error {response.status}: {error_text}"}

        except asyncio.CancelledError:
            yield {"type": "info", "content": "Request cancelled"}
            return
        except TimeoutError:
            logger.error(f"Request timeout after {timeout}s")
            yield {
                "type": "error",
                "content": f"Request timeout after {timeout}s - try increasing timeout in settings",
            }
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {str(e)}")
            # Re-raise to trigger retry decorator
            raise
        except Exception as e:
            logger.error(f"Unexpected error during generation: {str(e)}")
            yield {"type": "error", "content": f"Unexpected error: {str(e)}"}

    async def _generate_stream_no_retry(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
        think: bool = False,
        timeout: float = DEFAULT_RESPONSE_TIMEOUT,
    ) -> AsyncGenerator[dict[str, str], None]:
        """Internal method for generate_stream without retry decorator.

        Used when we need to call generate_stream recursively (e.g., retrying without thinking).
        """
        if not self._session:
            raise RuntimeError("Client must be used within async context manager")

        payload: dict[str, str | bool] = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "think": think,
        }

        if system and system.strip():
            payload["system"] = system.strip()

        try:
            async with self._session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                if response.status == 200:
                    try:
                        async for line in response.content:
                            if line:
                                try:
                                    chunk = json.loads(line.decode("utf-8"))

                                    # Yield thinking content if available
                                    if "thinking" in chunk and chunk["thinking"]:
                                        yield {"type": "thinking", "content": chunk["thinking"]}

                                    # Yield response content if available
                                    if "response" in chunk and chunk["response"]:
                                        yield {"type": "response", "content": chunk["response"]}

                                    if chunk.get("done", False):
                                        break
                                except json.JSONDecodeError:
                                    continue
                    except asyncio.CancelledError:
                        yield {"type": "info", "content": "Response cancelled by user"}
                        return
                else:
                    error_text = await response.text()
                    yield {"type": "error", "content": f"Error {response.status}: {error_text}"}

        except asyncio.CancelledError:
            yield {"type": "info", "content": "Request cancelled"}
            return
        except TimeoutError:
            yield {"type": "error", "content": f"Request timeout after {timeout}s"}
        except Exception as e:
            yield {"type": "error", "content": f"Connection error: {str(e)}"}
