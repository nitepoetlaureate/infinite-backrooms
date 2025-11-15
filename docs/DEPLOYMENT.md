# Deployment Guide

Complete guide for deploying Infinite AI Backrooms to production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
  - [Option 1: Streamlit Cloud](#option-1-streamlit-cloud-recommended-for-beginners)
  - [Option 2: Docker Deployment](#option-2-docker-deployment-recommended-for-production)
  - [Option 3: Railway](#option-3-railway)
  - [Option 4: Traditional VPS/Cloud Server](#option-4-traditional-vpscloud-server)
- [Ollama Backend Setup](#ollama-backend-setup)
- [Environment Configuration](#environment-configuration)
- [Health Checks and Monitoring](#health-checks-and-monitoring)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying, ensure you have:

1. **Python 3.12+** installed
2. **UV package manager** (or pip)
3. **Ollama** instance (local or remote) with models downloaded
4. **Git** for cloning the repository
5. Account on your chosen deployment platform

### Minimum System Requirements

- **CPU**: 2 cores (4+ recommended for Ollama)
- **RAM**: 4GB minimum (8GB+ recommended, 16GB+ for larger Ollama models)
- **Storage**: 10GB minimum (depends on Ollama models)
- **Network**: Stable internet connection

---

## Deployment Options

### Option 1: Streamlit Cloud (Recommended for Beginners)

Best for: Quick demos, testing, small-scale usage

#### Step 1: Fork the Repository

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/infinite-backrooms.git
cd infinite-backrooms
```

#### Step 2: Configure Secrets

Create `.streamlit/secrets.toml`:

```toml
# Ollama Configuration
OLLAMA_URL = "https://your-ollama-instance.com:11434"
OLLAMA_TIMEOUT = "120"
OLLAMA_RESPONSE_TIMEOUT = "300"
OLLAMA_VERIFY_SSL = "true"

# Logging
LOG_DIRECTORY = "conversations"
LOG_FILE_PREFIX = "streamlit_backroom"
LOG_LEVEL = "INFO"

# UI Configuration
MAX_HISTORY_MESSAGES = "50"
DEFAULT_CONTEXT_MESSAGES = "10"
DEFAULT_TEMPERATURE = "0.7"
ENABLE_THINKING = "true"

# Security
MAX_PERSONA_NAME_LENGTH = "50"
MAX_SYSTEM_PROMPT_LENGTH = "10000"
ENABLE_INPUT_VALIDATION = "true"
REGEX_TIMEOUT = "5"
```

#### Step 3: Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Set main file path: `streamlit_backroom.py`
6. Add secrets from above
7. Click "Deploy"

#### Limitations

- Streamlit Cloud has resource limits
- Requires external Ollama instance (cannot run Ollama on Streamlit Cloud)
- Limited to 1GB RAM in free tier

---

### Option 2: Docker Deployment (Recommended for Production)

Best for: Production deployments, scalability, isolation

#### Step 1: Create Dockerfile

Create `/Users/edsaga/infinite-backrooms/Dockerfile`:

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY requirements.txt ./
COPY src/ ./src/
COPY streamlit_backroom.py ./
COPY log_viewer.py ./
COPY static/ ./static/
COPY .streamlit/ ./.streamlit/

# Install dependencies
RUN uv sync --frozen

# Create conversations directory
RUN mkdir -p conversations

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run the application
CMD ["uv", "run", "streamlit", "run", "streamlit_backroom.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### Step 2: Create Docker Compose File

Create `/Users/edsaga/infinite-backrooms/docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OLLAMA_URL=${OLLAMA_URL:-http://ollama:11434}
      - OLLAMA_TIMEOUT=${OLLAMA_TIMEOUT:-120}
      - OLLAMA_RESPONSE_TIMEOUT=${OLLAMA_RESPONSE_TIMEOUT:-300}
      - LOG_DIRECTORY=${LOG_DIRECTORY:-conversations}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - MAX_HISTORY_MESSAGES=${MAX_HISTORY_MESSAGES:-50}
      - DEFAULT_CONTEXT_MESSAGES=${DEFAULT_CONTEXT_MESSAGES:-10}
    volumes:
      - ./conversations:/app/conversations
    depends_on:
      - ollama
    restart: unless-stopped
    networks:
      - backrooms

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    networks:
      - backrooms
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  ollama_data:

networks:
  backrooms:
    driver: bridge
```

#### Step 3: Create .dockerignore

Create `/Users/edsaga/infinite-backrooms/.dockerignore`:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/

# Testing
.pytest_cache/
htmlcov/
.coverage
*.cover

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
conversations/
*.log
.env

# Git
.git/
.gitignore

# Documentation
docs/
*.md
!README.md

# Tests
tests/
test_*.py

# Build
dist/
build/
*.egg-info/

# Node modules (from system-css)
system-css-main/
node_modules/
```

#### Step 4: Build and Deploy

```bash
# Build the image
docker build -t infinite-backrooms:latest .

# Run with docker-compose
docker-compose up -d

# Check logs
docker-compose logs -f app

# Stop the application
docker-compose down
```

#### Step 5: Pull Ollama Models

```bash
# Access the Ollama container
docker exec -it infinite-backrooms-ollama-1 bash

# Pull models
ollama pull granite3.3:8b
ollama pull llama2:latest
ollama pull mistral:latest

# Verify models
ollama list

# Exit container
exit
```

#### Production Deployment with Docker

For production, use a reverse proxy (nginx):

```nginx
# /etc/nginx/sites-available/infinite-backrooms
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Enable SSL with Let's Encrypt:

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

---

### Option 3: Railway

Best for: Easy deployment with minimal configuration

#### Step 1: Prepare Repository

1. Ensure `requirements.txt` is up to date:
   ```bash
   uv pip freeze > requirements.txt
   ```

2. Create `Procfile`:
   ```
   web: streamlit run streamlit_backroom.py --server.port=$PORT --server.address=0.0.0.0
   ```

3. Create `railway.json`:
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "numReplicas": 1,
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

#### Step 2: Deploy to Railway

1. Go to https://railway.app/
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select `infinite-backrooms`
5. Add environment variables:
   ```
   OLLAMA_URL=https://your-ollama-instance.com:11434
   OLLAMA_TIMEOUT=120
   OLLAMA_RESPONSE_TIMEOUT=300
   LOG_LEVEL=INFO
   ```
6. Deploy

#### Note on Ollama

Railway doesn't support running Ollama in the same instance. You'll need:
- External Ollama instance (separate server)
- Or use Railway's persistent volume for Ollama

---

### Option 4: Traditional VPS/Cloud Server

Best for: Full control, custom configurations

Supported platforms:
- AWS EC2
- Google Cloud Compute Engine
- DigitalOcean Droplets
- Linode
- Vultr
- Azure VMs

#### Step 1: Server Setup

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.12
sudo apt-get install -y python3.12 python3.12-venv python3-pip

# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Ollama
curl https://ollama.ai/install.sh | sh

# Start Ollama service
sudo systemctl start ollama
sudo systemctl enable ollama

# Verify Ollama
curl http://localhost:11434/api/tags
```

#### Step 2: Clone and Configure

```bash
# Create application user
sudo useradd -m -s /bin/bash backrooms
sudo su - backrooms

# Clone repository
git clone https://github.com/guinacio/infinite-backrooms.git
cd infinite-backrooms

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
nano .env
```

#### Step 3: Create Systemd Service

Create `/etc/systemd/system/infinite-backrooms.service`:

```ini
[Unit]
Description=Infinite AI Backrooms
After=network.target ollama.service
Requires=ollama.service

[Service]
Type=simple
User=backrooms
WorkingDirectory=/home/backrooms/infinite-backrooms
Environment="PATH=/home/backrooms/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/backrooms/.local/bin/uv run streamlit run streamlit_backroom.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable infinite-backrooms
sudo systemctl start infinite-backrooms
sudo systemctl status infinite-backrooms
```

#### Step 4: Configure Firewall

```bash
# Allow SSH (if not already)
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS for reverse proxy
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

#### Step 5: Setup Reverse Proxy (Nginx)

Install Nginx:

```bash
sudo apt-get install -y nginx
```

Create configuration:

```nginx
# /etc/nginx/sites-available/infinite-backrooms
server {
    listen 80;
    server_name your-domain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL configuration (after certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase timeouts for long-running AI requests
        proxy_read_timeout 600s;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
    }

    # Health check endpoint
    location /_stcore/health {
        proxy_pass http://localhost:8501/_stcore/health;
        access_log off;
    }
}
```

Enable configuration:

```bash
sudo ln -s /etc/nginx/sites-available/infinite-backrooms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Install SSL certificate:

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## Ollama Backend Setup

### Local Ollama Instance

Best for: Development, single-server deployments

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull recommended models
ollama pull granite3.3:8b      # IBM Granite (recommended)
ollama pull llama2:latest       # Meta Llama 2
ollama pull mistral:latest      # Mistral
ollama pull codellama:latest    # Code-focused

# Start Ollama service
ollama serve

# Verify models
ollama list
```

### Remote Ollama Instance

Best for: Distributed deployments, shared model server

#### Option A: Separate Server

1. Deploy Ollama on dedicated server:
   ```bash
   # On Ollama server
   curl https://ollama.ai/install.sh | sh

   # Configure to listen on all interfaces
   OLLAMA_HOST=0.0.0.0:11434 ollama serve
   ```

2. Configure firewall:
   ```bash
   sudo ufw allow from YOUR_APP_SERVER_IP to any port 11434
   ```

3. Update app environment:
   ```env
   OLLAMA_URL=http://ollama-server-ip:11434
   ```

#### Option B: Ollama as Docker Service

Use the docker-compose setup from Option 2.

#### Option C: Cloud-Hosted Ollama

Consider these providers:
- **Modal.com** - Serverless GPU with Ollama support
- **Replicate** - Managed model hosting
- **RunPod** - GPU cloud computing

### Model Selection Guide

| Model | Size | RAM Required | Speed | Quality | Best For |
|-------|------|--------------|-------|---------|----------|
| granite3.3:8b | 8B | 8GB | Fast | Good | General conversation |
| llama2:7b | 7B | 8GB | Fast | Good | Balanced performance |
| mistral:7b | 7B | 8GB | Fast | Very Good | Instruction following |
| llama2:13b | 13B | 16GB | Medium | Very Good | Complex reasoning |
| llama2:70b | 70B | 64GB+ | Slow | Excellent | Production quality |
| codellama:34b | 34B | 32GB | Medium | Excellent | Code-focused tasks |

### Performance Tuning

Configure Ollama for optimal performance:

```bash
# Set concurrent request limit
export OLLAMA_MAX_LOADED_MODELS=2

# Set GPU memory fraction
export OLLAMA_GPU_MEMORY_FRACTION=0.8

# Enable CPU fallback
export OLLAMA_NUM_PARALLEL=4
```

---

## Environment Configuration

### Required Environment Variables

```env
# Ollama Configuration (REQUIRED)
OLLAMA_URL=http://localhost:11434        # Ollama API endpoint
OLLAMA_TIMEOUT=120                       # Connection timeout (seconds)
OLLAMA_RESPONSE_TIMEOUT=300              # Response timeout (seconds)

# Logging Configuration
LOG_DIRECTORY=conversations              # Directory for log files
LOG_FILE_PREFIX=streamlit_backroom       # Prefix for log filenames
LOG_LEVEL=INFO                           # Logging level

# UI Configuration
MAX_HISTORY_MESSAGES=50                  # Max messages in UI
DEFAULT_CONTEXT_MESSAGES=10              # Default AI context window
DEFAULT_TEMPERATURE=0.7                  # AI creativity (0.0-2.0)
ENABLE_THINKING=true                     # Show AI thinking process

# Security Settings
MAX_PERSONA_NAME_LENGTH=50               # Max persona name length
MAX_SYSTEM_PROMPT_LENGTH=10000           # Max system prompt length
ENABLE_INPUT_VALIDATION=true             # Enable validation
REGEX_TIMEOUT=5                          # Regex timeout (seconds)

# Optional: SSL Configuration
OLLAMA_VERIFY_SSL=true                   # Verify SSL certificates
```

### Platform-Specific Configuration

#### Streamlit Cloud

Use `.streamlit/secrets.toml`:

```toml
OLLAMA_URL = "https://your-ollama-instance.com:11434"
# ... other variables
```

#### Docker

Use `docker-compose.yml` environment section or `.env` file.

#### Railway/Heroku

Set environment variables in platform dashboard.

#### VPS/Cloud Server

Use `.env` file or systemd environment file.

---

## Health Checks and Monitoring

### Health Check Endpoints

Streamlit provides built-in health check:

```bash
# Check if app is running
curl http://localhost:8501/_stcore/health

# Expected response: 200 OK
```

### Monitoring Ollama

```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Monitor Ollama logs
journalctl -u ollama -f

# Check GPU usage (if using GPU)
nvidia-smi
```

### Application Logs

```bash
# View systemd logs
sudo journalctl -u infinite-backrooms -f

# View application logs
tail -f /home/backrooms/infinite-backrooms/conversations/*.txt

# Docker logs
docker-compose logs -f app
```

### Automated Monitoring

Create monitoring script:

```bash
#!/bin/bash
# /usr/local/bin/check-backrooms.sh

# Check app health
if ! curl -s http://localhost:8501/_stcore/health > /dev/null; then
    echo "App is down, restarting..."
    systemctl restart infinite-backrooms
fi

# Check Ollama health
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Ollama is down, restarting..."
    systemctl restart ollama
fi
```

Add to crontab:

```bash
# Run health check every 5 minutes
*/5 * * * * /usr/local/bin/check-backrooms.sh
```

---

## Troubleshooting

### Application Won't Start

**Symptom**: Application fails to start or crashes immediately

**Solutions**:

1. Check logs:
   ```bash
   # Systemd
   sudo journalctl -u infinite-backrooms -n 50

   # Docker
   docker-compose logs app
   ```

2. Verify Python version:
   ```bash
   python3 --version  # Should be 3.12+
   ```

3. Reinstall dependencies:
   ```bash
   uv sync --frozen
   ```

4. Check file permissions:
   ```bash
   ls -la conversations/
   sudo chown -R backrooms:backrooms /home/backrooms/infinite-backrooms
   ```

### Cannot Connect to Ollama

**Symptom**: "Cannot connect to Ollama" error in UI

**Solutions**:

1. Verify Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. Check firewall rules:
   ```bash
   sudo ufw status
   ```

3. Verify OLLAMA_URL environment variable:
   ```bash
   echo $OLLAMA_URL
   ```

4. Check Ollama logs:
   ```bash
   sudo journalctl -u ollama -n 50
   ```

5. Test connectivity from app server:
   ```bash
   curl http://ollama-server-ip:11434/api/tags
   ```

### Slow Response Times

**Symptom**: AI responses take very long or timeout

**Solutions**:

1. Use smaller models:
   ```bash
   ollama pull llama2:7b  # Instead of 70b
   ```

2. Increase timeouts:
   ```env
   OLLAMA_RESPONSE_TIMEOUT=600  # 10 minutes
   ```

3. Check resource usage:
   ```bash
   htop
   nvidia-smi  # If using GPU
   ```

4. Reduce concurrent users or context window size

5. Enable GPU acceleration if available

### Memory Issues

**Symptom**: Out of memory errors or system freezing

**Solutions**:

1. Use smaller models
2. Reduce MAX_HISTORY_MESSAGES
3. Reduce DEFAULT_CONTEXT_MESSAGES
4. Add swap space:
   ```bash
   sudo fallocate -l 8G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

5. Monitor memory usage:
   ```bash
   free -h
   watch -n 1 free -h
   ```

### SSL/TLS Errors

**Symptom**: SSL certificate verification failures

**Solutions**:

1. Install CA certificates:
   ```bash
   sudo apt-get install ca-certificates
   ```

2. For self-signed certificates:
   ```env
   OLLAMA_VERIFY_SSL=false
   ```

3. Use proper SSL certificate (Let's Encrypt)

### Port Already in Use

**Symptom**: "Address already in use" error

**Solutions**:

1. Find process using port:
   ```bash
   sudo lsof -i :8501
   ```

2. Kill process:
   ```bash
   sudo kill -9 <PID>
   ```

3. Change port:
   ```bash
   streamlit run streamlit_backroom.py --server.port=8502
   ```

### Docker Build Failures

**Symptom**: Docker build fails with errors

**Solutions**:

1. Clear Docker cache:
   ```bash
   docker builder prune -a
   ```

2. Rebuild without cache:
   ```bash
   docker-compose build --no-cache
   ```

3. Check Docker resources:
   ```bash
   docker system df
   ```

4. Increase Docker memory limit (Docker Desktop)

---

## Additional Resources

- [Production Setup Guide](PRODUCTION_SETUP.md) - Production configuration and tuning
- [Security Guide](SECURITY.md) - Security best practices
- [Monitoring Guide](MONITORING.md) - Observability and monitoring setup
- [API Integration Guide](API_INTEGRATION.md) - Alternative LLM backends

---

## Getting Help

If you encounter issues not covered here:

1. Check [GitHub Issues](https://github.com/guinacio/infinite-backrooms/issues)
2. Review [Troubleshooting Section](#troubleshooting)
3. Check Ollama documentation: https://github.com/ollama/ollama
4. Check Streamlit documentation: https://docs.streamlit.io/

---

**Last Updated:** 2025-11-13
**Version:** 1.0.0
