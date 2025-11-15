"""Performance monitoring and profiling utilities."""

from __future__ import annotations

import functools
import time
from typing import Any, Callable, TypeVar
import logging

from src.monitoring.metrics import get_metrics_collector
from src.monitoring.profiler import PerformanceProfiler
from src.monitoring.logger import get_logger

logger = logging.getLogger(__name__)
structured_logger = get_logger("performance")

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


def timing_decorator(operation_name: str | None = None, enable_profiling: bool = False) -> Callable[[F], F]:
    """Decorator to measure function execution time.

    Args:
        operation_name: Optional custom name for the operation
        enable_profiling: Enable detailed profiling

    Returns:
        Decorated function

    Example:
        @timing_decorator("ollama_api_call")
        async def make_api_call():
            ...
    """
    def decorator(func: F) -> F:
        op_name = operation_name or f"{func.__module__}.{func.__name__}"
        metrics_collector = get_metrics_collector()

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            success = True

            # Start profiling if enabled
            if enable_profiling:
                profiler = PerformanceProfiler()
                profiler.start_profiling(op_name)

            try:
                structured_logger.log_operation_start(op_name)
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                structured_logger.error(f"Operation {op_name} failed", exception=e, operation=op_name)
                metrics_collector.record_error(type(e).__name__, op_name)
                raise
            finally:
                duration = time.perf_counter() - start
                duration_ms = duration * 1000

                # Record metrics in new monitoring system
                metrics_collector.record_timing(op_name, duration_ms)
                _metrics.record_timing(op_name, duration)  # Keep legacy metrics

                # Log completion
                structured_logger.log_operation_end(op_name, duration_ms, success)

                # Stop profiling if enabled
                if enable_profiling:
                    profiler.stop_profiling(op_name)

                # Log slow operations
                slow_threshold = 1.0 if success else 0.5
                if duration > slow_threshold:
                    logger.warning(f"Slow operation: {op_name} took {duration:.2f}s")

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            success = True

            # Start profiling if enabled
            if enable_profiling:
                profiler = PerformanceProfiler()
                profiler.start_profiling(op_name)

            try:
                structured_logger.log_operation_start(op_name)
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                structured_logger.error(f"Operation {op_name} failed", exception=e, operation=op_name)
                metrics_collector.record_error(type(e).__name__, op_name)
                raise
            finally:
                duration = time.perf_counter() - start
                duration_ms = duration * 1000

                # Record metrics in new monitoring system
                metrics_collector.record_timing(op_name, duration_ms)
                _metrics.record_timing(op_name, duration)  # Keep legacy metrics

                # Log completion
                structured_logger.log_operation_end(op_name, duration_ms, success)

                # Stop profiling if enabled
                if enable_profiling:
                    profiler.stop_profiling(op_name)

                # Log slow operations
                slow_threshold = 0.5 if success else 0.2
                if duration > slow_threshold:
                    logger.warning(f"Slow operation: {op_name} took {duration:.2f}s")

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

    def __init__(self, operation_name: str, log_threshold: float = 0.1, enable_profiling: bool = False) -> None:
        """Initialize timer.

        Args:
            operation_name: Name of the operation being timed
            log_threshold: Log warning if duration exceeds this (seconds)
            enable_profiling: Enable detailed profiling
        """
        self.operation_name = operation_name
        self.log_threshold = log_threshold
        self.enable_profiling = enable_profiling
        self.start_time: float = 0.0
        self.duration: float = 0.0
        self.success = True
        self.profiler = None
        self.metrics_collector = get_metrics_collector()

    def __enter__(self) -> PerformanceTimer:
        """Start timing."""
        self.start_time = time.perf_counter()
        self.success = True

        # Start profiling if enabled
        if self.enable_profiling:
            self.profiler = PerformanceProfiler()
            self.profiler.start_profiling(self.operation_name)

        # Log operation start
        structured_logger.log_operation_start(self.operation_name)

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop timing and record."""
        self.duration = time.perf_counter() - self.start_time
        duration_ms = self.duration * 1000
        self.success = exc_type is None

        # Record metrics in both systems
        _metrics.record_timing(self.operation_name, self.duration)  # Legacy
        self.metrics_collector.record_timing(self.operation_name, duration_ms)  # New

        # Log completion
        structured_logger.log_operation_end(self.operation_name, duration_ms, self.success)

        # Record error if exception occurred
        if not self.success:
            self.metrics_collector.record_error(type(exc_val).__name__, self.operation_name)

        # Stop profiling if enabled
        if self.enable_profiling and self.profiler:
            self.profiler.stop_profiling(self.operation_name)

        # Log slow operations
        if self.duration > self.log_threshold:
            logger.warning(
                f"Performance: {self.operation_name} took {duration_ms:.2f}ms"
            )
