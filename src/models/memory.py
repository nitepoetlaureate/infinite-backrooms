"""Memory management models and data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid


@dataclass
class MemoryConfig:
    """Configuration for memory management."""

    max_messages_memory: int = 500
    max_messages_total: int = 1000
    cleanup_threshold: int = 1000
    messages_per_page: int = 50
    archive_enabled: bool = True
    auto_cleanup: bool = True
    memory_threshold_mb: float = 500.0
    monitoring_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'max_messages_memory': self.max_messages_memory,
            'max_messages_total': self.max_messages_total,
            'cleanup_threshold': self.cleanup_threshold,
            'messages_per_page': self.messages_per_page,
            'archive_enabled': self.archive_enabled,
            'auto_cleanup': self.auto_cleanup,
            'memory_threshold_mb': self.memory_threshold_mb,
            'monitoring_enabled': self.monitoring_enabled
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MemoryConfig:
        """Create from dictionary."""
        return cls(
            max_messages_memory=data.get('max_messages_memory', 500),
            max_messages_total=data.get('max_messages_total', 1000),
            cleanup_threshold=data.get('cleanup_threshold', 1000),
            messages_per_page=data.get('messages_per_page', 50),
            archive_enabled=data.get('archive_enabled', True),
            auto_cleanup=data.get('auto_cleanup', True),
            memory_threshold_mb=data.get('memory_threshold_mb', 500.0),
            monitoring_enabled=data.get('monitoring_enabled', True)
        )


@dataclass
class MemorySnapshot:
    """Snapshot of memory usage at a point in time."""

    timestamp: datetime
    total_messages: int
    archived_messages: int
    memory_usage_mb: float
    cpu_usage_percent: float
    cleanup_count: int
    session_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_messages': self.total_messages,
            'archived_messages': self.archived_messages,
            'memory_usage_mb': self.memory_usage_mb,
            'cpu_usage_percent': self.cpu_usage_percent,
            'cleanup_count': self.cleanup_count,
            'session_id': self.session_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MemorySnapshot:
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            total_messages=data['total_messages'],
            archived_messages=data['archived_messages'],
            memory_usage_mb=data['memory_usage_mb'],
            cpu_usage_percent=data['cpu_usage_percent'],
            cleanup_count=data['cleanup_count'],
            session_id=data.get('session_id', '')
        )


@dataclass
class MemoryReport:
    """Comprehensive memory usage report."""

    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    total_messages_sent: int
    total_archived: int
    peak_memory_mb: float
    average_memory_mb: float
    total_cleanups: int
    snapshots: List[MemorySnapshot] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_messages_sent': self.total_messages_sent,
            'total_archived': self.total_archived,
            'peak_memory_mb': self.peak_memory_mb,
            'average_memory_mb': self.average_memory_mb,
            'total_cleanups': self.total_cleanups,
            'snapshots': [s.to_dict() for s in self.snapshots]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MemoryReport:
        """Create from dictionary."""
        return cls(
            session_id=data['session_id'],
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
            total_messages_sent=data['total_messages_sent'],
            total_archived=data['total_archived'],
            peak_memory_mb=data['peak_memory_mb'],
            average_memory_mb=data['average_memory_mb'],
            total_cleanups=data['total_cleanups'],
            snapshots=[MemorySnapshot.from_dict(s) for s in data.get('snapshots', [])]
        )


@dataclass
class SessionMetrics:
    """Session-level metrics tracking."""

    session_id: str
    start_time: datetime
    last_activity: datetime
    message_count: int = 0
    user_message_count: int = 0
    assistant_message_count: int = 0
    total_response_time: float = 0.0
    average_response_time: float = 0.0
    errors_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'message_count': self.message_count,
            'user_message_count': self.user_message_count,
            'assistant_message_count': self.assistant_message_count,
            'total_response_time': self.total_response_time,
            'average_response_time': self.average_response_time,
            'errors_count': self.errors_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SessionMetrics:
        """Create from dictionary."""
        return cls(
            session_id=data['session_id'],
            start_time=datetime.fromisoformat(data['start_time']),
            last_activity=datetime.fromisoformat(data['last_activity']),
            message_count=data.get('message_count', 0),
            user_message_count=data.get('user_message_count', 0),
            assistant_message_count=data.get('assistant_message_count', 0),
            total_response_time=data.get('total_response_time', 0.0),
            average_response_time=data.get('average_response_time', 0.0),
            errors_count=data.get('errors_count', 0)
        )

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now()

    def add_message(self, role: str, response_time: Optional[float] = None) -> None:
        """Record a new message."""
        self.message_count += 1
        self.update_activity()

        if role == "user":
            self.user_message_count += 1
        elif role == "assistant":
            self.assistant_message_count += 1
            if response_time is not None:
                self.total_response_time += response_time
                self.average_response_time = self.total_response_time / self.assistant_message_count

    def add_error(self) -> None:
        """Record an error."""
        self.errors_count += 1
        self.update_activity()


# Utility functions for memory management
def create_memory_config(
    max_messages_memory: int = 500,
    max_messages_total: int = 1000,
    cleanup_threshold: int = 1000,
    messages_per_page: int = 50,
    archive_enabled: bool = True,
    auto_cleanup: bool = True,
    memory_threshold_mb: float = 500.0
) -> MemoryConfig:
    """Create a memory configuration with sensible defaults.

    Args:
        max_messages_memory: Maximum messages to keep in memory
        max_messages_total: Maximum total messages before cleanup
        cleanup_threshold: Message count that triggers cleanup
        messages_per_page: Messages to display per page
        archive_enabled: Whether to archive old messages
        auto_cleanup: Whether to automatically cleanup
        memory_threshold_mb: Memory threshold in MB

    Returns:
        MemoryConfig instance
    """
    return MemoryConfig(
        max_messages_memory=max_messages_memory,
        max_messages_total=max_messages_total,
        cleanup_threshold=cleanup_threshold,
        messages_per_page=messages_per_page,
        archive_enabled=archive_enabled,
        auto_cleanup=auto_cleanup,
        memory_threshold_mb=memory_threshold_mb
    )


def create_session_metrics(session_id: Optional[str] = None) -> SessionMetrics:
    """Create session metrics tracking.

    Args:
        session_id: Optional session ID (generated if not provided)

    Returns:
        SessionMetrics instance
    """
    if not session_id:
        session_id = str(uuid.uuid4())

    now = datetime.now()
    return SessionMetrics(
        session_id=session_id,
        start_time=now,
        last_activity=now
    )


def create_memory_snapshot(
    total_messages: int,
    archived_messages: int,
    memory_usage_mb: float,
    cpu_usage_percent: float,
    cleanup_count: int,
    session_id: Optional[str] = None
) -> MemorySnapshot:
    """Create a memory usage snapshot.

    Args:
        total_messages: Total number of messages
        archived_messages: Number of archived messages
        memory_usage_mb: Current memory usage in MB
        cpu_usage_percent: Current CPU usage percentage
        cleanup_count: Number of cleanups performed
        session_id: Optional session ID

    Returns:
        MemorySnapshot instance
    """
    return MemorySnapshot(
        timestamp=datetime.now(),
        total_messages=total_messages,
        archived_messages=archived_messages,
        memory_usage_mb=memory_usage_mb,
        cpu_usage_percent=cpu_usage_percent,
        cleanup_count=cleanup_count,
        session_id=session_id or ""
    )


# Constants for memory management
DEFAULT_MEMORY_CONFIG = MemoryConfig()
MEMORY_STRATEGIES = ["memory", "hybrid"]
ARCHIVE_FORMAT_VERSION = "1.0"

# Thresholds for memory warnings
MEMORY_WARNING_THRESHOLD_MB = 400.0
MEMORY_CRITICAL_THRESHOLD_MB = 600.0

# Cleanup strategies
CLEANUP_STRATEGIES = {
    "oldest_first": "Remove oldest messages first",
    "keep_recent": "Keep most recent messages",
    "smart": "Intelligent cleanup based on content"
}