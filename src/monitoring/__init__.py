"""Monitoring package for Infinite AI Backrooms.

Provides comprehensive observability including:
- Metrics collection and aggregation
- Structured logging
- Health checks
- Performance profiling
- Resource monitoring
- Alerting and dashboards
"""

from __future__ import annotations

from .metrics import MetricsCollector, get_metrics_collector
from .health import HealthChecker, HealthStatus
from .profiler import PerformanceProfiler
from .alerts import AlertManager
from .logger import StructuredLogger
from .dashboard import DashboardManager

__all__ = [
    "MetricsCollector",
    "get_metrics_collector",
    "HealthChecker",
    "HealthStatus",
    "PerformanceProfiler",
    "AlertManager",
    "StructuredLogger",
    "DashboardManager",
]