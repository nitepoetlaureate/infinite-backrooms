"""Health checking and system status monitoring.

Provides comprehensive health checks for application components,
dependencies, and system resources.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import aiohttp
import psutil

from .metrics import get_metrics_collector


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a single health check."""
    name: str
    status: HealthStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class SystemHealth:
    """Overall system health status."""
    status: HealthStatus
    timestamp: datetime
    checks: List[HealthCheckResult] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "summary": self.summary,
            "checks": [check.to_dict() for check in self.checks],
        }


class HealthCheck:
    """Base class for health checks."""

    def __init__(self, name: str, timeout: int = 10):
        """Initialize health check.

        Args:
            name: Check name
            timeout: Timeout in seconds
        """
        self.name = name
        self.timeout = timeout

    async def check(self) -> HealthCheckResult:
        """Perform the health check.

        Returns:
            HealthCheckResult with check outcome
        """
        start_time = datetime.now()
        try:
            result = await self._do_check()
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            result.duration_ms = duration_ms
            result.timestamp = start_time
            return result
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {str(e)}",
                duration_ms=duration_ms,
                timestamp=start_time
            )

    async def _do_check(self) -> HealthCheckResult:
        """Implement actual health check logic.

        Returns:
            HealthCheckResult
        """
        raise NotImplementedError


class HTTPHealthCheck(HealthCheck):
    """Health check for HTTP endpoints."""

    def __init__(self, name: str, url: str, expected_status: int = 200, **kwargs):
        """Initialize HTTP health check.

        Args:
            name: Check name
            url: URL to check
            expected_status: Expected HTTP status code
            **kwargs: Additional arguments for HealthCheck
        """
        super().__init__(name, **kwargs)
        self.url = url
        self.expected_status = expected_status

    async def _do_check(self) -> HealthCheckResult:
        """Check HTTP endpoint."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.url,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                details = {
                    "url": self.url,
                    "status_code": response.status,
                    "expected_status": self.expected_status,
                }

                if response.status == self.expected_status:
                    return HealthCheckResult(
                        name=self.name,
                        status=HealthStatus.HEALTHY,
                        message=f"HTTP check successful (status {response.status})",
                        details=details
                    )
                else:
                    return HealthCheckResult(
                        name=self.name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Unexpected status code: {response.status}",
                        details=details
                    )


class DatabaseHealthCheck(HealthCheck):
    """Health check for database connections."""

    def __init__(self, name: str, connection_pool, **kwargs):
        """Initialize database health check.

        Args:
            name: Check name
            connection_pool: Database connection pool
            **kwargs: Additional arguments for HealthCheck
        """
        super().__init__(name, **kwargs)
        self.connection_pool = connection_pool

    async def _do_check(self) -> HealthCheckResult:
        """Check database connectivity."""
        try:
            # Simple connection test
            async with self.connection_pool.acquire() as conn:
                await conn.execute("SELECT 1")

            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message="Database connection successful"
            )
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}"
            )


class ResourceHealthCheck(HealthCheck):
    """Health check for system resources."""

    def __init__(self, name: str, resource_type: str, threshold: float, **kwargs):
        """Initialize resource health check.

        Args:
            name: Check name
            resource_type: Type of resource (cpu, memory, disk)
            threshold: Warning threshold (percentage)
            **kwargs: Additional arguments for HealthCheck
        """
        super().__init__(name, **kwargs)
        self.resource_type = resource_type.lower()
        self.threshold = threshold

    async def _do_check(self) -> HealthCheckResult:
        """Check system resource usage."""
        try:
            if self.resource_type == "cpu":
                usage = psutil.cpu_percent(interval=1)
                details = {"cpu_percent": usage}
            elif self.resource_type == "memory":
                memory = psutil.virtual_memory()
                usage = memory.percent
                details = {
                    "memory_percent": usage,
                    "available_gb": memory.available / (1024**3),
                    "used_gb": memory.used / (1024**3)
                }
            elif self.resource_type == "disk":
                disk = psutil.disk_usage('/')
                usage = (disk.used / disk.total) * 100
                details = {
                    "disk_percent": usage,
                    "free_gb": disk.free / (1024**3),
                    "used_gb": disk.used / (1024**3)
                }
            else:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Unknown resource type: {self.resource_type}"
                )

            if usage < self.threshold * 0.8:
                status = HealthStatus.HEALTHY
                message = f"{self.resource_type} usage normal: {usage:.1f}%"
            elif usage < self.threshold:
                status = HealthStatus.DEGRADED
                message = f"{self.resource_type} usage elevated: {usage:.1f}%"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"{self.resource_type} usage critical: {usage:.1f}%"

            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details=details
            )
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Resource check failed: {str(e)}"
            )


class CustomHealthCheck(HealthCheck):
    """Health check using custom async function."""

    def __init__(self, name: str, check_func: callable, **kwargs):
        """Initialize custom health check.

        Args:
            name: Check name
            check_func: Async function that returns (status, message, details)
            **kwargs: Additional arguments for HealthCheck
        """
        super().__init__(name, **kwargs)
        self.check_func = check_func

    async def _do_check(self) -> HealthCheckResult:
        """Execute custom check function."""
        result = await self.check_func()

        if isinstance(result, tuple) and len(result) >= 2:
            status, message = result[:2]
            details = result[2] if len(result) > 2 else {}
        else:
            status = HealthStatus.UNHEALTHY
            message = "Invalid check function result"
            details = {}

        return HealthCheckResult(
            name=self.name,
            status=status,
            message=message,
            details=details
        )


class HealthChecker:
    """Main health checking system."""

    def __init__(self):
        """Initialize health checker."""
        self.checks: List[HealthCheck] = []
        self.metrics = get_metrics_collector()

    def add_check(self, check: HealthCheck) -> None:
        """Add a health check.

        Args:
            check: Health check to add
        """
        self.checks.append(check)

    def add_http_check(self, name: str, url: str, expected_status: int = 200, **kwargs) -> None:
        """Add HTTP endpoint health check.

        Args:
            name: Check name
            url: URL to check
            expected_status: Expected HTTP status
            **kwargs: Additional arguments for HealthCheck
        """
        self.add_check(HTTPHealthCheck(name, url, expected_status, **kwargs))

    def add_resource_check(self, resource_type: str, threshold: float = 80.0, **kwargs) -> None:
        """Add system resource health check.

        Args:
            resource_type: Resource type (cpu, memory, disk)
            threshold: Warning threshold percentage
            **kwargs: Additional arguments for HealthCheck
        """
        name = kwargs.pop("name", f"{resource_type}_usage")
        self.add_check(ResourceHealthCheck(name, resource_type, threshold, **kwargs))

    def add_custom_check(self, name: str, check_func: callable, **kwargs) -> None:
        """Add custom health check.

        Args:
            name: Check name
            check_func: Async check function
            **kwargs: Additional arguments for HealthCheck
        """
        self.add_check(CustomHealthCheck(name, check_func, **kwargs))

    async def check_all(self) -> SystemHealth:
        """Run all health checks.

        Returns:
            SystemHealth with all check results
        """
        start_time = datetime.now()

        # Run all checks concurrently
        tasks = [check.check() for check in self.checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        check_results = []
        for result in results:
            if isinstance(result, Exception):
                check_results.append(HealthCheckResult(
                    name="unknown",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check execution failed: {str(result)}"
                ))
            else:
                check_results.append(result)

        # Determine overall status
        if not check_results:
            overall_status = HealthStatus.UNKNOWN
            summary = "No health checks configured"
        else:
            healthy_count = sum(1 for r in check_results if r.status == HealthStatus.HEALTHY)
            degraded_count = sum(1 for r in check_results if r.status == HealthStatus.DEGRADED)
            unhealthy_count = sum(1 for r in check_results if r.status == HealthStatus.UNHEALTHY)

            if unhealthy_count == 0 and degraded_count == 0:
                overall_status = HealthStatus.HEALTHY
                summary = f"All {len(check_results)} checks passed"
            elif unhealthy_count == 0:
                overall_status = HealthStatus.DEGRADED
                summary = f"{healthy_count} healthy, {degraded_count} degraded"
            else:
                overall_status = HealthStatus.UNHEALTHY
                summary = f"{healthy_count} healthy, {degraded_count} degraded, {unhealthy_count} unhealthy"

        # Record metrics
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.metrics.record_timing("health_check.total_duration_ms", duration_ms)
        self.metrics.record_counter("health_check.checks_executed", len(check_results))

        for status in HealthStatus:
            count = sum(1 for r in check_results if r.status == status)
            if count > 0:
                self.metrics.record_gauge(f"health_check.{status.value}_count", count)

        return SystemHealth(
            status=overall_status,
            timestamp=start_time,
            checks=check_results,
            summary=summary
        )

    async def check_single(self, name: str) -> Optional[HealthCheckResult]:
        """Run a single health check by name.

        Args:
            name: Check name

        Returns:
            HealthCheckResult or None if not found
        """
        for check in self.checks:
            if check.name == name:
                return await check.check()
        return None

    def get_check_names(self) -> List[str]:
        """Get names of all configured checks.

        Returns:
            List of check names
        """
        return [check.name for check in self.checks]

    async def run_periodic_checks(self, interval: int = 60, callback: Optional[callable] = None) -> None:
        """Run health checks periodically.

        Args:
            interval: Check interval in seconds
            callback: Optional callback function to call with results
        """
        while True:
            try:
                health = await self.check_all()
                if callback:
                    await callback(health)
            except Exception as e:
                print(f"Error in periodic health check: {e}")

            await asyncio.sleep(interval)

    def export_health_status(self, filepath: str) -> None:
        """Export current health status to file.

        Args:
            filepath: Output file path
        """
        # This would need to be async to get current status
        # For now, create a placeholder
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "configured_checks": self.get_check_names(),
            "note": "Use check_all() to get current status"
        }

        with open(filepath, 'w') as f:
            json.dump(health_data, f, indent=2)