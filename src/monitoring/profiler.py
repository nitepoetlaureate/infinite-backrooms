"""Performance profiling and bottleneck identification.

Provides tools for profiling application performance,
identifying bottlenecks, and optimizing resource usage.
"""

from __future__ import annotations

import cProfile
import io
import pstats
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .metrics import get_metrics_collector


@dataclass
class ProfileEntry:
    """Single profile entry with timing information."""
    function: str
    calls: int
    total_time: float
    per_call_time: float
    cumulative_time: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ProfileReport:
    """Complete profile report."""
    operation: str
    timestamp: datetime
    duration_seconds: float
    entries: List[ProfileEntry] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def get_slowest_functions(self, count: int = 10) -> List[ProfileEntry]:
        """Get slowest functions by total time."""
        return sorted(self.entries, key=lambda x: x.total_time, reverse=True)[:count]

    def get_most_called_functions(self, count: int = 10) -> List[ProfileEntry]:
        """Get most frequently called functions."""
        return sorted(self.entries, key=lambda x: x.calls, reverse=True)[:count]


class CallProfiler:
    """Function call profiler for performance analysis."""

    def __init__(self, max_entries: int = 1000):
        """Initialize call profiler.

        Args:
            max_entries: Maximum profile entries to keep
        """
        self.max_entries = max_entries
        self._active_profiles: Dict[str, cProfile.Profile] = {}
        self._completed_profiles: deque = deque(maxlen=max_entries)
        self._lock = threading.Lock()
        self.metrics = get_metrics_collector()

    def start_profile(self, operation: str) -> None:
        """Start profiling an operation.

        Args:
            operation: Operation name to profile
        """
        with self._lock:
            if operation in self._active_profiles:
                # Profile already running for this operation
                return

            profile = cProfile.Profile()
            profile.enable()
            self._active_profiles[operation] = profile

    def stop_profile(self, operation: str) -> Optional[ProfileReport]:
        """Stop profiling and generate report.

        Args:
            operation: Operation name to stop profiling

        Returns:
            ProfileReport if profile was active
        """
        with self._lock:
            if operation not in self._active_profiles:
                return None

            profile = self._active_profiles.pop(operation)
            profile.disable()

            # Generate report
            report = self._generate_report(operation, profile)
            self._completed_profiles.append(report)

            # Record metrics
            self.metrics.record_timing(
                f"profile.{operation}.duration_ms",
                report.duration_seconds * 1000
            )
            self.metrics.record_counter("profile.completed_reports")

            return report

    def _generate_report(self, operation: str, profile: cProfile.Profile) -> ProfileReport:
        """Generate profile report from cProfile data.

        Args:
            operation: Operation name
            profile: Completed profile

        Returns:
            ProfileReport
        """
        # Create string buffer for stats
        stream = io.StringIO()
        stats = pstats.Stats(profile, stream=stream)

        # Sort by cumulative time
        stats.sort_stats('cumulative')
        stats.print_stats(50)  # Top 50 functions

        # Parse the stats output
        entries = []
        lines = stream.getvalue().split('\n')[5:]  # Skip header

        for line in lines:
            if line.strip() and not line.startswith(' '):
                # Parse function line
                parts = line.split()
                if len(parts) >= 6 and parts[0].isdigit():
                    try:
                        calls = int(parts[0])
                        total_time = float(parts[2])
                        per_call_time = float(parts[3])
                        cumulative_time = float(parts[4])

                        # Extract function name (last part)
                        function = ' '.join(parts[6:]).strip()

                        entries.append(ProfileEntry(
                            function=function,
                            calls=calls,
                            total_time=total_time,
                            per_call_time=per_call_time,
                            cumulative_time=cumulative_time
                        ))
                    except (ValueError, IndexError):
                        continue

        # Calculate summary
        total_duration = sum(e.total_time for e in entries)
        total_calls = sum(e.calls for e in entries)

        summary = {
            "total_duration_seconds": total_duration,
            "total_function_calls": total_calls,
            "unique_functions": len(entries),
            "avg_function_duration": total_duration / len(entries) if entries else 0,
        }

        return ProfileReport(
            operation=operation,
            timestamp=datetime.now(),
            duration_seconds=total_duration,
            entries=entries,
            summary=summary
        )

    def get_latest_report(self, operation: Optional[str] = None) -> Optional[ProfileReport]:
        """Get latest profile report.

        Args:
            operation: Optional operation filter

        Returns:
            Latest ProfileReport or None
        """
        with self._lock:
            if operation:
                for report in reversed(self._completed_profiles):
                    if report.operation == operation:
                        return report
                return None
            else:
                return self._completed_profiles[-1] if self._completed_profiles else None

    def get_reports_by_operation(self, operation: str, limit: int = 10) -> List[ProfileReport]:
        """Get profile reports for specific operation.

        Args:
            operation: Operation name
            limit: Maximum reports to return

        Returns:
            List of ProfileReport
        """
        with self._lock:
            reports = [r for r in self._completed_profiles if r.operation == operation]
            return reports[-limit:] if len(reports) > limit else reports

    def get_all_operations(self) -> List[str]:
        """Get all profiled operation names.

        Returns:
            List of operation names
        """
        with self._lock:
            operations = set()
            for report in self._completed_profiles:
                operations.add(report.operation)
            return list(operations)

    def export_reports(self, filepath: str, operation: Optional[str] = None) -> None:
        """Export profile reports to JSON.

        Args:
            filepath: Output file path
            operation: Optional operation filter
        """
        reports_data = []

        with self._lock:
            if operation:
                reports = self.get_reports_by_operation(operation)
            else:
                reports = list(self._completed_profiles)

            for report in reports:
                reports_data.append({
                    "operation": report.operation,
                    "timestamp": report.timestamp.isoformat(),
                    "duration_seconds": report.duration_seconds,
                    "summary": report.summary,
                    "entries": [
                        {
                            "function": entry.function,
                            "calls": entry.calls,
                            "total_time": entry.total_time,
                            "per_call_time": entry.per_call_time,
                            "cumulative_time": entry.cumulative_time,
                        }
                        for entry in report.entries
                    ]
                })

        import json
        with open(filepath, 'w') as f:
            json.dump(reports_data, f, indent=2)


class MemoryProfiler:
    """Memory usage profiler for tracking memory consumption."""

    def __init__(self, max_snapshots: int = 100):
        """Initialize memory profiler.

        Args:
            max_snapshots: Maximum memory snapshots to keep
        """
        self.max_snapshots = max_snapshots
        self._snapshots: deque = deque(maxlen=max_snapshots)
        self._lock = threading.Lock()

    def take_snapshot(self, operation: str) -> None:
        """Take a memory snapshot.

        Args:
            operation: Operation name
        """
        try:
            import psutil
            import tracemalloc

            process = psutil.Process()

            snapshot = {
                "operation": operation,
                "timestamp": datetime.now(),
                "memory_rss_mb": process.memory_info().rss / (1024**2),
                "memory_vms_mb": process.memory_info().vms / (1024**2),
                "memory_percent": process.memory_percent(),
                "cpu_percent": process.cpu_percent(),
            }

            # Add tracemalloc data if available
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                snapshot["tracemalloc_current_mb"] = current / (1024**2)
                snapshot["tracemalloc_peak_mb"] = peak / (1024**2)

            with self._lock:
                self._snapshots.append(snapshot)

        except ImportError:
            # psutil not available
            pass
        except Exception as e:
            print(f"Error taking memory snapshot: {e}")

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get latest memory snapshot.

        Returns:
            Latest snapshot or None
        """
        with self._lock:
            return self._snapshots[-1] if self._snapshots else None

    def get_snapshots_by_operation(self, operation: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get memory snapshots for specific operation.

        Args:
            operation: Operation name
            limit: Maximum snapshots to return

        Returns:
            List of memory snapshots
        """
        with self._lock:
            snapshots = [s for s in self._snapshots if s["operation"] == operation]
            return snapshots[-limit:] if len(snapshots) > limit else snapshots

    def analyze_memory_trend(self, window_minutes: int = 30) -> Dict[str, Any]:
        """Analyze memory usage trend.

        Args:
            window_minutes: Time window to analyze

        Returns:
            Memory trend analysis
        """
        with self._lock:
            if not self._snapshots:
                return {"status": "no_data"}

            # Filter snapshots by time window
            cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
            recent_snapshots = [
                s for s in self._snapshots
                if s["timestamp"] >= cutoff_time
            ]

            if len(recent_snapshots) < 2:
                return {"status": "insufficient_data"}

            # Calculate trend
            memory_values = [s["memory_rss_mb"] for s in recent_snapshots]
            timestamps = [s["timestamp"] for s in recent_snapshots]

            # Simple trend calculation
            start_memory = memory_values[0]
            end_memory = memory_values[-1]
            memory_change = end_memory - start_memory

            # Calculate rate of change
            time_diff = (timestamps[-1] - timestamps[0]).total_seconds() / 60  # minutes
            memory_rate = memory_change / time_diff if time_diff > 0 else 0

            return {
                "status": "analyzed",
                "window_minutes": window_minutes,
                "snapshots_analyzed": len(recent_snapshots),
                "memory_trend": {
                    "start_memory_mb": start_memory,
                    "end_memory_mb": end_memory,
                    "memory_change_mb": memory_change,
                    "memory_rate_mb_per_minute": memory_rate,
                    "avg_memory_mb": sum(memory_values) / len(memory_values),
                    "max_memory_mb": max(memory_values),
                    "min_memory_mb": min(memory_values),
                },
                "timestamp": datetime.now().isoformat(),
            }


class PerformanceProfiler:
    """Main performance profiler combining call and memory profiling."""

    def __init__(self, enable_call_profiling: bool = True, enable_memory_profiling: bool = True):
        """Initialize performance profiler.

        Args:
            enable_call_profiling: Enable function call profiling
            enable_memory_profiling: Enable memory profiling
        """
        self.call_profiler = CallProfiler() if enable_call_profiling else None
        self.memory_profiler = MemoryProfiler() if enable_memory_profiling else None
        self.metrics = get_metrics_collector()

    def start_profiling(self, operation: str) -> None:
        """Start profiling an operation.

        Args:
            operation: Operation name
        """
        if self.call_profiler:
            self.call_profiler.start_profile(operation)

        if self.memory_profiler:
            self.memory_profiler.take_snapshot(f"{operation}_start")

        self.metrics.record_counter("profiling.started", labels={"operation": operation})

    def stop_profiling(self, operation: str) -> Dict[str, Any]:
        """Stop profiling and collect results.

        Args:
            operation: Operation name

        Returns:
            Dictionary with profiling results
        """
        results = {
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
            "call_profile": None,
            "memory_profile": None,
        }

        # Stop call profiling
        if self.call_profiler:
            report = self.call_profiler.stop_profile(operation)
            if report:
                results["call_profile"] = {
                    "duration_seconds": report.duration_seconds,
                    "summary": report.summary,
                    "slowest_functions": [
                        {
                            "function": entry.function,
                            "total_time": entry.total_time,
                            "calls": entry.calls,
                        }
                        for entry in report.get_slowest_functions(5)
                    ]
                }

        # Take memory snapshot
        if self.memory_profiler:
            self.memory_profiler.take_snapshot(f"{operation}_end")
            latest_snapshot = self.memory_profiler.get_latest_snapshot()
            if latest_snapshot:
                results["memory_profile"] = {
                    "memory_rss_mb": latest_snapshot["memory_rss_mb"],
                    "memory_percent": latest_snapshot["memory_percent"],
                }

        self.metrics.record_counter("profiling.completed", labels={"operation": operation})

        return results

    def get_performance_insights(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get performance insights and recommendations.

        Args:
            operation: Optional operation to focus on

        Returns:
            Performance insights and recommendations
        """
        insights = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "recommendations": [],
            "warnings": [],
        }

        # Analyze call profiles
        if self.call_profiler:
            report = self.call_profiler.get_latest_report(operation)
            if report:
                # Check for slow functions
                slow_functions = report.get_slowest_functions(5)
                if slow_functions and slow_functions[0].total_time > 1.0:
                    insights["warnings"].append(
                        f"Function '{slow_functions[0].function}' is slow "
                        f"({slow_functions[0].total_time:.2f}s)"
                    )
                    insights["recommendations"].append(
                        "Consider optimizing or caching expensive function calls"
                    )

                # Check for excessive function calls
                most_called = report.get_most_called_functions(5)
                if most_called and most_called[0].calls > 1000:
                    insights["recommendations"].append(
                        f"Function '{most_called[0].function}' called {most_called[0].calls} times. "
                        "Consider memoization or batching."
                    )

        # Analyze memory usage
        if self.memory_profiler:
            trend = self.memory_profiler.analyze_memory_trend()
            if trend["status"] == "analyzed":
                memory_trend = trend["memory_trend"]
                if memory_trend["memory_rate_mb_per_minute"] > 10:
                    insights["warnings"].append(
                        f"Memory usage increasing rapidly: "
                        f"{memory_trend['memory_rate_mb_per_minute']:.1f} MB/min"
                    )
                    insights["recommendations"].append(
                        "Investigate potential memory leaks or optimize memory usage"
                    )

        return insights

    def export_profiles(self, output_dir: str) -> None:
        """Export all profiling data to files.

        Args:
            output_dir: Output directory path
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if self.call_profiler:
            self.call_profiler.export_reports(output_path / "call_profiles.json")

        if self.memory_profiler:
            # Export memory snapshots
            with self._lock:
                import json
                snapshots = list(self.memory_profiler._snapshots)

            with open(output_path / "memory_snapshots.json", 'w') as f:
                json.dump(snapshots, f, indent=2, default=str)