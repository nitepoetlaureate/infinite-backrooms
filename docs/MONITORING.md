# Comprehensive Performance Monitoring and Observability

This document describes the comprehensive monitoring and observability system implemented for Infinite AI Backrooms.

## Overview

The monitoring system provides complete visibility into application performance, health status, and resource usage. It implements industry-standard monitoring practices including:

- **Four Golden Signals**: Latency, Traffic, Errors, Saturation
- **RED Method**: Rate, Errors, Duration
- **USE Method**: Utilization, Saturation, Errors

## Architecture

The monitoring system consists of several components:

### Core Components

1. **Metrics Collection** (`src/monitoring/metrics.py`)
   - Real-time metrics aggregation
   - Resource monitoring (CPU, memory, disk, network)
   - Operation performance tracking
   - Statistical summaries (percentiles, averages)

2. **Health Checks** (`src/monitoring/health.py`)
   - Application health monitoring
   - Dependency health checks
   - Resource utilization monitoring
   - Configurable health thresholds

3. **Structured Logging** (`src/monitoring/logger.py`)
   - JSON-formatted logs
   - Correlation IDs for request tracing
   - Context-aware logging
   - Log aggregation support

4. **Performance Profiling** (`src/monitoring/profiler.py`)
   - Function call profiling
   - Memory usage tracking
   - Bottleneck identification
   - Performance insights

5. **Alert Management** (`src/monitoring/alerts.py`)
   - Configurable alert rules
   - Multiple notification channels (email, webhook, Slack)
   - Alert deduplication and cooldown
   - Severity-based alerting

6. **Dashboard Generation** (`src/monitoring/dashboard.py`)
   - Real-time dashboards
   - Interactive visualizations
   - HTML/JSON export
   - Auto-refresh capabilities

## Quick Start

### 1. Basic Usage

```python
from src.monitoring import get_metrics_collector, get_logger

# Get metrics collector
metrics = get_metrics_collector()

# Record operation timing
metrics.record_timing("api_call", 150.5)  # ms

# Record counter
metrics.record_counter("requests", 1)

# Get logger
logger = get_logger("my_component")

# Log with context
logger.info("Operation completed", operation="api_call", duration_ms=150.5)
```

### 2. Using Performance Decorators

```python
from src.utils.performance import timing_decorator, PerformanceTimer

# Decorator approach
@timing_decorator("expensive_operation", enable_profiling=True)
async def process_data():
    # Your code here
    pass

# Context manager approach
with PerformanceTimer("data_processing"):
    # Your code here
    pass
```

### 3. Health Checks

```python
from src.monitoring.health import HealthChecker

# Create health checker
health_checker = HealthChecker()

# Add HTTP endpoint check
health_checker.add_http_check(
    name="api_health",
    url="http://localhost:8000/health",
    expected_status=200
)

# Run all checks
health_status = await health_checker.check_all()
print(f"Health: {health_status.status.value}")
```

### 4. Starting Full Monitoring

```bash
# Start monitoring service with default config
python scripts/start_monitoring.py

# Start with custom configuration
python scripts/start_monitoring.py --config monitoring_config.json

# Run health checks
python scripts/health_check.py --use-new-monitoring --verbose
```

## Configuration

### Environment Variables

```bash
# Metrics
MONITORING_METRICS_STORAGE_PATH="/path/to/metrics"
MONITORING_METRICS_MAX_SAMPLES="10000"

# Logging
MONITORING_LOG_LEVEL="INFO"
MONITORING_LOG_FILE="/path/to/logs/monitoring.log"
MONITORING_LOG_DIRECTORY="logs"

# Health Checks
STREAMLIT_URL="http://localhost:8501"
OLLAMA_BASE_URL="http://localhost:11434"
MONITORING_HEALTH_CHECK_INTERVAL="60"

# Alerts
ALERT_SMTP_SERVER="smtp.example.com"
ALERT_SMTP_USERNAME="alerts@example.com"
ALERT_SMTP_PASSWORD="password"
ALERT_SMTP_TO_EMAILS="admin@example.com,ops@example.com"
ALERT_WEBHOOK_URL="https://hooks.slack.com/..."
ALERT_SLACK_WEBHOOK_URL="https://hooks.slack.com/..."

# Profiling
MONITORING_PROFILING_ENABLED="true"

# Dashboard
MONITORING_DASHBOARD_PORT="8080"
```

### Configuration File

See `monitoring_config.json` for a complete configuration example. You can customize:

- Metrics collection intervals and retention
- Logging levels and output formats
- Health check thresholds and endpoints
- Alert rules and notification channels
- Profiling settings
- Dashboard configuration

## Metrics

### Available Metrics

#### System Metrics
- `system.cpu.percent` - CPU usage percentage
- `system.memory.percent` - Memory usage percentage
- `system.memory.available_gb` - Available memory in GB
- `system.disk.percent` - Disk usage percentage
- `system.network.bytes_sent` - Network bytes sent
- `system.network.bytes_recv` - Network bytes received

#### Process Metrics
- `process.cpu.percent` - Process CPU usage
- `process.memory.percent` - Process memory usage
- `process.memory.rss_mb` - Process RSS memory in MB

#### Application Metrics
- `operation.{name}.duration_ms` - Operation duration in milliseconds
- `counter.{name}` - Counter values
- `gauge.{name}` - Gauge values
- `errors.count` - Error occurrences

#### Health Metrics
- `health.overall_status` - Overall health status (1=healthy, 0=unhealthy)
- `health_check.{status}_count` - Health check counts by status

### Metric Types

1. **Counters**: Monotonically increasing values (request counts, error counts)
2. **Gauges**: Values that can go up or down (memory usage, CPU usage)
3. **Timings**: Duration measurements (response times, processing times)
4. **Histograms**: Statistical distributions of values

## Health Checks

### Built-in Health Checks

1. **HTTP Endpoint Checks**
   - Streamlit application health
   - Ollama API availability
   - Custom HTTP endpoints

2. **Resource Checks**
   - CPU usage monitoring
   - Memory usage monitoring
   - Disk usage monitoring

3. **Custom Checks**
   - Database connectivity
   - External service availability
   - Application-specific checks

### Health Check Configuration

```python
# Add custom health check
async def check_database():
    try:
        # Database health check logic
        return (HealthStatus.HEALTHY, "Database connected", {})
    except Exception as e:
        return (HealthStatus.UNHEALTHY, f"Database error: {e}", {})

health_checker.add_custom_check("database", check_database)
```

## Alerting

### Alert Rules

Create custom alert rules for specific conditions:

```python
from src.monitoring.alerts import AlertRule, AlertSeverity

# High error rate alert
high_error_rate = AlertRule(
    name="high_error_rate",
    condition=lambda metrics: calculate_error_rate(metrics) > 0.1,
    severity=AlertSeverity.ERROR,
    message_template="High error rate: {error_rate:.1%}",
    for_duration=300,  # 5 minutes
    cooldown=1800      # 30 minutes
)
```

### Notification Channels

1. **Email Alerts**
   - SMTP configuration
   - Multiple recipients
   - HTML-formatted alerts

2. **Webhook Alerts**
   - Custom webhook URLs
   - JSON payload format
   - HTTP headers support

3. **Slack Alerts**
   - Slack webhook integration
   - Channel targeting
   - Rich message formatting

## Dashboards

### Dashboard Features

- Real-time metrics visualization
- Interactive charts and graphs
- Health status overview
- Performance analytics
- Alert summary

### Accessing Dashboards

```python
from src.monitoring.dashboard import DashboardManager

# Create dashboard manager
dashboard = DashboardManager()

# Generate dashboards
dashboard.generate_all_dashboards()

# Access dashboard URL
dashboard_url = dashboard.get_dashboard_url("metrics")
```

## Performance Profiling

### Call Profiling

```python
from src.monitoring.profiler import PerformanceProfiler

profiler = PerformanceProfiler()

# Start profiling
profiler.start_profiling("operation_name")

# ... your code ...

# Stop and get results
results = profiler.stop_profiling("operation_name")
print(f"Duration: {results['call_profile']['duration_seconds']}s")
```

### Memory Profiling

```python
# Take memory snapshots
profiler.memory_profiler.take_snapshot("operation_name")

# Analyze memory trends
trend = profiler.memory_profiler.analyze_memory_trend(window_minutes=30)
print(f"Memory trend: {trend['memory_trend']}")
```

## Integration Examples

### Streamlit Integration

```python
import streamlit as st
from src.monitoring import get_metrics_collector, get_logger

# Initialize monitoring
metrics = get_metrics_collector()
logger = get_logger("streamlit_app")

def main():
    logger.info("Streamlit app started")

    with PerformanceTimer("page_load"):
        # Your Streamlit code
        st.title("Infinite Backrooms")

        # Record metrics
        metrics.record_counter("page_views", 1)

        # Log user interactions
        logger.info("User interaction", action="button_click", button="chat")
```

### API Integration

```python
from src.monitoring.metrics import timing_decorator
from src.monitoring.logger import get_logger

logger = get_logger("api")

@timing_decorator("api_generate_response")
async def generate_response(prompt: str):
    logger.info("Generating response", prompt_length=len(prompt))

    try:
        # API logic
        response = await call_ollama(prompt)
        logger.info("Response generated", response_length=len(response))
        return response
    except Exception as e:
        logger.error("Failed to generate response", exception=e)
        raise
```

## Best Practices

### 1. Instrumentation

- Add timing decorators to critical functions
- Use structured logging with context
- Record custom business metrics
- Monitor resource usage

### 2. Alert Configuration

- Set appropriate thresholds
- Use cooldown periods to prevent alert fatigue
- Configure multiple notification channels
- Test alert rules regularly

### 3. Performance Optimization

- Profile slow operations
- Monitor memory usage trends
- Identify and fix bottlenecks
- Optimize resource utilization

### 4. Monitoring in Production

- Enable all monitoring components
- Set up log aggregation
- Configure comprehensive health checks
- Implement proper alerting

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   - Check memory profiling data
   - Look for memory leaks
   - Monitor garbage collection

2. **Slow Response Times**
   - Review performance profiles
   - Check resource saturation
   - Analyze bottlenecks

3. **Health Check Failures**
   - Verify endpoint accessibility
   - Check timeout configurations
   - Monitor resource thresholds

### Debug Information

Enable debug logging for detailed troubleshooting:

```python
from src.monitoring.logger import LogLevel, init_logging

init_logging(log_level=LogLevel.DEBUG)
```

## Security Considerations

- Secure sensitive configuration (passwords, API keys)
- Use environment variables for secrets
- Implement proper access controls for dashboards
- Monitor security-related metrics

## Scaling and Performance

- Configure appropriate metric retention periods
- Implement metric aggregation for long-term storage
- Use sampling for high-frequency metrics
- Monitor the monitoring system itself

## Further Reading

- [Observability Engineering](https://www.oreilly.com/library/view/observability-engineering/9781492076438/)
- [Site Reliability Engineering](https://sre.google/books/)
- [Prometheus Monitoring Guide](https://prometheus.io/docs/guides/)
- [Distributed Systems Observability](https://www.oreilly.com/library/view/distributed-systems-observability/9781492033431/)