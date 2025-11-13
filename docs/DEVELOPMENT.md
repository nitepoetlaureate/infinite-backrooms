# Development Guide

This guide helps you set up a development environment and contribute to the Infinite AI Backrooms project.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Code Quality Tools](#code-quality-tools)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Debugging](#debugging)
- [Performance Profiling](#performance-profiling)

---

## Prerequisites

### Required Software

1. **Python 3.12+**
   ```bash
   python --version  # Should show 3.12 or higher
   ```

2. **UV Package Manager**
   ```bash
   # Install uv
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Or with pip
   pip install uv

   # Verify installation
   uv --version
   ```

3. **Ollama**
   ```bash
   # Install Ollama (varies by platform)
   # See: https://ollama.ai/download

   # Start Ollama server
   ollama serve

   # Pull at least one model
   ollama pull llama2:latest
   ```

4. **Git**
   ```bash
   git --version
   ```

### Optional Tools

- **VSCode** or **PyCharm** for IDE support
- **Docker** for containerized development
- **Make** for automation scripts

---

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/guinacio/infinite-backrooms.git
cd infinite-backrooms
```

### 2. Install Dependencies

```bash
# Install all dependencies including dev tools
uv pip install -e ".[dev]"

# Or using uv sync (recommended)
uv sync

# Verify installation
uv pip list
```

This installs:
- **Runtime dependencies**: aiohttp, streamlit, pandas, python-dotenv
- **Dev dependencies**: pytest, mypy, ruff, black, pytest-cov

### 3. Configure Environment (Optional)

Create a `.env` file for custom configuration:

```bash
cp .env.example .env
```

Edit `.env`:
```env
# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_TIMEOUT=120
OLLAMA_RESPONSE_TIMEOUT=300

# Logging
LOG_DIRECTORY=conversations
LOG_FILE_PREFIX=streamlit_backroom

# Development
DEBUG=true
```

### 4. Verify Setup

```bash
# Test Ollama connection
curl http://localhost:11434/api/tags

# Run the application
uv run streamlit run streamlit_backroom.py

# Run tests
uv run pytest

# Check code quality
uv run ruff check .
uv run black --check .
uv run mypy .
```

---

## Running Tests

### Basic Test Commands

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_ollama_client.py

# Run specific test
uv run pytest tests/test_persona.py::TestAIPersona::test_persona_creation

# Run tests matching pattern
uv run pytest -k "test_connection"
```

### Coverage Reports

```bash
# Run tests with coverage
uv run pytest --cov

# Generate HTML coverage report
uv run pytest --cov --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# Generate XML coverage (for CI)
uv run pytest --cov --cov-report=xml
```

### Test Markers

```bash
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Skip slow tests
uv run pytest -m "not slow"
```

### Watch Mode

Use `pytest-watch` for continuous testing during development:

```bash
# Install pytest-watch
uv pip install pytest-watch

# Run in watch mode
uv run ptw
```

---

## Code Quality Tools

### Linting with Ruff

Ruff is a fast Python linter:

```bash
# Check all files
uv run ruff check .

# Check specific files
uv run ruff check streamlit_backroom.py

# Auto-fix issues
uv run ruff check --fix .

# Show all rule violations
uv run ruff check --show-files .
```

**Configuration:** See `[tool.ruff]` in `pyproject.toml`

### Formatting with Black

Black formats code automatically:

```bash
# Check formatting
uv run black --check .

# Format all files
uv run black .

# Format specific files
uv run black streamlit_backroom.py

# Show diff without formatting
uv run black --diff .
```

**Configuration:** See `[tool.black]` in `pyproject.toml`

### Type Checking with Mypy

Mypy checks type hints:

```bash
# Check all files
uv run mypy .

# Check specific files
uv run mypy streamlit_backroom.py

# Show error codes
uv run mypy --show-error-codes .

# Generate HTML report
uv run mypy --html-report mypy-report .
```

**Configuration:** See `[tool.mypy]` in `pyproject.toml`

### Security Scanning

#### Bandit (Security Linter)

```bash
# Install bandit
uv pip install bandit

# Scan all files
uv run bandit -r .

# Generate JSON report
uv run bandit -r . -f json -o bandit-report.json

# Exclude tests
uv run bandit -r . --exclude tests/
```

#### Safety (Dependency Vulnerabilities)

```bash
# Install safety
uv pip install safety

# Check dependencies
uv run safety check

# Check with detailed output
uv run safety check --json
```

### Pre-commit Hooks (Recommended)

Install pre-commit to run checks automatically:

```bash
# Install pre-commit
uv pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.0
    hooks:
      - id: mypy
```

### All-in-One Quality Check

```bash
# Run all quality checks
uv run ruff check . && \
uv run black --check . && \
uv run mypy . && \
uv run pytest --cov
```

Or create a `Makefile`:
```makefile
.PHONY: quality
quality:
	uv run ruff check .
	uv run black --check .
	uv run mypy .
	uv run pytest --cov

.PHONY: fix
fix:
	uv run ruff check --fix .
	uv run black .
```

Then run:
```bash
make quality  # Run all checks
make fix      # Auto-fix issues
```

---

## Project Structure

```
infinite-backrooms/
├── streamlit_backroom.py      # Main application entry point
├── log_viewer.py              # Standalone log viewer
├── pyproject.toml             # Project configuration
├── requirements.txt           # Pinned dependencies
├── uv.lock                    # Locked dependencies
├── README.md                  # User documentation
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
│
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures
│   ├── test_ollama_client.py
│   ├── test_logger.py
│   ├── test_persona.py
│   ├── test_validation.py
│   └── fixtures/
│       ├── __init__.py
│       └── mock_responses.py
│
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md        # System design
│   ├── API.md                 # API reference
│   └── DEVELOPMENT.md         # This file
│
├── conversations/             # Log files (created at runtime)
│   └── streamlit_backroom_YYYY-MM-DD.txt
│
├── scripts/                   # Utility scripts
│   ├── migrate_logs.py        # Log migration
│   └── setup_dev.sh           # Development setup
│
└── .github/                   # GitHub configuration
    └── workflows/
        ├── ci.yml             # CI/CD pipeline
        └── security.yml       # Security scanning
```

### Key Files

- **streamlit_backroom.py**: Main Streamlit application with UI and logic
- **log_viewer.py**: Separate app for analyzing conversation logs
- **pyproject.toml**: Project metadata and tool configuration
- **tests/**: Comprehensive test suite with 80%+ coverage goal

---

## Development Workflow

### 1. Create a Feature Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Edit code
- Write tests for new functionality
- Update documentation if needed

### 3. Run Quality Checks

```bash
# Format code
uv run black .

# Fix linting issues
uv run ruff check --fix .

# Run tests
uv run pytest

# Type check
uv run mypy .
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add new persona role template"

# Or use conventional commit format
git commit -m "fix(logger): handle unicode characters in log files"
```

**Commit Message Format:**
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### 5. Push and Create PR

```bash
# Push to remote
git push origin feature/your-feature-name

# Create pull request on GitHub
# Use the PR template and fill in details
```

### 6. Code Review

- Address reviewer feedback
- Make requested changes
- Update PR

### 7. Merge

Once approved and CI passes:
- Squash and merge (preferred)
- Or regular merge for complex features

---

## Debugging

### Streamlit Debugging

```python
import streamlit as st

# Debug session state
st.write("Debug Info:", st.session_state)

# Debug specific variables
st.write(f"Personas: {len(st.session_state.personas)}")

# Use expander for debug info
with st.expander("Debug Info"):
    st.json(st.session_state.to_dict())
```

### Async Debugging

```python
import asyncio
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Add debug statements
async def debug_example():
    logger = logging.getLogger(__name__)
    logger.debug(f"Starting operation...")
    result = await some_async_function()
    logger.debug(f"Result: {result}")
    return result
```

### VSCode Launch Configuration

Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Streamlit",
            "type": "python",
            "request": "launch",
            "module": "streamlit",
            "args": [
                "run",
                "streamlit_backroom.py"
            ],
            "console": "integratedTerminal"
        },
        {
            "name": "Pytest",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["-v"],
            "console": "integratedTerminal"
        }
    ]
}
```

---

## Performance Profiling

### Profile Streamlit App

```python
import cProfile
import pstats
import io

# Profile a function
def profile_function():
    pr = cProfile.Profile()
    pr.enable()

    # Your code here
    expensive_operation()

    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats()
    st.text(s.getvalue())
```

### Memory Profiling

```bash
# Install memory profiler
uv pip install memory-profiler

# Profile script
python -m memory_profiler streamlit_backroom.py
```

### Streamlit Performance

```bash
# Run with performance metrics
streamlit run streamlit_backroom.py --logger.level=debug
```

---

## Troubleshooting

### Common Issues

**1. Ollama Connection Fails**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve
```

**2. Import Errors**
```bash
# Reinstall dependencies
uv pip install -e ".[dev]"
```

**3. Test Failures**
```bash
# Run with verbose output to see details
uv run pytest -vv

# Run specific failing test
uv run pytest tests/test_name.py::test_function -v
```

**4. Type Check Errors**
```bash
# See detailed error messages
uv run mypy --show-error-codes .

# Ignore specific errors temporarily
# type: ignore[error-code]
```

---

## Contributing Guidelines

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Code of Conduct
- How to submit issues
- Pull request process
- Code standards
- Review process

---

## Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [Python Async/Await Guide](https://docs.python.org/3/library/asyncio.html)
- [pytest Documentation](https://docs.pytest.org/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)

---

**Last Updated:** 2024-11-13
**Version:** 0.1.0
