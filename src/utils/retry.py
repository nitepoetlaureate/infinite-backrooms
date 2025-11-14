"""Retry utility with exponential backoff for handling transient failures."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

import aiohttp

logger = logging.getLogger(__name__)

T = TypeVar("T")


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (
        aiohttp.ClientError,
        asyncio.TimeoutError,
        ConnectionError,
    ),
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator for retrying async functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds between retries (default: 1.0)
        max_delay: Maximum delay in seconds between retries (default: 10.0)
        exponential_base: Base for exponential backoff calculation (default: 2.0)
        exceptions: Tuple of exception types to catch and retry (default: network errors)

    Returns:
        Decorated function that retries on specified exceptions

    Example:
        @async_retry(max_attempts=5, base_delay=2.0)
        async def fetch_data():
            # Function that might fail with network errors
            pass
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    # Don't retry on the last attempt
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {str(e)}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base**attempt), max_delay)

                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1}/{max_attempts} failed: {str(e)}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    await asyncio.sleep(delay)

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError(f"{func.__name__} failed without raising an exception")

        return wrapper

    return decorator


def async_retry_generator(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (
        aiohttp.ClientError,
        asyncio.TimeoutError,
        ConnectionError,
    ),
) -> Callable[
    [Callable[..., Any]],
    Callable[..., Any],
]:
    """Decorator for retrying async generator functions with exponential backoff.

    This is specifically designed for streaming functions that yield results.
    If an exception occurs during iteration, the entire generator is retried.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds between retries (default: 1.0)
        max_delay: Maximum delay in seconds between retries (default: 10.0)
        exponential_base: Base for exponential backoff calculation (default: 2.0)
        exceptions: Tuple of exception types to catch and retry (default: network errors)

    Returns:
        Decorated generator function that retries on specified exceptions

    Example:
        @async_retry_generator(max_attempts=5)
        async def stream_data():
            async for chunk in source:
                yield chunk
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_attempts):
                try:
                    async for item in func(*args, **kwargs):
                        yield item
                    return  # Successfully completed
                except exceptions as e:
                    # Don't retry on the last attempt
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {str(e)}"
                        )
                        # Yield error information instead of raising
                        yield {
                            "type": "error",
                            "content": f"Failed after {max_attempts} retry attempts: {str(e)}",
                        }
                        return

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base**attempt), max_delay)

                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1}/{max_attempts} failed: {str(e)}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    # Yield retry info
                    yield {
                        "type": "info",
                        "content": f"Connection issue detected. Retrying in {delay:.1f}s... (attempt {attempt + 1}/{max_attempts})",
                    }

                    await asyncio.sleep(delay)

        return wrapper

    return decorator
