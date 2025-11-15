#!/usr/bin/env python3
"""Monitoring demonstration script.

This script demonstrates the comprehensive monitoring capabilities
by simulating application activity and showing monitoring data.
"""

import asyncio
import random
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from monitoring.config import load_config
from monitoring.metrics import init_metrics_collector
from monitoring.logger import init_logging, get_logger, LogLevel
from monitoring.health import HealthChecker
from monitoring.alerts import AlertManager, AlertSeverity
from monitoring.dashboard import DashboardManager
from utils.performance import timing_decorator, PerformanceTimer


async def simulate_api_requests(metrics, logger, duration_seconds: int = 60):
    """Simulate API requests with varying performance characteristics."""
    logger.info("Starting API request simulation")

    end_time = time.time() + duration_seconds

    while time.time() < end_time:
        # Simulate different types of operations
        operations = [
            ("user_chat", random.uniform(100, 500)),  # 100-500ms
            ("persona_generation", random.uniform(200, 1000)),  # 200-1000ms
            ("message_processing", random.uniform(50, 200)),  # 50-200ms
            ("data_fetch", random.uniform(20, 100)),  # 20-100ms
        ]

        operation, base_duration = random.choice(operations)

        # Add some variability and occasional slowness
        if random.random() < 0.1:  # 10% chance of slow request
            duration = base_duration * random.uniform(2, 5)
            logger.warning(f"Slow operation detected", operation=operation, duration_ms=duration)
        else:
            duration = base_duration * random.uniform(0.8, 1.2)

        # Record the operation
        metrics.record_timing(operation, duration)
        metrics.record_counter(f"{operation}_requests")

        # Simulate occasional errors
        if random.random() < 0.02:  # 2% error rate
            metrics.record_error("TimeoutError", operation)
            logger.error(f"Simulated error in {operation}", operation=operation)

        await asyncio.sleep(random.uniform(0.1, 0.5))

    logger.info("API request simulation completed")


@timing_decorator("expensive_batch_operation")
async def simulate_batch_processing(metrics, logger):
    """Simulate a batch processing operation with profiling."""
    logger.info("Starting batch processing")

    with PerformanceTimer("batch_processing", enable_profiling=True):
        # Simulate work items
        work_items = list(range(100))

        for i, item in enumerate(work_items):
            # Process each item
            processing_time = random.uniform(10, 100)
            await asyncio.sleep(processing_time / 1000)  # Convert to seconds

            metrics.record_timing("process_item", processing_time)

            if i % 20 == 0:
                logger.info(f"Processed {i}/{len(work_items)} items")

    logger.info("Batch processing completed")


async def demonstrate_health_checks(health_checker):
    """Demonstrate health check functionality."""
    print("\n=== Health Check Demonstration ===")

    # Add some example health checks
    health_checker.add_http_check(
        name="example_api",
        url="https://httpbin.org/status/200",
        expected_status=200
    )

    health_checker.add_resource_check("cpu", threshold=50.0)

    # Run health checks
    health_status = await health_checker.check_all()

    print(f"Overall Health: {health_status.status.value.upper()}")
    print(f"Summary: {health_status.summary}")
    print("\nIndividual Checks:")
    for check in health_status.checks:
        status_symbol = "✓" if check.status.value == "healthy" else "✗"
        print(f"  {status_symbol} {check.name}: {check.status.value.upper()}")
        if check.message:
            print(f"    {check.message}")


async def demonstrate_alerting(alert_manager, metrics):
    """Demonstrate alerting functionality."""
    print("\n=== Alerting Demonstration ===")

    # Create a custom alert rule for demonstration
    from monitoring.alerts import AlertRule

    demo_rule = AlertRule(
        name="demo_high_requests",
        condition=lambda m: sum(
            m.store.get_summary(name, 1).count if m.store.get_summary(name, 1) else 0
            for name in m.store.get_all_metric_names()
            if name.endswith("_requests")
        ) > 50,  # Alert if >50 requests
        severity=AlertSeverity.WARNING,
        message_template="High request volume detected: {request_count} requests",
        for_duration=5,  # 5 seconds
        cooldown=30      # 30 seconds cooldown
    )

    alert_manager.add_rule(demo_rule)

    # Generate some requests to trigger the alert
    print("Generating requests to potentially trigger alerts...")
    for i in range(60):  # This should trigger the alert
        metrics.record_counter("demo_requests")
        await asyncio.sleep(0.1)

    # Check for alerts
    alerts = await alert_manager.check_alerts()
    active_alerts = alert_manager.get_active_alerts()

    if active_alerts:
        print(f"\nActive Alerts: {len(active_alerts)}")
        for alert in active_alerts:
            print(f"  - {alert.name}: {alert.message}")
    else:
        print("No active alerts")


async def demonstrate_dashboards(dashboard_manager):
    """Demonstrate dashboard generation."""
    print("\n=== Dashboard Demonstration ===")

    # Generate dashboards
    generated_files = dashboard_manager.generate_all_dashboards()

    print("Generated dashboards:")
    for file_path in generated_files:
        print(f"  - {file_path}")

    # Show dashboard URL
    dashboard_url = dashboard_manager.get_dashboard_url("metrics")
    print(f"\nDashboard URL: {dashboard_url}")


async def main():
    """Main demonstration function."""
    print("=== Infinite Backrooms Monitoring Demonstration ===\n")

    # Initialize monitoring components
    config = load_config()

    # Initialize logging
    init_logging(
        log_file="logs/demo.log",
        log_level=LogLevel.INFO,
        enable_console=True,
        enable_json=False
    )
    logger = get_logger("demo")
    logger.info("Starting monitoring demonstration")

    # Initialize metrics
    metrics = init_metrics_collector()
    logger.info("Metrics collection initialized")

    # Initialize other components
    health_checker = HealthChecker()
    alert_manager = AlertManager(metrics)
    dashboard_manager = DashboardManager()

    print("Monitoring components initialized successfully!")

    try:
        # Run demonstrations
        print("\n1. Simulating API requests (30 seconds)...")
        await asyncio.gather(
            simulate_api_requests(metrics, logger, 30),
            simulate_batch_processing(metrics, logger)
        )

        print("\n2. Demonstrating health checks...")
        await demonstrate_health_checks(health_checker)

        print("\n3. Demonstrating alerting...")
        await demonstrate_alerting(alert_manager, metrics)

        print("\n4. Demonstrating dashboards...")
        await demonstrate_dashboards(dashboard_manager)

        # Show metrics summary
        print("\n=== Metrics Summary ===")
        all_stats = metrics.get_all_stats(window_minutes=5)

        if all_stats["operations"]:
            print("Operations:")
            for op_name, op_stats in all_stats["operations"].items():
                print(f"  {op_name}:")
                print(f"    Requests: {op_stats['requests']['total']}")
                print(f"    Avg Response: {op_stats['duration']['avg_ms']:.1f}ms")
                print(f"    P95 Response: {op_stats['duration']['p95_ms']:.1f}ms")
                print(f"    Error Rate: {op_stats['errors']['rate']:.1%}")

        if all_stats["system"]:
            print("\nSystem Resources:")
            system = all_stats["system"]
            if "cpu" in system:
                print(f"  CPU Usage: {system['cpu']['usage_percent']['avg']:.1f}%")
            if "memory" in system:
                print(f"  Memory Usage: {system['memory']['usage_percent']['avg']:.1f}%")

        print(f"\n=== Demonstration Complete ===")
        print(f"Check the generated dashboards and log files for more details!")
        print(f"Logs: logs/demo.log")
        print(f"Dashboards: monitoring/dashboards/")

    except KeyboardInterrupt:
        print("\nDemonstration interrupted")
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        logger.error("Demonstration failed", exception=e)
    finally:
        # Cleanup
        if metrics:
            metrics.cleanup()


if __name__ == "__main__":
    asyncio.run(main())