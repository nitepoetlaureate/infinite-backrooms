# Infinite AI Backrooms - Production Deployment Guide

This guide provides comprehensive instructions for deploying the Infinite AI Backrooms Streamlit app to production.

## Table of Contents
- [Critical Deployment Challenge](#critical-deployment-challenge)
- [Deployment Options](#deployment-options)
- [Quick Start Deployments](#quick-start-deployments)
- [Docker Deployment](#docker-deployment)
- [Environment Variables](#environment-variables)
- [Health Checks](#health-checks)
- [Troubleshooting](#troubleshooting)

---

## Critical Deployment Challenge

### The Ollama Backend Problem

**IMPORTANT**: Your app currently uses a local Ollama instance at `http://localhost:11434`. This will NOT work in production cloud deployments because:

1. Cloud platforms don't have Ollama pre-installed
2. Running LLMs requires significant compute resources (CPU/GPU)
3. Most free tiers don't provide enough resources for local LLM inference

### Solutions (Choose One):

#### Option 1: Self-Hosted Ollama Server (Recommended for Full Control)
Deploy Ollama on a separate server with GPU support:
- **DigitalOcean GPU Droplet** ($65/month with GPU)
- **AWS EC2 g4dn instance** (~$0.50/hour with GPU)
- **Google Cloud Compute with GPU** (similar pricing)
- **Vast.ai or RunPod** (cheaper GPU rentals)

Steps:
1. Provision a GPU server
2. Install Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
3. Pull your models: `ollama pull granite3.3:8b`
4. Expose Ollama API (use nginx + SSL)
5. Set `OLLAMA_URL` environment variable to your server URL

#### Option 2: Ollama Cloud Proxy Services
Use a managed Ollama hosting service:
- **Replicate** - https://replicate.com (pay per use)
- **Together.ai** - https://together.ai (Ollama-compatible API)
- **Fireworks.ai** - https://fireworks.ai (fast inference)

#### Option 3: Switch to Hosted LLM APIs
Modify the app to use commercial APIs:
- **OpenAI GPT-4** - Best quality, $10/month + usage
- **Anthropic Claude** - Great for conversations
- **Google Gemini** - Free tier available
- **Groq** - Very fast inference, free tier

**Code changes needed**: Modify `src/services/ollama_client.py` to use different API

#### Option 4: Docker Compose (For VPS/Dedicated Server)
Deploy both Streamlit + Ollama together:
```bash
docker-compose up -d
```
This requires a server with at least 16GB RAM and ideally a GPU.

---

## Deployment Options

### 1. Streamlit Cloud (Easiest - FREE)

**Limitations**: Cannot run Ollama locally. You MUST use Option 1, 2, or 3 above.

**Steps**:
1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Connect your GitHub repository
4. Select `streamlit_backroom.py` as main file
5. Add secrets in dashboard:
   ```
   OLLAMA_URL = "https://your-ollama-server.com"
   OLLAMA_TIMEOUT = "120"
   OLLAMA_RESPONSE_TIMEOUT = "300"
   ```
6. Deploy!

**Pros**:
- Free hosting
- Automatic HTTPS
- Easy updates via git push
- Built-in authentication

**Cons**:
- Requires external Ollama hosting
- Limited to 1GB RAM
- Public by default

---

### 2. Railway.app (Recommended - Easy with Docker)

**Best for**: Apps with external Ollama server or small Docker deployments

**Steps**:
1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. Initialize project:
   ```bash
   railway init
   ```

3. Add environment variables:
   ```bash
   railway variables set OLLAMA_URL=https://your-ollama-server.com
   railway variables set PYTHON_VERSION=3.12.0
   ```

4. Deploy:
   ```bash
   railway up
   ```

**Pricing**: $5/month starter plan, includes 500 hours

**Pros**:
- Easy Docker support
- Auto-scaling
- Custom domains
- Environment variable management

**Cons**:
- Still requires external Ollama
- Not free tier

---

### 3. Render.com

**Best for**: Docker deployments with managed services

**Steps**:
1. Push code to GitHub
2. Go to https://render.com
3. New Web Service
4. Connect repository
5. Use `render.yaml` configuration (already provided)
6. Add environment variables in dashboard
7. Deploy

**Pricing**: Free tier available, $7/month for production

**Pros**:
- Free tier with automatic SSL
- Easy environment management
- Docker support

**Cons**:
- Requires external Ollama
- Free tier has limitations

---

### 4. Docker Deployment (VPS/Dedicated Server)

**Best for**: Full control, running Ollama locally

**Requirements**:
- VPS with 16GB+ RAM
- GPU recommended (NVIDIA for Ollama)
- Ubuntu 22.04 or similar

**Steps**:

1. **Install Docker & Docker Compose**:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   sudo apt install docker-compose-plugin
   ```

2. **Clone repository**:
   ```bash
   git clone https://github.com/nitepoetlaureate/infinite-backrooms.git
   cd infinite-backrooms
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Start services**:
   ```bash
   docker compose up -d
   ```

5. **Pull Ollama models**:
   ```bash
   docker exec -it infinite-backrooms-ollama ollama pull granite3.3:8b
   docker exec -it infinite-backrooms-ollama ollama pull qwen2.5:7b
   ```

6. **Access app**:
   - Streamlit: http://your-server-ip:8501
   - Ollama API: http://your-server-ip:11434

**Setup Nginx Reverse Proxy** (recommended):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**Pros**:
- Full control
- Can run Ollama locally
- No monthly platform fees (just server cost)
- Best performance

**Cons**:
- Server management required
- Need GPU for good performance
- More complex setup

---

### 5. Kubernetes (Advanced)

For enterprise deployments, see `docs/kubernetes-deployment.md` (create this if needed).

---

## Environment Variables

### Required Variables

| Variable | Description | Default | Production Value |
|----------|-------------|---------|------------------|
| `OLLAMA_URL` | Ollama API endpoint | `http://localhost:11434` | Your Ollama server URL |
| `OLLAMA_TIMEOUT` | Connection timeout (seconds) | `120` | `120` |
| `OLLAMA_RESPONSE_TIMEOUT` | Response timeout (seconds) | `300` | `300-600` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_HISTORY_MESSAGES` | Max messages in UI | `50` |
| `DEFAULT_CONTEXT_MESSAGES` | Context for AI | `10` |
| `AUTO_RUN_DELAY_MIN` | Min delay (seconds) | `2` |
| `AUTO_RUN_DELAY_MAX` | Max delay (seconds) | `8` |
| `ENABLE_THINKING` | Show AI thinking | `true` |
| `DEBUG` | Debug mode | `false` |

### Setting Environment Variables

**Streamlit Cloud**:
- Dashboard → Secrets → Add key-value pairs

**Railway**:
```bash
railway variables set KEY=value
```

**Render**:
- Dashboard → Environment → Add variable

**Docker**:
- Edit `.env` file or use `-e` flag

---

## Health Checks

The app includes built-in health checks at:
- **Endpoint**: `/_stcore/health`
- **Method**: GET
- **Response**: 200 OK if healthy

**Configure monitoring**:
1. UptimeRobot (free): https://uptimerobot.com
2. Better Uptime: https://betteruptime.com
3. Built-in platform monitoring

---

## Quick Start Commands

### Test Locally with Docker
```bash
docker build -t infinite-backrooms .
docker run -p 8501:8501 -e OLLAMA_URL=http://your-ollama infinite-backrooms
```

### Deploy to Railway
```bash
railway init
railway variables set OLLAMA_URL=https://your-ollama-server.com
railway up
railway open
```

### Deploy with Docker Compose
```bash
docker compose up -d
docker compose logs -f streamlit-app
```

### Update Deployment
```bash
git pull origin main
docker compose down
docker compose up -d --build
```

---

## Recommended Deployment Path (Budget Conscious)

### For Testing/Demo ($0-5/month):
1. Deploy Streamlit to **Streamlit Cloud** (FREE)
2. Use **Groq** or **Together.ai** free tier for LLM (modify code)
3. Total cost: $0/month

### For Production (Basic) ($15-20/month):
1. Deploy Streamlit to **Railway** ($5/month)
2. Self-host Ollama on **Vast.ai GPU** ($10-15/month)
3. Total cost: ~$20/month

### For Production (Full Control) ($30-65/month):
1. VPS with GPU: **DigitalOcean GPU Droplet** ($65/month)
2. Run both Streamlit + Ollama with Docker Compose
3. Total cost: $65/month
4. Alternative: CPU-only VPS ($12/month) + Groq API for LLM

---

## Troubleshooting

### Ollama Connection Failed
```
Error: Could not connect to Ollama at http://localhost:11434
```
**Solution**: Set `OLLAMA_URL` environment variable to your Ollama server

### App Crashes on Startup
```
Error: Python version mismatch
```
**Solution**: Ensure `runtime.txt` specifies Python 3.12

### Static CSS Not Loading
```
Error: FileNotFoundError: static/css/system.css
```
**Solution**: Ensure `static/` directory is included in deployment
- Check `.dockerignore` doesn't exclude `static/`
- Verify files are committed to git

### Out of Memory
```
Error: Container killed (OOM)
```
**Solution**:
- Reduce `MAX_HISTORY_MESSAGES` to 20
- Use smaller Ollama models (e.g., `tinyllama`)
- Upgrade to plan with more RAM

### Slow Response Times
**Solution**:
- Use Groq or Together.ai for faster inference
- Enable GPU on Ollama server
- Reduce `DEFAULT_CONTEXT_MESSAGES` to 5-7

---

## Security Checklist

Before deploying to production:

- [ ] Set `DEBUG=false` in environment variables
- [ ] Use HTTPS for all connections (platform usually handles this)
- [ ] Secure Ollama API endpoint (use API keys or VPN)
- [ ] Enable Streamlit authentication (Streamlit Cloud provides this)
- [ ] Set appropriate CORS settings
- [ ] Regularly update dependencies: `pip install -U streamlit aiohttp`
- [ ] Monitor logs for suspicious activity
- [ ] Backup conversation logs regularly

---

## Performance Optimization

### For Better Performance:
1. **Use GPU-accelerated Ollama** server
2. **Enable response caching** in Ollama
3. **Use quantized models** (8-bit vs 16-bit)
4. **Limit context window** to reduce token processing
5. **Use CDN** for static assets
6. **Enable WebSocket compression** (already configured)

### Recommended Ollama Models for Production:
- **Fast**: `tinyllama` (1.1B), `phi3:mini` (3.8B)
- **Balanced**: `mistral:7b`, `granite3.3:8b`, `qwen2.5:7b`
- **Quality**: `mixtral:8x7b`, `llama3.1:70b` (requires significant GPU)

---

## Monitoring & Observability

### Metrics to Monitor:
- Response times (p50, p95, p99)
- Error rates
- Ollama API latency
- Memory usage
- Active user sessions

### Tools:
- **Logs**: Platform-provided logging
- **Metrics**: Prometheus + Grafana (for Docker deployments)
- **Alerts**: UptimeRobot, Better Uptime, PagerDuty
- **APM**: Sentry (for error tracking)

---

## Support & Resources

- **GitHub Issues**: https://github.com/nitepoetlaureate/infinite-backrooms/issues
- **Ollama Docs**: https://ollama.com/docs
- **Streamlit Docs**: https://docs.streamlit.io
- **Docker Docs**: https://docs.docker.com

---

## License

See LICENSE file in repository.

---

**Last Updated**: November 2025
**Version**: 1.0.0
