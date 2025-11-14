# AGGRESSIVE FIX PLAN - Infinite AI Backrooms

**Plan Created:** 2025-11-14
**Target Completion:** 2025-11-21 (7 days)
**Priority:** MAXIMUM

---

## EXECUTION STRATEGY

This plan is organized into **5 PHASES** with **ZERO TOLERANCE FOR FAILURE**.

Each phase MUST be completed before moving to the next.
All items are **MANDATORY** unless marked [OPTIONAL].

---

## PHASE 1: CRITICAL BUGS (P0) - DAY 1
**Goal:** Fix all showstopper bugs that prevent basic functionality

### 1.1 Fix Conversations Directory Bug ✓
**File:** `log_viewer.py`
**Line:** 17-18

```python
# BEFORE (BROKEN):
def __init__(self, log_dir: str = "conversations"):
    self.log_dir = Path(log_dir)

# AFTER (FIXED):
def __init__(self, log_dir: str = "conversations"):
    self.log_dir = Path(log_dir)
    self.log_dir.mkdir(exist_ok=True)  # CREATE IF MISSING
```

**Test:** Verify app doesn't crash on first run

---

### 1.2 Fix Log File Naming Inconsistency ✓
**File:** `log_viewer.py`
**Line:** 27-30

```python
# BEFORE (BROKEN):
patterns = ["backroom_*.txt", "ai_conversation_*.txt"]

# AFTER (FIXED):
patterns = ["backroom_*.txt", "ai_conversation_*.txt", "streamlit_backroom_*.txt"]
```

**Test:** Create a log file, verify log viewer can find it

---

### 1.3 Fix Async Event Loop Mess ✓
**Files:** `streamlit_backroom.py`
**Lines:** 311-324, 892-1002, 1109-1119

**Strategy:** Create a proper async runner utility

```python
# NEW FILE: async_utils.py
import asyncio
from typing import TypeVar, Callable, Awaitable

T = TypeVar('T')

def run_async(coro: Awaitable[T]) -> T:
    """Properly run async code in Streamlit context"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already in async context - should not happen in Streamlit
            raise RuntimeError("Cannot run async in running loop")
        return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop exists
        return asyncio.run(coro)
```

**Replace all instances** of manual event loop creation with `run_async()`

**Test:** Verify no asyncio warnings appear

---

## PHASE 2: INFRASTRUCTURE (P1) - DAY 2-3
**Goal:** Add essential development infrastructure

### 2.1 Add Test Framework ✓
**New files to create:**

```
tests/
├── __init__.py
├── conftest.py
├── test_ollama_client.py
├── test_conversation_logger.py
├── test_log_parser.py
└── test_streamlit_app.py
```

**Install test dependencies:**
```bash
uv add --dev pytest pytest-asyncio pytest-cov pytest-mock
```

**Minimum tests required:**
- OllamaClient connection test
- OllamaClient generate_stream test (mocked)
- ConversationLogger file creation test
- ConversationLogger message cleaning test
- LogParser file parsing test
- Persona creation test

**Target: 50% code coverage minimum**

---

### 2.2 Add Type Hints ✓
**Tools:**
```bash
uv add --dev mypy types-aiohttp
```

**Files to type:**
1. `streamlit_backroom.py` - ALL functions
2. `log_viewer.py` - ALL functions

**Create:** `pyproject.toml` mypy configuration

```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

**Test:** `mypy . --strict` should pass

---

### 2.3 Add CI/CD Pipeline ✓
**New file:** `.github/workflows/ci.yml`

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install UV
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install dependencies
        run: uv sync
      - name: Run tests
        run: uv run pytest --cov --cov-report=xml
      - name: Type check
        run: uv run mypy .
      - name: Lint
        run: uv run ruff check .
      - name: Format check
        run: uv run ruff format --check .

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Security scan
        run: |
          pip install bandit
          bandit -r . -f json -o bandit-report.json
```

---

### 2.4 Add Linting and Formatting ✓
```bash
uv add --dev ruff black isort
```

**Create:** `.ruff.toml`

```toml
line-length = 100
target-version = "py312"

[lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "A", "C4", "DTZ", "T10", "EM", "ISC", "ICN", "PIE", "PT", "Q", "RSE", "RET", "SIM", "TID", "ARG", "PTH", "ERA", "PD", "PGH", "PL", "TRY", "NPY", "RUF"]
ignore = ["E501"]  # Line too long (handled by formatter)
```

**Run:**
```bash
uv run ruff check --fix .
uv run ruff format .
```

---

## PHASE 3: CODE QUALITY (P1) - DAY 4-5
**Goal:** Improve code architecture and maintainability

### 3.1 Extract Constants ✓
**New file:** `constants.py`

```python
"""Application constants and configuration"""

# Ollama Configuration
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_TIMEOUT = 10

# Message Limits
MIN_HISTORY_MESSAGES = 10
MAX_HISTORY_MESSAGES = 200
DEFAULT_HISTORY_MESSAGES = 50

MIN_CONTEXT_MESSAGES = 1
MAX_CONTEXT_MESSAGES = 25
DEFAULT_CONTEXT_MESSAGES = 10

# Timeouts
MIN_RESPONSE_TIMEOUT = 30
MAX_RESPONSE_TIMEOUT = 600
DEFAULT_RESPONSE_TIMEOUT = 300

# Delays
MIN_RESPONSE_DELAY = 1
MAX_RESPONSE_DELAY = 60
DEFAULT_RESPONSE_DELAY_MIN = 2
DEFAULT_RESPONSE_DELAY_MAX = 8

# Logging
LOG_DIR = "conversations"
LOG_FILE_PREFIX = "streamlit_backroom"
LOG_TIMESTAMP_FORMAT = "%H:%M:%S"
LOG_DATE_FORMAT = "%Y-%m-%d"

# UI Colors
DEFAULT_PERSONA_COLOR = "#1f77b4"
```

**Replace all magic numbers** in both files

---

### 3.2 Extract Role Definitions ✓
**New file:** `roles.py`

```python
"""Persona role definitions and utilities"""
from dataclasses import dataclass
from typing import Dict

@dataclass
class RoleDefinition:
    """Definition of a persona role"""
    name: str
    description: str
    emoji: str
    special_instructions: str = ""

# All role definitions in ONE place
ROLES: Dict[str, RoleDefinition] = {
    "Moderator": RoleDefinition(
        name="Moderator",
        description="A skilled conversation facilitator...",
        emoji="🎯",
        special_instructions="As a Moderator, focus on..."
    ),
    # ... all other roles
}

def get_role_emoji(role: str) -> str:
    """Get emoji for role, with fallback"""
    return ROLES.get(role, RoleDefinition("", "", "🤖")).emoji
```

**Delete duplicated role maps** from main file

---

### 3.3 Refactor StreamlitBackroomApp ✓
**Strategy:** Split into separate modules

**New structure:**
```
src/
├── __init__.py
├── ui/
│   ├── __init__.py
│   ├── conversation_tab.py
│   ├── personas_tab.py
│   ├── settings_tab.py
│   └── export_tab.py
├── services/
│   ├── __init__.py
│   ├── ollama_service.py
│   ├── conversation_service.py
│   └── logging_service.py
├── models/
│   ├── __init__.py
│   ├── persona.py
│   └── message.py
└── utils/
    ├── __init__.py
    ├── async_utils.py
    └── validation.py
```

**This is a MAJOR refactor** - estimate 8-10 hours

---

### 3.4 Add Configuration Management ✓
**New file:** `config.py`

```python
"""Configuration management using environment variables"""
from pathlib import Path
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings"""

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout: int = 10

    # Logging
    log_dir: Path = Path("conversations")
    log_level: str = "INFO"

    # Features
    enable_thinking_default: bool = True

    class Config:
        env_prefix = "BACKROOM_"
        env_file = ".env"

settings = Settings()
```

**Create:** `.env.example`

```bash
# Ollama Configuration
BACKROOM_OLLAMA_BASE_URL=http://localhost:11434
BACKROOM_OLLAMA_TIMEOUT=10

# Logging
BACKROOM_LOG_DIR=conversations
BACKROOM_LOG_LEVEL=INFO

# Features
BACKROOM_ENABLE_THINKING_DEFAULT=true
```

**Install:** `uv add pydantic pydantic-settings python-dotenv`

---

## PHASE 4: SECURITY & VALIDATION (P2) - DAY 6
**Goal:** Harden security and add input validation

### 4.1 Add Input Validation ✓
**New file:** `validators.py`

```python
"""Input validation utilities"""
from typing import Optional
import re

MAX_PERSONA_NAME_LENGTH = 50
MAX_SYSTEM_PROMPT_LENGTH = 5000
MAX_MESSAGE_LENGTH = 10000

class ValidationError(Exception):
    """Raised when validation fails"""
    pass

def validate_persona_name(name: str) -> str:
    """Validate and sanitize persona name"""
    name = name.strip()

    if not name:
        raise ValidationError("Persona name cannot be empty")

    if len(name) > MAX_PERSONA_NAME_LENGTH:
        raise ValidationError(f"Persona name too long (max {MAX_PERSONA_NAME_LENGTH})")

    if not re.match(r'^[a-zA-Z0-9_\- ]+$', name):
        raise ValidationError("Persona name contains invalid characters")

    return name

def validate_system_prompt(prompt: str) -> str:
    """Validate and sanitize system prompt"""
    prompt = prompt.strip()

    if len(prompt) > MAX_SYSTEM_PROMPT_LENGTH:
        raise ValidationError(f"System prompt too long (max {MAX_SYSTEM_PROMPT_LENGTH})")

    # Check for potential injection attempts
    dangerous_patterns = [
        r'<script',
        r'javascript:',
        r'onerror=',
        r'onclick=',
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            raise ValidationError("System prompt contains potentially dangerous content")

    return prompt

def validate_message(message: str) -> str:
    """Validate message content"""
    if len(message) > MAX_MESSAGE_LENGTH:
        raise ValidationError(f"Message too long (max {MAX_MESSAGE_LENGTH})")

    return message
```

**Apply validation** to all user inputs

---

### 4.2 Add Rate Limiting ✓
**New file:** `rate_limiter.py`

```python
"""Rate limiting for API calls"""
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict

class RateLimiter:
    """Simple rate limiter"""

    def __init__(self, max_requests: int, time_window: timedelta):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, list] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed"""
        now = datetime.now()
        cutoff = now - self.time_window

        # Remove old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > cutoff
        ]

        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            return False

        # Record request
        self.requests[key].append(now)
        return True

# Global rate limiter: 10 requests per minute per persona
ollama_rate_limiter = RateLimiter(max_requests=10, time_window=timedelta(minutes=1))
```

**Apply to Ollama API calls**

---

### 4.3 Add Security Headers ✓
**New file:** `.streamlit/config.toml`

```toml
[server]
enableXsrfProtection = true
enableCORS = false

[browser]
gatherUsageStats = false
```

---

### 4.4 Add Logging Framework ✓
**Replace direct file writes** with proper logging

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configure application logging"""
    logger = logging.getLogger("backroom")
    logger.setLevel(logging.INFO)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter('%(levelname)s: %(message)s')
    )

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
```

---

## PHASE 5: DOCUMENTATION & DEPLOYMENT (P3) - DAY 7
**Goal:** Make project production-ready

### 5.1 Add Comprehensive Documentation ✓

**Files to create:**

1. `CONTRIBUTING.md` - Developer guide
2. `ARCHITECTURE.md` - System architecture
3. `DEPLOYMENT.md` - Deployment guide
4. `TROUBLESHOOTING.md` - Common issues
5. `CHANGELOG.md` - Version history
6. `CODE_OF_CONDUCT.md` - Community guidelines

**Update:** `README.md` with accurate information

---

### 5.2 Add Docker Support ✓
**New file:** `Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application
COPY . .

# Create conversations directory
RUN mkdir -p conversations

# Expose Streamlit port
EXPOSE 8501

# Run application
CMD ["uv", "run", "streamlit", "run", "streamlit_backroom.py", "--server.address", "0.0.0.0"]
```

**New file:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./conversations:/app/conversations
    environment:
      - BACKROOM_OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
```

---

### 5.3 Add Monitoring [OPTIONAL] ✓
**Install:** `uv add prometheus-client`

**Add:** Health check endpoint and metrics

---

### 5.4 Add Database [OPTIONAL] ⚠️
**This is OPTIONAL but recommended for persistence**

**Install:** `uv add sqlalchemy alembic`

**Create:** Database models for:
- Personas
- Messages
- Conversation sessions

---

## IMPLEMENTATION ORDER

Execute in this EXACT order:

1. **PHASE 1** - Critical bugs (4 hours)
2. **PHASE 2** - Infrastructure (12 hours)
3. **PHASE 3** - Code quality (16 hours)
4. **PHASE 4** - Security (8 hours)
5. **PHASE 5** - Documentation (8 hours)

**TOTAL TIME:** ~48 hours (6 work days)

---

## TESTING CHECKLIST

After each phase, verify:

- [ ] All tests pass
- [ ] No mypy errors
- [ ] No ruff errors
- [ ] CI pipeline passes
- [ ] Manual smoke test successful
- [ ] No console warnings/errors

---

## SUCCESS CRITERIA

Project is considered **COMPLETE** when:

1. ✅ All critical bugs fixed
2. ✅ Test coverage >50%
3. ✅ CI/CD pipeline passing
4. ✅ No type checking errors
5. ✅ No linting errors
6. ✅ All documentation complete
7. ✅ Docker deployment working
8. ✅ No security vulnerabilities
9. ✅ Manual testing successful
10. ✅ Code review approved

---

## NEXT STEPS

**IMMEDIATE ACTIONS:**

1. Create new branch: `aggressive-fixes`
2. Start with Phase 1 bugs
3. Commit after each fix
4. Run tests after each phase
5. Deploy to staging environment
6. Final production deployment

**NO EXCUSES. NO SHORTCUTS. GET IT DONE.**

---

**Plan Author:** Claude (Sonnet 4.5)
**Commitment:** MAXIMUM EFFORT
**Deadline:** 2025-11-21
