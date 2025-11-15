"""Dashboard generation and management for monitoring.

Creates dashboards for visualizing metrics, health status,
and system performance data.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .health import HealthChecker
from .metrics import get_metrics_collector


class DashboardManager:
    """Dashboard management and generation."""

    def __init__(self, output_dir: str = "monitoring/dashboards"):
        """Initialize dashboard manager.

        Args:
            output_dir: Directory to store dashboard files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metrics = get_metrics_collector()

    def generate_metrics_dashboard(self, window_minutes: int = 60) -> Dict[str, Any]:
        """Generate metrics dashboard data.

        Args:
            window_minutes: Time window for metrics

        Returns:
            Dashboard data dictionary
        """
        stats = self.metrics.get_all_stats(window_minutes)

        dashboard = {
            "title": "Infinite Backrooms - Metrics Dashboard",
            "generated_at": datetime.now().isoformat(),
            "window_minutes": window_minutes,
            "overview": self._generate_overview_section(stats),
            "system_metrics": self._generate_system_section(stats),
            "operations": self._generate_operations_section(stats),
            "alerts": self._generate_alerts_section(),
        }

        return dashboard

    def _generate_overview_section(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overview section of dashboard.

        Args:
            stats: Statistics data

        Returns:
            Overview section data
        """
        # Calculate key metrics
        total_operations = len(stats.get("operations", {}))
        total_requests = sum(
            op.get("requests", {}).get("total", 0)
            for op in stats.get("operations", {}).values()
        )

        # Calculate error rate
        total_errors = sum(
            op.get("errors", {}).get("count", 0)
            for op in stats.get("operations", {}).values()
        )
        error_rate = total_errors / total_requests if total_requests > 0 else 0

        # Calculate average response time
        avg_response_times = [
            op.get("duration", {}).get("avg_ms", 0)
            for op in stats.get("operations", {}).values()
        ]
        overall_avg_response = sum(avg_response_times) / len(avg_response_times) if avg_response_times else 0

        return {
            "title": "System Overview",
            "metrics": {
                "total_operations": total_operations,
                "total_requests": total_requests,
                "requests_per_minute": total_requests / max(1, stats.get("window_minutes", 1)),
                "error_rate_percent": error_rate * 100,
                "average_response_time_ms": overall_avg_response,
                "uptime_percent": (1 - error_rate) * 100 if error_rate < 1 else 0,
            },
            "status": "healthy" if error_rate < 0.05 else "degraded" if error_rate < 0.1 else "unhealthy"
        }

    def _generate_system_section(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Generate system metrics section.

        Args:
            stats: Statistics data

        Returns:
            System metrics section data
        """
        system_data = stats.get("system", {})
        system_section = {
            "title": "System Resources",
            "metrics": {},
            "charts": {}
        }

        # CPU metrics
        if "cpu" in system_data:
            cpu_data = system_data["cpu"]["usage_percent"]
            system_section["metrics"]["cpu"] = {
                "current": cpu_data.get("current", 0),
                "average": cpu_data.get("avg", 0),
                "maximum": cpu_data.get("max", 0),
                "status": "good" if cpu_data.get("current", 0) < 70 else "warning" if cpu_data.get("current", 0) < 90 else "critical"
            }

        # Memory metrics
        if "memory" in system_data:
            memory_data = system_data["memory"]["usage_percent"]
            system_section["metrics"]["memory"] = {
                "current": memory_data.get("avg", 0),
                "maximum": memory_data.get("max", 0),
                "status": "good" if memory_data.get("avg", 0) < 70 else "warning" if memory_data.get("avg", 0) < 90 else "critical"
            }

        # Process metrics
        if "process" in system_data:
            process_data = system_data["process"]
            system_section["metrics"]["process"] = {}
            if "cpu_percent" in process_data:
                system_section["metrics"]["process"]["cpu"] = {
                    "average": process_data["cpu_percent"].get("avg", 0),
                    "maximum": process_data["cpu_percent"].get("max", 0)
                }
            if "memory_mb" in process_data:
                system_section["metrics"]["process"]["memory"] = {
                    "average": process_data["memory_mb"].get("avg", 0),
                    "maximum": process_data["memory_mb"].get("max", 0)
                }

        return system_section

    def _generate_operations_section(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Generate operations performance section.

        Args:
            stats: Statistics data

        Returns:
            Operations section data
        """
        operations_data = []
        operations = stats.get("operations", {})

        for operation_name, op_stats in operations.items():
            op_data = {
                "name": operation_name,
                "requests": {
                    "total": op_stats.get("requests", {}).get("total", 0),
                    "rate_per_minute": op_stats.get("requests", {}).get("rate_per_minute", 0),
                },
                "duration": {
                    "avg_ms": op_stats.get("duration", {}).get("avg_ms", 0),
                    "p95_ms": op_stats.get("duration", {}).get("p95_ms", 0),
                    "p99_ms": op_stats.get("duration", {}).get("p99_ms", 0),
                },
                "errors": {
                    "count": op_stats.get("errors", {}).get("count", 0),
                    "rate": op_stats.get("errors", {}).get("rate", 0),
                },
                "availability": op_stats.get("availability", 1.0),
                "status": "healthy" if op_stats.get("availability", 1.0) > 0.95 else "degraded" if op_stats.get("availability", 1.0) > 0.9 else "unhealthy"
            }
            operations_data.append(op_data)

        # Sort by request count (descending)
        operations_data.sort(key=lambda x: x["requests"]["total"], reverse=True)

        return {
            "title": "Operations Performance",
            "operations": operations_data,
            "summary": {
                "total_operations": len(operations_data),
                "healthy_operations": len([op for op in operations_data if op["status"] == "healthy"]),
                "degraded_operations": len([op for op in operations_data if op["status"] == "degraded"]),
                "unhealthy_operations": len([op for op in operations_data if op["status"] == "unhealthy"]),
            }
        }

    def _generate_alerts_section(self) -> Dict[str, Any]:
        """Generate alerts section.

        Returns:
            Alerts section data
        """
        # This would integrate with AlertManager
        # For now, return placeholder
        return {
            "title": "Active Alerts",
            "alerts": [],
            "summary": {
                "total": 0,
                "critical": 0,
                "error": 0,
                "warning": 0,
                "info": 0
            }
        }

    def generate_health_dashboard(self, health_checker: HealthChecker) -> Dict[str, Any]:
        """Generate health status dashboard.

        Args:
            health_checker: Health checker instance

        Returns:
            Health dashboard data
        """
        # This would need to be async to get current health status
        # For now, return a template
        return {
            "title": "Infinite Backrooms - Health Dashboard",
            "generated_at": datetime.now().isoformat(),
            "configured_checks": health_checker.get_check_names(),
            "sections": {
                "service_health": {
                    "title": "Service Health",
                    "checks": []
                },
                "dependency_health": {
                    "title": "Dependency Health",
                    "checks": []
                },
                "resource_health": {
                    "title": "Resource Health",
                    "checks": []
                }
            }
        }

    def generate_html_dashboard(self, dashboard_data: Dict[str, Any], template_name: str = "default") -> str:
        """Generate HTML dashboard from data.

        Args:
            dashboard_data: Dashboard data
            template_name: Template name to use

        Returns:
            HTML dashboard content
        """
        html_template = self._get_html_template(template_name)

        # Convert data to JSON for JavaScript
        dashboard_json = json.dumps(dashboard_data, indent=2)

        # Replace placeholders
        html_content = html_template.replace(
            "{{DASHBOARD_DATA}}",
            dashboard_json
        ).replace(
            "{{GENERATED_TIME}}",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        return html_content

    def _get_html_template(self, template_name: str) -> str:
        """Get HTML template for dashboard.

        Args:
            template_name: Template name

        Returns:
            HTML template content
        """
        if template_name == "default":
            return self._get_default_html_template()
        else:
            # Could support multiple templates in the future
            return self._get_default_html_template()

    def _get_default_html_template(self) -> str:
        """Get default HTML template.

        Returns:
            Default HTML template
        """
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Infinite Backrooms Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .dashboard {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .metric-label {
            color: #666;
            font-size: 14px;
        }
        .status-good { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-critical { color: #dc3545; }
        .chart-container {
            height: 300px;
            margin: 20px 0;
        }
        .operations-table {
            width: 100%;
            border-collapse: collapse;
        }
        .operations-table th,
        .operations-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .status-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        .status-healthy { background: #d4edda; color: #155724; }
        .status-degraded { background: #fff3cd; color: #856404; }
        .status-unhealthy { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>{{DASHBOARD_DATA.title}}</h1>
            <p>Generated at: {{GENERATED_TIME}}</p>
        </div>

        <div id="overview" class="section">
            <h2>System Overview</h2>
            <div class="metrics-grid" id="overview-metrics">
                <!-- Metrics will be populated by JavaScript -->
            </div>
        </div>

        <div id="system-metrics" class="section">
            <h2>System Resources</h2>
            <div class="metrics-grid" id="system-metrics-grid">
                <!-- System metrics will be populated by JavaScript -->
            </div>
            <div class="chart-container">
                <canvas id="resourceChart"></canvas>
            </div>
        </div>

        <div id="operations" class="section">
            <h2>Operations Performance</h2>
            <table class="operations-table" id="operations-table">
                <thead>
                    <tr>
                        <th>Operation</th>
                        <th>Requests</th>
                        <th>Avg Response (ms)</th>
                        <th>P95 Response (ms)</th>
                        <th>Error Rate</th>
                        <th>Availability</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Operations will be populated by JavaScript -->
                </tbody>
            </table>
        </div>

        <div id="alerts" class="section">
            <h2>Active Alerts</h2>
            <div id="alerts-content">
                <!-- Alerts will be populated by JavaScript -->
            </div>
        </div>
    </div>

    <script>
        const dashboardData = {{DASHBOARD_DATA}};

        // Populate overview metrics
        function populateOverview() {
            const overview = dashboardData.overview;
            const container = document.getElementById('overview-metrics');

            const metrics = [
                { label: 'Total Requests', value: overview.metrics.total_requests.toLocaleString() },
                { label: 'Requests/min', value: overview.metrics.requests_per_minute.toFixed(1) },
                { label: 'Error Rate', value: overview.metrics.error_rate_percent.toFixed(2) + '%' },
                { label: 'Avg Response', value: overview.metrics.average_response_time_ms.toFixed(0) + 'ms' },
                { label: 'Uptime', value: overview.metrics.uptime_percent.toFixed(2) + '%' },
            ];

            container.innerHTML = metrics.map(metric => `
                <div class="metric-card">
                    <div class="metric-value">${metric.value}</div>
                    <div class="metric-label">${metric.label}</div>
                </div>
            `).join('');
        }

        // Populate system metrics
        function populateSystemMetrics() {
            const system = dashboardData.system_metrics;
            const container = document.getElementById('system-metrics-grid');

            let metricsHtml = '';

            if (system.metrics.cpu) {
                const cpu = system.metrics.cpu;
                metricsHtml += `
                    <div class="metric-card">
                        <div class="metric-value status-${cpu.status}">${cpu.current.toFixed(1)}%</div>
                        <div class="metric-label">CPU Usage</div>
                    </div>
                `;
            }

            if (system.metrics.memory) {
                const memory = system.metrics.memory;
                metricsHtml += `
                    <div class="metric-card">
                        <div class="metric-value status-${memory.status}">${memory.current.toFixed(1)}%</div>
                        <div class="metric-label">Memory Usage</div>
                    </div>
                `;
            }

            container.innerHTML = metricsHtml;
        }

        // Populate operations table
        function populateOperations() {
            const operations = dashboardData.operations.operations;
            const tbody = document.querySelector('#operations-table tbody');

            tbody.innerHTML = operations.map(op => `
                <tr>
                    <td>${op.name}</td>
                    <td>${op.requests.total.toLocaleString()}</td>
                    <td>${op.duration.avg_ms.toFixed(0)}</td>
                    <td>${op.duration.p95_ms.toFixed(0)}</td>
                    <td>${(op.errors.rate * 100).toFixed(2)}%</td>
                    <td>${(op.availability * 100).toFixed(2)}%</td>
                    <td><span class="status-badge status-${op.status}">${op.status.toUpperCase()}</span></td>
                </tr>
            `).join('');
        }

        // Create resource chart
        function createResourceChart() {
            const ctx = document.getElementById('resourceChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['5m ago', '4m ago', '3m ago', '2m ago', '1m ago', 'Now'],
                    datasets: [
                        {
                            label: 'CPU Usage %',
                            data: [65, 68, 70, 72, 75, dashboardData.system_metrics.metrics.cpu?.current || 0],
                            borderColor: 'rgb(255, 99, 132)',
                            backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        },
                        {
                            label: 'Memory Usage %',
                            data: [45, 48, 50, 52, 55, dashboardData.system_metrics.metrics.memory?.current || 0],
                            borderColor: 'rgb(54, 162, 235)',
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        }

        // Initialize dashboard
        function initDashboard() {
            populateOverview();
            populateSystemMetrics();
            populateOperations();
            createResourceChart();
        }

        // Run when page loads
        document.addEventListener('DOMContentLoaded', initDashboard);

        // Auto-refresh every 30 seconds
        setInterval(() => {
            location.reload();
        }, 30000);
    </script>
</body>
</html>"""

    def save_dashboard(self, dashboard_data: Dict[str, Any], filename: str, format: str = "json") -> str:
        """Save dashboard to file.

        Args:
            dashboard_data: Dashboard data
            filename: Output filename
            format: Output format (json or html)

        Returns:
            Path to saved file
        """
        if format == "html":
            content = self.generate_html_dashboard(dashboard_data)
            filepath = self.output_dir / f"{filename}.html"
        else:
            content = json.dumps(dashboard_data, indent=2)
            filepath = self.output_dir / f"{filename}.json"

        with open(filepath, 'w') as f:
            f.write(content)

        return str(filepath)

    def generate_all_dashboards(self) -> List[str]:
        """Generate all dashboard types.

        Returns:
            List of generated file paths
        """
        generated_files = []

        # Metrics dashboard
        metrics_data = self.generate_metrics_dashboard()
        metrics_file = self.save_dashboard(metrics_data, "metrics", "json")
        metrics_html = self.save_dashboard(metrics_data, "metrics", "html")
        generated_files.extend([metrics_file, metrics_html])

        return generated_files

    def get_dashboard_url(self, filename: str) -> str:
        """Get URL for dashboard file.

        Args:
            filename: Dashboard filename

        Returns:
            Dashboard URL
        """
        return f"/monitoring/dashboards/{filename}.html"