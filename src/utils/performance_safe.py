"""Safe performance monitoring utilities without external dependencies."""

from __future__ import annotations

import functools
import time
from typing import Any, Callable, TypeVar
import logging

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class PerformanceMetrics:
    """Track performance metrics for the application."""

    def __init__(self) -> None:
        """Initialize performance metrics tracker."""
        self.timings: dict[str, list[float]] = {}
        self.counters: dict[str, int] = {}

    def record_timing(self, operation: str, duration: float) -> None:
        """Record timing for an operation.

        Args:
            operation: Name of the operation
            duration: Duration in seconds
        """
        if operation not in self.timings:
            self.timings[operation] = []
        self.timings[operation].append(duration)

    def increment_counter(self, counter: str) -> None:
        """Increment a counter.

        Args:
            counter: Name of the counter
        """
        self.counters[counter] = self.counters.get(counter, 0) + 1

    def get_average_timing(self, operation: str) -> float | None:
        """Get average timing for an operation.

        Args:
            operation: Name of the operation

        Returns:
            Average duration in seconds or None if no data
        """
        timings = self.timings.get(operation, [])
        return sum(timings) / len(timings) if timings else None

    def get_stats(self) -> dict[str, Any]:
        """Get all performance statistics.

        Returns:
            Dictionary of statistics
        """
        stats = {
            "timings": {},
            "counters": self.counters.copy(),
        }

        for operation, timings in self.timings.items():
            if timings:
                stats["timings"][operation] = {
                    "count": len(timings),
                    "average": sum(timings) / len(timings),
                    "min": min(timings),
                    "max": max(timings),
                    "total": sum(timings),
                }

        return stats

    def reset(self) -> None:
        """Reset all metrics."""
        self.timings.clear()
        self.counters.clear()


# Global performance metrics instance
_metrics = PerformanceMetrics()


def get_metrics() -> PerformanceMetrics:
    """Get the global performance metrics instance.

    Returns:
        Global PerformanceMetrics instance
    """
    return _metrics


def timing_decorator(operation_name: str | None = None) -> Callable[[F], F]:
    """Decorator to measure function execution time.

    Args:
        operation_name: Optional custom name for the operation

    Returns:
        Decorated function

    Example:
        @timing_decorator("ollama_api_call")
        async def make_api_call():
            ...
    """
    def decorator(func: F) -> F:
        op_name = operation_name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            success = True

            try:
                logger.debug(f"Starting async operation: {op_name}")
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                logger.error(f"Async operation {op_name} failed: {str(e)}")
                raise
            finally:
                duration = time.perf_counter() - start
                _metrics.record_timing(op_name, duration)

                # Log slow operations
                slow_threshold = 1.0 if success else 0.5
                if duration > slow_threshold:
                    logger.warning(f"Slow async operation: {op_name} took {duration:.2f}s")

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            success = True

            try:
                logger.debug(f"Starting sync operation: {op_name}")
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                logger.error(f"Sync operation {op_name} failed: {str(e)}")
                raise
            finally:
                duration = time.perf_counter() - start
                _metrics.record_timing(op_name, duration)

                # Log slow operations
                slow_threshold = 0.5 if success else 0.2
                if duration > slow_threshold:
                    logger.warning(f"Slow sync operation: {op_name} took {duration:.2f}s")

        # Return appropriate wrapper based on whether function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


class PerformanceTimer:
    """Context manager for timing code blocks.

    Example:
        with PerformanceTimer("render_messages"):
            render_messages()
    """

    def __init__(self, operation_name: str, log_threshold: float = 0.1) -> None:
        """Initialize timer.

        Args:
            operation_name: Name of the operation being timed
            log_threshold: Log warning if duration exceeds this (seconds)
        """
        self.operation_name = operation_name
        self.log_threshold = log_threshold
        self.start_time: float = 0.0
        self.duration: float = 0.0
        self.success = True

    def __enter__(self) -> PerformanceTimer:
        """Start timing."""
        self.start_time = time.perf_counter()
        self.success = True
        logger.debug(f"Starting operation: {self.operation_name}")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop timing and record."""
        self.duration = time.perf_counter() - self.start_time
        self.success = exc_type is None

        # Record metrics
        _metrics.record_timing(self.operation_name, self.duration)

        # Log slow operations
        if self.duration > self.log_threshold:
            logger.warning(
                f"Performance: {self.operation_name} took {self.duration:.2f}s"
            )