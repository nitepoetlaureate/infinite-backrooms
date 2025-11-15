# python-async-client-consolidator

**Purpose**: Consolidate multiple async Python client implementations into a single canonical version

**Use When**: Multiple client files exist with similar functionality, causing confusion and maintenance burden

---

## Domain Knowledge

### Async Python Client Patterns
- Context manager protocol (`__aenter__`, `__aexit__`)
- Connection pooling with `aiohttp.TCPConnector`
- Resource cleanup and proper error handling
- Streaming responses with async generators

### Connection Pooling Strategies
- Connection limits and timeouts
- Keepalive connections for performance
- Connection reuse and lifecycle management
- Graceful shutdown and cleanup

### API Design Principles
- Clean, intuitive interface
- Comprehensive error handling
- Type hints for all public methods
- Detailed docstrings with examples

---

## Workflow

### Step 1: Audit All Client Implementations (60-90 min)

```bash
# Find all client files
find . -name "*ollama*client*.py" -type f

# Search for class definitions
grep -r "class.*Client" --include="*client*.py"
```

**Actions**:
- List all client files (expect 10+ files)
- Read each implementation
- Document unique features of each
- Identify code duplication

**Create Feature Matrix**:
| File | Connection Pool | Async/Await | Health Checks | Error Handling | Resource Cleanup |
|------|----------------|-------------|---------------|----------------|------------------|
| ollama_client.py | ❌ | ✓ | ❌ | Basic | ❌ |
| ollama_client_optimized.py | ✓ | ✓ | ✓ | Comprehensive | ✓ |
| ... | ... | ... | ... | ... | ... |

### Step 2: Design Unified Client API (45-60 min)

**Canonical API Structure**:
```python
from typing import AsyncGenerator, Optional
import aiohttp

class OllamaClient:
    """Unified Ollama API client with connection pooling and streaming support.

    Features:
    - Connection pooling for performance
    - Async/await for non-blocking operations
    - Proper resource cleanup via context manager
    - Health monitoring and diagnostics
    - Streaming response support
    - Comprehensive error handling

    Example:
        async with OllamaClient() as client:
            connected, models = await client.test_connection()
            if connected:
                async for chunk in client.generate_stream("llama2", "Hello"):
                    print(chunk)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: int = 300,
        max_connections: int = 100
    ):
        """Initialize client with connection pooling."""

    async def __aenter__(self):
        """Context manager entry - initialize connection pool."""

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""

    async def test_connection(self) -> tuple[bool, list[str]]:
        """Test connection and retrieve available models."""

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        think: bool = False,
        timeout: int = 300
    ) -> AsyncGenerator[dict, None]:
        """Generate streaming response from model."""

    async def health_check(self) -> bool:
        """Check if Ollama service is healthy."""
```

**Actions**:
- Document all methods with type hints
- Include comprehensive docstrings
- Design for extensibility
- Plan error handling strategy

### Step 3: Implement Canonical Client (2-3 hours)

**Implementation Pattern**:
```python
import aiohttp
import logging
from typing import AsyncGenerator, Optional

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_URL = "http://localhost:11434"


class OllamaClient:
    """Unified Ollama API client."""

    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_URL,
        timeout: int = 300,
        max_connections: int = 100
    ):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=10,
            keepalive_timeout=30
        )

    async def __aenter__(self):
        """Initialize connection pool."""
        self._session = aiohttp.ClientSession(
            connector=self._connector,
            timeout=self.timeout
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources."""
        if self._session:
            await self._session.close()
        if self._connector:
            await self._connector.close()

    async def test_connection(self) -> tuple[bool, list[str]]:
        """Test connection and get available models.

        Returns:
            tuple: (connected: bool, models: list[str])

        Example:
            async with OllamaClient() as client:
                connected, models = await client.test_connection()
                if connected:
                    print(f"Available models: {models}")
        """
        try:
            if not self._session:
                raise RuntimeError("Client not initialized. Use 'async with' context manager.")

            async with self._session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    return True, models
                else:
                    logger.error(f"Connection failed with status {response.status}")
                    return False, []

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False, []

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        think: bool = False,
        timeout: int = 300
    ) -> AsyncGenerator[dict, None]:
        """Generate streaming response from model.

        Args:
            model: Model name to use
            prompt: User prompt
            system_prompt: Optional system prompt
            think: Enable extended thinking mode
            timeout: Request timeout in seconds

        Yields:
            dict: Response chunks with 'type' and 'content' keys

        Example:
            async with OllamaClient() as client:
                async for chunk in client.generate_stream("llama2", "Hello"):
                    if chunk["type"] == "response":
                        print(chunk["content"], end="")
        """
        if not self._session:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True
        }

        if system_prompt:
            payload["system"] = system_prompt

        if think:
            payload["options"] = {"thinking": True}

        try:
            async with self._session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                response.raise_for_status()

                async for line in response.content:
                    if line:
                        try:
                            chunk = json.loads(line)
                            if chunk.get("response"):
                                yield {"type": "response", "content": chunk["response"]}
                            if chunk.get("done"):
                                yield {"type": "done"}
                                break
                        except json.JSONDecodeError:
                            continue

        except asyncio.TimeoutError:
            logger.error(f"Request timed out after {timeout}s")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Request failed: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if Ollama service is healthy.

        Returns:
            bool: True if service is responding

        Example:
            async with OllamaClient() as client:
                if await client.health_check():
                    print("Service is healthy")
        """
        try:
            connected, _ = await self.test_connection()
            return connected
        except Exception:
            return False
```

**Actions**:
- Merge best features from all implementations
- Add comprehensive type hints
- Include detailed docstrings with examples
- Implement proper error handling
- Add logging throughout

### Step 4: Update All Imports (45-60 min)

```bash
# Find all imports of old clients
grep -r "from.*ollama.*client" --include="*.py" src/ tests/ *.py

# Find all instantiations
grep -r "OllamaClient\|OllamaClientOptimized" --include="*.py"
```

**Update Pattern**:
```python
# ❌ OLD
from src.services.ollama_client_optimized import OllamaClientOptimized
client = OllamaClientOptimized()

# ✅ NEW
from src.services.ollama_client import OllamaClient
client = OllamaClient()
```

**Actions**:
- Use MultiEdit for bulk updates
- Update all imports consistently
- Update all instantiations
- Test after each major update

### Step 5: Remove Duplicate Files (15-30 min)

**Files to Delete**:
```bash
# Remove old implementations
rm src/services/ollama_client_streamlit.py
rm src/services/optimized_ollama_client.py
rm src/services/optimized_ollama_client_streamlit.py
rm src/services/streamlit_ollama_client.py
rm streamlit_backroom_unsafe.py
rm streamlit_backroom_optimized.py
rm streamlit_backroom.py.backup
```

**Actions**:
- Verify no references remain to deleted files
- Clean up any backup or temp files
- Update .gitignore if needed

### Step 6: Validate with Tests (30-45 min)

```bash
# Test the unified client
pytest tests/test_ollama_client.py -v

# Run all tests to check for breaks
pytest -v

# Test imports work
python -c "from src.services.ollama_client import OllamaClient; print('Success')"
```

---

## Best Practices

### Connection Pooling
1. Use `TCPConnector` with appropriate limits
2. Enable keepalive for performance
3. Set reasonable timeouts
4. Clean up connections properly

### Context Manager Pattern
1. Always use `async with` for resource management
2. Initialize session in `__aenter__`
3. Clean up in `__aexit__`
4. Handle exceptions gracefully

### Error Handling
1. Catch specific exceptions
2. Log errors comprehensively
3. Provide helpful error messages
4. Don't swallow exceptions silently

### Type Hints
1. Use `Optional` for nullable returns
2. Use `AsyncGenerator` for streaming
3. Document all type parameters
4. Enable strict type checking

### Documentation
1. Include usage examples in docstrings
2. Document all parameters and returns
3. Explain error conditions
4. Provide migration guide from old clients

---

## Success Criteria

- [ ] Single canonical `src/services/ollama_client.py` exists
- [ ] All features from old clients preserved
- [ ] No duplicate client files remain
- [ ] All imports updated throughout codebase
- [ ] Tests pass with unified client
- [ ] Connection pooling verified working
- [ ] Context manager pattern working
- [ ] Comprehensive docstrings included
- [ ] Type hints throughout

---

## Common Issues & Solutions

### Issue: "session not initialized"
**Solution**: Ensure client used with `async with` context manager

### Issue: "connection pool exhausted"
**Solution**: Increase `max_connections` parameter or improve connection cleanup

### Issue: "tests failing after consolidation"
**Solution**: Check test mocks match new API, update fixtures

---

## Tools Available
- Read: Audit existing client files
- Write: Create canonical client
- Edit: Update imports
- Grep: Find all client references
- Glob: Find all client files
- MultiEdit: Bulk import updates

---

## Validation Commands

```bash
# Find client files
find . -name "*client*.py" -type f

# Check imports
grep -r "ollama_client" --include="*.py"

# Test unified client
pytest tests/test_ollama_client.py -v

# Verify no old references
grep -r "OllamaClientOptimized\|ollama_client_streamlit" --include="*.py"
```
