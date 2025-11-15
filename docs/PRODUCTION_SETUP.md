# Production Setup Guide

Comprehensive guide for configuring and optimizing Infinite AI Backrooms for production environments.

## Table of Contents

- [Production vs Development](#production-vs-development)
- [Configuration Management](#configuration-management)
- [Performance Optimization](#performance-optimization)
- [Resource Management](#resource-management)
- [Backup Strategies](#backup-strategies)
- [High Availability](#high-availability)
- [Scaling Considerations](#scaling-considerations)
- [Production Checklist](#production-checklist)

---

## Production vs Development

### Key Differences

| Aspect | Development | Production |
|--------|------------|------------|
| Debug Mode | Enabled | Disabled |
| Logging Level | DEBUG | INFO or WARNING |
| Error Display | Full stack traces | User-friendly messages |
| SSL/TLS | Optional | Required |
| Timeouts | Short | Longer, appropriate |
| Resource Limits | Unlimited | Configured |
| Monitoring | Optional | Required |
| Backups | Not required | Automated |
| Security | Relaxed | Hardened |

### Environment-Specific Configuration

#### Development (.env.development)

```env
# Development settings
DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_PROFILING=true

# Shorter timeouts for faster feedback
OLLAMA_TIMEOUT=30
OLLAMA_RESPONSE_TIMEOUT=60

# Local Ollama
OLLAMA_URL=http://localhost:11434

# Minimal security for easier testing
OLLAMA_VERIFY_SSL=false
```

#### Production (.env.production)

```env
# Production settings
DEBUG=false
LOG_LEVEL=INFO
ENABLE_PROFILING=false

# Production timeouts
OLLAMA_TIMEOUT=120
OLLAMA_RESPONSE_TIMEOUT=300

# Production Ollama (with SSL)
OLLAMA_URL=https://ollama.your-domain.com:11434
OLLAMA_VERIFY_SSL=true

# Enhanced security
ENABLE_INPUT_VALIDATION=true
MAX_PERSONA_NAME_LENGTH=50
MAX_SYSTEM_PROMPT_LENGTH=10000
REGEX_TIMEOUT=5
```

---

## Configuration Management

### Using Environment Files

#### Best Practice: Environment-Specific Files

```bash
# Project structure
infinite-backrooms/
├── .env.example          # Template
├── .env.development      # Dev config (gitignored)
├── .env.staging          # Staging config (gitignored)
├── .env.production       # Prod config (gitignored)
└── config/
    └── load_env.py       # Environment loader
```

#### Environment Loader

Create `config/load_env.py`:

```python
"""
Environment configuration loader.
Loads appropriate .env file based on APP_ENV variable.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

def load_environment():
    """Load environment variables based on APP_ENV setting."""
    app_env = os.getenv("APP_ENV", "development")

    env_file = Path(__file__).parent.parent / f".env.{app_env}"

    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded environment from {env_file}")
    else:
        print(f"Warning: {env_file} not found, using system environment")

    return app_env

# Load on import
current_env = load_environment()
```

Usage in application:

```python
# At the top of streamlit_backroom.py
import config.load_env  # Loads appropriate environment

# Access variables
import os
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
```

### Configuration Validation

Create `config/validate.py`:

```python
"""
Configuration validation for production deployments.
"""
import os
import sys
from typing import List, Tuple

def validate_required_vars() -> Tuple[bool, List[str]]:
    """Validate required environment variables."""
    required = [
        "OLLAMA_URL",
        "LOG_DIRECTORY",
    ]

    missing = []
    for var in required:
        if not os.getenv(var):
            missing.append(var)

    return len(missing) == 0, missing

def validate_production_config() -> Tuple[bool, List[str]]:
    """Validate production-specific configuration."""
    issues = []

    # Check debug mode
    if os.getenv("DEBUG", "false").lower() == "true":
        issues.append("DEBUG should be false in production")

    # Check SSL verification
    if os.getenv("OLLAMA_VERIFY_SSL", "true").lower() == "false":
        issues.append("OLLAMA_VERIFY_SSL should be true in production")

    # Check log level
    log_level = os.getenv("LOG_LEVEL", "INFO")
    if log_level == "DEBUG":
        issues.append("LOG_LEVEL should not be DEBUG in production")

    # Check timeouts
    timeout = int(os.getenv("OLLAMA_TIMEOUT", "120"))
    if timeout < 60:
        issues.append("OLLAMA_TIMEOUT should be at least 60 seconds in production")

    return len(issues) == 0, issues

def validate_config():
    """Run all configuration validations."""
    all_valid = True

    # Required variables
    valid, missing = validate_required_vars()
    if not valid:
        print("ERROR: Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        all_valid = False

    # Production config (only in production)
    if os.getenv("APP_ENV") == "production":
        valid, issues = validate_production_config()
        if not valid:
            print("WARNING: Production configuration issues:")
            for issue in issues:
                print(f"  - {issue}")

    if not all_valid:
        sys.exit(1)

    print("Configuration validated successfully")

if __name__ == "__main__":
    validate_config()
```

Run validation before deployment:

```bash
# Validate configuration
APP_ENV=production python config/validate.py

# Or add to startup script
export APP_ENV=production
python config/validate.py && uv run streamlit run streamlit_backroom.py
```

### Secrets Management

#### For Docker

Use Docker secrets:

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    secrets:
      - ollama_url
      - api_key
    environment:
      - OLLAMA_URL_FILE=/run/secrets/ollama_url

secrets:
  ollama_url:
    file: ./secrets/ollama_url.txt
  api_key:
    file: ./secrets/api_key.txt
```

#### For Kubernetes

Use Kubernetes secrets:

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: backrooms-secrets
type: Opaque
stringData:
  ollama-url: "https://ollama.internal:11434"
  log-level: "INFO"
```

#### For Cloud Platforms

Use platform-specific secret managers:
- AWS: AWS Secrets Manager or Parameter Store
- GCP: Secret Manager
- Azure: Key Vault
- HashiCorp Vault for multi-cloud

---

## Performance Optimization

### Application-Level Optimization

#### 1. Streamlit Configuration

Create `.streamlit/config.toml`:

```toml
[server]
port = 8501
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 200
maxMessageSize = 200

# Performance settings
runOnSave = false
fileWatcherType = "none"

[browser]
gatherUsageStats = false
serverAddress = "0.0.0.0"

[runner]
magicEnabled = true
fastReruns = true

# Memory management
maxCachedMessageAge = 3600
```

#### 2. Caching Strategy

Implement Streamlit caching:

```python
import streamlit as st
from functools import lru_cache

# Cache expensive operations
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_role_templates():
    """Load role templates (expensive operation)."""
    return {
        "analyst": "...",
        "creative": "...",
        # ...
    }

# Cache resource connections
@st.cache_resource
def get_ollama_client():
    """Get cached Ollama client."""
    return OllamaClient(base_url=OLLAMA_URL)

# LRU cache for Python functions
@lru_cache(maxsize=128)
def format_message(message: str, persona: str) -> str:
    """Format message with caching."""
    # Formatting logic
    return formatted_message
```

#### 3. Async Optimization

Optimize async operations:

```python
import asyncio
import aiohttp

class OptimizedOllamaClient:
    def __init__(self, base_url: str, max_connections: int = 10):
        self.base_url = base_url
        self.max_connections = max_connections
        self._connector = None
        self._session = None

    async def __aenter__(self):
        # Connection pooling
        self._connector = aiohttp.TCPConnector(
            limit=self.max_connections,
            ttl_dns_cache=300,
            force_close=False,  # Reuse connections
            enable_cleanup_closed=True
        )

        # Session with timeouts
        timeout = aiohttp.ClientTimeout(
            total=300,
            connect=10,
            sock_read=60
        )

        self._session = aiohttp.ClientSession(
            connector=self._connector,
            timeout=timeout,
            raise_for_status=True
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
        if self._connector:
            await self._connector.close()
```

### Ollama Optimization

#### 1. Model Configuration

Optimize model loading:

```bash
# Set environment variables for Ollama
export OLLAMA_MAX_LOADED_MODELS=2          # Keep 2 models in memory
export OLLAMA_NUM_PARALLEL=4               # Handle 4 concurrent requests
export OLLAMA_MAX_QUEUE=512                # Request queue size
export OLLAMA_RUNNERS_DIR=/fast/storage    # Use fast storage (SSD)
```

#### 2. GPU Optimization

Configure GPU settings:

```bash
# Use GPU efficiently
export OLLAMA_GPU_LAYERS=35                # Offload layers to GPU
export OLLAMA_GPU_MEMORY_FRACTION=0.8      # Use 80% of GPU memory
export CUDA_VISIBLE_DEVICES=0              # Specific GPU

# Monitor GPU usage
nvidia-smi dmon -s u -d 1
```

#### 3. Model Selection for Performance

Performance-optimized model choices:

```bash
# Fast models (< 2s response time)
ollama pull phi:latest          # 2.7B params, very fast
ollama pull orca-mini:latest    # 3B params, fast

# Balanced (2-5s response time)
ollama pull granite3.3:8b       # Good quality, reasonable speed
ollama pull llama2:7b           # Standard choice

# Quality-focused (5-15s response time)
ollama pull mistral:7b          # Better quality
ollama pull llama2:13b          # Enhanced reasoning
```

### Database and Storage Optimization

#### 1. Conversation Log Optimization

Implement log rotation:

```python
# src/services/logger.py
import os
from pathlib import Path
from datetime import datetime, timedelta

class OptimizedLogger:
    def __init__(self, log_dir: str, max_age_days: int = 30):
        self.log_dir = Path(log_dir)
        self.max_age_days = max_age_days

    def cleanup_old_logs(self):
        """Remove logs older than max_age_days."""
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)

        for log_file in self.log_dir.glob("*.txt"):
            # Parse date from filename
            try:
                file_date_str = log_file.stem.split("_")[-1]
                file_date = datetime.strptime(file_date_str, "%Y-%m-%d")

                if file_date < cutoff_date:
                    log_file.unlink()
                    print(f"Deleted old log: {log_file}")
            except (ValueError, IndexError):
                pass  # Skip files with unexpected names

    def compress_old_logs(self):
        """Compress logs older than 7 days."""
        import gzip
        cutoff_date = datetime.now() - timedelta(days=7)

        for log_file in self.log_dir.glob("*.txt"):
            try:
                file_date_str = log_file.stem.split("_")[-1]
                file_date = datetime.strptime(file_date_str, "%Y-%m-%d")

                if file_date < cutoff_date and not log_file.with_suffix(".txt.gz").exists():
                    # Compress file
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(f"{log_file}.gz", 'wb') as f_out:
                            f_out.writelines(f_in)

                    # Delete original
                    log_file.unlink()
                    print(f"Compressed log: {log_file}")
            except (ValueError, IndexError):
                pass
```

Add to startup:

```python
# Run cleanup on app start
logger = OptimizedLogger(log_dir="conversations", max_age_days=30)
logger.cleanup_old_logs()
logger.compress_old_logs()
```

#### 2. Session State Optimization

Optimize session state management:

```python
# Limit conversation history
MAX_MEMORY_MESSAGES = 100  # Keep last 100 messages in memory

def manage_conversation_history(history: list) -> list:
    """Trim conversation history to prevent memory issues."""
    if len(history) > MAX_MEMORY_MESSAGES:
        # Keep most recent messages
        return history[-MAX_MEMORY_MESSAGES:]
    return history

# Usage
st.session_state.conversation_history = manage_conversation_history(
    st.session_state.conversation_history
)
```

---

## Resource Management

### CPU and Memory Limits

#### Docker Resource Limits

```yaml
# docker-compose.yml
services:
  app:
    build: .
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  ollama:
    image: ollama/ollama:latest
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 16G
        reservations:
          cpus: '2'
          memory: 8G
```

#### Systemd Resource Limits

```ini
# /etc/systemd/system/infinite-backrooms.service
[Service]
# CPU limits (50% of one core)
CPUQuota=50%

# Memory limits
MemoryLimit=4G
MemoryMax=6G

# I/O limits
IOReadBandwidthMax=/dev/sda 10M
IOWriteBandwidthMax=/dev/sda 10M

# Process limits
TasksMax=100
```

### Disk Space Management

#### Monitor Disk Usage

Create monitoring script:

```bash
#!/bin/bash
# /usr/local/bin/check-disk-space.sh

THRESHOLD=80  # Alert at 80% usage
USAGE=$(df /home/backrooms/infinite-backrooms/conversations | awk 'NR==2 {print $5}' | sed 's/%//')

if [ $USAGE -gt $THRESHOLD ]; then
    echo "ALERT: Disk usage is at ${USAGE}%"

    # Clean up old logs
    find /home/backrooms/infinite-backrooms/conversations -name "*.txt" -mtime +30 -delete

    # Notify admin (configure email/slack/etc)
    # send_notification "Disk space alert: ${USAGE}%"
fi
```

Add to crontab:

```bash
# Check disk space daily
0 2 * * * /usr/local/bin/check-disk-space.sh
```

---

## Backup Strategies

### Automated Backup Script

Create `scripts/backup.sh`:

```bash
#!/bin/bash
# Production backup script

set -e

# Configuration
BACKUP_DIR="/var/backups/infinite-backrooms"
APP_DIR="/home/backrooms/infinite-backrooms"
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup conversations
echo "Backing up conversations..."
tar -czf "$BACKUP_DIR/conversations_$TIMESTAMP.tar.gz" \
    -C "$APP_DIR" conversations/

# Backup configuration
echo "Backing up configuration..."
cp "$APP_DIR/.env" "$BACKUP_DIR/env_$TIMESTAMP"

# Backup personas (if exported)
if [ -f "$APP_DIR/personas_export.json" ]; then
    cp "$APP_DIR/personas_export.json" "$BACKUP_DIR/personas_$TIMESTAMP.json"
fi

# Clean old backups
echo "Cleaning old backups..."
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "env_*" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "personas_*.json" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $TIMESTAMP"

# Optional: Upload to cloud storage
# aws s3 sync "$BACKUP_DIR" s3://your-bucket/backups/
# gsutil -m rsync -r "$BACKUP_DIR" gs://your-bucket/backups/
```

Make executable and schedule:

```bash
chmod +x scripts/backup.sh

# Add to crontab (daily at 3 AM)
0 3 * * * /home/backrooms/infinite-backrooms/scripts/backup.sh >> /var/log/backrooms-backup.log 2>&1
```

### Database Backup (Future)

If using PostgreSQL for storage:

```bash
#!/bin/bash
# Database backup script

DB_NAME="infinite_backrooms"
BACKUP_DIR="/var/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Full backup
pg_dump -Fc $DB_NAME > "$BACKUP_DIR/db_$TIMESTAMP.dump"

# Rotate old backups
find "$BACKUP_DIR" -name "db_*.dump" -mtime +7 -delete
```

### Cloud Storage Backup

#### AWS S3

```bash
# Install AWS CLI
sudo apt-get install awscli

# Configure credentials
aws configure

# Sync backups to S3
aws s3 sync /var/backups/infinite-backrooms/ s3://your-bucket/backrooms-backups/ \
    --storage-class STANDARD_IA \
    --delete
```

#### Google Cloud Storage

```bash
# Install gsutil
curl https://sdk.cloud.google.com | bash

# Authenticate
gcloud auth login

# Sync to GCS
gsutil -m rsync -r /var/backups/infinite-backrooms/ gs://your-bucket/backrooms-backups/
```

---

## High Availability

### Load Balancing

#### Nginx Load Balancer

```nginx
# /etc/nginx/conf.d/load-balancer.conf

upstream backrooms_backend {
    least_conn;  # Route to least busy server

    server 10.0.0.10:8501 max_fails=3 fail_timeout=30s;
    server 10.0.0.11:8501 max_fails=3 fail_timeout=30s;
    server 10.0.0.12:8501 max_fails=3 fail_timeout=30s;

    # Health check (nginx plus)
    # health_check interval=10s fails=2 passes=3;
}

server {
    listen 80;
    server_name backrooms.your-domain.com;

    location / {
        proxy_pass http://backrooms_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;

        # Sticky sessions (if needed)
        # ip_hash;
    }
}
```

### Shared Ollama Backend

Configure all app instances to use shared Ollama:

```env
# All app servers point to shared Ollama
OLLAMA_URL=http://ollama-cluster.internal:11434
```

Deploy Ollama cluster with load balancer.

### Session Persistence

For multi-server deployments, use shared session storage:

#### Redis Session Store (Future Enhancement)

```python
# Install redis
# pip install redis streamlit-redis

import redis
import streamlit as st

# Connect to Redis
redis_client = redis.Redis(
    host='redis.internal',
    port=6379,
    db=0,
    decode_responses=True
)

# Store session data
def save_session(session_id: str, data: dict):
    redis_client.setex(
        f"session:{session_id}",
        3600,  # 1 hour TTL
        json.dumps(data)
    )

# Load session data
def load_session(session_id: str) -> dict:
    data = redis_client.get(f"session:{session_id}")
    return json.loads(data) if data else {}
```

---

## Scaling Considerations

### Horizontal Scaling

#### Application Tier

Multiple app instances behind load balancer:

```
            ┌──────────────┐
            │Load Balancer │
            └──────┬───────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
   ┌────▼───┐ ┌───▼────┐ ┌───▼────┐
   │ App 1  │ │ App 2  │ │ App 3  │
   └────┬───┘ └───┬────┘ └───┬────┘
        │         │          │
        └─────────┼──────────┘
                  │
           ┌──────▼───────┐
           │Ollama Cluster│
           └──────────────┘
```

#### Ollama Tier

Distributed Ollama instances:

```
        ┌─────────────────┐
        │  App Instances  │
        └────────┬────────┘
                 │
          ┌──────▼───────┐
          │Ollama LB     │
          └──────┬───────┘
                 │
     ┌───────────┼───────────┐
     │           │           │
┌────▼────┐ ┌───▼────┐ ┌───▼────┐
│Ollama 1 │ │Ollama 2│ │Ollama 3│
│GPU Node │ │GPU Node│ │GPU Node│
└─────────┘ └────────┘ └────────┘
```

### Vertical Scaling

#### When to Scale Up

Scale vertically when:
- Single model needs more resources
- Using large models (70B+)
- Need lower latency

#### Recommended Specs by Scale

| Scale | Users | App Server | Ollama Server |
|-------|-------|------------|---------------|
| Small | 1-10 | 2 CPU, 4GB | 4 CPU, 16GB, GPU |
| Medium | 10-50 | 4 CPU, 8GB | 8 CPU, 32GB, 2x GPU |
| Large | 50-200 | 8 CPU, 16GB | 16 CPU, 64GB, 4x GPU |
| Enterprise | 200+ | Multiple instances | Cluster with load balancing |

### Auto-Scaling (Kubernetes)

Example Kubernetes HPA:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backrooms-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: infinite-backrooms
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Production Checklist

### Pre-Deployment Checklist

- [ ] All environment variables configured
- [ ] SSL/TLS certificates installed
- [ ] Firewall rules configured
- [ ] Backup system implemented
- [ ] Monitoring configured
- [ ] Health checks working
- [ ] Load testing completed
- [ ] Security scan passed
- [ ] Documentation updated
- [ ] Rollback plan prepared

### Security Checklist

- [ ] DEBUG mode disabled
- [ ] SSL verification enabled
- [ ] Input validation enabled
- [ ] Error messages sanitized
- [ ] Secrets properly managed
- [ ] Firewall configured
- [ ] Regular updates scheduled
- [ ] Security headers configured
- [ ] Rate limiting implemented (if needed)
- [ ] Access logs enabled

### Performance Checklist

- [ ] Caching configured
- [ ] Resource limits set
- [ ] Timeouts configured appropriately
- [ ] Connection pooling enabled
- [ ] Log rotation configured
- [ ] Disk space monitoring enabled
- [ ] Performance baselines established
- [ ] Auto-scaling configured (if applicable)

### Operational Checklist

- [ ] Automated backups running
- [ ] Monitoring alerts configured
- [ ] Log aggregation setup
- [ ] On-call rotation defined
- [ ] Incident response plan documented
- [ ] Change management process
- [ ] Regular maintenance window scheduled

---

## Additional Resources

- [Deployment Guide](DEPLOYMENT.md) - Platform-specific deployment instructions
- [Security Guide](SECURITY.md) - Security best practices
- [Monitoring Guide](MONITORING.md) - Observability setup
- [Architecture Documentation](ARCHITECTURE.md) - System architecture

---

**Last Updated:** 2025-11-13
**Version:** 1.0.0
