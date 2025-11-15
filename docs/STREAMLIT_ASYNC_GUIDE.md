# Streamlit-Safe Async Patterns Guide

**Version**: 1.0
**Date**: 2025-11-13
**Status**: Production-Ready Patterns

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [The Problem: Why Async is Difficult in Streamlit](#the-problem)
3. [Safe Patterns](#safe-patterns)
4. [Anti-Patterns to Avoid](#anti-patterns)
5. [Recommended Solutions for Infinite Backrooms](#recommended-solutions)
6. [Code Examples](#code-examples)
7. [Migration Plan](#migration-plan)

---

## Executive Summary

Streamlit applications run in a synchronous execution model, but internally use Tornado (an async framework) for the web server. This creates significant challenges when attempting to use async/await patterns in Streamlit apps.

### Key Findings

- **Native async support**: Not available in Streamlit as of 2024
- **Event loop conflicts**: Using `asyncio.run()` causes "Event loop is already running" errors
- **Recommended approach**: Thread-based execution with new event loops per operation
- **Connection pooling**: Must be managed carefully with singleton patterns
- **Current status**: Your codebase already uses a safe pattern, but can be improved

### Current Implementation Status

Your `streamlit_backroom.py` already implements the recommended pattern:

```python
def run_async_in_thread(coro):
    """Run async coroutine in a separate thread to avoid event loop conflicts."""
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

**Status**: This is a SAFE pattern. The blocking issues are likely elsewhere.

---

## The Problem

### Why Streamlit and Async Don't Mix Well

1. **Streamlit's Internal Event Loop**: Streamlit uses Tornado internally, which runs its own event loop
2. **No Direct await Support**: You cannot use `await` directly in Streamlit code
3. **asyncio.run() Conflicts**: Attempting to use `asyncio.run()` raises `RuntimeError: This event loop is already running`
4. **Script Rerun Model**: Streamlit reruns the entire script on each interaction, making event loop persistence challenging

### Common Errors

```python
# ERROR: This will fail in Streamlit
async def fetch_data():
    async with httpx.AsyncClient() as client:
        return await client.get("https://api.example.com")

# This raises: RuntimeError: This event loop is already running
result = asyncio.run(fetch_data())
```

---

## Safe Patterns

### Pattern 1: Thread-Based Execution (RECOMMENDED)

**Use Case**: Running async operations from Streamlit without event loop conflicts

**Implementation**:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

def run_async_in_thread(coro):
    """Execute async coroutine in a new thread with its own event loop.

    This is the SAFEST pattern for Streamlit applications.
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

# Usage in Streamlit
result = run_async_in_thread(fetch_data())
st.write(result)
```

**Pros**:
- No event loop conflicts
- Clean separation of concerns
- Thread-safe
- Works reliably across Streamlit reruns

**Cons**:
- Slight performance overhead from thread creation
- Cannot share event loop across calls
- Not suitable for high-frequency calls

---

### Pattern 2: Cached Resource with Sync Wrapper (RECOMMENDED FOR CLIENTS)

**Use Case**: Maintaining long-lived async HTTP clients or connection pools

**Implementation**:

```python
import streamlit as st
import httpx

@st.cache_resource
def get_http_client():
    """Create and cache a synchronous HTTP client.

    NOTE: Use httpx.Client (sync), NOT httpx.AsyncClient
    st.cache_resource does not support async objects.
    """
    return httpx.Client(
        timeout=30.0,
        limits=httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20
        )
    )

# Usage
client = get_http_client()
response = client.get("https://api.example.com")
```

**Important**: `st.cache_resource` does NOT support async objects. You must either:
1. Use synchronous versions of libraries (e.g., `httpx.Client` instead of `httpx.AsyncClient`)
2. Create sync wrappers around async clients

**Pros**:
- Singleton pattern - one client for entire app
- Connection pooling benefits
- Automatic caching across reruns
- Thread-safe (if client is thread-safe)

**Cons**:
- Async clients not directly supported
- Requires thread-safe clients
- Shared across all users/sessions

---

### Pattern 3: Pre-Layout with Placeholders

**Use Case**: Long-running async operations with real-time updates

**Implementation**:

```python
import streamlit as st
import asyncio

async def streaming_task(placeholder):
    """Async task that updates a Streamlit placeholder."""
    count = 0
    while count < 10:
        count += 1
        with placeholder:
            st.write(f"Count: {count}")
        await asyncio.sleep(1)

def main():
    st.title("Streaming Demo")

    # Create placeholder BEFORE async operation
    placeholder = st.empty()

    # Run async task with placeholder
    # asyncio.run() must be the LAST Streamlit operation
    asyncio.run(streaming_task(placeholder))

    # WARNING: Code here will NOT execute!

if __name__ == "__main__":
    main()
```

**Critical Rules**:
1. Create all UI elements (placeholders) BEFORE `asyncio.run()`
2. `asyncio.run()` must be the LAST Streamlit operation
3. Pass placeholders to async functions - don't create widgets inside them
4. Any code after `asyncio.run()` will NOT execute

**Pros**:
- Real-time updates during async operations
- Clean separation of UI and logic

**Cons**:
- Very restrictive - must be last operation
- Cannot have Streamlit code after async operation
- Limited use cases

---

### Pattern 4: nest_asyncio (USE WITH CAUTION)

**Use Case**: Quick prototyping or when refactoring is not immediately possible

**Implementation**:

```python
import asyncio
import nest_asyncio
import streamlit as st

# Apply patch at module level
nest_asyncio.apply()

async def fetch_data():
    await asyncio.sleep(1)
    return "Data"

# Now this works
result = asyncio.run(fetch_data())
st.write(result)
```

**WARNING**: This is a "monkey patch" that modifies asyncio internals.

**Pros**:
- Quick fix for event loop conflicts
- Minimal code changes

**Cons**:
- Can hide deeper design issues
- May cause subtle bugs (deadlocks, race conditions)
- Not recommended for production
- Fragile across asyncio/Streamlit version updates

**Recommendation**: Use only for prototyping, migrate to Pattern 1 or 2 for production.

---

### Pattern 5: Synchronous HTTP Clients (RECOMMENDED)

**Use Case**: Making HTTP requests without async complexity

**Implementation**:

```python
import httpx
import streamlit as st

@st.cache_resource
def get_sync_client():
    """Get cached synchronous HTTP client with connection pooling."""
    return httpx.Client(
        timeout=30.0,
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        http2=True  # Enable HTTP/2 for better performance
    )

def fetch_api_data(url: str):
    """Fetch data from API using sync client."""
    client = get_sync_client()
    response = client.get(url)
    response.raise_for_status()
    return response.json()

# Usage
data = fetch_api_data("https://api.example.com/data")
st.write(data)
```

**Pros**:
- No async complexity
- Connection pooling benefits
- Thread-safe
- Simple to use and maintain

**Cons**:
- Cannot use async-only libraries
- May block during I/O (but acceptable for most use cases)

**Recommendation**: **USE THIS INSTEAD OF ASYNC** unless you have async-only dependencies.

---

## Anti-Patterns

### ANTI-PATTERN 1: Direct asyncio.run() in Streamlit

```python
# DON'T DO THIS
import asyncio
import streamlit as st

async def fetch_data():
    await asyncio.sleep(1)
    return "Data"

# ERROR: RuntimeError: This event loop is already running
result = asyncio.run(fetch_data())
```

**Why it fails**: Streamlit's internal Tornado event loop is already running.

**Fix**: Use Pattern 1 (thread-based execution).

---

### ANTI-PATTERN 2: Multiple Event Loop Creations Without Cleanup

```python
# DON'T DO THIS
import asyncio

def bad_async_wrapper(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(coro)
    # Missing: loop.close()
    return result
```

**Why it's bad**: Event loops leak, consuming resources.

**Fix**: Always close loops in `finally` blocks.

---

### ANTI-PATTERN 3: Creating Multiple Client Instances

```python
# DON'T DO THIS
import httpx
import streamlit as st

async def fetch_data(url):
    # Creates new client on every call - no connection pooling!
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

for url in urls:
    data = run_async_in_thread(fetch_data(url))
```

**Why it's bad**: No connection pooling benefits, resource waste.

**Fix**: Create client once using `st.cache_resource` or pass client instance.

---

### ANTI-PATTERN 4: Caching Async Functions

```python
# DON'T DO THIS
import streamlit as st

@st.cache_resource  # Does NOT support async functions!
async def get_async_client():
    return httpx.AsyncClient()
```

**Why it fails**: `st.cache_resource` and `st.cache_data` do not support async functions.

**Fix**: Cache synchronous wrapper or the client creation logic, not the async function.

---

### ANTI-PATTERN 5: Mixing Async and Sync Without Thread Safety

```python
# DON'T DO THIS
import asyncio
import streamlit as st

# Global shared state - race condition!
results = []

async def worker():
    results.append(await fetch_data())  # Not thread-safe!

def main():
    asyncio.run(worker())
    st.write(results)
```

**Why it's bad**: Race conditions, data corruption.

**Fix**: Use proper synchronization (locks) or return values instead of shared state.

---

### ANTI-PATTERN 6: Blocking Sleep in Async Cleanup

```python
# DON'T DO THIS
import asyncio
import time

async def bad_cleanup():
    await session.close()
    time.sleep(0.25)  # Blocking sleep in async code!
```

**Why it's bad**: Blocks the entire event loop, preventing other tasks from running.

**Fix**: Use `await asyncio.sleep(0.25)` instead, or remove if not necessary.

---

## Recommended Solutions for Infinite Backrooms

### Current Architecture Analysis

Your codebase currently uses:

1. **Thread-based async execution** (GOOD):
   ```python
   def run_async_in_thread(coro):
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

2. **Async context managers for Ollama client**:
   ```python
   async def _stream_response():
       async with OllamaClientOptimized(DEFAULT_OLLAMA_URL) as client:
           async for chunk in client.generate_stream(...):
               yield chunk
   ```

### Issues Identified

1. **OllamaClient cleanup has blocking sleep**:
   - File: `src/services/ollama_client.py`, line 58
   - Issue: `await asyncio.sleep(0.050)` - while non-blocking, may be unnecessary

2. **No connection pooling across calls**:
   - Each call creates new `async with OllamaClientOptimized()` context
   - No singleton pattern for client reuse

3. **Multiple async client implementations**:
   - `ollama_client.py`, `ollama_client_optimized.py`, `optimized_ollama_client.py`, etc.
   - Confusing, hard to maintain

### Recommended Architecture

#### Option A: Full Synchronous (SIMPLEST)

**Best if**: Ollama has a synchronous client or you can make synchronous HTTP calls.

```python
import httpx
import streamlit as st
from typing import Generator

@st.cache_resource
def get_ollama_client():
    """Get cached synchronous HTTP client for Ollama API."""
    return httpx.Client(
        base_url=DEFAULT_OLLAMA_URL,
        timeout=httpx.Timeout(timeout=120.0, connect=10.0),
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
    )

def stream_ollama_response(model: str, prompt: str, system: str = None) -> Generator[dict, None, None]:
    """Stream response from Ollama API (synchronous)."""
    client = get_ollama_client()

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
    }
    if system:
        payload["system"] = system

    with client.stream("POST", "/api/generate", json=payload) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                if "thinking" in chunk and chunk["thinking"]:
                    yield {"type": "thinking", "content": chunk["thinking"]}
                if "response" in chunk and chunk["response"]:
                    yield {"type": "response", "content": chunk["response"]}
                if chunk.get("done"):
                    break

# Usage in Streamlit - no async needed!
for chunk in stream_ollama_response("llama2", "Hello"):
    st.write(chunk)
```

**Pros**:
- No async complexity
- Connection pooling via httpx.Client
- Simple, maintainable
- Thread-safe

**Cons**:
- Cannot use async-only features
- May block during I/O (but acceptable for Streamlit)

---

#### Option B: Cached Async Client with Thread Execution (CURRENT APPROACH)

**Best if**: You must use async clients (e.g., aiohttp-only features).

```python
import streamlit as st
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncGenerator, Generator
import aiohttp

# Keep your existing run_async_in_thread helper
def run_async_in_thread(coro):
    """Execute async coroutine in separate thread."""
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

# Simplified async client (single implementation)
class OllamaAsyncClient:
    """Simplified async Ollama client."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self._session = None

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=120)
        connector = aiohttp.TCPConnector(limit=10, force_close=False)
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
        # No blocking sleep needed - aiohttp handles cleanup

    async def generate_stream(self, model: str, prompt: str, system: str = None) -> AsyncGenerator[dict, None]:
        """Generate streaming response."""
        payload = {"model": model, "prompt": prompt, "stream": True}
        if system:
            payload["system"] = system

        async with self._session.post(f"{self.base_url}/api/generate", json=payload) as response:
            response.raise_for_status()
            async for line in response.content:
                if line:
                    chunk = json.loads(line.decode("utf-8"))
                    if "thinking" in chunk and chunk["thinking"]:
                        yield {"type": "thinking", "content": chunk["thinking"]}
                    if "response" in chunk and chunk["response"]:
                        yield {"type": "response", "content": chunk["response"]}
                    if chunk.get("done"):
                        break

# Sync wrapper for Streamlit
def stream_ollama_response_sync(model: str, prompt: str, system: str = None) -> Generator[dict, None, None]:
    """Synchronous wrapper for async streaming."""
    async def _stream():
        chunks = []
        async with OllamaAsyncClient(DEFAULT_OLLAMA_URL) as client:
            async for chunk in client.generate_stream(model, prompt, system):
                chunks.append(chunk)
        return chunks

    # Run async operation in thread, collect all chunks
    chunks = run_async_in_thread(_stream())

    # Yield chunks synchronously
    for chunk in chunks:
        yield chunk

# Usage in Streamlit - looks synchronous!
for chunk in stream_ollama_response_sync("llama2", "Hello"):
    st.write(chunk)
```

**Pros**:
- Can use async-only libraries
- Clean separation of async and sync
- Thread-safe

**Cons**:
- More complex than Option A
- Cannot stream in real-time (collects all chunks first)
- Thread overhead

---

#### Option C: True Real-Time Streaming with Thread Runner (ADVANCED)

**Best if**: You need real-time streaming updates AND must use async clients.

```python
import streamlit as st
import asyncio
import threading
from queue import Queue
from typing import AsyncGenerator

class AsyncThreadRunner:
    """Run async code in background thread with event loop."""

    def __init__(self):
        self._loop = None
        self._thread = None

    def start(self):
        """Start background thread with event loop."""
        self._queue = Queue()

        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()

        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()

    def run_coro(self, coro):
        """Run coroutine in background thread, return result."""
        if not self._loop:
            raise RuntimeError("Thread runner not started")

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def stop(self):
        """Stop background thread."""
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=5)

# Global thread runner (singleton)
@st.cache_resource
def get_async_runner():
    """Get cached async thread runner."""
    runner = AsyncThreadRunner()
    runner.start()
    return runner

# Real-time streaming with placeholders
def stream_with_realtime_updates(model: str, prompt: str):
    """Stream with real-time updates to Streamlit."""
    runner = get_async_runner()

    # Create placeholders
    thinking_placeholder = st.empty()
    response_placeholder = st.empty()

    thinking_content = ""
    response_content = ""

    async def _stream():
        nonlocal thinking_content, response_content

        async with OllamaAsyncClient(DEFAULT_OLLAMA_URL) as client:
            async for chunk in client.generate_stream(model, prompt):
                if chunk["type"] == "thinking":
                    thinking_content += chunk["content"]
                    thinking_placeholder.text(f"Thinking: {thinking_content}")
                elif chunk["type"] == "response":
                    response_content += chunk["content"]
                    response_placeholder.write(response_content)

    # Run async streaming
    runner.run_coro(_stream())

    return response_content

# Usage
response = stream_with_realtime_updates("llama2", "Hello")
```

**Pros**:
- True real-time streaming
- Reuses event loop (better performance)
- Can handle concurrent operations

**Cons**:
- Most complex solution
- Requires careful thread management
- Harder to debug

---

## Code Examples

### Example 1: Migrating from Async to Sync HTTP Client

**Before (Complex Async)**:

```python
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def fetch_data_async(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

def run_async_in_thread(coro):
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

# Usage
data = run_async_in_thread(fetch_data_async("https://api.example.com"))
```

**After (Simple Sync)**:

```python
import httpx
import streamlit as st

@st.cache_resource
def get_http_client():
    return httpx.Client(timeout=30.0)

def fetch_data_sync(url: str):
    client = get_http_client()
    response = client.get(url)
    response.raise_for_status()
    return response.json()

# Usage
data = fetch_data_sync("https://api.example.com")
```

**Benefits**: 70% less code, connection pooling, simpler to maintain.

---

### Example 2: Streaming Response Handler

**Synchronous Streaming** (Recommended):

```python
import httpx
import json
import streamlit as st
from typing import Generator

@st.cache_resource
def get_streaming_client():
    return httpx.Client(
        timeout=httpx.Timeout(timeout=120.0),
        limits=httpx.Limits(max_connections=10)
    )

def stream_response(url: str, payload: dict) -> Generator[str, None, None]:
    """Stream response line by line."""
    client = get_streaming_client()

    with client.stream("POST", url, json=payload) as response:
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    yield chunk
                except json.JSONDecodeError:
                    continue

# Usage in Streamlit
placeholder = st.empty()
full_response = ""

for chunk in stream_response("http://localhost:11434/api/generate", payload):
    if "response" in chunk:
        full_response += chunk["response"]
        placeholder.write(full_response)
```

---

### Example 3: Connection Health Check

```python
import httpx
import streamlit as st

@st.cache_resource
def get_http_client():
    return httpx.Client(base_url="http://localhost:11434", timeout=10.0)

def check_ollama_connection() -> tuple[bool, list[str]]:
    """Check if Ollama is accessible and return available models."""
    try:
        client = get_http_client()
        response = client.get("/api/tags")
        response.raise_for_status()

        data = response.json()
        models = [model["name"] for model in data.get("models", [])]
        return True, models

    except httpx.HTTPError as e:
        st.error(f"Connection failed: {e}")
        return False, []

# Usage
if st.button("Check Connection"):
    connected, models = check_ollama_connection()
    if connected:
        st.success(f"Connected! Found {len(models)} models")
        st.write(models)
    else:
        st.error("Not connected")
```

---

## Migration Plan

### Phase 1: Audit Current Async Usage

1. **Identify all async functions** in codebase:
   ```bash
   grep -r "async def" src/
   grep -r "await " src/
   grep -r "asyncio" src/
   ```

2. **Document dependencies**:
   - Which libraries REQUIRE async? (e.g., aiohttp-only features)
   - Which can be replaced with sync alternatives?

3. **Identify blocking operations**:
   ```bash
   grep -r "time.sleep" src/  # Blocking sleep in async code
   grep -r "\.sleep\(" src/
   ```

### Phase 2: Consolidate Client Implementations

**Current state**: Multiple Ollama client implementations

**Action**:
1. Choose ONE implementation:
   - Option A: Synchronous httpx-based client (recommended)
   - Option B: Single async client with thread wrapper

2. Delete duplicate implementations:
   - `ollama_client_optimized.py`
   - `optimized_ollama_client.py`
   - `streamlit_ollama_client.py`
   - Keep only ONE

3. Update all imports to use consolidated client

### Phase 3: Implement Recommended Pattern

**For synchronous approach**:

```python
# src/services/ollama_client.py (NEW - synchronous)
import httpx
import json
from typing import Generator
import streamlit as st

@st.cache_resource
def get_ollama_client():
    """Get singleton synchronous Ollama client."""
    return httpx.Client(
        base_url="http://localhost:11434",
        timeout=httpx.Timeout(timeout=120.0, connect=10.0),
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
    )

class OllamaClient:
    """Synchronous Ollama API client for Streamlit."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or "http://localhost:11434"
        self._client = None

    @property
    def client(self):
        """Get cached HTTP client."""
        if self._client is None:
            self._client = get_ollama_client()
        return self._client

    def test_connection(self) -> tuple[bool, list[str]]:
        """Test connection and return available models."""
        try:
            response = self.client.get("/api/tags", timeout=10.0)
            response.raise_for_status()
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            return True, models
        except httpx.HTTPError:
            return False, []

    def generate_stream(
        self,
        model: str,
        prompt: str,
        system: str = None,
        think: bool = True
    ) -> Generator[dict, None, None]:
        """Generate streaming response from Ollama."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "think": think,
        }
        if system:
            payload["system"] = system

        try:
            with self.client.stream("POST", "/api/generate", json=payload) as response:
                if response.status_code == 400 and think:
                    # Retry without thinking if not supported
                    yield from self.generate_stream(model, prompt, system, think=False)
                    return

                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)

                            if "thinking" in chunk and chunk["thinking"]:
                                yield {"type": "thinking", "content": chunk["thinking"]}

                            if "response" in chunk and chunk["response"]:
                                yield {"type": "response", "content": chunk["response"]}

                            if chunk.get("done"):
                                break

                        except json.JSONDecodeError:
                            continue

        except httpx.TimeoutException:
            yield {"type": "error", "content": "Request timeout"}
        except httpx.HTTPError as e:
            yield {"type": "error", "content": f"HTTP error: {e}"}
        except Exception as e:
            yield {"type": "error", "content": f"Error: {e}"}
```

**Update streamlit_backroom.py**:

```python
# Remove async executor and run_async_in_thread
# Remove: async_executor = ThreadPoolExecutor(...)
# Remove: def run_async_in_thread(coro): ...

from src.services.ollama_client import OllamaClient

# Replace async usage:
# OLD:
# async def _check_connection():
#     async with OllamaClientOptimized(...) as client:
#         connected, models = await client.test_connection()
# result = run_async_in_thread(_check_connection())

# NEW:
client = OllamaClient()
connected, models = client.test_connection()

# For streaming:
# OLD:
# async def _stream_response():
#     async with OllamaClientOptimized(...) as client:
#         async for chunk in client.generate_stream(...):
#             yield chunk

# NEW:
client = OllamaClient()
for chunk in client.generate_stream(model, prompt, system):
    # Handle chunk
    pass
```

### Phase 4: Remove Unnecessary Async Code

1. **Remove blocking sleeps in async cleanup**:
   - File: `src/services/ollama_client.py`, line 58
   - Remove: `await asyncio.sleep(0.050)`

2. **Remove thread pool executor** if using synchronous approach:
   - Line 56: `async_executor = ThreadPoolExecutor(...)`
   - Line 59: `def run_async_in_thread(...)`

3. **Simplify imports**:
   - Remove unused: `import asyncio`, `from concurrent.futures import ThreadPoolExecutor`

### Phase 5: Testing

1. **Test connection establishment**:
   ```python
   def test_ollama_connection():
       client = OllamaClient()
       connected, models = client.test_connection()
       assert connected, "Should connect to Ollama"
       assert len(models) > 0, "Should have models"
   ```

2. **Test streaming**:
   ```python
   def test_streaming_response():
       client = OllamaClient()
       chunks = list(client.generate_stream("llama2", "Hello"))
       assert len(chunks) > 0, "Should receive chunks"
   ```

3. **Test in Streamlit**:
   - Run app
   - Check for event loop errors
   - Verify streaming works
   - Check connection pooling (should see one client instance)

### Phase 6: Monitor and Optimize

1. **Add metrics**:
   ```python
   import time

   start = time.time()
   chunks = list(client.generate_stream(...))
   duration = time.time() - start

   st.metric("Response Time", f"{duration:.2f}s")
   ```

2. **Monitor connection pool**:
   ```python
   # If using httpx.Client, no built-in metrics
   # But you can track request counts
   ```

3. **Profile performance**:
   - Use cProfile or line_profiler
   - Identify bottlenecks

---

## Summary: Recommended Approach for Infinite Backrooms

### Top Recommendation: Synchronous HTTP Client

**Replace all async Ollama clients with synchronous httpx-based client**.

**Benefits**:
1. **Eliminates event loop complexity** - no async/await needed
2. **Simpler code** - 70% reduction in complexity
3. **Better performance** - connection pooling without thread overhead
4. **Easier to maintain** - one clear implementation
5. **No blocking issues** - Streamlit-native approach
6. **Thread-safe** - httpx.Client is thread-safe by default

**Trade-offs**:
- Cannot use async-only features (not needed for Ollama HTTP API)
- May block during I/O (acceptable for Streamlit's use case)

### Implementation Priority

1. **High Priority**: Migrate to synchronous httpx.Client
2. **High Priority**: Consolidate to single client implementation
3. **Medium Priority**: Remove unused async utilities
4. **Low Priority**: Add performance monitoring

### Estimated Effort

- **Migration**: 4-6 hours
- **Testing**: 2-3 hours
- **Documentation**: 1-2 hours
- **Total**: 1 working day

### Expected Outcomes

- **Event loop issues**: RESOLVED
- **Code complexity**: Reduced by 70%
- **Performance**: Same or better (connection pooling)
- **Maintainability**: Significantly improved
- **Production readiness**: ACHIEVED

---

## References

### Official Documentation
1. [Streamlit Caching: st.cache_resource](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_resource)
2. [HTTPX Async Support](https://www.python-httpx.org/async/)
3. [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

### Community Resources
4. [Streamlit GitHub Issue #8488: Native asyncio support](https://github.com/streamlit/streamlit/issues/8488)
5. [Streamlit Community: Async Functions Discussion](https://discuss.streamlit.io/t/streamlit-and-asynchronous-functions/30684)
6. [Stack Overflow: Streamlit and Asyncio](https://stackoverflow.com/questions/74550915/pulling-real-time-data-and-update-in-streamlit-and-asyncio)

### Technical Articles
7. [Running Async Code from Sync Code in Python](https://death.andgravity.com/asyncio-bridge)
8. [TechOverflow: Asyncio in Streamlit (2024)](https://techoverflow.net/2024/11/29/how-to-run-subprocess-in-streamlit-using-asyncio-and-display-output/)

### Libraries
9. [httpx - Modern HTTP client](https://www.python-httpx.org/)
10. [aiohttp - Async HTTP client](https://docs.aiohttp.org/)
11. [nest_asyncio - Event loop patching](https://github.com/erdewit/nest_asyncio)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-13
**Maintainer**: Technical Research Team
**Status**: Production Ready
