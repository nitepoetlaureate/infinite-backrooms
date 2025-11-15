# Quick Deployment Guide

Deploy Infinite AI Backrooms in under 10 minutes!

## Prerequisites

Before deploying, you MUST have:
1. A GitHub account with this repository forked/uploaded
2. An Ollama API endpoint (see options below)

## Step 1: Choose Your Ollama Backend

You have 3 options:

### Option A: Use a Free Hosted Alternative (Easiest)

Instead of Ollama, use a compatible API:

**Groq (Fast & Free Tier)**
```
OLLAMA_URL=https://api.groq.com/openai/v1
# Note: Requires code modification to use OpenAI-compatible endpoint
```

**Together.ai (Ollama-compatible)**
```
OLLAMA_URL=https://api.together.xyz
# Get API key at: https://together.ai
```

### Option B: Self-Host Ollama (Full Control)

1. Get a GPU server:
   - **Vast.ai**: Cheapest GPU rentals ($0.20-0.50/hour)
   - **RunPod**: Easy GPU deployment
   - **DigitalOcean GPU Droplet**: $65/month

2. Install Ollama:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull granite3.3:8b
   ```

3. Expose API (use nginx + SSL or Cloudflare Tunnel)

### Option C: Use Ollama Docker Image

See docker-compose.yml for local setup.

## Step 2: Deploy to Platform

Choose ONE platform below:

---

## 🚀 Deploy to Streamlit Cloud (FREE)

**Best for**: Free hosting, easiest setup

1. Go to https://share.streamlit.io
2. Click "New app"
3. Connect GitHub repository
4. Set main file: `streamlit_backroom.py`
5. Add secrets:
   ```toml
   OLLAMA_URL = "https://your-ollama-server.com"
   OLLAMA_TIMEOUT = "120"
   OLLAMA_RESPONSE_TIMEOUT = "300"
   ```
6. Deploy!

**Time**: 5 minutes
**Cost**: FREE
**URL**: `https://your-app.streamlit.app`

---

## 🚂 Deploy to Railway.app

**Best for**: Docker support, auto-scaling

### One-Click Deploy:
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/nitepoetlaureate/infinite-backrooms)

### Manual Deploy:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize
railway init

# Set variables
railway variables set OLLAMA_URL=https://your-ollama-server.com

# Deploy
railway up
```

**Time**: 5 minutes
**Cost**: $5/month starter
**URL**: `https://your-app.railway.app`

---

## 🎨 Deploy to Render.com

**Best for**: Free tier with Docker support

1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect GitHub repository
4. Render will auto-detect `render.yaml`
5. Set environment variable:
   - `OLLAMA_URL`: Your Ollama server URL
6. Deploy

**Time**: 5 minutes
**Cost**: Free tier (or $7/month)
**URL**: `https://your-app.onrender.com`

---

## 🐳 Deploy with Docker (VPS)

**Best for**: Full control, running Ollama locally

```bash
# Clone repository
git clone https://github.com/nitepoetlaureate/infinite-backrooms.git
cd infinite-backrooms

# Create .env file
cp .env.example .env
nano .env  # Edit OLLAMA_URL if needed

# Start everything
docker compose up -d

# Pull Ollama models
docker exec -it infinite-backrooms-ollama ollama pull granite3.3:8b
docker exec -it infinite-backrooms-ollama ollama pull qwen2.5:7b

# Access app at http://localhost:8501
```

**Time**: 10 minutes
**Cost**: VPS cost ($5-65/month depending on specs)
**Requirements**: 16GB+ RAM, GPU recommended

---

## Step 3: Verify Deployment

1. Open your app URL
2. Click "Check Ollama Connection" button
3. If successful, you'll see available models
4. Add personas and start chatting!

### Troubleshooting

**"Could not connect to Ollama"**
- Verify OLLAMA_URL is correct
- Ensure Ollama server is running
- Check firewall/security group settings

**"Out of Memory"**
- Use smaller models (tinyllama, phi3:mini)
- Reduce MAX_HISTORY_MESSAGES to 20
- Upgrade to larger plan

**"Static CSS not loading"**
- Ensure static/ directory is included in deployment
- Check .dockerignore doesn't exclude static/
- Verify files are committed to git

---

## Production Checklist

Before going live:

- [ ] OLLAMA_URL is set correctly (not localhost)
- [ ] DEBUG=false in environment
- [ ] SSL/HTTPS enabled
- [ ] Ollama API secured (API key or VPN)
- [ ] Monitoring set up (UptimeRobot)
- [ ] Backups configured for conversations/
- [ ] Health check endpoint working: `/_stcore/health`

---

## Cost Breakdown

### Free Option (Testing):
- **Streamlit Cloud**: FREE
- **Groq API**: FREE tier (limited)
- **Total**: $0/month

### Budget Option:
- **Railway.app**: $5/month
- **Vast.ai GPU**: ~$10/month
- **Total**: ~$15/month

### Production Option:
- **DigitalOcean GPU Droplet**: $65/month
- Everything on one server
- **Total**: $65/month

---

## Next Steps

1. Read full deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md)
2. Run pre-deployment checks: `./scripts/deploy_check.sh`
3. Set up monitoring and alerts
4. Configure custom domain (optional)
5. Enable authentication (Streamlit Cloud provides this)

---

## Support

- **Issues**: https://github.com/nitepoetlaureate/infinite-backrooms/issues
- **Docs**: See DEPLOYMENT.md for detailed instructions

---

**Deployment created**: November 2025
**Status**: Production Ready ✓
