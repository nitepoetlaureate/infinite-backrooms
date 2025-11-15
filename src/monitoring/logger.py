"""Structured logging for monitoring and observability.

Provides structured logging with correlation IDs, request tracing,
and log aggregation support.
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .metrics import get_metrics_collector


class LogLevel(Enum):
    """Log levels aligned with standard logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogContext:
    """Structured log context with correlation information."""
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    operation: Optional[str] = None
    component: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def merge(self, other: LogContext) -> LogContext:
        """Merge another context into this one."""
        return LogContext(
            request_id=other.request_id or self.request_id,
            session_id=other.session_id or self.session_id,
            user_id=other.user_id or self.user_id,
            operation=other.operation or self.operation,
            component=other.component or self.component,
            tags={**self.tags, **other.tags},
            metadata={**self.metadata, **other.metadata}
        )


@dataclass
class StructuredLogEntry:
    """Structured log entry with all context."""
    timestamp: datetime
    level: LogLevel
    message: str
    context: LogContext
    exception: Optional[str] = None
    stack_trace: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "message": self.message,
            "context": {
                "request_id": self.context.request_id,
                "session_id": self.context.session_id,
                "user_id": self.context.user_id,
                "operation": self.context.operation,
                "component": self.context.component,
                "tags": self.context.tags,
                "metadata": self.context.metadata,
            },
            "exception": self.exception,
            "stack_trace": self.stack_trace,
        }


class ContextManager:
    """Thread-local context manager for logging."""

    def __init__(self):
        """Initialize context manager."""
        self._local = threading.local()

    def set_context(self, context: LogContext) -> None:
        """Set context for current thread.

        Args:
            context: Log context to set
        """
        self._local.context = context

    def get_context(self) -> LogContext:
        """Get context for current thread.

        Returns:
            Current thread's context or empty context
        """
        return getattr(self._local, 'context', LogContext())

    def update_context(self, **kwargs) -> None:
        """Update current context with new values.

        Args:
            **kwargs: Context fields to update
        """
        current = self.get_context()
        new_context = LogContext(**{**asdict(current), **kwargs})
        self.set_context(new_context)

    def clear_context(self) -> None:
        """Clear context for current thread."""
        self._local.context = LogContext()

    def with_context(self, context: LogContext):
        """Context manager for temporary context.

        Args:
            context: Context to use temporarily

        Yields:
            Context manager
        """
        old_context = self.get_context()
        try:
            self.set_context(context)
            yield
        finally:
            self.set_context(old_context)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON formatted log entry
        """
        # Extract context from record if available
        context = getattr(record, 'context', LogContext())
        structured_entry = StructuredLogEntry(
            timestamp=datetime.fromtimestamp(record.created),
            level=LogLevel(record.levelname),
            message=record.getMessage(),
            context=context,
            exception=record.exc_text,
            stack_trace=self._format_stack_trace(record)
        )

        return json.dumps(structured_entry.to_dict(), default=str)

    def _format_stack_trace(self, record: logging.LogRecord) -> Optional[str]:
        """Format stack trace from log record.

        Args:
            record: Log record

        Returns:
            Formatted stack trace or None
        """
        if record.exc_info:
            return ''.join(traceback.format_exception(*record.exc_info))
        return None


class StructuredLogger:
    """Main structured logging system."""

    def __init__(
        self,
        name: str,
        level: LogLevel = LogLevel.INFO,
        log_file: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        enable_console: bool = True,
        enable_json: bool = True
    ):
        """Initialize structured logger.

        Args:
            name: Logger name
            level: Log level
            log_file: Optional log file path
            max_file_size: Maximum file size in bytes
            backup_count: Number of backup files
            enable_console: Enable console logging
            enable_json: Enable JSON formatting
        """
        self.name = name
        self.level = level
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.value))
        self.context_manager = ContextManager()
        self.metrics = get_metrics_collector()

        # Clear existing handlers
        self.logger.handlers.clear()

        # Add console handler if enabled
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            if enable_json:
                console_handler.setFormatter(JSONFormatter())
            else:
                console_handler.setFormatter(
                    logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )
                )
            self.logger.addHandler(console_handler)

        # Add file handler if log file specified
        if log_file:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            if enable_json:
                file_handler.setFormatter(JSONFormatter())
            else:
                file_handler.setFormatter(
                    logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )
                )
            self.logger.addHandler(file_handler)

        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        self._log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        self._log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log error message.

        Args:
            message: Log message
            exception: Optional exception to include
            **kwargs: Additional context fields
        """
        if exception:
            kwargs['exception'] = str(exception)
            kwargs['exception_type'] = type(exception).__name__

        self._log(LogLevel.ERROR, message, **kwargs)

        # Record error metrics
        self.metrics.record_error(
            error_type=kwargs.get('exception_type', 'unknown'),
            operation=kwargs.get('operation', ''),
            labels=kwargs.get('tags', {})
        )

    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log critical message.

        Args:
            message: Log message
            exception: Optional exception to include
            **kwargs: Additional context fields
        """
        if exception:
            kwargs['exception'] = str(exception)
            kwargs['exception_type'] = type(exception).__name__

        self._log(LogLevel.CRITICAL, message, **kwargs)

        # Record critical error metrics
        self.metrics.record_error(
            error_type="critical",
            operation=kwargs.get('operation', ''),
            labels=kwargs.get('tags', {})
        )

    def _log(self, level: LogLevel, message: str, **kwargs) -> None:
        """Internal logging method.

        Args:
            level: Log level
            message: Log message
            **kwargs: Additional context fields
        """
        # Merge with current context
        current_context = self.context_manager.get_context()

        # Create updated context
        updated_context = LogContext(
            request_id=kwargs.pop('request_id', current_context.request_id),
            session_id=kwargs.pop('session_id', current_context.session_id),
            user_id=kwargs.pop('user_id', current_context.user_id),
            operation=kwargs.pop('operation', current_context.operation),
            component=kwargs.pop('component', current_context.component),
            tags={**current_context.tags, **kwargs.pop('tags', {})},
            metadata={**current_context.metadata, **kwargs.pop('metadata', kwargs)}
        )

        # Create log record with context
        extra = {'context': updated_context}

        # Log the message
        log_method = getattr(self.logger, level.value.lower())
        log_method(message, extra=extra)

        # Record log metrics
        self.metrics.record_counter("logs.written", labels={
            "level": level.value,
            "component": updated_context.component or "unknown"
        })

    def set_context(self, **kwargs) -> None:
        """Set logging context.

        Args:
            **kwargs: Context fields
        """
        self.context_manager.update_context(**kwargs)

    def clear_context(self) -> None:
        """Clear logging context."""
        self.context_manager.clear_context()

    def with_context(self, **kwargs):
        """Context manager for temporary context.

        Args:
            **kwargs: Context fields

        Yields:
            Context manager
        """
        context = LogContext(**kwargs)
        return self.context_manager.with_context(context)

    def log_operation_start(self, operation: str, **kwargs) -> None:
        """Log operation start.

        Args:
            operation: Operation name
            **kwargs: Additional context
        """
        self.info(f"Starting operation: {operation}", operation=operation, **kwargs)

    def log_operation_end(self, operation: str, duration_ms: float, success: bool = True, **kwargs) -> None:
        """Log operation completion.

        Args:
            operation: Operation name
            duration_ms: Operation duration in milliseconds
            success: Whether operation succeeded
            **kwargs: Additional context
        """
        level = LogLevel.INFO if success else LogLevel.ERROR
        status = "completed" if success else "failed"
        message = f"Operation {operation} {status} in {duration_ms:.2f}ms"

        self._log(level, message, operation=operation, **{
            **kwargs,
            "duration_ms": duration_ms,
            "success": success,
            "status": status
        })

        # Record operation metrics
        self.metrics.record_timing(operation, duration_ms, labels=kwargs.get('tags'))
        if not success:
            self.metrics.record_counter(f"{operation}_failures", labels=kwargs.get('tags'))

    def log_request(self, method: str, path: str, status_code: int, duration_ms: float, **kwargs) -> None:
        """Log HTTP request.

        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            **kwargs: Additional context
        """
        self.info(
            f"{method} {path} - {status_code} ({duration_ms:.2f}ms)",
            operation="http_request",
            **{
                **kwargs,
                "http_method": method,
                "http_path": path,
                "http_status_code": status_code,
                "http_duration_ms": duration_ms
            }
        )

        # Record HTTP metrics
        self.metrics.record_timing("http_request", duration_ms, labels={
            "method": method,
            "path": path,
            "status_code": str(status_code)
        })

        if status_code >= 400:
            self.metrics.record_counter("http_errors", labels={
                "method": method,
                "path": path,
                "status_code": str(status_code)
            })

    def log_api_call(self, api_name: str, endpoint: str, duration_ms: float, success: bool = True, **kwargs) -> None:
        """Log external API call.

        Args:
            api_name: Name of the API/service
            endpoint: API endpoint
            duration_ms: Call duration in milliseconds
            success: Whether call succeeded
            **kwargs: Additional context
        """
        level = LogLevel.INFO if success else LogLevel.WARNING
        status = "successful" if success else "failed"
        message = f"API call to {api_name} {endpoint} {status} ({duration_ms:.2f}ms)"

        self._log(level, message, operation="api_call", **{
            **kwargs,
            "api_name": api_name,
            "api_endpoint": endpoint,
            "success": success,
            "duration_ms": duration_ms
        })

        # Record API metrics
        self.metrics.record_timing(f"api.{api_name}", duration_ms, labels={
            "endpoint": endpoint,
            "success": str(success)
        })

        if not success:
            self.metrics.record_counter("api_failures", labels={
                "api_name": api_name,
                "endpoint": endpoint
            })

    def search_logs(
        self,
        level: Optional[LogLevel] = None,
        component: Optional[str] = None,
        operation: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search logs (basic implementation).

        Args:
            level: Filter by log level
            component: Filter by component
            operation: Filter by operation
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum results

        Returns:
            List of matching log entries
        """
        # This is a simplified implementation
        # In production, you'd use proper log aggregation tools
        return []


# Global logger instances
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str = "infinite_backrooms", **kwargs) -> StructuredLogger:
    """Get or create structured logger.

    Args:
        name: Logger name
        **kwargs: Additional logger configuration

    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, **kwargs)
    return _loggers[name]


def init_logging(
    log_file: Optional[str] = None,
    log_level: LogLevel = LogLevel.INFO,
    **kwargs
) -> StructuredLogger:
    """Initialize default logging configuration.

    Args:
        log_file: Optional log file path
        log_level: Default log level
        **kwargs: Additional logger configuration

    Returns:
        Default structured logger
    """
    logger = get_logger("infinite_backrooms", level=log_level, log_file=log_file, **kwargs)
    return logger