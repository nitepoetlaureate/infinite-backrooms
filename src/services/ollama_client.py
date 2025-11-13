"""Ollama API client with proper async resource management."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

import aiohttp

from src.utils.constants import DEFAULT_OLLAMA_URL, DEFAULT_RESPONSE_TIMEOUT


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

    def __init__(self, base_url: str = DEFAULT_OLLAMA_URL) -> None:
        """Initialize Ollama client.

        Args:
            base_url: Base URL for Ollama API (default: http://localhost:11434)
        """
        self.base_url = base_url
        self._session: aiohttp.ClientSession | None = None
        self._connector: aiohttp.TCPConnector | None = None

    async def __aenter__(self) -> OllamaClient:
        """Enter async context manager - create session and connector."""
        self._connector = aiohttp.TCPConnector(
            limit=10, ttl_dns_cache=300, force_close=True, enable_cleanup_closed=True
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
        await asyncio.sleep(0.250)

    async def test_connection(self) -> tuple[bool, list[str]]:
        """Test if Ollama API is accessible and return available models.

        Returns:
            Tuple of (success: bool, models: list of model names)
        """
        if not self._session:
            raise RuntimeError("Client must be used within async context manager")

        try:
            async with self._session.get(
                f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    models = [model["name"] for model in result.get("models", [])]
                    return True, models
                else:
                    return False, []
        except Exception:
            return False, []

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
        think: bool = True,
        timeout: int = DEFAULT_RESPONSE_TIMEOUT,
    ) -> AsyncGenerator[dict[str, str], None]:
        """Generate streaming response from Ollama model.

        Args:
            model: Model name to use
            prompt: User prompt
            system: Optional system prompt
            think: Enable thinking mode (if supported by model)
            timeout: Request timeout in seconds

        Yields:
            Chunks as dict with keys: type ("thinking", "response", "error", "info"), content
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

                elif response.status == 400 and think:
                    # Check if the error is about thinking not being supported
                    error_text = await response.text()
                    if "does not support thinking" in error_text:
                        yield {
                            "type": "info",
                            "content": f"Model {model} doesn't support thinking mode",
                        }
                        # Retry without thinking
                        async for chunk in self.generate_stream(
                            model, prompt, system, think=False, timeout=timeout
                        ):
                            yield chunk
                        return
                    else:
                        yield {"type": "error", "content": f"Error {response.status}: {error_text}"}
                else:
                    error_text = await response.text()
                    yield {"type": "error", "content": f"Error {response.status}: {error_text}"}

        except asyncio.CancelledError:
            yield {"type": "info", "content": "Request cancelled"}
            return
        except asyncio.TimeoutError:
            yield {"type": "error", "content": "Request timeout"}
        except Exception as e:
            yield {"type": "error", "content": f"Connection error: {str(e)}"}
