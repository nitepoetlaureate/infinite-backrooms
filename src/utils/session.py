"""Session management utilities for Streamlit application.

This module provides utilities for managing stateful resources across Streamlit reruns,
including cached OllamaClient instances for improved performance.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.services.ollama_client import OllamaClient
    import streamlit as st

logger = logging.getLogger(__name__)


async def get_ollama_client(session_state: "st.SessionStateProxy", base_url: str) -> "OllamaClient":
    """Get or create a cached OllamaClient instance.

    This function maintains a single OllamaClient instance in Streamlit session state,
    avoiding the performance overhead of creating new clients on every rerun.

    Args:
        session_state: Streamlit session state object
        base_url: Ollama server URL

    Returns:
        Cached or newly created OllamaClient instance

    Note:
        The client's async context manager (__aenter__) is called automatically
        when first created. The client persists across Streamlit reruns until
        manually cleared or the session ends.
    """
    from src.services.ollama_client import OllamaClient

    # Initialize client cache if not exists
    if "_ollama_client" not in session_state:
        session_state._ollama_client = None
        session_state._ollama_client_url = None

    # Create new client if needed or URL changed
    if session_state._ollama_client is None or session_state._ollama_client_url != base_url:
        # Clean up old client if exists
        if session_state._ollama_client is not None:
            try:
                await session_state._ollama_client.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error cleaning up old OllamaClient: {e}")

        # Create and initialize new client
        client = OllamaClient(base_url=base_url)
        await client.__aenter__()

        # Cache in session state
        session_state._ollama_client = client
        session_state._ollama_client_url = base_url
        logger.info(f"Created new cached OllamaClient for {base_url}")

    return session_state._ollama_client


async def cleanup_ollama_client(session_state: "st.SessionStateProxy") -> None:
    """Clean up cached OllamaClient instance.

    This should be called when changing Ollama URL or when explicitly
    needing to reset the connection.

    Args:
        session_state: Streamlit session state object
    """
    if "_ollama_client" in session_state and session_state._ollama_client is not None:
        try:
            await session_state._ollama_client.__aexit__(None, None, None)
            logger.info("Cleaned up cached OllamaClient")
        except Exception as e:
            logger.warning(f"Error cleaning up OllamaClient: {e}")
        finally:
            session_state._ollama_client = None
            session_state._ollama_client_url = None
