# streamlit-comprehensive-test-generator

**Purpose**: Generate comprehensive test suite for Streamlit applications with unit, integration, and component tests

**Use When**: Building test infrastructure from scratch or improving existing test coverage for Streamlit projects

---

## Domain Knowledge

### Streamlit Testing Challenges
- Streamlit reruns entire script on every interaction
- Session state requires special mocking
- UI components can't be tested in isolation without mocking
- `st.set_page_config()` must be first Streamlit command

### Pytest + Streamlit Patterns
- Mock Streamlit components with `unittest.mock`
- Use fixtures for session state simulation
- Test business logic separately from UI
- Integration tests validate full user workflows

### Test Coverage Strategy
- **Unit Tests (60%)**: Business logic, utilities, models
- **Integration Tests (30%)**: Service interactions, async flows
- **Component Tests (10%)**: UI component behavior

### Async Testing Best Practices
- Use `@pytest.mark.asyncio` for async tests
- Mock async dependencies with `AsyncMock`
- Test streaming responses with async generators
- Validate timeout and error handling

---

## Workflow

### Step 1: Analyze Current Test Coverage (30-45 min)

**Actions**:
```bash
# Generate coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing

# Identify untested modules
pytest --cov=src --cov-report=term-missing | grep "0%"

# Find all source files
find src/ -name "*.py" -type f | wc -l

# Count existing tests
find tests/ -name "test_*.py" -type f | wc -l

# Analyze test distribution
for file in tests/test_*.py; do
    echo "$file: $(grep -c "^def test_" $file) tests"
done
```

**Create Coverage Analysis**:
| Module | Coverage | Lines | Missing | Priority |
|--------|----------|-------|---------|----------|
| ollama_client.py | 45% | 250 | 138 | HIGH |
| logger.py | 20% | 180 | 144 | HIGH |
| persona.py | 80% | 50 | 10 | LOW |
| validation.py | 10% | 120 | 108 | CRITICAL |

### Step 2: Design Test Architecture (45-60 min)

**Test Structure**:
```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_models.py
│   ├── test_validation.py
│   ├── test_sanitization.py
│   └── test_utils.py
├── integration/             # Integration tests (services)
│   ├── test_ollama_client.py
│   ├── test_logger.py
│   ├── test_orchestrator.py
│   └── test_memory_manager.py
├── component/               # Component tests (UI)
│   ├── test_chat_interface.py
│   ├── test_persona_manager.py
│   └── test_accessibility.py
└── e2e/                     # End-to-end tests
    └── test_full_workflow.py
```

**Test Categorization Strategy**:
```python
# pytest.ini markers
[pytest]
markers =
    unit: Fast unit tests with no external dependencies
    integration: Integration tests requiring mock services
    component: Streamlit component tests
    e2e: End-to-end workflow tests
    asyncio: Async tests requiring event loop
```

### Step 3: Create Core Test Fixtures (60-90 min)

**Pattern: Comprehensive conftest.py**:
```python
"""Shared test fixtures for all test suites."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from typing import AsyncGenerator

from src.services.ollama_client import OllamaClient
from src.services.logger import ConversationLogger
from src.models.persona import AIPersona
from src.state.session_manager import SessionManager


@pytest.fixture
def temp_log_dir(tmp_path: Path) -> Path:
    """Create temporary directory for test logs.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        Path: Temporary log directory
    """
    log_dir = tmp_path / "test_logs"
    log_dir.mkdir(exist_ok=True)
    return log_dir


@pytest.fixture
def sample_persona() -> AIPersona:
    """Create sample AI persona for testing.

    Returns:
        AIPersona: Test persona instance
    """
    return AIPersona(
        name="TestBot",
        model="llama2",
        description="A test AI persona",
        thinking_enabled=False
    )


@pytest.fixture
def sample_personas() -> list[AIPersona]:
    """Create list of sample personas for multi-AI tests.

    Returns:
        list: Multiple test persona instances
    """
    return [
        AIPersona(
            name="Alice",
            model="llama2",
            description="First test persona",
            thinking_enabled=False
        ),
        AIPersona(
            name="Bob",
            model="mistral",
            description="Second test persona",
            thinking_enabled=True
        ),
    ]


@pytest.fixture
async def mock_ollama_client() -> AsyncMock:
    """Create mock Ollama client with realistic behavior.

    Returns:
        AsyncMock: Mocked Ollama client
    """
    client = AsyncMock(spec=OllamaClient)
    client.base_url = "http://localhost:11434"

    # Mock successful connection
    client.test_connection = AsyncMock(
        return_value=(True, ["llama2", "mistral", "codellama"])
    )

    # Mock health check
    client.health_check = AsyncMock(return_value=True)

    # Mock streaming response
    async def mock_stream(*args, **kwargs):
        """Simulate streaming response."""
        chunks = [
            {"type": "response", "content": "Hello "},
            {"type": "response", "content": "from "},
            {"type": "response", "content": "test!"},
            {"type": "done"}
        ]
        for chunk in chunks:
            yield chunk

    client.generate_stream = mock_stream

    # Mock context manager
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    return client


@pytest.fixture
async def mock_ollama_client_error() -> AsyncMock:
    """Create mock Ollama client that simulates errors.

    Returns:
        AsyncMock: Mocked Ollama client with error behavior
    """
    client = AsyncMock(spec=OllamaClient)
    client.base_url = "http://localhost:11434"

    # Simulate connection failure
    client.test_connection = AsyncMock(
        return_value=(False, [])
    )

    # Simulate health check failure
    client.health_check = AsyncMock(return_value=False)

    # Simulate timeout
    async def mock_timeout(*args, **kwargs):
        import asyncio
        raise asyncio.TimeoutError("Request timed out")

    client.generate_stream = mock_timeout

    return client


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit components for component tests.

    Yields:
        MagicMock: Mocked streamlit module
    """
    with patch('streamlit.session_state', {}) as mock_state, \
         patch('streamlit.error') as mock_error, \
         patch('streamlit.success') as mock_success, \
         patch('streamlit.warning') as mock_warning, \
         patch('streamlit.info') as mock_info, \
         patch('streamlit.write') as mock_write, \
         patch('streamlit.markdown') as mock_markdown:

        yield {
            'session_state': mock_state,
            'error': mock_error,
            'success': mock_success,
            'warning': mock_warning,
            'info': mock_info,
            'write': mock_write,
            'markdown': mock_markdown
        }


@pytest.fixture
def mock_logger(temp_log_dir: Path) -> ConversationLogger:
    """Create mock conversation logger.

    Args:
        temp_log_dir: Temporary log directory

    Returns:
        ConversationLogger: Logger instance using temp directory
    """
    return ConversationLogger(log_dir=temp_log_dir)


@pytest.fixture
def mock_session_manager() -> SessionManager:
    """Create mock session manager.

    Returns:
        SessionManager: Session manager instance
    """
    manager = SessionManager()
    manager.initialize_session()
    return manager
```

### Step 4: Generate Unit Tests (2-3 hours)

**Pattern: Model Testing**:
```python
"""Unit tests for AI Persona model."""
import pytest
from src.models.persona import AIPersona


class TestAIPersona:
    """Test suite for AIPersona model."""

    def test_create_valid_persona(self):
        """Test creating valid persona succeeds."""
        persona = AIPersona(
            name="TestBot",
            model="llama2",
            description="A test persona",
            thinking_enabled=False
        )

        assert persona.name == "TestBot"
        assert persona.model == "llama2"
        assert persona.description == "A test persona"
        assert persona.thinking_enabled is False

    def test_validate_name_required(self):
        """Test that name is required."""
        with pytest.raises(ValueError, match="name.*required"):
            AIPersona(
                name="",
                model="llama2",
                description="Test"
            )

    def test_validate_model_required(self):
        """Test that model is required."""
        with pytest.raises(ValueError, match="model.*required"):
            AIPersona(
                name="TestBot",
                model="",
                description="Test"
            )

    def test_validate_name_length(self):
        """Test name length validation."""
        with pytest.raises(ValueError, match="name.*too long"):
            AIPersona(
                name="A" * 101,  # Exceeds max length
                model="llama2",
                description="Test"
            )

    def test_to_dict(self):
        """Test converting persona to dictionary."""
        persona = AIPersona(
            name="TestBot",
            model="llama2",
            description="A test persona",
            thinking_enabled=True
        )

        result = persona.to_dict()

        assert result == {
            "name": "TestBot",
            "model": "llama2",
            "description": "A test persona",
            "thinking_enabled": True
        }

    @pytest.mark.parametrize("thinking", [True, False])
    def test_thinking_mode(self, thinking: bool):
        """Test thinking mode configuration."""
        persona = AIPersona(
            name="TestBot",
            model="llama2",
            description="Test",
            thinking_enabled=thinking
        )

        assert persona.thinking_enabled == thinking
```

**Pattern: Validation Testing**:
```python
"""Unit tests for input validation."""
import pytest
from src.utils.validation import (
    validate_model_name,
    validate_prompt,
    sanitize_path,
    validate_conversation_id
)


class TestValidation:
    """Test suite for validation functions."""

    @pytest.mark.parametrize("valid_name", [
        "llama2",
        "mistral",
        "codellama",
        "llama2:13b"
    ])
    def test_validate_model_name_valid(self, valid_name: str):
        """Test valid model names pass validation."""
        result = validate_model_name(valid_name)
        assert result is True

    @pytest.mark.parametrize("invalid_name", [
        "",
        " ",
        "../../../etc/passwd",
        "model; rm -rf /",
        "model\nwith\nnewlines"
    ])
    def test_validate_model_name_invalid(self, invalid_name: str):
        """Test invalid model names fail validation."""
        with pytest.raises(ValueError):
            validate_model_name(invalid_name)

    def test_validate_prompt_max_length(self):
        """Test prompt length validation."""
        long_prompt = "A" * 10001  # Exceeds max length

        with pytest.raises(ValueError, match="too long"):
            validate_prompt(long_prompt)

    def test_sanitize_path_prevents_traversal(self):
        """Test path sanitization prevents directory traversal."""
        malicious_path = "../../../etc/passwd"

        result = sanitize_path(malicious_path)

        assert ".." not in result
        assert result.is_absolute() is False

    def test_validate_conversation_id_format(self):
        """Test conversation ID format validation."""
        valid_id = "conv_20250114_123456"

        result = validate_conversation_id(valid_id)

        assert result is True

    def test_validate_conversation_id_invalid_format(self):
        """Test invalid conversation ID fails."""
        invalid_id = "../../malicious"

        with pytest.raises(ValueError):
            validate_conversation_id(invalid_id)
```

### Step 5: Generate Integration Tests (2-3 hours)

**Pattern: Ollama Client Integration Tests**:
```python
"""Integration tests for Ollama client."""
import pytest
import asyncio
from unittest.mock import AsyncMock

from src.services.ollama_client import OllamaClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestOllamaClientIntegration:
    """Integration test suite for OllamaClient."""

    async def test_connection_lifecycle(self, mock_ollama_client):
        """Test client connection lifecycle."""
        async with mock_ollama_client as client:
            # Client should be initialized
            assert client is not None

            # Connection should be testable
            connected, models = await client.test_connection()
            assert connected is True
            assert len(models) > 0

        # Context manager should cleanup properly
        mock_ollama_client.__aexit__.assert_called_once()

    async def test_generate_stream_success(self, mock_ollama_client):
        """Test successful streaming generation."""
        async with mock_ollama_client as client:
            chunks = []

            async for chunk in client.generate_stream(
                model="llama2",
                prompt="Test prompt"
            ):
                chunks.append(chunk)

            # Should receive response chunks and done signal
            assert len(chunks) == 4
            assert chunks[-1]["type"] == "done"

            # Should have received content
            content_chunks = [c for c in chunks if c["type"] == "response"]
            assert len(content_chunks) == 3

    async def test_generate_stream_timeout(self, mock_ollama_client_error):
        """Test streaming with timeout handling."""
        async with mock_ollama_client_error as client:
            with pytest.raises(asyncio.TimeoutError):
                async for chunk in client.generate_stream(
                    model="llama2",
                    prompt="Test"
                ):
                    pass

    async def test_health_check_success(self, mock_ollama_client):
        """Test successful health check."""
        async with mock_ollama_client as client:
            healthy = await client.health_check()
            assert healthy is True

    async def test_health_check_failure(self, mock_ollama_client_error):
        """Test failed health check."""
        async with mock_ollama_client_error as client:
            healthy = await client.health_check()
            assert healthy is False

    async def test_concurrent_requests(self, mock_ollama_client):
        """Test handling concurrent requests."""
        async with mock_ollama_client as client:
            # Create multiple concurrent requests
            tasks = [
                client.test_connection()
                for _ in range(10)
            ]

            results = await asyncio.gather(*tasks)

            # All should succeed
            assert all(r[0] is True for r in results)
```

**Pattern: Conversation Orchestrator Tests**:
```python
"""Integration tests for conversation orchestrator."""
import pytest
from unittest.mock import AsyncMock

from src.services.conversation_orchestrator import ConversationOrchestrator


@pytest.mark.integration
@pytest.mark.asyncio
class TestConversationOrchestrator:
    """Integration tests for ConversationOrchestrator."""

    async def test_execute_turn(
        self,
        mock_ollama_client,
        sample_persona,
        mock_logger
    ):
        """Test executing single conversation turn."""
        orchestrator = ConversationOrchestrator(
            client=mock_ollama_client,
            logger=mock_logger
        )

        result = await orchestrator.execute_turn(
            persona=sample_persona,
            context="Previous conversation context"
        )

        assert result is not None
        assert len(result) > 0

    async def test_execute_conversation(
        self,
        mock_ollama_client,
        sample_personas,
        mock_logger
    ):
        """Test executing full multi-turn conversation."""
        orchestrator = ConversationOrchestrator(
            client=mock_ollama_client,
            logger=mock_logger
        )

        results = await orchestrator.execute_conversation(
            personas=sample_personas,
            turns=3
        )

        # Should have results for each persona * turns
        assert len(results) == len(sample_personas) * 3

    async def test_error_handling(
        self,
        mock_ollama_client_error,
        sample_persona,
        mock_logger
    ):
        """Test orchestrator error handling."""
        orchestrator = ConversationOrchestrator(
            client=mock_ollama_client_error,
            logger=mock_logger
        )

        # Should handle errors gracefully
        with pytest.raises(Exception):
            await orchestrator.execute_turn(
                persona=sample_persona,
                context="Test"
            )
```

### Step 6: Generate Component Tests (1-2 hours)

**Pattern: Streamlit Component Tests**:
```python
"""Component tests for Streamlit UI."""
import pytest
from unittest.mock import patch, MagicMock

from src.ui.components import render_chat_message, render_persona_card


@pytest.mark.component
class TestChatComponents:
    """Test suite for chat UI components."""

    def test_render_chat_message(self, mock_streamlit):
        """Test rendering chat message."""
        with patch('src.ui.components.st', mock_streamlit):
            render_chat_message(
                persona_name="TestBot",
                content="Hello, world!",
                thinking=False
            )

            # Should call markdown to render content
            mock_streamlit['markdown'].assert_called()

    def test_render_chat_message_with_thinking(self, mock_streamlit):
        """Test rendering message with thinking content."""
        with patch('src.ui.components.st', mock_streamlit):
            render_chat_message(
                persona_name="TestBot",
                content="<think>Internal thoughts</think>Response",
                thinking=True
            )

            # Should render both thinking and response
            assert mock_streamlit['markdown'].call_count >= 2

    def test_render_persona_card(self, mock_streamlit, sample_persona):
        """Test rendering persona card."""
        with patch('src.ui.components.st', mock_streamlit):
            render_persona_card(sample_persona)

            # Should display persona information
            mock_streamlit['write'].assert_called()
```

### Step 7: Add Coverage Validation (30-45 min)

**Create Coverage Script**:
```python
"""Validate test coverage meets requirements."""
import subprocess
import sys
import json
from pathlib import Path


def check_coverage(min_coverage: float = 80.0) -> bool:
    """Check if test coverage meets minimum threshold.

    Args:
        min_coverage: Minimum coverage percentage required

    Returns:
        bool: True if coverage meets threshold

    Raises:
        SystemExit: If coverage is insufficient
    """
    # Run pytest with coverage
    result = subprocess.run(
        ["pytest", "--cov=src", "--cov-report=json", "--cov-report=term"],
        capture_output=True,
        text=True
    )

    # Load coverage data
    coverage_file = Path("coverage.json")
    if not coverage_file.exists():
        print("ERROR: Coverage file not generated")
        sys.exit(1)

    with open(coverage_file) as f:
        data = json.load(f)

    total_coverage = data["totals"]["percent_covered"]

    print(f"Total Coverage: {total_coverage:.2f}%")
    print(f"Required: {min_coverage:.2f}%")

    if total_coverage < min_coverage:
        print(f"FAIL: Coverage {total_coverage:.2f}% below threshold {min_coverage:.2f}%")
        sys.exit(1)

    print(f"PASS: Coverage {total_coverage:.2f}% meets threshold")
    return True


if __name__ == "__main__":
    check_coverage(min_coverage=80.0)
```

---

## Best Practices

### Test Organization
1. Group tests by type (unit/integration/component)
2. Use descriptive test names following "test_<method>_<scenario>"
3. One assertion per test when possible
4. Use parametrize for similar test cases

### Fixture Design
1. Keep fixtures focused and reusable
2. Use fixture scope appropriately (function/class/module/session)
3. Document fixture behavior and dependencies
4. Avoid fixture interdependencies

### Mocking Strategy
1. Mock at boundaries (external services only)
2. Use `spec=` for type-safe mocks
3. Return realistic data structures
4. Test both success and failure paths

### Async Testing
1. Always mark async tests with `@pytest.mark.asyncio`
2. Use `AsyncMock` for async functions
3. Test concurrent scenarios
4. Validate timeout and cancellation

### Coverage Goals
1. Aim for 80%+ total coverage
2. 100% coverage for critical paths
3. Test edge cases and error conditions
4. Don't sacrifice quality for coverage percentage

---

## Success Criteria

- [ ] Test coverage reaches 80%+ overall
- [ ] All critical modules have 90%+ coverage
- [ ] Unit tests run in <5 seconds
- [ ] Integration tests complete in <30 seconds
- [ ] All async operations properly tested
- [ ] Error handling comprehensively validated
- [ ] Fixtures are reusable and well-documented
- [ ] Test suite passes consistently (no flaky tests)
- [ ] Coverage report generated and reviewed

---

## Common Issues & Solutions

### Issue: "RuntimeError: Event loop is closed"
**Solution**: Use `@pytest.mark.asyncio` and ensure proper async fixture handling

### Issue: Flaky tests (intermittent failures)
**Solution**: Avoid timing dependencies, use proper mocking, ensure test isolation

### Issue: Slow test suite
**Solution**: Optimize fixtures, use appropriate test markers, run unit tests separately

### Issue: Mock not matching actual interface
**Solution**: Always use `spec=` parameter with mock classes

---

## Tools Available
- Read: Read source files to understand implementation
- Write: Create new test files
- Edit: Update existing tests
- Bash: Run pytest, generate coverage reports
- Grep: Find untested functions
- Glob: Discover all source files

---

## Validation Commands

```bash
# Run all tests
pytest -v

# Run specific test category
pytest -m unit -v
pytest -m integration -v
pytest -m component -v

# Generate coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run tests with coverage threshold
pytest --cov=src --cov-fail-under=80

# Find untested files
pytest --cov=src --cov-report=term-missing | grep "0%"

# Open HTML coverage report
open htmlcov/index.html

# Check test count
pytest --collect-only | grep "test session starts"

# Run fast tests only
pytest -m "not integration and not e2e" -v
```
