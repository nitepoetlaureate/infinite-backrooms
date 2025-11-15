"""Alerting and notification system for monitoring.

Provides configurable alerts based on metrics thresholds,
error rates, and system health status.
"""

from __future__ import annotations

import json
import smtplib
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from email.mime.text import MimeText
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Set, Union

from .metrics import MetricsCollector, get_metrics_collector


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert lifecycle status."""
    FIRING = "firing"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class Alert:
    """Single alert instance."""
    name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)
    fingerprint: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "severity": self.severity.value,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels,
            "fingerprint": self.fingerprint,
        }

    def generate_fingerprint(self) -> str:
        """Generate unique fingerprint for this alert."""
        import hashlib
        content = f"{self.name}:{self.severity.value}:{frozenset(self.labels.items())}"
        return hashlib.md5(content.encode()).hexdigest()[:16]


class AlertNotifier(Protocol):
    """Protocol for alert notifiers."""

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert notification.

        Args:
            alert: Alert to send

        Returns:
            True if successful, False otherwise
        """
        ...


class EmailNotifier:
    """Email alert notifier."""

    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, from_email: str, to_emails: List[str]):
        """Initialize email notifier.

        Args:
            smtp_server: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
            from_email: From email address
            to_emails: List of recipient email addresses
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via email.

        Args:
            alert: Alert to send

        Returns:
            True if successful, False otherwise
        """
        try:
            subject = f"[{alert.severity.value.upper()}] {alert.name}"
            body = self._format_email_body(alert)

            msg = MimeText(body)
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Failed to send email alert: {e}")
            return False

    def _format_email_body(self, alert: Alert) -> str:
        """Format alert as email body.

        Args:
            alert: Alert to format

        Returns:
            Formatted email body
        """
        body = f"""
Alert: {alert.name}
Severity: {alert.severity.value.upper()}
Status: {alert.status.value.upper()}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Message:
{alert.message}

Details:
{json.dumps(alert.details, indent=2)}
"""
        return body


class WebhookNotifier:
    """Webhook alert notifier."""

    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        """Initialize webhook notifier.

        Args:
            webhook_url: Webhook URL
            headers: Optional HTTP headers
        """
        self.webhook_url = webhook_url
        self.headers = headers or {}

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via webhook.

        Args:
            alert: Alert to send

        Returns:
            True if successful, False otherwise
        """
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                payload = alert.to_dict()
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    return response.status < 400
        except Exception as e:
            print(f"Failed to send webhook alert: {e}")
            return False


class SlackNotifier:
    """Slack alert notifier."""

    def __init__(self, webhook_url: str, channel: Optional[str] = None):
        """Initialize Slack notifier.

        Args:
            webhook_url: Slack webhook URL
            channel: Optional Slack channel
        """
        self.webhook_url = webhook_url
        self.channel = channel

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to Slack.

        Args:
            alert: Alert to send

        Returns:
            True if successful, False otherwise
        """
        try:
            import aiohttp

            color_map = {
                AlertSeverity.INFO: "#36a64f",      # green
                AlertSeverity.WARNING: "#ff9500",   # orange
                AlertSeverity.ERROR: "#ff0000",     # red
                AlertSeverity.CRITICAL: "#8b0000",  # dark red
            }

            payload = {
                "text": f"Alert: {alert.name}",
                "attachments": [{
                    "color": color_map.get(alert.severity, "#808080"),
                    "title": alert.name,
                    "text": alert.message,
                    "fields": [
                        {"title": "Severity", "value": alert.severity.value.upper(), "short": True},
                        {"title": "Status", "value": alert.status.value.upper(), "short": True},
                        {"title": "Time", "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'), "short": True},
                    ],
                    "footer": "Infinite Backrooms Monitoring",
                    "ts": int(alert.timestamp.timestamp()),
                }]
            }

            if self.channel:
                payload["channel"] = self.channel

            if alert.details:
                details_text = "\n".join([f"{k}: {v}" for k, v in alert.details.items()])
                payload["attachments"][0]["fields"].append({
                    "title": "Details",
                    "value": f"```\n{details_text}\n```",
                    "short": False
                })

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    return response.status < 400
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")
            return False


class AlertRule:
    """Alert rule definition."""

    def __init__(
        self,
        name: str,
        condition: callable,
        severity: AlertSeverity,
        message_template: str,
        labels: Optional[Dict[str, str]] = None,
        for_duration: int = 0,
        cooldown: int = 300
    ):
        """Initialize alert rule.

        Args:
            name: Rule name
            condition: Function that returns True if alert should fire
            severity: Alert severity
            message_template: Message template with {variable} placeholders
            labels: Additional labels for the alert
            for_duration: Duration in seconds condition must be true before alerting
            cooldown: Cooldown period in seconds between alerts
        """
        self.name = name
        self.condition = condition
        self.severity = severity
        self.message_template = message_template
        self.labels = labels or {}
        self.for_duration = for_duration
        self.cooldown = cooldown
        self._last_fired: Optional[datetime] = None
        self._condition_start: Optional[datetime] = None

    def should_fire(self, metrics: MetricsCollector) -> tuple[bool, Dict[str, Any]]:
        """Check if alert should fire.

        Args:
            metrics: Metrics collector instance

        Returns:
            Tuple of (should_fire, context_data)
        """
        try:
            should_fire, context = self.condition(metrics)
            now = datetime.now()

            if should_fire:
                if self._condition_start is None:
                    self._condition_start = now

                # Check if condition has been true long enough
                duration_met = (now - self._condition_start).total_seconds() >= self.for_duration

                # Check cooldown
                cooldown_met = (
                    self._last_fired is None or
                    (now - self._last_fired).total_seconds() >= self.cooldown
                )

                if duration_met and cooldown_met:
                    return True, context
            else:
                # Reset condition start time
                self._condition_start = None

            return False, {}
        except Exception as e:
            print(f"Error in alert rule '{self.name}': {e}")
            return False, {}

    def fire_alert(self, context: Dict[str, Any]) -> Alert:
        """Create and fire alert.

        Args:
            context: Context data for message formatting

        Returns:
            Created Alert
        """
        # Format message with context
        try:
            message = self.message_template.format(**context)
        except KeyError:
            message = self.message_template  # Fallback if formatting fails

        alert = Alert(
            name=self.name,
            severity=self.severity,
            status=AlertStatus.FIRING,
            message=message,
            details=context,
            labels=self.labels.copy()
        )

        alert.fingerprint = alert.generate_fingerprint()
        self._last_fired = datetime.now()
        return alert


class AlertManager:
    """Main alert management system."""

    def __init__(self, metrics: Optional[MetricsCollector] = None):
        """Initialize alert manager.

        Args:
            metrics: Metrics collector instance
        """
        self.metrics = metrics or get_metrics_collector()
        self.rules: List[AlertRule] = []
        self.notifiers: List[AlertNotifier] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.max_history = 1000

    def add_rule(self, rule: AlertRule) -> None:
        """Add alert rule.

        Args:
            rule: Alert rule to add
        """
        self.rules.append(rule)

    def add_notifier(self, notifier: AlertNotifier) -> None:
        """Add alert notifier.

        Args:
            notifier: Notifier to add
        """
        self.notifiers.append(notifier)

    def add_email_notifier(self, smtp_config: Dict[str, Any]) -> None:
        """Add email notifier.

        Args:
            smtp_config: SMTP configuration dictionary
        """
        notifier = EmailNotifier(
            smtp_server=smtp_config["server"],
            smtp_port=smtp_config["port"],
            username=smtp_config["username"],
            password=smtp_config["password"],
            from_email=smtp_config["from_email"],
            to_emails=smtp_config["to_emails"]
        )
        self.add_notifier(notifier)

    def add_webhook_notifier(self, webhook_url: str, headers: Optional[Dict[str, str]] = None) -> None:
        """Add webhook notifier.

        Args:
            webhook_url: Webhook URL
            headers: Optional HTTP headers
        """
        notifier = WebhookNotifier(webhook_url, headers)
        self.add_notifier(notifier)

    def add_slack_notifier(self, webhook_url: str, channel: Optional[str] = None) -> None:
        """Add Slack notifier.

        Args:
            webhook_url: Slack webhook URL
            channel: Optional Slack channel
        """
        notifier = SlackNotifier(webhook_url, channel)
        self.add_notifier(notifier)

    async def check_alerts(self) -> List[Alert]:
        """Check all alert rules and fire if needed.

        Returns:
            List of newly fired alerts
        """
        new_alerts = []

        for rule in self.rules:
            should_fire, context = rule.should_fire(self.metrics)
            fingerprint = f"{rule.name}:{rule.severity.value}"

            if should_fire and fingerprint not in self.active_alerts:
                # Fire new alert
                alert = rule.fire_alert(context)
                new_alerts.append(alert)
                self.active_alerts[fingerprint] = alert

                # Record metrics
                self.metrics.record_counter("alerts.fired", labels={
                    "rule": rule.name,
                    "severity": rule.severity.value
                })

            elif not should_fire and fingerprint in self.active_alerts:
                # Resolve alert
                resolved_alert = self.active_alerts[fingerprint]
                resolved_alert.status = AlertStatus.RESOLVED
                resolved_alert.timestamp = datetime.now()

                # Move to history
                self.alert_history.append(resolved_alert)
                del self.active_alerts[fingerprint]

                # Record metrics
                self.metrics.record_counter("alerts.resolved", labels={
                    "rule": rule.name,
                    "severity": rule.severity.value
                })

                # Send resolution notification
                await self._send_notification(resolved_alert)

        # Send notifications for new alerts
        for alert in new_alerts:
            await self._send_notification(alert)
            self.alert_history.append(alert)

        # Trim history if needed
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]

        return new_alerts

    async def _send_notification(self, alert: Alert) -> None:
        """Send alert to all notifiers.

        Args:
            alert: Alert to send
        """
        for notifier in self.notifiers:
            try:
                success = await notifier.send_alert(alert)
                if success:
                    self.metrics.record_counter("alerts.notifications_sent")
                else:
                    self.metrics.record_counter("alerts.notifications_failed")
            except Exception as e:
                print(f"Error sending notification: {e}")
                self.metrics.record_counter("alerts.notifications_failed")

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts.

        Returns:
            List of active alerts
        """
        return list(self.active_alerts.values())

    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for time period.

        Args:
            hours: Number of hours to look back

        Returns:
            List of alerts from time period
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.alert_history
            if alert.timestamp >= cutoff_time
        ]

    def create_common_rules(self) -> None:
        """Create common alert rules for typical monitoring scenarios."""

        # High error rate
        self.add_rule(AlertRule(
            name="high_error_rate",
            condition=lambda m: self._calculate_error_rate(m) > 0.1,  # 10% error rate
            severity=AlertSeverity.ERROR,
            message_template="High error rate detected: {error_rate:.1%}",
            for_duration=300,  # 5 minutes
            cooldown=1800      # 30 minutes
        ))

        # High latency
        self.add_rule(AlertRule(
            name="high_latency",
            condition=lambda m: self._get_avg_latency(m) > 5000,  # 5 seconds
            severity=AlertSeverity.WARNING,
            message_template="High latency detected: {avg_latency_ms:.0f}ms",
            for_duration=120,  # 2 minutes
            cooldown=900       # 15 minutes
        ))

        # High CPU usage
        self.add_rule(AlertRule(
            name="high_cpu_usage",
            condition=lambda m: self._get_cpu_usage(m) > 90,  # 90% CPU
            severity=AlertSeverity.WARNING,
            message_template="High CPU usage: {cpu_percent:.1f}%",
            for_duration=300,  # 5 minutes
            cooldown=900       # 15 minutes
        ))

        # High memory usage
        self.add_rule(AlertRule(
            name="high_memory_usage",
            condition=lambda m: self._get_memory_usage(m) > 90,  # 90% memory
            severity=AlertSeverity.WARNING,
            message_template="High memory usage: {memory_percent:.1f}%",
            for_duration=300,  # 5 minutes
            cooldown=900       # 15 minutes
        ))

    def _calculate_error_rate(self, metrics: MetricsCollector) -> float:
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

    def _get_avg_latency(self, metrics: MetricsCollector) -> float:
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

    def _get_cpu_usage(self, metrics: MetricsCollector) -> float:
        """Get current CPU usage."""
        try:
            summary = metrics.store.get_summary("system.cpu.percent", window_minutes=5)
            return summary.avg if summary else 0.0
        except:
            return 0.0

    def _get_memory_usage(self, metrics: MetricsCollector) -> float:
        """Get current memory usage."""
        try:
            summary = metrics.store.get_summary("system.memory.percent", window_minutes=5)
            return summary.avg if summary else 0.0
        except:
            return 0.0

    async def run_periodic_checks(self, interval: int = 60) -> None:
        """Run periodic alert checks.

        Args:
            interval: Check interval in seconds
        """
        import asyncio

        while True:
            try:
                await self.check_alerts()
            except Exception as e:
                print(f"Error in periodic alert check: {e}")

            await asyncio.sleep(interval)

    def export_alerts(self, filepath: str) -> None:
        """Export alert data to JSON file.

        Args:
            filepath: Output file path
        """
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "active_alerts": [alert.to_dict() for alert in self.get_active_alerts()],
            "alert_history": [alert.to_dict() for alert in self.get_alert_history(24)],
            "rules_count": len(self.rules),
            "notifiers_count": len(self.notifiers),
        }

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)