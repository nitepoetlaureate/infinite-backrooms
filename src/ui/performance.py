"""Performance optimization utilities for Streamlit UI."""

from typing import Any
import streamlit as st

from src.utils.constants import ROLE_EMOJI_MAP, ROLE_TEMPLATES
from src.models.persona import AIPersona


@st.cache_data
def get_role_emoji_map() -> dict[str, str]:
    """Get cached role emoji mapping.

    Returns:
        Dictionary mapping role names to emoji strings
    """
    return ROLE_EMOJI_MAP.copy()


@st.cache_data
def get_role_templates() -> dict[str, str]:
    """Get cached role templates.

    Returns:
        Dictionary mapping role names to template strings
    """
    return ROLE_TEMPLATES.copy()


@st.cache_data
def get_available_roles() -> list[str]:
    """Get list of available role names (cached).

    Returns:
        List of role names
    """
    return list(ROLE_TEMPLATES.keys())


def create_persona_lookup(personas: list[AIPersona]) -> dict[str, AIPersona]:
    """Create efficient lookup dictionary for personas by name.

    Args:
        personas: List of AIPersona objects

    Returns:
        Dictionary mapping persona names to AIPersona objects

    Example:
        >>> personas = [persona1, persona2, persona3]
        >>> lookup = create_persona_lookup(personas)
        >>> persona = lookup.get("Alice")
    """
    return {p.name: p for p in personas}


class PaginationHelper:
    """Helper for paginating long lists of messages."""

    def __init__(self, items_per_page: int = 50):
        """Initialize pagination helper.

        Args:
            items_per_page: Number of items to show per page
        """
        self.items_per_page = items_per_page

    def get_current_page(self, key: str = "page") -> int:
        """Get current page number from session state.

        Args:
            key: Session state key for page number

        Returns:
            Current page number (0-indexed)
        """
        if key not in st.session_state:
            st.session_state[key] = 0
        return st.session_state[key]

    def set_page(self, page: int, key: str = "page") -> None:
        """Set current page number in session state.

        Args:
            page: Page number to set (0-indexed)
            key: Session state key for page number
        """
        st.session_state[key] = page

    def get_page_slice(
        self, items: list[Any], page: int | None = None, key: str = "page"
    ) -> tuple[list[Any], int, int]:
        """Get slice of items for current page.

        Args:
            items: List of items to paginate
            page: Optional page number (uses session state if None)
            key: Session state key for page number

        Returns:
            Tuple of (items_slice, start_index, end_index)

        Example:
            >>> helper = PaginationHelper(items_per_page=50)
            >>> messages_slice, start, end = helper.get_page_slice(messages)
        """
        if page is None:
            page = self.get_current_page(key)

        total_items = len(items)
        start_idx = page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, total_items)

        return items[start_idx:end_idx], start_idx, end_idx

    def get_total_pages(self, items: list[Any]) -> int:
        """Get total number of pages for items.

        Args:
            items: List of items

        Returns:
            Total number of pages
        """
        if not items:
            return 0
        return (len(items) + self.items_per_page - 1) // self.items_per_page

    def show_pagination_controls(
        self, items: list[Any], key: str = "page", container: Any = st
    ) -> None:
        """Show pagination navigation controls.

        Args:
            items: List of items being paginated
            key: Session state key for page number
            container: Streamlit container to render in (default: st)

        Example:
            >>> helper = PaginationHelper()
            >>> helper.show_pagination_controls(messages)
        """
        current_page = self.get_current_page(key)
        total_pages = self.get_total_pages(items)

        if total_pages <= 1:
            return  # No pagination needed

        col1, col2, col3 = container.columns([1, 2, 1])

        with col1:
            if current_page > 0:
                if container.button("⬅️ Previous", key=f"{key}_prev"):
                    self.set_page(current_page - 1, key)
                    st.rerun()

        with col2:
            container.markdown(
                f"<div style='text-align: center;'>Page {current_page + 1} of {total_pages}</div>",
                unsafe_allow_html=True,
            )

        with col3:
            if current_page < total_pages - 1:
                if container.button("Next ➡️", key=f"{key}_next"):
                    self.set_page(current_page + 1, key)
                    st.rerun()


class BatchStateUpdate:
    """Context manager for batching state updates to minimize reruns.

    Example:
        >>> with BatchStateUpdate() as batch:
        ...     batch.update("key1", value1)
        ...     batch.update("key2", value2)
        ...     batch.update("key3", value3)
        ...     # Single rerun happens here if any updates were made
    """

    def __init__(self):
        """Initialize batch update context."""
        self.updates = {}
        self.needs_rerun = False

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and apply updates."""
        if self.needs_rerun:
            # Apply all updates
            for key, value in self.updates.items():
                st.session_state[key] = value
            # Single rerun
            st.rerun()

    def update(self, key: str, value: Any) -> None:
        """Add an update to the batch.

        Args:
            key: Session state key
            value: Value to set
        """
        if key not in st.session_state or st.session_state[key] != value:
            self.updates[key] = value
            self.needs_rerun = True


def optimize_rerun() -> dict[str, Any]:
    """Context for optimizing multiple state changes.

    Returns:
        Dictionary to track state changes

    Example:
        >>> changes = optimize_rerun()
        >>> changes["personas"] = new_personas
        >>> changes["messages"] = new_messages
        >>> if changes:
        ...     apply_changes(changes)
        ...     st.rerun()
    """
    return {}


@st.cache_data(ttl=60)
def get_cached_stats(total_messages: int, total_personas: int) -> dict[str, int]:
    """Get cached conversation statistics.

    Args:
        total_messages: Total number of messages
        total_personas: Total number of personas

    Returns:
        Dictionary with statistics

    Note:
        TTL of 60 seconds to balance freshness and performance
    """
    return {
        "messages": total_messages,
        "personas": total_personas,
        "avg_messages_per_persona": total_messages // total_personas
        if total_personas > 0
        else 0,
    }


def lazy_load_messages(
    messages: list[Any], threshold: int = 100, recent_count: int = 50
) -> list[Any]:
    """Lazy load messages for better performance with long conversations.

    Args:
        messages: Full list of messages
        threshold: Only lazy load if message count exceeds this
        recent_count: Number of recent messages to show

    Returns:
        Filtered list of messages

    Example:
        >>> messages_to_display = lazy_load_messages(all_messages)
    """
    if len(messages) <= threshold:
        return messages

    # Show only most recent messages
    return messages[-recent_count:]
