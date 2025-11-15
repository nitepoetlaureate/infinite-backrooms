"""Monitoring configuration and setup.

Central configuration for all monitoring components including
metrics collection, alerting rules, health checks, and dashboards.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .alerts import AlertRule, AlertSeverity
from .health import HealthCheck


@dataclass
class MetricsConfig:
    """Configuration for metrics collection."""
    max_samples: int = 10000
    cleanup_interval: int = 300
    resource_monitoring_interval: int = 30
    storage_path: Optional[str] = None
    export_interval: int = 3600  # Export every hour
    retention_hours: int = 24


@dataclass
class LoggingConfig:
    """Configuration for structured logging."""
    log_level: str = "INFO"
    log_file: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_console: bool = True
    enable_json: bool = True
    log_directory: str = "logs"


@dataclass
class HealthCheckConfig:
    """Configuration for health checks."""
    enabled_checks: List[str] = field(default_factory=lambda: [
        "streamlit_app",
        "ollama_api",
        "ollama_inference",
        "cpu_usage",
        "memory_usage",
        "disk_usage"
    ])
    streamlit_url: str = "http://localhost:8501"
    ollama_url: str = "http://localhost:11434"
    check_interval: int = 60
    timeout: int = 10
    cpu_threshold: float = 80.0
    memory_threshold: float = 85.0
    disk_threshold: float = 90.0


@dataclass
class AlertConfig:
    """Configuration for alerting."""
    enabled: bool = True
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_to_emails: List[str] = field(default_factory=list)
    webhook_url: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    check_interval: int = 60
    rules: List[AlertRule] = field(default_factory=list)


@dataclass
class ProfilingConfig:
    """Configuration for performance profiling."""
    enabled: bool = False
    call_profiling: bool = True
    memory_profiling: bool = True
    max_profile_entries: int = 1000
    max_memory_snapshots: int = 100
    export_directory: str = "monitoring/profiles"


@dataclass
class DashboardConfig:
    """Configuration for monitoring dashboards."""
    enabled: bool = True
    output_directory: str = "monitoring/dashboards"
    auto_generate: bool = True
    generate_interval: int = 300  # Every 5 minutes
    serve_dashboard: bool = False
    dashboard_port: int = 8080


@dataclass
class MonitoringConfig:
    """Complete monitoring configuration."""
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    health_checks: HealthCheckConfig = field(default_factory=HealthCheckConfig)
    alerts: AlertConfig = field(default_factory=AlertConfig)
    profiling: ProfilingConfig = field(default_factory=ProfilingConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)

    def __post_init__(self) -> None:
        """Post-initialization setup."""
        # Load configuration from environment variables
        self._load_from_env()

        # Create default alert rules if none provided
        if not self.alerts.rules:
            self.alerts.rules = self._create_default_alert_rules()

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Metrics config
        if os.getenv("MONITORING_METRICS_STORAGE_PATH"):
            self.metrics.storage_path = os.getenv("MONITORING_METRICS_STORAGE_PATH")
        if os.getenv("MONITORING_METRICS_MAX_SAMPLES"):
            self.metrics.max_samples = int(os.getenv("MONITORING_METRICS_MAX_SAMPLES"))

        # Logging config
        if os.getenv("MONITORING_LOG_LEVEL"):
            self.logging.log_level = os.getenv("MONITORING_LOG_LEVEL")
        if os.getenv("MONITORING_LOG_FILE"):
            self.logging.log_file = os.getenv("MONITORING_LOG_FILE")
        if os.getenv("MONITORING_LOG_DIRECTORY"):
            self.logging.log_directory = os.getenv("MONITORING_LOG_DIRECTORY")

        # Health check config
        if os.getenv("STREAMLIT_URL"):
            self.health_checks.streamlit_url = os.getenv("STREAMLIT_URL")
        if os.getenv("OLLAMA_BASE_URL"):
            self.health_checks.ollama_url = os.getenv("OLLAMA_BASE_URL")
        if os.getenv("MONITORING_HEALTH_CHECK_INTERVAL"):
            self.health_checks.check_interval = int(os.getenv("MONITORING_HEALTH_CHECK_INTERVAL"))

        # Alert config
        if os.getenv("ALERT_SMTP_SERVER"):
            self.alerts.smtp_server = os.getenv("ALERT_SMTP_SERVER")
        if os.getenv("ALERT_SMTP_PORT"):
            self.alerts.smtp_port = int(os.getenv("ALERT_SMTP_PORT"))
        if os.getenv("ALERT_SMTP_USERNAME"):
            self.alerts.smtp_username = os.getenv("ALERT_SMTP_USERNAME")
        if os.getenv("ALERT_SMTP_PASSWORD"):
            self.alerts.smtp_password = os.getenv("ALERT_SMTP_PASSWORD")
        if os.getenv("ALERT_SMTP_FROM_EMAIL"):
            self.alerts.smtp_from_email = os.getenv("ALERT_SMTP_FROM_EMAIL")
        if os.getenv("ALERT_SMTP_TO_EMAILS"):
            self.alerts.smtp_to_emails = os.getenv("ALERT_SMTP_TO_EMAILS").split(",")
        if os.getenv("ALERT_WEBHOOK_URL"):
            self.alerts.webhook_url = os.getenv("ALERT_WEBHOOK_URL")
        if os.getenv("ALERT_SLACK_WEBHOOK_URL"):
            self.alerts.slack_webhook_url = os.getenv("ALERT_SLACK_WEBHOOK_URL")
        if os.getenv("ALERT_SLACK_CHANNEL"):
            self.alerts.slack_channel = os.getenv("ALERT_SLACK_CHANNEL")

        # Profiling config
        if os.getenv("MONITORING_PROFILING_ENABLED"):
            self.profiling.enabled = os.getenv("MONITORING_PROFILING_ENABLED").lower() == "true"

        # Dashboard config
        if os.getenv("MONITORING_DASHBOARD_PORT"):
            self.dashboard.dashboard_port = int(os.getenv("MONITORING_DASHBOARD_PORT"))

    def _create_default_alert_rules(self) -> List[AlertRule]:
        """Create default alert rules."""
        rules = []

        # High error rate alert
        rules.append(AlertRule(
            name="high_error_rate",
            condition=lambda m: self._calculate_error_rate(m) > 0.1,  # 10% error rate
            severity=AlertSeverity.ERROR,
            message_template="High error rate detected: {error_rate:.1%}",
            for_duration=300,  # 5 minutes
            cooldown=1800      # 30 minutes
        ))

        # High latency alert
        rules.append(AlertRule(
            name="high_latency",
            condition=lambda m: self._get_avg_latency(m) > 5000,  # 5 seconds
            severity=AlertSeverity.WARNING,
            message_template="High latency detected: {avg_latency_ms:.0f}ms",
            for_duration=120,  # 2 minutes
            cooldown=900       # 15 minutes
        ))

        # High CPU usage alert
        rules.append(AlertRule(
            name="high_cpu_usage",
            condition=lambda m: self._get_cpu_usage(m) > 90,  # 90% CPU
            severity=AlertSeverity.WARNING,
            message_template="High CPU usage: {cpu_percent:.1f}%",
            for_duration=300,  # 5 minutes
            cooldown=900       # 15 minutes
        ))

        # High memory usage alert
        rules.append(AlertRule(
            name="high_memory_usage",
            condition=lambda m: self._get_memory_usage(m) > 90,  # 90% memory
            severity=AlertSeverity.WARNING,
            message_template="High memory usage: {memory_percent:.1f}%",
            for_duration=300,  # 5 minutes
            cooldown=900       # 15 minutes
        ))

        return rules

    def _calculate_error_rate(self, metrics) -> float:
        """Calculate current error rate."""
        try:
            error_summary = metrics.store.get_summary("errors.count", window_minutes=5)
            if not error_summary:
                return 0.0

            total_requests = 0
            for name in metrics.store.get_all_metric_names():
                if name.startswith("operation.") and name.endswith(".duration_ms"):
                    summary = metrics.store.get_summary(name, window_minutes=5)
                    if summary:
                        total_requests += summary.count

            if total_requests == 0:
                return 0.0

            return error_summary.count / total_requests
        except:
            return 0.0

    def _get_avg_latency(self, metrics) -> float:
        """Get average latency across all operations."""
        try:
            latencies = []
            for name in metrics.store.get_all_metric_names():
                if name.startswith("operation.") and name.endswith(".duration_ms"):
                    summary = metrics.store.get_summary(name, window_minutes=5)
                    if summary and summary.avg > 0:
                        latencies.append(summary.avg)

            return sum(latencies) / len(latencies) if latencies else 0.0
        except:
            return 0.0

    def _get_cpu_usage(self, metrics) -> float:
        """Get current CPU usage."""
        try:
            summary = metrics.store.get_summary("system.cpu.percent", window_minutes=5)
            return summary.avg if summary else 0.0
        except:
            return 0.0

    def _get_memory_usage(self, metrics) -> float:
        """Get current memory usage."""
        try:
            summary = metrics.store.get_summary("system.memory.percent", window_minutes=5)
            return summary.avg if summary else 0.0
        except:
            return 0.0


def load_config(config_file: Optional[str] = None) -> MonitoringConfig:
    """Load monitoring configuration.

    Args:
        config_file: Optional path to configuration file

    Returns:
        Monitoring configuration
    """
    config = MonitoringConfig()

    # Load from file if provided
    if config_file and Path(config_file).exists():
        import json
        with open(config_file, 'r') as f:
            data = json.load(f)

        # Update config with loaded data (simplified)
        if 'metrics' in data:
            for key, value in data['metrics'].items():
                if hasattr(config.metrics, key):
                    setattr(config.metrics, key, value)

        if 'logging' in data:
            for key, value in data['logging'].items():
                if hasattr(config.logging, key):
                    setattr(config.logging, key, value)

        if 'health_checks' in data:
            for key, value in data['health_checks'].items():
                if hasattr(config.health_checks, key):
                    setattr(config.health_checks, key, value)

        if 'alerts' in data:
            for key, value in data['alerts'].items():
                if hasattr(config.alerts, key):
                    setattr(config.alerts, key, value)

        if 'profiling' in data:
            for key, value in data['profiling'].items():
                if hasattr(config.profiling, key):
                    setattr(config.profiling, key, value)

        if 'dashboard' in data:
            for key, value in data['dashboard'].items():
                if hasattr(config.dashboard, key):
                    setattr(config.dashboard, key, value)

    return config


def save_config(config: MonitoringConfig, config_file: str) -> None:
    """Save monitoring configuration to file.

    Args:
        config: Configuration to save
        config_file: Output file path
    """
    import json
    from dataclasses import asdict

    config_data = {
        'metrics': asdict(config.metrics),
        'logging': asdict(config.logging),
        'health_checks': asdict(config.health_checks),
        'alerts': asdict(config.alerts),
        'profiling': asdict(config.profiling),
        'dashboard': asdict(config.dashboard),
    }

    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)