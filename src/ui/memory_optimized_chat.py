"""Memory-optimized chat interface with pagination and cleanup."""

from __future__ import annotations

import gc
import json
import logging
import psutil
import threading
import time
import weakref
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Set, Tuple
import uuid

import streamlit as st

from src.models.persona import AIPersona
from src.ui.components import get_persona_avatar, highlight_mentions, render_persona_header
from src.utils.performance import PerformanceTimer, get_metrics

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Lightweight message representation for memory optimization.

    Attributes:
        id: Unique message identifier
        role: Message role (user/assistant)
        content: Message content
        timestamp: Message timestamp
        persona_name: Name of the persona (for assistant messages)
        model: Model name (for assistant messages)
        thinking: Optional thinking content
        metadata: Additional metadata stored efficiently
    """
    id: str
    role: str
    content: str
    timestamp: datetime
    persona_name: str = ""
    model: str = ""
    thinking: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "persona_name": self.persona_name,
            "model": self.model,
            "thinking": self.thinking,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChatMessage:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            role=data["role"],
            content=data["content"],
            timestamp=data["timestamp"],
            persona_name=data.get("persona_name", ""),
            model=data.get("model", ""),
            thinking=data.get("thinking", ""),
            metadata=data.get("metadata", {})
        )


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    total_messages: int = 0
    archived_messages: int = 0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    last_cleanup: Optional[datetime] = None
    cleanup_count: int = 0


class MessageStorage(ABC):
    """Abstract base class for message storage implementations."""

    @abstractmethod
    def add_message(self, message: ChatMessage) -> None:
        """Add a message to storage."""
        pass

    @abstractmethod
    def get_messages(self, limit: Optional[int] = None, offset: int = 0) -> List[ChatMessage]:
        """Get messages with pagination."""
        pass

    @abstractmethod
    def count_messages(self) -> int:
        """Get total message count."""
        pass

    @abstractmethod
    def cleanup_old_messages(self, keep_count: int) -> int:
        """Clean up old messages, returning count removed."""
        pass


class InMemoryStorage(MessageStorage):
    """In-memory message storage with size limits."""

    def __init__(self, max_messages: int = 1000) -> None:
        """Initialize in-memory storage.

        Args:
            max_messages: Maximum number of messages to keep in memory
        """
        self.max_messages = max_messages
        self._messages: Deque[ChatMessage] = deque(maxlen=max_messages)
        self._lock = threading.RLock()

    def add_message(self, message: ChatMessage) -> None:
        """Add a message to storage."""
        with self._lock:
            self._messages.append(message)

    def get_messages(self, limit: Optional[int] = None, offset: int = 0) -> List[ChatMessage]:
        """Get messages with pagination."""
        with self._lock:
            messages = list(self._messages)
            if offset >= len(messages):
                return []

            end_idx = offset + (limit or len(messages))
            return messages[offset:end_idx]

    def count_messages(self) -> int:
        """Get total message count."""
        with self._lock:
            return len(self._messages)

    def cleanup_old_messages(self, keep_count: int) -> int:
        """Clean up old messages, returning count removed."""
        with self._lock:
            current_count = len(self._messages)
            if current_count <= keep_count:
                return 0

            remove_count = current_count - keep_count
            # Remove from the front (oldest messages)
            for _ in range(remove_count):
                if self._messages:
                    self._messages.popleft()

            return remove_count


class HybridStorage(MessageStorage):
    """Hybrid storage using memory + disk for large conversation histories."""

    def __init__(
        self,
        memory_limit: int = 500,
        archive_file: Optional[Path] = None,
        cleanup_threshold: int = 1000
    ) -> None:
        """Initialize hybrid storage.

        Args:
            memory_limit: Number of messages to keep in memory
            archive_file: Path to archive file for old messages
            cleanup_threshold: Total message count that triggers cleanup
        """
        self.memory_limit = memory_limit
        self.cleanup_threshold = cleanup_threshold

        if archive_file is None:
            archive_file = Path("data/chat_archive.json")

        self.archive_file = archive_file
        self.archive_file.parent.mkdir(parents=True, exist_ok=True)

        self._memory_storage = InMemoryStorage(memory_limit)
        self._archived_count = 0
        self._lock = threading.RLock()

    def add_message(self, message: ChatMessage) -> None:
        """Add a message, triggering cleanup if needed."""
        with self._lock:
            # Check if we need to cleanup
            total_count = self._memory_storage.count_messages() + self._archived_count
            if total_count >= self.cleanup_threshold:
                self._perform_cleanup()

            # Add new message
            self._memory_storage.add_message(message)

    def get_messages(self, limit: Optional[int] = None, offset: int = 0) -> List[ChatMessage]:
        """Get messages from memory (archived messages not returned by default)."""
        return self._memory_storage.get_messages(limit, offset)

    def get_all_messages(self, limit: Optional[int] = None, offset: int = 0) -> List[ChatMessage]:
        """Get all messages including archived ones (for export)."""
        with self._lock:
            messages = []

            # Load archived messages if needed
            if self._archived_count > 0 and self.archive_file.exists():
                try:
                    with open(self.archive_file, 'r', encoding='utf-8') as f:
                        archived_data = json.load(f)
                        for msg_data in archived_data.get('messages', []):
                            messages.append(ChatMessage.from_dict(msg_data))
                except Exception as e:
                    logger.error(f"Failed to load archived messages: {e}")

            # Add memory messages
            memory_messages = self._memory_storage.get_messages()
            messages.extend(memory_messages)

            # Apply pagination
            if offset >= len(messages):
                return []

            end_idx = offset + (limit or len(messages))
            return messages[offset:end_idx]

    def count_messages(self) -> int:
        """Get total message count including archived."""
        with self._lock:
            return self._memory_storage.count_messages() + self._archived_count

    def cleanup_old_messages(self, keep_count: int) -> int:
        """Clean up old messages."""
        with self._lock:
            return self._perform_cleanup()

    def _perform_cleanup(self) -> int:
        """Perform cleanup of old messages to archive."""
        current_messages = self._memory_storage.get_messages()

        if len(current_messages) <= self.memory_limit // 2:
            return 0

        # Move oldest messages to archive
        messages_to_archive = current_messages[:len(current_messages) // 2]
        archive_data = []

        for msg in messages_to_archive:
            archive_data.append(msg.to_dict())

        # Load existing archive
        existing_archive = []
        if self.archive_file.exists():
            try:
                with open(self.archive_file, 'r', encoding='utf-8') as f:
                    existing_archive = json.load(f).get('messages', [])
            except Exception as e:
                logger.error(f"Failed to load existing archive: {e}")

        # Combine and save
        combined_archive = existing_archive + archive_data

        try:
            with open(self.archive_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'archived_at': datetime.now().isoformat(),
                    'messages': combined_archive
                }, f, ensure_ascii=False, indent=2, default=str)

            # Update counts
            archived_count = len(messages_to_archive)
            self._archived_count += archived_count

            # Remove archived messages from memory storage
            self._memory_storage.cleanup_old_messages(self.memory_limit // 2)

            logger.info(f"Archived {archived_count} messages, total archived: {self._archived_count}")
            return archived_count

        except Exception as e:
            logger.error(f"Failed to archive messages: {e}")
            return 0


class MemoryMonitor:
    """Monitor memory usage and trigger cleanup operations."""

    def __init__(self, memory_threshold_mb: float = 500.0) -> None:
        """Initialize memory monitor.

        Args:
            memory_threshold_mb: Memory threshold in MB to trigger cleanup
        """
        self.memory_threshold_mb = memory_threshold_mb
        self.process = psutil.Process()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None

    def start_monitoring(self) -> None:
        """Start background memory monitoring."""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop background memory monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)

    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self._monitoring:
            try:
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024

                if memory_mb > self.memory_threshold_mb:
                    logger.warning(f"High memory usage detected: {memory_mb:.1f} MB")
                    # Trigger garbage collection
                    gc.collect()

                time.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                time.sleep(60)

    def get_memory_usage(self) -> Tuple[float, float]:
        """Get current memory usage in MB and CPU usage percentage.

        Returns:
            Tuple of (memory_mb, cpu_percent)
        """
        try:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            cpu_percent = self.process.cpu_percent()
            return memory_mb, cpu_percent
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return 0.0, 0.0


class MemoryOptimizedChat:
    """Memory-optimized chat interface with pagination and automatic cleanup."""

    def __init__(
        self,
        storage: Optional[MessageStorage] = None,
        messages_per_page: int = 50,
        cleanup_threshold: int = 1000,
        auto_cleanup: bool = True
    ) -> None:
        """Initialize memory-optimized chat.

        Args:
            storage: Message storage implementation
            messages_per_page: Number of messages to display per page
            cleanup_threshold: Message count that triggers cleanup
            auto_cleanup: Whether to automatically cleanup old messages
        """
        self.storage = storage or HybridStorage()
        self.messages_per_page = messages_per_page
        self.cleanup_threshold = cleanup_threshold
        self.auto_cleanup = auto_cleanup

        self.memory_monitor = MemoryMonitor()
        self.stats = MemoryStats()

        # Initialize session state for pagination
        if "chat_page" not in st.session_state:
            st.session_state.chat_page = 1
        if "total_chat_pages" not in st.session_state:
            st.session_state.total_chat_pages = 1

    def start_monitoring(self) -> None:
        """Start memory monitoring."""
        self.memory_monitor.start_monitoring()

    def stop_monitoring(self) -> None:
        """Stop memory monitoring."""
        self.memory_monitor.stop_monitoring()

    def add_message(
        self,
        role: str,
        content: str,
        persona_name: str = "",
        model: str = "",
        thinking: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a new message to the chat.

        Args:
            role: Message role (user/assistant)
            content: Message content
            persona_name: Name of the persona (for assistant messages)
            model: Model name (for assistant messages)
            thinking: Optional thinking content
            metadata: Additional metadata

        Returns:
            Message ID
        """
        message_id = str(uuid.uuid4())
        message = ChatMessage(
            id=message_id,
            role=role,
            content=content,
            timestamp=datetime.now(),
            persona_name=persona_name,
            model=model,
            thinking=thinking,
            metadata=metadata or {}
        )

        with PerformanceTimer("add_message"):
            self.storage.add_message(message)

            # Trigger auto cleanup if enabled
            if self.auto_cleanup:
                total_count = self.storage.count_messages()
                if total_count >= self.cleanup_threshold:
                    self.perform_cleanup()

            # Update pagination
            self._update_pagination()

        return message_id

    def get_messages_page(self, page: int = 1) -> List[ChatMessage]:
        """Get messages for a specific page.

        Args:
            page: Page number (1-based)

        Returns:
            List of messages for the page
        """
        if page < 1:
            page = 1

        offset = (page - 1) * self.messages_per_page
        return self.storage.get_messages(limit=self.messages_per_page, offset=offset)

    def _update_pagination(self) -> None:
        """Update pagination state."""
        total_messages = self.storage.count_messages()
        st.session_state.total_chat_pages = max(1,
            (total_messages + self.messages_per_page - 1) // self.messages_per_page)

        # Adjust current page if needed
        if st.session_state.chat_page > st.session_state.total_chat_pages:
            st.session_state.chat_page = st.session_state.total_chat_pages

    def render_chat_interface(self, personas: List[AIPersona]) -> None:
        """Render the memory-optimized chat interface.

        Args:
            personas: List of available personas for highlighting
        """
        # Update stats
        self._update_stats()

        # Display memory stats
        self._render_memory_stats()

        # Pagination controls
        self._render_pagination_controls()

        # Get current page messages
        current_page = st.session_state.chat_page
        messages = self.get_messages_page(current_page)

        # Display messages
        if messages:
            for message in messages:
                self._render_message(message, personas)
        else:
            st.info("No messages yet. Start a conversation!")

    def _render_memory_stats(self) -> None:
        """Render memory usage statistics."""
        memory_mb, cpu_percent = self.memory_monitor.get_memory_usage()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Messages", self.stats.total_messages)

        with col2:
            st.metric("Archived", self.stats.archived_messages)

        with col3:
            st.metric("Memory (MB)", f"{memory_mb:.1f}")

        with col4:
            st.metric("CPU (%)", f"{cpu_percent:.1f}")

        # Memory usage warning
        if memory_mb > 400:  # Warning threshold
            st.warning(f"⚠️ High memory usage: {memory_mb:.1f} MB")

        if memory_mb > 600:  # Critical threshold
            st.error(f"🚨 Critical memory usage: {memory_mb:.1f} MB. Consider manual cleanup.")

    def _render_pagination_controls(self) -> None:
        """Render pagination controls."""
        total_pages = st.session_state.total_chat_pages
        current_page = st.session_state.chat_page

        if total_pages <= 1:
            return

        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

        with col1:
            if st.button("⬅️ Previous", disabled=current_page <= 1):
                st.session_state.chat_page = max(1, current_page - 1)
                st.rerun()

        with col2:
            if st.button("Next ➡️", disabled=current_page >= total_pages):
                st.session_state.chat_page = min(total_pages, current_page + 1)
                st.rerun()

        with col3:
            page_numbers = list(range(1, min(total_pages + 1, 11)))
            if total_pages > 10:
                page_numbers.extend([total_pages])

            selected_page = st.selectbox(
                "Page",
                options=page_numbers,
                index=current_page - 1,
                format_func=lambda x: f"Page {x}"
            )

            if selected_page != current_page:
                st.session_state.chat_page = selected_page
                st.rerun()

        with col4:
            st.write(f"of {total_pages}")

        with col5:
            if st.button("🗑️ Clear All"):
                self.clear_all_messages()
                st.rerun()

    def _render_message(self, message: ChatMessage, personas: List[AIPersona]) -> None:
        """Render a single message.

        Args:
            message: Message to render
            personas: List of personas for highlighting
        """
        # Find persona for assistant messages
        persona = None
        if message.role == "assistant" and message.persona_name:
            for p in personas:
                if p.name == message.persona_name:
                    persona = p
                    break

        if message.role == "user":
            with st.chat_message("user"):
                st.write(message.content)
                st.caption(f"🕒 {message.timestamp.strftime('%H:%M:%S')}")
        else:
            avatar = get_persona_avatar(persona)

            with st.chat_message("assistant", avatar=avatar):
                # Show persona header
                if persona:
                    render_persona_header(persona)
                else:
                    st.write(message.persona_name)

                # Show thinking if available
                if message.thinking and message.thinking.strip():
                    with st.expander("🧠 AI's Thinking Process", expanded=False):
                        st.code(message.thinking, language="text", wrap_lines=True)

                # Show message content with @mention highlighting
                content = message.content
                content_with_highlights = highlight_mentions(content, personas)

                if "@" in content and content != content_with_highlights:
                    st.markdown(content_with_highlights, unsafe_allow_html=True)
                else:
                    st.write(message.content)

                # Show timestamp and model
                st.caption(
                    f"🕒 {message.timestamp.strftime('%H:%M:%S')} • 🤖 {message.model}"
                )

    def perform_cleanup(self, keep_count: Optional[int] = None) -> int:
        """Perform cleanup of old messages.

        Args:
            keep_count: Number of messages to keep (uses default if None)

        Returns:
            Number of messages removed
        """
        if keep_count is None:
            keep_count = self.cleanup_threshold // 2

        with PerformanceTimer("cleanup_messages"):
            removed_count = self.storage.cleanup_old_messages(keep_count)

            if removed_count > 0:
                self.stats.cleanup_count += 1
                self.stats.last_cleanup = datetime.now()

                # Force garbage collection
                gc.collect()

                st.success(f"🧹 Cleaned up {removed_count} old messages")
                logger.info(f"Cleanup completed: {removed_count} messages removed")

            return removed_count

    def clear_all_messages(self) -> None:
        """Clear all messages from storage."""
        if hasattr(self.storage, '_memory_storage'):
            self.storage._memory_storage._messages.clear()

        if hasattr(self.storage, '_archived_count'):
            self.storage._archived_count = 0

        # Clear archive file if exists
        if hasattr(self.storage, 'archive_file') and self.storage.archive_file.exists():
            try:
                self.storage.archive_file.unlink()
            except Exception as e:
                logger.error(f"Failed to delete archive file: {e}")

        # Reset pagination
        st.session_state.chat_page = 1
        st.session_state.total_chat_pages = 1

        # Force garbage collection
        gc.collect()

        st.success("🗑️ All messages cleared")

    def export_messages(self) -> List[Dict[str, Any]]:
        """Export all messages including archived ones.

        Returns:
            List of message dictionaries
        """
        if hasattr(self.storage, 'get_all_messages'):
            messages = self.storage.get_all_messages()
        else:
            messages = self.storage.get_messages()

        return [msg.to_dict() for msg in messages]

    def get_stats(self) -> MemoryStats:
        """Get current memory statistics.

        Returns:
            MemoryStats object
        """
        self._update_stats()
        return self.stats

    def _update_stats(self) -> None:
        """Update internal statistics."""
        memory_mb, cpu_percent = self.memory_monitor.get_memory_usage()

        self.stats.total_messages = self.storage.count_messages()
        self.stats.memory_usage_mb = memory_mb
        self.stats.cpu_usage_percent = cpu_percent

        if hasattr(self.storage, '_archived_count'):
            self.stats.archived_messages = self.storage._archived_count

    def __del__(self) -> None:
        """Cleanup when object is destroyed."""
        try:
            self.stop_monitoring()
        except Exception:
            pass


# Factory functions for different storage strategies
def create_memory_optimized_chat(
    strategy: str = "hybrid",
    **kwargs: Any
) -> MemoryOptimizedChat:
    """Create a memory-optimized chat with specified strategy.

    Args:
        strategy: Storage strategy ("memory" or "hybrid")
        **kwargs: Additional arguments for chat initialization

    Returns:
        MemoryOptimizedChat instance
    """
    if strategy == "memory":
        storage = InMemoryStorage(kwargs.get("max_messages", 1000))
    elif strategy == "hybrid":
        storage = HybridStorage(
            memory_limit=kwargs.get("memory_limit", 500),
            archive_file=kwargs.get("archive_file"),
            cleanup_threshold=kwargs.get("cleanup_threshold", 1000)
        )
    else:
        raise ValueError(f"Unknown storage strategy: {strategy}")

    return MemoryOptimizedChat(storage=storage, **kwargs)