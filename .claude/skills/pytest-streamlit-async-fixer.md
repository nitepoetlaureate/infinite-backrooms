# pytest-streamlit-async-fixer

**Purpose**: Fix pytest test infrastructure for Streamlit applications with async components

**Use When**: Test suite has import errors, async fixtures are broken, or pytest can't find tests in a Streamlit project

---

## Domain Knowledge

### Streamlit Testing Patterns
- Streamlit modules must be imported after `st.set_page_config()`
- Session state requires special handling in tests
- Async components need proper event loop management

### Pytest Configuration
- `pytest.ini` or `pyproject.toml` configuration
- Test discovery patterns (`test_*.py`, `*_test.py`)
- Async test markers (`@pytest.mark.asyncio`)

### Async Testing Best Practices
- Use `AsyncMock` from `unittest.mock` for async functions
- Specify `spec=ClassName` for type-safe mocks
- Use `pytest-asyncio` for async test support
- Proper async generator mocking for streaming responses

### Common Import Issues
- Circular imports in test fixtures
- Missing `__init__.py` files
- Incorrect module paths in conftest.py
- Version mismatches between test dependencies

---

## Workflow

### Step 1: Diagnose Test Failures (30-60 min)
```bash
# Run pytest with verbose output
pytest -v

# Check test discovery
pytest --collect-only

# Run with full traceback
pytest --tb=long
```

**Actions**:
- Document all import errors
- List all affected test files
- Identify missing dependencies
- Note async-related failures

### Step 2: Fix conftest.py Imports (30-45 min)

**Common Patterns**:
```python
# ❌ WRONG: Importing from main app file
from streamlit_backroom import OllamaClient

# ✅ CORRECT: Import from actual module locations
from streamlit_backroom import StreamlitBackroomSafeApp
from src.services.ollama_client_optimized import OllamaClientOptimized
from src.services.logger import ConversationLogger
from src.models.persona import AIPersona
```

**Actions**:
- Read actual codebase structure
- Update all imports to match reality
- Add comments explaining import sources
- Ensure __init__.py files exist

### Step 3: Update Async Mock Fixtures (45-60 min)

**Pattern for Async Client Mocks**:
```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
async def mock_ollama_client():
    """Mock Ollama client for testing."""
    client = AsyncMock(spec=OllamaClientOptimized)
    client.base_url = "http://localhost:11434"

    # Mock async methods with proper return values
    client.test_connection = AsyncMock(
        return_value=(True, ["llama2", "mistral"])
    )

    # Mock async generators for streaming
    async def mock_stream(*args, **kwargs):
        yield {"type": "response", "content": "test response"}
        yield {"type": "done"}

    client.generate_stream = mock_stream
    return client
```

**Actions**:
- Identify all async methods needing mocks
- Create properly typed AsyncMock fixtures
- Test fixtures work independently
- Document mock behavior

### Step 4: Fix Test File Imports (30-45 min)

**Actions**:
- Update imports in all test_*.py files
- Ensure consistency with conftest.py
- Add missing pytest markers
- Fix any parametrize decorators

### Step 5: Configure pytest (15-30 min)

**Create/Update pytest.ini**:
```ini
[pytest]
minversion = 7.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=src
    --cov-report=html
    --cov-report=term-missing
markers =
    asyncio: Async tests
    integration: Integration tests requiring live services
    unit: Unit tests (fast, no external dependencies)
    security: Security-focused tests
```

### Step 6: Validate and Establish Baseline (30-45 min)

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run only unit tests
pytest -m unit -v

# Check coverage percentage
pytest --cov=src --cov-report=term | grep "TOTAL"

# Open coverage report
open htmlcov/index.html
```

**Actions**:
- Document baseline coverage percentage
- Identify which tests pass
- Note remaining failures for follow-up
- Create coverage report

---

## Best Practices

### Import Organization
1. Group imports: stdlib, third-party, local
2. Use absolute imports over relative
3. Document why specific imports are needed
4. Keep conftest.py minimal and focused

### Mock Strategy
1. Use `spec=` for type safety
2. Mock at the boundary (external dependencies only)
3. Return realistic data structures
4. Test mocks independently before using

### Async Patterns
1. Always use `@pytest.mark.asyncio` for async tests
2. Use `AsyncMock` not `Mock` for async functions
3. Test async generators with proper iteration
4. Handle event loop cleanup properly

### Incremental Fixing
1. Fix imports first, then mocks, then tests
2. Validate after each change
3. Commit working changes incrementally
4. Don't try to fix everything at once

---

## Success Criteria

- [ ] `pytest --collect-only` runs without errors
- [ ] `pytest -v` runs without import errors
- [ ] At least 50% of existing tests pass
- [ ] Coverage baseline established and documented
- [ ] All fixtures properly typed with `spec=`
- [ ] Async mocks work correctly
- [ ] Coverage report generated (`htmlcov/index.html`)

---

## Common Issues & Solutions

### Issue: "ImportError: cannot import name X from Y"
**Solution**: Check actual module structure, update import paths in conftest.py

### Issue: "RuntimeError: Event loop is closed"
**Solution**: Use `@pytest.mark.asyncio` and ensure proper event loop management

### Issue: "TypeError: object Mock can't be used in 'await' expression"
**Solution**: Use `AsyncMock` instead of `Mock` for async functions

### Issue: Tests not discovered
**Solution**: Check pytest.ini configuration, ensure test files match patterns

---

## Example: Complete Test Fixture Fix

**Before**:
```python
# Broken fixture
@pytest.fixture
def ollama_client():
    return Mock()  # ❌ Wrong for async
```

**After**:
```python
# Fixed fixture
@pytest.fixture
async def mock_ollama_client():
    """Mock Ollama client with proper async support."""
    client = AsyncMock(spec=OllamaClientOptimized)
    client.base_url = "http://localhost:11434"

    client.test_connection = AsyncMock(
        return_value=(True, ["llama2"])
    )

    async def mock_stream(*args, **kwargs):
        yield {"type": "response", "content": "test"}
        yield {"type": "done"}

    client.generate_stream = mock_stream
    return client
```

---

## Tools Available
- Read: Read test files and conftest.py
- Edit: Update imports and fixtures
- Write: Create new test configuration
- Bash: Run pytest and validation commands
- Grep: Search for import patterns
- Glob: Find all test files

---

## Validation Commands

```bash
# Diagnose
pytest -v --tb=short
pytest --collect-only

# Run tests
pytest -v
pytest -m unit -v

# Coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Check specific file
pytest tests/test_ollama_client.py -v
```
