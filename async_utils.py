#!/usr/bin/env python3
"""
Async utilities for running async code in Streamlit context
Fixes the event loop catastrophe by providing proper async execution
"""

import asyncio
from typing import TypeVar, Awaitable, Coroutine

T = TypeVar('T')


def run_async(coro: Awaitable[T]) -> T:
    """
    Properly run async code in Streamlit context.

    This function handles the complexity of running async code in Streamlit,
    which doesn't natively support async/await.

    Args:
        coro: The coroutine to execute

    Returns:
        The result of the coroutine

    Raises:
        RuntimeError: If called from within an already running event loop
    """
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()

        # Check if loop is running (should not happen in Streamlit)
        if loop.is_running():
            raise RuntimeError(
                "Cannot use run_async from within a running event loop. "
                "Use await instead."
            )

        # Run the coroutine in the existing loop
        return loop.run_until_complete(coro)

    except RuntimeError as e:
        # No event loop exists, create a new one
        if "no running event loop" in str(e).lower() or "no current event loop" in str(e).lower():
            return asyncio.run(coro)
        else:
            # Re-raise if it's a different RuntimeError
            raise


def create_task_and_run(coro: Coroutine) -> T:
    """
    Alternative method for running async code.
    Creates a task and runs it to completion.

    Args:
        coro: The coroutine to execute

    Returns:
        The result of the coroutine
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        task = loop.create_task(coro)
        result = loop.run_until_complete(task)

        # Give async cleanup a moment to complete
        loop.run_until_complete(asyncio.sleep(0.1))

        return result
    finally:
        # Properly close the loop
        try:
            # Cancel any remaining tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()

            # Wait for cancellations to complete
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

            # Close the loop
            loop.close()
        except Exception:
            # Ignore cleanup errors
            pass
