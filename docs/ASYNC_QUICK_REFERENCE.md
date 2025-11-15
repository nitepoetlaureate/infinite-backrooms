# Streamlit Async Quick Reference Card

**Last Updated**: 2025-11-13

---

## DO THIS (Safe Patterns)

### 1. Use Synchronous HTTP Clients

```python
import httpx
import streamlit as st

@st.cache_resource
def get_http_client():
    return httpx.Client(
        timeout=30.0,
        limits=httpx.Limits(max_connections=100)
    )

# Usage
client = get_http_client()
response = client.get("https://api.example.com")
```

**Why**: No async complexity, connection pooling, thread-safe, Streamlit-native.

---

### 2. Thread-Based Async Execution (If Async Required)

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

def run_async_in_thread(coro):
    def run_in_new_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()  # CRITICAL

    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(run_in_new_loop).result()

# Usage
result = run_async_in_thread(async_function())
```

**Why**: Avoids event loop conflicts, safe across Streamlit reruns.

---

### 3. Cache Resources (Singletons)

```python
import streamlit as st

@st.cache_resource
def get_database_connection():
    return create_connection()  # Called once, reused forever

# Usage
conn = get_database_connection()
```

**Why**: One instance shared across all users, sessions, and reruns.

---

### 4. Synchronous Streaming

```python
import httpx
import streamlit as st

@st.cache_resource
def get_streaming_client():
    return httpx.Client(timeout=120.0)

def stream_response(url, payload):
    client = get_streaming_client()
    with client.stream("POST", url, json=payload) as response:
        for line in response.iter_lines():
            yield line

# Usage with real-time updates
placeholder = st.empty()
for chunk in stream_response(url, data):
    placeholder.write(chunk)
```

**Why**: Real-time streaming without async complexity.

---

## DON'T DO THIS (Anti-Patterns)

### 1. Direct asyncio.run()

```python
# WRONG - Event loop already running
import asyncio

async def fetch():
    return "data"

result = asyncio.run(fetch())  # RuntimeError!
```

**Fix**: Use thread-based execution or synchronous client.

---

### 2. Multiple Client Instances

```python
# WRONG - No connection pooling
async def fetch(url):
    async with httpx.AsyncClient() as client:  # New client each time!
        return await client.get(url)

for url in urls:
    data = run_async_in_thread(fetch(url))
```

**Fix**: Create client once with `@st.cache_resource`.

---

### 3. Missing Event Loop Cleanup

```python
# WRONG - Resource leak
def bad_wrapper(coro):
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(coro)
    # Missing: loop.close()
    return result
```

**Fix**: Always close loops in `finally` block.

---

### 4. Blocking Sleep in Async Code

```python
# WRONG - Blocks event loop
import time

async def bad_cleanup():
    await session.close()
    time.sleep(0.25)  # Blocking!
```

**Fix**: Use `await asyncio.sleep(0.25)` or remove entirely.

---

### 5. Caching Async Functions

```python
# WRONG - Not supported
@st.cache_resource
async def get_client():  # Async not supported!
    return httpx.AsyncClient()
```

**Fix**: Cache synchronous wrapper or use sync client.

---

## Decision Tree

```
Need to make HTTP requests?
│
├─ Can use sync client? (httpx.Client, requests)
│  └─ YES → Use sync client with @st.cache_resource
│     SIMPLE, RECOMMENDED
│
└─ Must use async? (aiohttp, async-only library)
   │
   ├─ Prototype/quick test?
   │  └─ Use nest_asyncio.apply()
   │     TEMPORARY ONLY
   │
   └─ Production?
      └─ Use thread-based execution
         SAFE, PRODUCTION-READY
```

---

## Common Scenarios

### Scenario: Ollama API Client

**Recommended**: Synchronous httpx.Client

```python
import httpx
import streamlit as st

@st.cache_resource
def get_ollama_client():
    return httpx.Client(
        base_url="http://localhost:11434",
        timeout=120.0
    )

def generate_stream(model, prompt):
    client = get_ollama_client()
    with client.stream("POST", "/api/generate", json={...}) as response:
        for line in response.iter_lines():
            yield parse_line(line)
```

**Why Not Async**: HTTP API doesn't require async, sync is simpler.

---

### Scenario: Database Connection

**Recommended**: Sync driver with caching

```python
import streamlit as st
import psycopg2

@st.cache_resource
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="mydb"
    )

# Usage
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("SELECT ...")
```

**Why**: Most DB drivers have sync versions, simpler to use.

---

### Scenario: Multiple API Calls

**Recommended**: ThreadPoolExecutor with sync client

```python
from concurrent.futures import ThreadPoolExecutor
import httpx
import streamlit as st

@st.cache_resource
def get_client():
    return httpx.Client()

def fetch_all(urls):
    client = get_client()

    def fetch_one(url):
        return client.get(url).json()

    with ThreadPoolExecutor(max_workers=5) as executor:
        return list(executor.map(fetch_one, urls))

# Usage
results = fetch_all(["url1", "url2", "url3"])
```

**Why**: Concurrent without async complexity, still uses connection pool.

---

## Troubleshooting

### Error: "RuntimeError: This event loop is already running"

**Cause**: Using `asyncio.run()` in Streamlit

**Fix**: Use thread-based execution or sync client

---

### Error: "RuntimeError: Event loop is closed"

**Cause**: Trying to reuse closed event loop

**Fix**: Create new loop for each operation or use persistent runner

---

### Warning: "Unclosed client session"

**Cause**: Not closing async clients properly

**Fix**: Use `async with` or call `await client.aclose()`

---

### Error: "UnserializableReturnValueError" with st.cache_data

**Cause**: Caching coroutine objects (async functions)

**Fix**: Don't cache async functions; cache sync wrappers instead

---

## Performance Tips

1. **Connection Pooling**: Always use `@st.cache_resource` for HTTP clients
2. **Timeouts**: Set aggressive timeouts to prevent hanging
3. **Limits**: Configure connection limits based on load
4. **Keep-Alive**: Enable keep-alive connections for reuse
5. **HTTP/2**: Use HTTP/2 when supported for multiplexing

---

## Example: Complete Migration

### Before (Complex Async)

```python
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def fetch_ollama(prompt):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama2", "prompt": prompt}
        ) as response:
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
        return executor.submit(run_in_new_loop).result()

# Usage
result = run_async_in_thread(fetch_ollama("Hello"))
```

### After (Simple Sync)

```python
import httpx
import streamlit as st

@st.cache_resource
def get_ollama_client():
    return httpx.Client(
        base_url="http://localhost:11434",
        timeout=120.0
    )

def fetch_ollama(prompt):
    client = get_ollama_client()
    response = client.post(
        "/api/generate",
        json={"model": "llama2", "prompt": prompt}
    )
    return response.json()

# Usage
result = fetch_ollama("Hello")
```

**Benefits**: 70% less code, same functionality, better performance.

---

## Libraries Reference

| Library | Sync Support | Async Support | Recommended for Streamlit |
|---------|--------------|---------------|---------------------------|
| httpx | ✅ Client | ✅ AsyncClient | ✅ Use sync Client |
| requests | ✅ | ❌ | ✅ Good for simple cases |
| aiohttp | ❌ | ✅ | ⚠️ Only if required |
| urllib3 | ✅ | ❌ | ✅ Low-level option |

---

## Checklist for Production

- [ ] All HTTP clients cached with `@st.cache_resource`
- [ ] No direct `asyncio.run()` calls
- [ ] All event loops closed in `finally` blocks
- [ ] No blocking `time.sleep()` in async code
- [ ] Connection timeouts configured
- [ ] Connection pool limits set
- [ ] No multiple client instantiations
- [ ] Thread-safety verified for cached resources
- [ ] Error handling for network failures
- [ ] Monitoring/logging added

---

## Quick Migration Steps

1. **Replace async clients** with sync equivalents (httpx.Client)
2. **Add `@st.cache_resource`** to client creation
3. **Remove async/await** keywords
4. **Remove thread wrappers** (no longer needed)
5. **Test** thoroughly
6. **Monitor** performance and errors

---

## Need Help?

1. Check full guide: `docs/STREAMLIT_ASYNC_GUIDE.md`
2. Review research: `docs/ASYNC_RESEARCH_SUMMARY.json`
3. Ask in Streamlit Community: https://discuss.streamlit.io/

---

**Remember**: When in doubt, use synchronous clients. They're simpler, safer, and sufficient for 95% of Streamlit use cases.
