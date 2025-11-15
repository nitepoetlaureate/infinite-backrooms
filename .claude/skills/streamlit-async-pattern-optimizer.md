# streamlit-async-pattern-optimizer

**Purpose**: Optimize async patterns for Streamlit applications to avoid event loop conflicts

**Use When**: Experiencing "Event loop is closed" errors or async operations causing Streamlit crashes

---

## Domain Knowledge

### Streamlit Event Loop Model
- Streamlit runs its own event loop internally
- Creating new event loops can cause conflicts
- Manual event loop manipulation is dangerous
- Streamlit reruns scripts on every interaction

### Singleton Pattern for Resources
- `st.experimental_singleton` caches resources across reruns
- Perfect for database connections, API clients
- Persists for application lifetime
- Proper cleanup on app shutdown

### Async Execution Strategies
1. **`asyncio.run()`**: Clean, standard approach (preferred)
2. **Thread-based execution**: Fallback for edge cases
3. **Streamlit native async**: Limited support, evolving

---

## Workflow

### Step 1: Research Streamlit Async Best Practices (30-45 min)

**Key Resources**:
- Streamlit documentation on async support
- Community patterns for async in Streamlit
- Known issues with event loops

**Document Findings**:
- Current Streamlit version capabilities
- Recommended patterns
- Anti-patterns to avoid

### Step 2: Design Singleton Client Management (45-60 min)

**Pattern: Resource Singleton**:
```python
import streamlit as st
from src.services.ollama_client import OllamaClient

@st.experimental_singleton
def get_ollama_client() -> OllamaClient:
    """Get or create singleton Ollama client.

    This client persists across Streamlit reruns and manages
    its own connection pool for optimal performance.

    Returns:
        OllamaClient: Singleton client instance

    Example:
        client = get_ollama_client()
        connected, models = asyncio.run(client.test_connection())
    """
    return OllamaClient()
```

**Benefits**:
- Client created once per app lifecycle
- Connection pool reused across requests
- Proper resource management
- No repeated initialization overhead

### Step 3: Implement Safe Async Execution (60-90 min)

**Pattern: Safe Async Call with Fallback**:
```python
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar, Coroutine

logger = logging.getLogger(__name__)

T = TypeVar('T')

def safe_async_call(coro: Coroutine) -> T:
    """Execute async coroutine with proper error handling.

    Attempts to use asyncio.run() first, falls back to thread-based
    execution if event loop issues occur.

    Args:
        coro: Async coroutine to execute

    Returns:
        Result of coroutine execution

    Raises:
        Exception: Re-raises any exception except event loop errors

    Example:
        client = get_ollama_client()
        result = safe_async_call(client.test_connection())
    """
    try:
        # Try standard asyncio.run first
        return asyncio.run(coro)

    except RuntimeError as e:
        error_msg = str(e).lower()

        # Check for event loop errors
        if "event loop is closed" in error_msg or \
           "this event loop is already running" in error_msg:

            logger.debug(
                "Event loop conflict detected, using thread-based execution"
            )
            return _run_async_in_thread(coro)

        # Re-raise other runtime errors
        raise

    except Exception:
        # Re-raise all other exceptions
        raise


def _run_async_in_thread(coro: Coroutine) -> T:
    """Run async coroutine in separate thread with new event loop.

    This is a fallback for edge cases where Streamlit's event loop
    conflicts with asyncio.run(). Should rarely be needed.

    Args:
        coro: Async coroutine to execute

    Returns:
        Result of coroutine execution
    """
    def run_in_new_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_in_new_loop)
        return future.result()
```

**Key Design Decisions**:
- Try `asyncio.run()` first (cleaner, standard)
- Fallback to thread-based only if needed
- Comprehensive error handling
- Detailed logging for debugging
- Type hints for clarity

### Step 4: Update All Async Call Sites (60-90 min)

**Pattern: Before (Unsafe)**:
```python
# ❌ UNSAFE: Manual event loop creation
def check_connection():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = OllamaClient()
    result = loop.run_until_complete(client.test_connection())
    loop.close()
    return result
```

**Pattern: After (Safe)**:
```python
# ✅ SAFE: Using singleton and safe execution
def check_connection():
    """Check Ollama connection using safe async pattern."""
    client = get_ollama_client()

    try:
        connected, models = safe_async_call(client.test_connection())
        return connected, models

    except asyncio.TimeoutError:
        logger.error("Connection check timed out")
        return False, []

    except Exception as e:
        logger.error(f"Connection check failed: {e}")
        return False, []
```

**Actions**:
- Find all async operation call sites
- Replace with singleton + safe_async_call pattern
- Add proper error handling
- Test each update

### Step 5: Add Comprehensive Error Handling (30-45 min)

**Error Handling Pattern**:
```python
def execute_conversation_turn(persona, context):
    """Execute a single conversation turn with error handling."""
    client = get_ollama_client()

    try:
        # Safe async execution
        response_generator = safe_async_call(
            client.generate_stream(
                model=persona.model,
                prompt=build_prompt(context),
                system_prompt=persona.description
            )
        )

        return response_generator

    except asyncio.TimeoutError:
        logger.error(f"Turn timed out for {persona.name}")
        st.error("Request timed out. Please try again.")
        return None

    except aiohttp.ClientError as e:
        logger.error(f"Network error for {persona.name}: {e}")
        st.error("Network error occurred. Check Ollama connection.")
        return None

    except Exception as e:
        logger.error(f"Unexpected error for {persona.name}: {e}")
        st.error("An unexpected error occurred.")
        return None
```

**Error Categories**:
- **Timeout**: Network or processing timeout
- **Network**: Connection failures
- **Event Loop**: Async execution issues
- **Unexpected**: Catch-all for unknown issues

### Step 6: Test for Event Loop Errors (45-60 min)

**Test Scenarios**:
1. Rapid successive async calls
2. Concurrent async operations
3. Streamlit reruns during async execution
4. Error recovery and retry

**Testing Commands**:
```bash
# Run integration tests
pytest tests/test_integration_real.py -v

# Run app and monitor logs
streamlit run streamlit_backroom.py &
sleep 10

# Check for event loop errors
grep -i "event loop" logs/ || echo "No errors found"

# Stop app
pkill -f streamlit
```

### Step 7: Profile Performance (30-45 min)

**Performance Comparison**:
```python
import time

def benchmark_async_patterns():
    """Compare performance of different async patterns."""

    # Pattern 1: Direct asyncio.run()
    start = time.time()
    for _ in range(100):
        asyncio.run(client.test_connection())
    direct_time = time.time() - start

    # Pattern 2: Thread-based
    start = time.time()
    for _ in range(100):
        _run_async_in_thread(client.test_connection())
    thread_time = time.time() - start

    logger.info(f"Direct: {direct_time:.2f}s, Thread: {thread_time:.2f}s")
```

**Actions**:
- Measure before/after performance
- Ensure no performance regression
- Document performance characteristics
- Optimize if needed

---

## Best Practices

### Resource Management
1. Use `st.experimental_singleton` for clients
2. Initialize once, reuse across reruns
3. Proper cleanup in context managers
4. Monitor resource usage

### Async Execution
1. Prefer `asyncio.run()` over manual loops
2. Use thread-based execution only as fallback
3. Never create event loops manually
4. Handle RuntimeError gracefully

### Error Handling
1. Catch specific exceptions first
2. Provide user-friendly error messages
3. Log detailed error information
4. Allow retry on transient failures

### Logging
1. Log async execution path taken
2. Log all errors comprehensively
3. Debug level for event loop details
4. Error level for failures

---

## Success Criteria

- [ ] No "Event loop is closed" errors in testing
- [ ] No event loop creation warnings
- [ ] Singleton pattern implemented
- [ ] `safe_async_call()` function created
- [ ] All async call sites updated
- [ ] Comprehensive error handling added
- [ ] Performance maintained or improved
- [ ] Integration tests pass
- [ ] Resource cleanup verified

---

## Common Issues & Solutions

### Issue: "Event loop is closed"
**Solution**: Use `asyncio.run()` or `safe_async_call()`, don't create loops manually

### Issue: "This event loop is already running"
**Solution**: Fallback to thread-based execution via `safe_async_call()`

### Issue: Performance degradation
**Solution**: Ensure singleton pattern used, connection pooling active

### Issue: Memory leaks
**Solution**: Verify context manager cleanup, check for unreleased connections

---

## Anti-Patterns to Avoid

❌ **Manual Event Loop Creation**:
```python
# DON'T DO THIS
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
```

❌ **Global Event Loop**:
```python
# DON'T DO THIS
global_loop = asyncio.new_event_loop()
```

❌ **Blocking Sleep in Async**:
```python
# DON'T DO THIS
async def wait():
    time.sleep(1)  # Use await asyncio.sleep(1)
```

❌ **Resource Re-initialization**:
```python
# DON'T DO THIS
def every_request():
    client = OllamaClient()  # Creates new client each time
```

---

## Tools Available
- Read: Analyze current async patterns
- Edit: Update async call sites
- Write: Create new async utilities
- Bash: Run tests and benchmarks
- Grep: Find async operation sites

---

## Validation Commands

```bash
# Find old async patterns
grep -rn "asyncio.new_event_loop\|run_until_complete" --include="*.py"

# Run integration tests
pytest tests/test_integration_real.py -v

# Start app and test
streamlit run streamlit_backroom.py

# Check logs for errors
grep -i "event loop\|runtime error" logs/

# Performance test
python scripts/benchmark_async.py
```
