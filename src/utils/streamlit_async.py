"""Streamlit-safe async execution utilities.

This module provides utilities for executing async operations in Streamlit
without causing event loop conflicts or corruption.
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Coroutine, TypeVar, Generator
from functools import wraps

import streamlit as st

logger = logging.getLogger(__name__)

T = TypeVar('T')


def safe_async_call(coro: Coroutine) -> Any:
    """Execute async coroutine with proper error handling for Streamlit.

    Attempts to use asyncio.run() first, falls back to thread-based
    execution if event loop issues occur.

    Args:
        coro: Async coroutine to execute

    Returns:
        Result of coroutine execution

    Raises:
        Exception: Re-raises any exception except event loop errors

    Example:
        client = get_ollama_client()
        result = safe_async_call(client.test_connection())
    """
    try:
        # Try standard asyncio.run first (preferred approach)
        return asyncio.run(coro)

    except RuntimeError as e:
        error_msg = str(e).lower()

        # Check for event loop errors
        if "event loop is closed" in error_msg or \
           "this event loop is already running" in error_msg:

            logger.debug(
                "Event loop conflict detected, using thread-based execution"
            )
            return _run_async_in_thread(coro)

        # Re-raise other runtime errors
        raise

    except Exception:
        # Re-raise all other exceptions
        raise


def _run_async_in_thread(coro: Coroutine) -> Any:
    """Run async coroutine in separate thread with new event loop.

    This is a fallback for edge cases where Streamlit's event loop
    conflicts with asyncio.run(). Should rarely be needed.

    Args:
        coro: Async coroutine to execute

    Returns:
        Result of coroutine execution
    """
    def run_in_new_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_in_new_loop)
        return future.result()


def streamlit_singleton_resource(resource_factory, resource_name: str = None):
    """Create a Streamlit singleton resource that persists across reruns.

    Args:
        resource_factory: Function that creates the resource
        resource_name: Optional name for the resource key

    Returns:
        Cached resource instance

    Example:
        @streamlit_singleton_resource
        def get_ollama_client():
            return OllamaClient()
    """
    if resource_name is None:
        resource_name = resource_factory.__name__

    # Use Streamlit's experimental_singleton if available (Streamlit 1.27+)
    try:
        # Check if st.experimental_singleton exists
        if hasattr(st, 'experimental_singleton'):
            return st.experimental_singleton(resource_factory)
    except Exception:
        # Fallback to session state caching
        pass

    # Manual session state caching
    cache_key = f"singleton_{resource_name}"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = resource_factory()

    return st.session_state[cache_key]


class AsyncStreamProcessor:
    """Helper class for processing async streams in Streamlit context."""

    def __init__(self, async_generator, batch_size: int = 10):
        """Initialize stream processor.

        Args:
            async_generator: Async generator to process
            batch_size: Number of items to collect per batch
        """
        self.async_generator = async_generator
        self.batch_size = batch_size

    def collect_and_yield(self) -> Generator[Any, None, None]:
        """Collect all async generator results and yield them synchronously.

        Yields:
            Items from the async generator
        """
        async def _collect_all():
            results = []
            try:
                async for item in self.async_generator:
                    results.append(item)
            except Exception as e:
                logger.error(f"Error in async stream: {e}")
                results.append({"type": "error", "content": str(e)})
            return results

        try:
            # Try to collect all results
            results = safe_async_call(_collect_all())
            for result in results:
                yield result
        except Exception as e:
            logger.error(f"Failed to process async stream: {e}")
            yield {"type": "error", "content": str(e)}


def safe_stream_wrapper(async_stream_generator):
    """Decorator to make async generators safe for use in Streamlit.

    Args:
        async_stream_generator: Async generator function

    Returns:
        Synchronous generator function

    Example:
        @safe_stream_wrapper
        async def my_async_stream(data):
            for item in data:
                yield await process_async(item)
    """
    @wraps(async_stream_generator)
    def wrapper(*args, **kwargs):
        # Create async generator
        async_gen = async_stream_generator(*args, **kwargs)

        # Process safely and yield results
        processor = AsyncStreamProcessor(async_gen)
        yield from processor.collect_and_yield()

    return wrapper


# Streamlit-specific singleton resource management
def get_streamlit_cached_client(client_factory, client_name: str = "ollama_client"):
    """Get or create a cached Ollama client for Streamlit.

    Args:
        client_factory: Function to create the client
        client_name: Name for caching

    Returns:
        Cached OllamaClient instance
    """
    return streamlit_singleton_resource(client_factory, client_name)


# Error handling utilities
def handle_streamlit_async_error(error: Exception, context: str = "async operation") -> str:
    """Convert async errors to user-friendly messages.

    Args:
        error: Exception that occurred
        context: Context where error occurred

    Returns:
        User-friendly error message
    """
    error_msg = str(error).lower()

    if "event loop is closed" in error_msg:
        return f"Event loop error in {context}. Please try again."
    elif "connection" in error_msg:
        return f"Connection error in {context}. Please check Ollama service."
    elif "timeout" in error_msg:
        return f"Timeout in {context}. Please try again."
    else:
        return f"Error in {context}: {str(error)}"