#!/usr/bin/env python3
"""Start comprehensive monitoring for Infinite AI Backrooms.

This script initializes and starts all monitoring components including
metrics collection, health checks, alerting, and dashboards.
"""

import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from monitoring.config import load_config
from monitoring.metrics import init_metrics_collector
from monitoring.logger import init_logging, get_logger, LogLevel
from monitoring.health import HealthChecker
from monitoring.alerts import AlertManager
from monitoring.dashboard import DashboardManager
from monitoring.profiler import PerformanceProfiler


class MonitoringService:
    """Main monitoring service that coordinates all monitoring components."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize monitoring service.

        Args:
            config_file: Optional path to configuration file
        """
        self.config = load_config(config_file)
        self.logger = None
        self.metrics_collector = None
        self.health_checker = None
        self.alert_manager = None
        self.dashboard_manager = None
        self.profiler = None
        self.running = False
        self.tasks = []

    async def start(self) -> None:
        """Start all monitoring components."""
        print("Starting Infinite Backrooms Monitoring Service...")

        # Initialize logging first
        await self._init_logging()
        self.logger.info("Monitoring service starting")

        # Initialize metrics collection
        await self._init_metrics()
        self.logger.info("Metrics collection initialized")

        # Initialize health checks
        await self._init_health_checks()
        self.logger.info("Health checks initialized")

        # Initialize alerting
        await self._init_alerts()
        self.logger.info("Alert system initialized")

        # Initialize profiling
        await self._init_profiling()
        self.logger.info("Performance profiling initialized")

        # Initialize dashboards
        await self._init_dashboards()
        self.logger.info("Dashboard system initialized")

        # Start background tasks
        await self._start_background_tasks()

        self.running = True
        self.logger.info("Monitoring service started successfully")

    async def stop(self) -> None:
        """Stop all monitoring components."""
        if not self.running:
            return

        self.logger.info("Monitoring service stopping")
        self.running = False

        # Cancel all background tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Cleanup components
        if self.metrics_collector:
            self.metrics_collector.cleanup()

        self.logger.info("Monitoring service stopped")

    async def _init_logging(self) -> None:
        """Initialize structured logging."""
        log_file = None
        if self.config.logging.log_file:
            log_file = self.config.logging.log_file
        else:
            # Create default log file
            log_dir = Path(self.config.logging.log_directory)
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = str(log_dir / "monitoring.log")

        init_logging(
            log_file=log_file,
            log_level=LogLevel(self.config.logging.log_level),
            max_file_size=self.config.logging.max_file_size,
            backup_count=self.config.logging.backup_count,
            enable_console=self.config.logging.enable_console,
            enable_json=self.config.logging.enable_json
        )

        self.logger = get_logger("monitoring_service")

    async def _init_metrics(self) -> None:
        """Initialize metrics collection."""
        storage_path = None
        if self.config.metrics.storage_path:
            storage_path = self.config.metrics.storage_path

        self.metrics_collector = init_metrics_collector(storage_path)

    async def _init_health_checks(self) -> None:
        """Initialize health checks."""
        self.health_checker = HealthChecker()

        # Add health checks based on configuration
        if "streamlit_app" in self.config.health_checks.enabled_checks:
            self.health_checker.add_http_check(
                name="streamlit_app",
                url=self.config.health_checks.streamlit_url + "/_stcore/health",
                expected_status=200,
                timeout=self.config.health_checks.timeout
            )

        if "ollama_api" in self.config.health_checks.enabled_checks:
            self.health_checker.add_http_check(
                name="ollama_api",
                url=self.config.health_checks.ollama_url + "/api/tags",
                expected_status=200,
                timeout=self.config.health_checks.timeout
            )

        if "ollama_inference" in self.config.health_checks.enabled_checks:
            async def check_ollama_inference():
                import aiohttp
                try:
                    async with aiohttp.ClientSession() as session:
                        payload = {
                            "model": "tinyllama",
                            "prompt": "Hello",
                            "stream": False,
                        }
                        async with session.post(
                            f"{self.config.health_checks.ollama_url}/api/generate",
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=30),
                        ) as response:
                            if response.status == 200:
                                return ("healthy", "Inference successful", {})
                            else:
                                return ("unhealthy", f"Inference failed with status {response.status}", {})
                except Exception as e:
                    return ("unhealthy", f"Inference error: {str(e)}", {})

            self.health_checker.add_custom_check("ollama_inference", check_ollama_inference)

        if "cpu_usage" in self.config.health_checks.enabled_checks:
            self.health_checker.add_resource_check(
                "cpu",
                threshold=self.config.health_checks.cpu_threshold,
                timeout=self.config.health_checks.timeout
            )

        if "memory_usage" in self.config.health_checks.enabled_checks:
            self.health_checker.add_resource_check(
                "memory",
                threshold=self.config.health_checks.memory_threshold,
                timeout=self.config.health_checks.timeout
            )

        if "disk_usage" in self.config.health_checks.enabled_checks:
            self.health_checker.add_resource_check(
                "disk",
                threshold=self.config.health_checks.disk_threshold,
                timeout=self.config.health_checks.timeout
            )

    async def _init_alerts(self) -> None:
        """Initialize alert system."""
        if not self.config.alerts.enabled:
            return

        self.alert_manager = AlertManager(self.metrics_collector)

        # Add default rules
        for rule in self.config.alerts.rules:
            self.alert_manager.add_rule(rule)

        # Add notifiers based on configuration
        if self.config.alerts.smtp_server and self.config.alerts.smtp_username:
            smtp_config = {
                "server": self.config.alerts.smtp_server,
                "port": self.config.alerts.smtp_port,
                "username": self.config.alerts.smtp_username,
                "password": self.config.alerts.smtp_password,
                "from_email": self.config.alerts.smtp_from_email,
                "to_emails": self.config.alerts.smtp_to_emails
            }
            self.alert_manager.add_email_notifier(smtp_config)

        if self.config.alerts.webhook_url:
            self.alert_manager.add_webhook_notifier(self.config.alerts.webhook_url)

        if self.config.alerts.slack_webhook_url:
            self.alert_manager.add_slack_notifier(
                self.config.alerts.slack_webhook_url,
                self.config.alerts.slack_channel
            )

    async def _init_profiling(self) -> None:
        """Initialize performance profiling."""
        if not self.config.profiling.enabled:
            return

        self.profiler = PerformanceProfiler(
            enable_call_profiling=self.config.profiling.call_profiling,
            enable_memory_profiling=self.config.profiling.memory_profiling
        )

    async def _init_dashboards(self) -> None:
        """Initialize dashboard system."""
        if not self.config.dashboard.enabled:
            return

        self.dashboard_manager = DashboardManager(self.config.dashboard.output_directory)

    async def _start_background_tasks(self) -> None:
        """Start background monitoring tasks."""
        # Health check task
        if self.health_checker:
            task = asyncio.create_task(
                self.health_checker.run_periodic_checks(
                    interval=self.config.health_checks.check_interval,
                    callback=self._health_check_callback
                )
            )
            self.tasks.append(task)

        # Alert check task
        if self.alert_manager:
            task = asyncio.create_task(
                self.alert_manager.run_periodic_checks(
                    interval=self.config.alerts.check_interval
                )
            )
            self.tasks.append(task)

        # Dashboard generation task
        if self.dashboard_manager and self.config.dashboard.auto_generate:
            task = asyncio.create_task(
                self._dashboard_generation_task()
            )
            self.tasks.append(task)

        # Metrics export task
        if self.metrics_collector:
            task = asyncio.create_task(
                self._metrics_export_task()
            )
            self.tasks.append(task)

    async def _health_check_callback(self, health_result) -> None:
        """Callback for health check results."""
        self.logger.info(
            f"Health check completed: {health_result.status.value} - {health_result.summary}"
        )

        # Record health status metrics
        health_status_value = 1 if health_result.status.value == "healthy" else 0
        self.metrics_collector.record_gauge(
            "health.overall_status",
            health_status_value,
            labels={"status": health_result.status.value}
        )

    async def _dashboard_generation_task(self) -> None:
        """Background task to generate dashboards."""
        while self.running:
            try:
                if self.dashboard_manager:
                    files = self.dashboard_manager.generate_all_dashboards()
                    self.logger.debug(f"Generated dashboards: {files}")
            except Exception as e:
                self.logger.error(f"Error generating dashboards: {e}")

            await asyncio.sleep(self.config.dashboard.generate_interval)

    async def _metrics_export_task(self) -> None:
        """Background task to export metrics."""
        while self.running:
            try:
                if self.metrics_collector and self.config.metrics.storage_path:
                    export_file = Path(self.config.metrics.storage_path) / "metrics_export.json"
                    self.metrics_collector.export_metrics(str(export_file))
                    self.logger.debug(f"Metrics exported to {export_file}")
            except Exception as e:
                self.logger.error(f"Error exporting metrics: {e}")

            await asyncio.sleep(self.config.metrics.export_interval)


async def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Start monitoring service")
    parser.add_argument(
        "--config",
        help="Path to monitoring configuration file"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as daemon (background process)"
    )

    args = parser.parse_args()

    # Create monitoring service
    service = MonitoringService(args.config)

    # Setup signal handlers
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, stopping monitoring service...")
        asyncio.create_task(service.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start the service
        await service.start()

        # Keep running until stopped
        while service.running:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nKeyboard interrupt received")
    except Exception as e:
        print(f"Error in monitoring service: {e}")
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())