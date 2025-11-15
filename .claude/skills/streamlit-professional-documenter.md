# streamlit-professional-documenter

**Purpose**: Create comprehensive professional documentation for Streamlit applications

**Use When**: Need to document application for users, developers, operators, or stakeholders

---

## Domain Knowledge

### Documentation Types
- **User Documentation**: How to use the application
- **Developer Documentation**: How to contribute/extend
- **API Documentation**: Endpoint references
- **Architecture Documentation**: System design
- **Operations Documentation**: Deployment and maintenance

### Documentation Audiences
- **End Users**: Feature guides, tutorials, FAQs
- **Developers**: Setup, API reference, contributing guide
- **Operators**: Deployment, monitoring, troubleshooting
- **Stakeholders**: Architecture, decisions, roadmap

### Documentation Standards
- **README.md**: Project overview and quick start
- **CONTRIBUTING.md**: How to contribute
- **docs/**: Detailed documentation directory
- **API.md**: API reference
- **ARCHITECTURE.md**: System design
- **DEPLOYMENT.md**: Deployment guide
- **TROUBLESHOOTING.md**: Common issues and solutions

---

## Workflow

### Step 1: Create Comprehensive README.md (60-90 min)

**Pattern: Professional README**:
```markdown
# Infinite Backrooms

> Multi-AI conversation orchestration platform built with Streamlit

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.30+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](https://github.com/yourusername/infinite-backrooms/actions)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)](https://codecov.io/gh/yourusername/infinite-backrooms)

## Overview

Infinite Backrooms is a production-ready Streamlit application that orchestrates conversations between multiple AI personas powered by Ollama. Features include real-time streaming, conversation history, memory management, and comprehensive monitoring.

### Key Features

- 🤖 **Multi-AI Orchestration**: Manage conversations between multiple AI personas
- 📊 **Real-time Streaming**: Stream AI responses in real-time
- 💾 **Conversation History**: Persistent storage and retrieval
- 🔒 **Security Hardened**: XSS prevention, input validation, rate limiting
- ⚡ **Performance Optimized**: Connection pooling, memory management
- 📈 **Comprehensive Monitoring**: Metrics, health checks, alerting
- 🎨 **Retro UI**: Classic Mac OS System 7 aesthetic

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [Ollama](https://ollama.ai/) installed and running
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/infinite-backrooms.git
cd infinite-backrooms

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run streamlit_backroom.py
```

### First Run

1. **Start Ollama**: Ensure Ollama is running on `localhost:11434`
2. **Open Browser**: Navigate to `http://localhost:8501`
3. **Check Connection**: Click "Check Ollama Connection"
4. **Create Personas**: Define your AI personas
5. **Start Conversation**: Begin your multi-AI conversation

## Documentation

- [User Guide](docs/USER_GUIDE.md) - How to use the application
- [Developer Guide](docs/DEVELOPER_GUIDE.md) - Contributing and development setup
- [API Documentation](docs/API.md) - API reference
- [Architecture](docs/ARCHITECTURE.md) - System design and architecture
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## Project Structure

```
infinite-backrooms/
├── src/
│   ├── models/          # Data models (Persona, Memory)
│   ├── services/        # Business logic (Client, Logger, Orchestrator)
│   ├── ui/              # Streamlit UI components
│   ├── utils/           # Utilities (validation, sanitization)
│   └── monitoring/      # Monitoring and observability
├── tests/
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   ├── component/       # Component tests
│   └── e2e/             # End-to-end tests
├── docs/                # Documentation
├── scripts/             # Utility scripts
├── .streamlit/          # Streamlit configuration
└── streamlit_backroom.py # Main application
```

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html

# Run linting
ruff check src/

# Run type checking
mypy src/
```

### Running Tests

```bash
# All tests
pytest -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# E2E tests (requires app running)
pytest tests/e2e/ -v

# With coverage
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Deployment

### Production Deployment

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for comprehensive deployment guide.

Quick deployment options:

- **Railway**: One-click deploy with provided configuration
- **Render**: Automatic deploys from GitHub
- **Docker**: Multi-platform container support
- **Streamlit Cloud**: Native Streamlit hosting

### Environment Variables

```bash
OLLAMA_BASE_URL=http://localhost:11434
LOG_LEVEL=INFO
MAX_MESSAGES=1000
MESSAGE_RETENTION_DAYS=30
ENABLE_MONITORING=true
```

See `.env.example` for complete configuration.

## Monitoring

### Health Checks

- **Application Health**: `http://localhost:8501/healthz`
- **Ollama Connection**: Monitored continuously
- **Memory Usage**: Real-time metrics dashboard

### Metrics

- Request rate and latency
- Error rates and types
- Memory usage and limits
- Connection pool status

See [docs/MONITORING.md](docs/MONITORING.md) for details.

## Security

- ✅ Input validation and sanitization
- ✅ XSS prevention with HTML sanitization
- ✅ Path traversal protection
- ✅ Rate limiting
- ✅ Secure logging
- ✅ Dependency vulnerability scanning

See [SECURITY.md](SECURITY.md) for security policy.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest -v`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Performance

- **Response Time**: < 2s (p95)
- **Uptime**: 99.9% target
- **Test Coverage**: 85%
- **Memory Usage**: Bounded with automatic cleanup

## Roadmap

- [ ] Multi-user support with authentication
- [ ] Conversation branching and forking
- [ ] Advanced memory with vector search
- [ ] Custom model fine-tuning
- [ ] Mobile-responsive design
- [ ] API for programmatic access

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Streamlit](https://streamlit.io/) - Web framework
- [Ollama](https://ollama.ai/) - Local LLM server
- [aiohttp](https://docs.aiohttp.org/) - Async HTTP client
- [bleach](https://bleach.readthedocs.io/) - HTML sanitization

## Support

- 📧 Email: support@example.com
- 💬 Discord: [Join our community](https://discord.gg/example)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/infinite-backrooms/issues)
- 📖 Docs: [Documentation](https://docs.example.com)

---

Made with ❤️ by [Your Name](https://github.com/yourusername)
```

### Step 2: Create User Guide (90-120 min)

**Pattern: Comprehensive User Guide** (`docs/USER_GUIDE.md`):
```markdown
# Infinite Backrooms User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Creating AI Personas](#creating-ai-personas)
3. [Starting Conversations](#starting-conversations)
4. [Managing Conversation History](#managing-conversation-history)
5. [Advanced Features](#advanced-features)
6. [Troubleshooting](#troubleshooting)

## Getting Started

### First Launch

When you first launch Infinite Backrooms, you'll be greeted with a welcome screen:

1. **Check Ollama Connection**: Click the "Check Ollama Connection" button to verify your Ollama server is running
2. **View Available Models**: See which AI models are available
3. **Configure Settings**: Adjust default settings if needed

### Interface Overview

The main interface consists of four sections:

- **Sidebar**: Navigation and settings
- **Persona Manager**: Create and edit AI personas
- **Conversation Area**: Active conversation display
- **Control Panel**: Start, stop, and manage conversations

## Creating AI Personas

### Basic Persona Creation

1. Click "Create New Persona" in the sidebar
2. Fill in the required fields:
   - **Name**: Give your AI persona a name (e.g., "Alice", "Bob")
   - **Model**: Select from available Ollama models
   - **System Prompt**: Describe the persona's behavior and personality
3. Click "Create Persona"

### Example Personas

**Helpful Assistant**:
```
Name: Alice
Model: llama2
System Prompt: You are a helpful, friendly AI assistant. Answer questions clearly and concisely.
```

**Creative Writer**:
```
Name: Bob
Model: mistral
System Prompt: You are a creative writer who loves storytelling. Be imaginative and descriptive.
```

### Advanced Persona Options

- **Thinking Mode**: Enable to see the AI's internal reasoning
- **Temperature**: Control creativity (0.0 = focused, 1.0 = creative)
- **Context Window**: Adjust how much conversation history to use

## Starting Conversations

### Single AI Conversation

1. Select a persona from the dropdown
2. Type your message in the input box
3. Press Enter or click "Send"
4. Watch the AI response stream in real-time

### Multi-AI Conversations

1. Click "Multi-AI Conversation"
2. Select multiple personas
3. Set the number of turns
4. Click "Start Conversation"
5. Watch the AIs converse with each other

### Conversation Controls

- **Pause**: Temporarily pause generation
- **Stop**: Stop generation completely
- **Clear**: Clear current conversation
- **Export**: Download conversation as JSON or Markdown

## Managing Conversation History

### Viewing History

- Click "Conversation History" in sidebar
- Browse past conversations by date
- Search conversations by content or persona

### Exporting Conversations

1. Select a conversation
2. Click "Export"
3. Choose format (JSON, Markdown, PDF)
4. Download the file

### Deleting Conversations

1. Select a conversation
2. Click "Delete"
3. Confirm deletion (this cannot be undone)

## Advanced Features

### Thinking Mode

Enable thinking mode to see AI's reasoning process:

```
<think>
Let me break down this question...
1. First, I need to understand...
2. Then, I should consider...
3. Finally, I'll conclude...
</think>

Here's my response: [actual response]
```

### Memory Management

Configure how conversations are stored:

- **Max Messages**: Limit conversation length (default: 1000)
- **Retention Period**: Auto-delete old conversations (default: 30 days)
- **Archive**: Permanently save important conversations

### Customization

**Themes**:
- System 7 (default retro Mac aesthetic)
- Modern (clean, minimal design)
- Custom (create your own)

**Keyboard Shortcuts**:
- `Ctrl+Enter`: Send message
- `Ctrl+N`: New conversation
- `Ctrl+E`: Export conversation
- `Ctrl+K`: Clear conversation

## Troubleshooting

### "Cannot connect to Ollama"

**Solution**:
1. Ensure Ollama is installed: `ollama --version`
2. Start Ollama service: `ollama serve`
3. Verify it's running on port 11434
4. Check firewall settings

### "Model not found"

**Solution**:
1. List available models: `ollama list`
2. Pull the model: `ollama pull llama2`
3. Refresh the application

### "Response is slow"

**Possible causes**:
- Large model selected (try a smaller model)
- Long conversation history (clear or start new conversation)
- System resources low (close other applications)

### Getting Help

- Check [Troubleshooting Guide](TROUBLESHOOTING.md)
- Search [GitHub Issues](https://github.com/yourusername/infinite-backrooms/issues)
- Join [Discord Community](https://discord.gg/example)
- Email support@example.com

---

*Last updated: 2025-01-14*
```

### Step 3: Create API Documentation (60-90 min)

**Pattern: API Reference** (`docs/API.md`):
```markdown
# API Documentation

## Core Classes

### OllamaClient

Async HTTP client for Ollama API with connection pooling.

```python
from src.services.ollama_client import OllamaClient

async with OllamaClient() as client:
    connected, models = await client.test_connection()
```

#### Methods

##### `__init__(base_url: str = "http://localhost:11434", timeout: int = 300, max_connections: int = 100)`

Initialize Ollama client.

**Parameters**:
- `base_url` (str): Ollama server URL
- `timeout` (int): Request timeout in seconds
- `max_connections` (int): Maximum concurrent connections

**Example**:
```python
client = OllamaClient(
    base_url="http://localhost:11434",
    timeout=300,
    max_connections=100
)
```

##### `async test_connection() -> tuple[bool, list[str]]`

Test connection and retrieve available models.

**Returns**:
- `tuple[bool, list[str]]`: (connected, models list)

**Raises**:
- `aiohttp.ClientError`: Connection failed

**Example**:
```python
async with OllamaClient() as client:
    connected, models = await client.test_connection()
    if connected:
        print(f"Available models: {models}")
```

##### `async generate_stream(model: str, prompt: str, system_prompt: Optional[str] = None, think: bool = False, timeout: int = 300) -> AsyncGenerator[dict, None]`

Generate streaming response from model.

**Parameters**:
- `model` (str): Model name to use
- `prompt` (str): User prompt
- `system_prompt` (Optional[str]): System prompt for persona
- `think` (bool): Enable thinking mode
- `timeout` (int): Request timeout

**Yields**:
- `dict`: Response chunks with 'type' and 'content' keys

**Example**:
```python
async with OllamaClient() as client:
    async for chunk in client.generate_stream("llama2", "Hello"):
        if chunk["type"] == "response":
            print(chunk["content"], end="")
```

### ConversationOrchestrator

Orchestrates multi-AI conversations.

```python
from src.services.conversation_orchestrator import ConversationOrchestrator

orchestrator = ConversationOrchestrator(client=client, logger=logger)
```

#### Methods

##### `async execute_turn(persona: AIPersona, context: str) -> str`

Execute single conversation turn.

**Parameters**:
- `persona` (AIPersona): Persona to generate response
- `context` (str): Conversation context

**Returns**:
- `str`: Generated response

**Example**:
```python
response = await orchestrator.execute_turn(
    persona=alice,
    context="Previous conversation..."
)
```

## Data Models

### AIPersona

Represents an AI persona.

**Attributes**:
- `name` (str): Persona name
- `model` (str): Ollama model name
- `description` (str): System prompt
- `thinking_enabled` (bool): Enable thinking mode

**Example**:
```python
from src.models.persona import AIPersona

persona = AIPersona(
    name="Alice",
    model="llama2",
    description="You are a helpful assistant",
    thinking_enabled=False
)
```

## Utilities

### SecurityValidator

Input validation for security.

```python
from src.utils.validation import SecurityValidator

# Validate model name
validated = SecurityValidator.validate_model_name("llama2")

# Validate file path
safe_path = SecurityValidator.validate_path(path, base_dir)
```

### HTMLSanitizer

HTML sanitization to prevent XSS.

```python
from src.utils.html_sanitizer import HTMLSanitizer

# Sanitize HTML
clean_html = HTMLSanitizer.sanitize_html(user_input)

# Sanitize markdown
clean_md = HTMLSanitizer.sanitize_markdown(user_input)
```

---

*Generated from source code. Last updated: 2025-01-14*
```

### Step 4: Create Operations Runbook (60-90 min)

**Pattern: Operations Runbook** (`docs/RUNBOOK.md`):
```markdown
# Operations Runbook

## Quick Reference

| Issue | Command | Expected Result |
|-------|---------|-----------------|
| Check app status | `curl http://localhost:8501/healthz` | `{"status": "healthy"}` |
| View logs | `tail -f logs/app.log` | Real-time logs |
| Restart app | `systemctl restart streamlit` | Application restarts |
| Check Ollama | `curl http://localhost:11434/api/tags` | List of models |

## Health Checks

### Application Health

```bash
# Check if app is running
curl http://localhost:8501/healthz

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-01-14T12:00:00Z",
  "ollama_connected": true
}
```

### Ollama Connection

```bash
# Test Ollama connection
curl http://localhost:11434/api/tags

# Should return list of models
```

## Common Operations

### Starting the Application

```bash
# Production (systemd)
sudo systemctl start streamlit

# Development
streamlit run streamlit_backroom.py
```

### Stopping the Application

```bash
# Production
sudo systemctl stop streamlit

# Development
# Press Ctrl+C in terminal
```

### Viewing Logs

```bash
# Application logs
tail -f logs/app.log

# Error logs only
grep ERROR logs/app.log

# Last 100 lines
tail -n 100 logs/app.log
```

### Clearing Cache

```bash
# Clear Streamlit cache
streamlit cache clear

# Clear conversation history
rm -rf data/conversations/*

# Clear logs (be careful!)
rm -rf logs/*.log
```

## Troubleshooting

### Application Won't Start

1. Check if port 8501 is available:
   ```bash
   lsof -i :8501
   ```

2. Check Ollama is running:
   ```bash
   systemctl status ollama
   ```

3. Check logs for errors:
   ```bash
   tail -n 50 logs/app.log
   ```

### High Memory Usage

1. Check memory usage:
   ```bash
   free -h
   ```

2. Check application memory:
   ```bash
   ps aux | grep streamlit
   ```

3. Clear conversation history to free memory

### Slow Response Times

1. Check Ollama model size:
   ```bash
   ollama list
   ```

2. Monitor resource usage:
   ```bash
   htop
   ```

3. Check connection pool:
   - Look for "pool exhausted" in logs

## Monitoring

### Key Metrics to Monitor

- **Request Rate**: < 1000 requests/minute
- **Response Time**: p95 < 2 seconds
- **Error Rate**: < 0.1%
- **Memory Usage**: < 2GB
- **CPU Usage**: < 80%

### Alerting Thresholds

- **CRITICAL**: Error rate > 5%
- **WARNING**: Response time p95 > 5s
- **INFO**: Memory usage > 1.5GB

---

*For emergencies, contact: oncall@example.com*
```

---

## Best Practices

### Documentation Writing
1. Write for your audience
2. Use examples liberally
3. Keep content up-to-date
4. Include troubleshooting
5. Add screenshots where helpful

### Documentation Structure
1. Overview first, details later
2. Logical progression
3. Clear navigation
4. Searchable content
5. Version control

### Maintenance
1. Review quarterly
2. Update with code changes
3. Validate examples work
4. Fix broken links
5. Gather user feedback

---

## Success Criteria

- [ ] README.md comprehensive and professional
- [ ] User guide complete with examples
- [ ] API documentation accurate
- [ ] Architecture documented
- [ ] Deployment guide created
- [ ] Operations runbook written
- [ ] Troubleshooting guide included
- [ ] All examples validated

---

## Tools Available
- Read: Read existing documentation
- Write: Create new documentation
- Edit: Update documentation
- Bash: Validate examples
- Grep: Find documentation gaps

---

## Validation Commands

```bash
# Check all docs exist
ls -lh docs/

# Validate Markdown syntax
markdownlint docs/*.md

# Check for broken links
markdown-link-check docs/*.md

# Generate table of contents
doctoc docs/*.md

# Spell check
aspell check README.md
```
