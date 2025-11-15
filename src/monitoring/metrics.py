"""Comprehensive metrics collection and aggregation.

This module implements the four golden signals of monitoring:
- Latency: Response times for operations
- Traffic: Request volume and rate
- Errors: Failure rates and types
- Saturation: Resource utilization

Also implements RED (Rate, Errors, Duration) and USE (Utilization, Saturation, Errors) methods.
"""

from __future__ import annotations

import json
import psutil
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricValue:
    """Single metric value with metadata."""
    value: Union[int, float]
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels
        }


@dataclass
class MetricSummary:
    """Statistical summary of metric values over a time window."""
    count: int
    sum: float
    min: float
    max: float
    avg: float
    p50: float
    p95: float
    p99: float

    @classmethod
    def from_values(cls, values: List[float]) -> MetricSummary:
        """Create summary from list of values."""
        if not values:
            return cls(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        sorted_values = sorted(values)
        n = len(sorted_values)

        return cls(
            count=n,
            sum=sum(sorted_values),
            min=sorted_values[0],
            max=sorted_values[-1],
            avg=sum(sorted_values) / n,
            p50=sorted_values[int(n * 0.5)],
            p95=sorted_values[int(n * 0.95)],
            p99=sorted_values[int(n * 0.99)],
        )


class MetricsStore:
    """In-memory metrics storage with configurable retention."""

    def __init__(self, max_samples: int = 10000, cleanup_interval: int = 300):
        """Initialize metrics store.

        Args:
            max_samples: Maximum samples to keep per metric
            cleanup_interval: Cleanup interval in seconds
        """
        self.max_samples = max_samples
        self.cleanup_interval = cleanup_interval
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_samples))
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    def add_metric(self, name: str, value: Union[int, float], labels: Optional[Dict[str, str]] = None) -> None:
        """Add a metric value.

        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels
        """
        with self._lock:
            metric = MetricValue(
                value=value,
                timestamp=datetime.now(),
                labels=labels or {}
            )
            self._metrics[name].append(metric)
            self._maybe_cleanup()

    def get_metrics(self, name: str, since: Optional[datetime] = None) -> List[MetricValue]:
        """Get metrics for a name since optional timestamp.

        Args:
            name: Metric name
            since: Optional timestamp filter

        Returns:
            List of metric values
        """
        with self._lock:
            metrics = list(self._metrics[name])
            if since:
                metrics = [m for m in metrics if m.timestamp >= since]
            return metrics

    def get_summary(self, name: str, window_minutes: int = 5) -> Optional[MetricSummary]:
        """Get statistical summary for a metric over time window.

        Args:
            name: Metric name
            window_minutes: Time window in minutes

        Returns:
            Metric summary or None if no data
        """
        since = datetime.now() - timedelta(minutes=window_minutes)
        metrics = self.get_metrics(name, since)
        values = [m.value for m in metrics]

        if not values:
            return None

        return MetricSummary.from_values(values)

    def get_all_metric_names(self) -> List[str]:
        """Get all available metric names."""
        with self._lock:
            return list(self._metrics.keys())

    def _maybe_cleanup(self) -> None:
        """Clean up old metrics if needed."""
        now = time.time()
        if now - self._last_cleanup > self.cleanup_interval:
            # Deques automatically handle cleanup via maxlen
            self._last_cleanup = now


class ResourceMonitor:
    """Monitor system resources (CPU, memory, disk, network)."""

    def __init__(self, interval: int = 30):
        """Initialize resource monitor.

        Args:
            interval: Monitoring interval in seconds
        """
        self.interval = interval
        self._monitoring = False
        self._thread: Optional[threading.Thread] = None

    def start_monitoring(self, metrics_store: MetricsStore) -> None:
        """Start resource monitoring in background thread.

        Args:
            metrics_store: Metrics store to record data
        """
        if self._monitoring:
            return

        self._monitoring = True
        self._thread = threading.Thread(
            target=self._monitor_loop,
            args=(metrics_store,),
            daemon=True
        )
        self._thread.start()
        logger.info("Resource monitoring started")

    def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        self._monitoring = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Resource monitoring stopped")

    def _monitor_loop(self, metrics_store: MetricsStore) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                # CPU metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                metrics_store.add_metric("system.cpu.percent", cpu_percent)

                # Memory metrics
                memory = psutil.virtual_memory()
                metrics_store.add_metric("system.memory.percent", memory.percent)
                metrics_store.add_metric("system.memory.available_gb", memory.available / (1024**3))
                metrics_store.add_metric("system.memory.used_gb", memory.used / (1024**3))

                # Disk metrics
                disk = psutil.disk_usage('/')
                metrics_store.add_metric("system.disk.percent", (disk.used / disk.total) * 100)
                metrics_store.add_metric("system.disk.free_gb", disk.free / (1024**3))

                # Network metrics
                network = psutil.net_io_counters()
                metrics_store.add_metric("system.network.bytes_sent", network.bytes_sent)
                metrics_store.add_metric("system.network.bytes_recv", network.bytes_recv)

                # Process-specific metrics
                process = psutil.Process()
                metrics_store.add_metric("process.cpu.percent", process.cpu_percent())
                metrics_store.add_metric("process.memory.percent", process.memory_percent())
                metrics_store.add_metric("process.memory.rss_mb", process.memory_info().rss / (1024**2))

            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")

            time.sleep(self.interval)


class MetricsCollector:
    """Main metrics collection and aggregation system."""

    def __init__(self, storage_path: Optional[str] = None):
        """Initialize metrics collector.

        Args:
            storage_path: Optional path to persist metrics
        """
        self.store = MetricsStore()
        self.resource_monitor = ResourceMonitor()
        self.storage_path = Path(storage_path) if storage_path else None

        # Start resource monitoring
        self.resource_monitor.start_monitoring(self.store)

        logger.info("Metrics collector initialized")

    def record_timing(self, operation: str, duration_ms: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record operation timing.

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            labels: Optional labels
        """
        metric_name = f"operation.{operation}.duration_ms"
        self.store.add_metric(metric_name, duration_ms, labels)

    def record_counter(self, counter: str, increment: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """Record counter increment.

        Args:
            counter: Counter name
            increment: Increment value
            labels: Optional labels
        """
        metric_name = f"counter.{counter}"
        self.store.add_metric(metric_name, increment, labels)

    def record_gauge(self, gauge: str, value: Union[int, float], labels: Optional[Dict[str, str]] = None) -> None:
        """Record gauge value.

        Args:
            gauge: Gauge name
            value: Gauge value
            labels: Optional labels
        """
        metric_name = f"gauge.{gauge}"
        self.store.add_metric(metric_name, value, labels)

    def record_error(self, error_type: str, operation: str = "", labels: Optional[Dict[str, str]] = None) -> None:
        """Record an error occurrence.

        Args:
            error_type: Type of error
            operation: Operation where error occurred
            labels: Optional labels
        """
        error_labels = {"error_type": error_type}
        if operation:
            error_labels["operation"] = operation
        if labels:
            error_labels.update(labels)

        metric_name = "errors.count"
        self.store.add_metric(metric_name, 1, error_labels)

    def get_operation_stats(self, operation: str, window_minutes: int = 5) -> Optional[Dict[str, Any]]:
        """Get comprehensive statistics for an operation.

        Args:
            operation: Operation name
            window_minutes: Time window in minutes

        Returns:
            Dictionary with operation statistics
        """
        duration_metric = f"operation.{operation}.duration_ms"
        summary = self.store.get_summary(duration_metric, window_minutes)

        if not summary:
            return None

        # Calculate error rate
        error_labels = {"operation": operation}
        errors = self.store.get_metrics("errors.count", since=datetime.now() - timedelta(minutes=window_minutes))
        operation_errors = [e for e in errors if e.labels.get("operation") == operation]

        # Calculate request rate
        request_rate = summary.count / window_minutes if window_minutes > 0 else 0
        error_rate = len(operation_errors) / summary.count if summary.count > 0 else 0

        return {
            "operation": operation,
            "window_minutes": window_minutes,
            "requests": {
                "total": summary.count,
                "rate_per_minute": request_rate,
            },
            "duration": {
                "avg_ms": summary.avg,
                "min_ms": summary.min,
                "max_ms": summary.max,
                "p50_ms": summary.p50,
                "p95_ms": summary.p95,
                "p99_ms": summary.p99,
            },
            "errors": {
                "count": len(operation_errors),
                "rate": error_rate,
            },
            "availability": 1.0 - error_rate,
        }

    def get_system_stats(self, window_minutes: int = 5) -> Dict[str, Any]:
        """Get system resource statistics.

        Args:
            window_minutes: Time window for stats

        Returns:
            Dictionary with system statistics
        """
        stats = {}

        # CPU stats
        cpu_summary = self.store.get_summary("system.cpu.percent", window_minutes)
        if cpu_summary:
            stats["cpu"] = {
                "usage_percent": {
                    "avg": cpu_summary.avg,
                    "max": cpu_summary.max,
                    "current": cpu_summary.avg,  # Approximate
                }
            }

        # Memory stats
        memory_summary = self.store.get_summary("system.memory.percent", window_minutes)
        if memory_summary:
            stats["memory"] = {
                "usage_percent": {
                    "avg": memory_summary.avg,
                    "max": memory_summary.max,
                }
            }

        # Process stats
        process_cpu = self.store.get_summary("process.cpu.percent", window_minutes)
        process_memory = self.store.get_summary("process.memory.rss_mb", window_minutes)

        if process_cpu or process_memory:
            stats["process"] = {}
            if process_cpu:
                stats["process"]["cpu_percent"] = {"avg": process_cpu.avg, "max": process_cpu.max}
            if process_memory:
                stats["process"]["memory_mb"] = {"avg": process_memory.avg, "max": process_memory.max}

        return stats

    def get_all_stats(self, window_minutes: int = 5) -> Dict[str, Any]:
        """Get all statistics for monitoring dashboards.

        Args:
            window_minutes: Time window for stats

        Returns:
            Complete statistics dictionary
        """
        all_stats = {
            "timestamp": datetime.now().isoformat(),
            "window_minutes": window_minutes,
            "system": self.get_system_stats(window_minutes),
            "operations": {},
            "errors": {},
        }

        # Get stats for all operations
        metric_names = self.store.get_all_metric_names()
        operation_names = set()

        for name in metric_names:
            if name.startswith("operation.") and name.endswith(".duration_ms"):
                operation_name = name[len("operation."):-len(".duration_ms")]
                operation_names.add(operation_name)

        for operation in operation_names:
            op_stats = self.get_operation_stats(operation, window_minutes)
            if op_stats:
                all_stats["operations"][operation] = op_stats

        return all_stats

    def export_metrics(self, filepath: str, window_minutes: int = 60) -> None:
        """Export metrics to JSON file.

        Args:
            filepath: Output file path
            window_minutes: Time window to export
        """
        stats = self.get_all_stats(window_minutes)

        with open(filepath, 'w') as f:
            json.dump(stats, f, indent=2)

        logger.info(f"Metrics exported to {filepath}")

    def cleanup(self) -> None:
        """Cleanup resources."""
        self.resource_monitor.stop_monitoring()


# Global metrics collector instance
_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance.

    Returns:
        Global MetricsCollector instance
    """
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


def init_metrics_collector(storage_path: Optional[str] = None) -> MetricsCollector:
    """Initialize the global metrics collector.

    Args:
        storage_path: Optional storage path for metrics

    Returns:
        MetricsCollector instance
    """
    global _collector
    _collector = MetricsCollector(storage_path)
    return _collector