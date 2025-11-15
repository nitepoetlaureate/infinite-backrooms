# Unified Ollama Client API Design

## Overview

This document presents the unified design for the Ollama client API that consolidates all existing implementations into a single, production-ready canonical client. The design incorporates the best features from all existing implementations while providing a clean, extensible interface.

## Design Goals

1. **Unification**: Consolidate 4+ existing client implementations into one canonical client
2. **Performance**: Leverage advanced connection pooling from OptimizedOllamaClient
3. **Compatibility**: Support both async and Streamlit-safe sync usage patterns
4. **Extensibility**: Clean API design that can accommodate future enhancements
5. **Production-Ready**: Comprehensive error handling, monitoring, and configuration

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Unified Client API                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │   Core Client   │  │     Streamlit Compatibility      │  │
│  │                 │  │      Layer (Sync Wrapper)        │  │
│  └─────────────────┘  └──────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                Connection Pooling Layer                      │
│  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │  Advanced Pool  │  │      Health Monitoring           │  │
│  │   Management    │  │      & Auto-Recovery             │  │
│  └─────────────────┘  └──────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    HTTP Transport Layer                     │
│  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │   aiohttp Core  │  │      Error Recovery & Retry      │  │
│  │                 │  │      Logic                        │  │
│  └─────────────────┘  └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## API Specification

### Core Client Class

```python
from typing import AsyncGenerator, Optional, Dict, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp
import logging

class ClientMode(Enum):
    """Client operation mode."""
    ASYNC = "async"
    STREAMLIT_SAFE = "streamlit_safe"

class LogLevel(Enum):
    """Logging levels for the client."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

@dataclass
class ConnectionConfig:
    """Configuration for connection pooling."""
    min_connections: int = 2
    max_connections: int = 10
    keepalive_timeout: int = 300
    health_check_interval: int = 30
    max_idle_time: int = 600
    max_failures: int = 3
    enable_pooling: bool = True

@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_retries: int = 3
    retry_delay: float = 1.0
    exponential_backoff: bool = True
    retry_on_status: list[int] = None

@dataclass
class TimeoutConfig:
    """Configuration for timeouts."""
    connect: int = 10
    read: int = 300
    total: Optional[int] = None

@dataclass
class ClientConfig:
    """Comprehensive client configuration."""
    # Basic configuration
    base_url: str = DEFAULT_OLLAMA_URL
    mode: ClientMode = ClientMode.ASYNC

    # Connection pooling
    connection: ConnectionConfig = None

    # Retry logic
    retry: RetryConfig = None

    # Timeouts
    timeout: TimeoutConfig = None

    # Logging and monitoring
    log_level: LogLevel = LogLevel.INFO
    enable_metrics: bool = True

    # SSL and security
    verify_ssl: bool = True

    def __post_init__(self):
        # Initialize default configurations if not provided
        if self.connection is None:
            self.connection = ConnectionConfig()
        if self.retry is None:
            self.retry = RetryConfig()
        if self.retry.retry_on_status is None:
            self.retry.retry_on_status = [500, 502, 503, 504]
        if self.timeout is None:
            self.timeout = TimeoutConfig()

@dataclass
class GenerationOptions:
    """Options for model generation."""
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    num_predict: int = -1
    seed: Optional[int] = None
    stop: Optional[list[str]] = None

@dataclass
class ModelInfo:
    """Information about an available model."""
    name: str
    size: int
    digest: str
    modified_at: str
    details: Optional[Dict[str, Any]] = None

class OllamaClient:
    """Unified Ollama API client with comprehensive features.

    This is the canonical client that consolidates all functionality from
    multiple implementations into a single, production-ready interface.

    Features:
    - Advanced connection pooling with health monitoring
    - Comprehensive error handling and retry logic
    - Both async and Streamlit-safe sync interfaces
    - Configurable timeouts and parameters
    - Performance monitoring and metrics
    - Type-safe API with comprehensive documentation

    Example:
        # Async usage
        async with OllamaClient() as client:
            connected, models = await client.test_connection()
            if connected:
                async for chunk in client.generate_stream("llama2", "Hello"):
                    print(chunk["content"])

        # Streamlit-safe usage
        client = OllamaClient(mode=ClientMode.STREAMLIT_SAFE)
        connected, models = client.test_connection()
        for chunk in client.generate_stream("llama2", "Hello"):
            print(chunk["content"])
    """

    def __init__(
        self,
        config: Optional[ClientConfig] = None,
        **kwargs: Any
    ) -> None:
        """Initialize the unified Ollama client.

        Args:
            config: Complete client configuration (optional)
            **kwargs: Individual configuration parameters that override config
        """
        # Initialize configuration
        if config is None:
            config = ClientConfig()

        # Apply any overrides from kwargs
        self.config = self._apply_config_overrides(config, kwargs)

        # Internal state
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
        self._connection_pool: Optional[OllamaConnectionPool] = None
        self._closed = False

        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.setLevel(self.config.log_level.value.upper())

        # Metrics collection (if enabled)
        self._metrics = ClientMetrics() if self.config.enable_metrics else None

    async def __aenter__(self) -> "OllamaClient":
        """Enter async context manager - initialize resources."""
        if self._closed:
            raise RuntimeError("Client has been closed")

        await self._initialize_resources()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> None:
        """Exit async context manager - cleanup resources."""
        await self.close()

    # ========== Core API Methods ==========

    async def test_connection(self) -> Tuple[bool, list[str]]:
        """Test connection to Ollama and retrieve available models.

        Returns:
            Tuple of (connected: bool, models: list[str])

        Raises:
            RuntimeError: If client is not initialized
            ConnectionError: If connection test fails

        Example:
            async with OllamaClient() as client:
                connected, models = await client.test_connection()
                if connected:
                    print(f"Available models: {models}")
        """
        return await self._execute_with_retry(
            "Connection test",
            self._perform_connection_test
        )

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
        think: bool = False,
        timeout: Optional[int] = None,
        **kwargs: Any
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming response from model.

        Args:
            model: Model name to use
            prompt: User prompt
            system_prompt: Optional system prompt
            options: Generation options (temperature, etc.)
            think: Enable thinking mode (if supported)
            timeout: Override default timeout for this request
            **kwargs: Additional model options

        Yields:
            dict: Response chunks with standardized format:
                - {"type": "thinking", "content": str}
                - {"type": "response", "content": str}
                - {"type": "error", "content": str}
                - {"type": "done"}
                - {"type": "metrics", "data": dict}

        Raises:
            RuntimeError: If client is not initialized
            ValueError: If model name is invalid
            TimeoutError: If request times out

        Example:
            async with OllamaClient() as client:
                async for chunk in client.generate_stream(
                    model="llama2",
                    prompt="Explain quantum computing",
                    think=True
                ):
                    if chunk["type"] == "response":
                        print(chunk["content"], end="")
        """
        async for chunk in self._execute_stream_with_retry(
            f"Stream generation for model {model}",
            self._perform_generate_stream,
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            options=options,
            think=think,
            timeout=timeout,
            **kwargs
        ):
            yield chunk

    async def generate(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
        think: bool = False,
        timeout: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """Generate complete response (non-streaming).

        This is a convenience method that collects all chunks from
        generate_stream() and returns the complete response.

        Args:
            model: Model name to use
            prompt: User prompt
            system_prompt: Optional system prompt
            options: Generation options
            think: Enable thinking mode
            timeout: Request timeout
            **kwargs: Additional model options

        Returns:
            str: Complete response text

        Raises:
            RuntimeError: If client is not initialized
            ValueError: If parameters are invalid
            TimeoutError: If request times out

        Example:
            async with OllamaClient() as client:
                response = await client.generate(
                    model="llama2",
                    prompt="Write a haiku about AI"
                )
                print(response)
        """
        response_parts = []

        async for chunk in self.generate_stream(
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            options=options,
            think=think,
            timeout=timeout,
            **kwargs
        ):
            if chunk["type"] == "response":
                response_parts.append(chunk["content"])
            elif chunk["type"] == "error":
                raise RuntimeError(f"Generation failed: {chunk['content']}")
            elif chunk["type"] == "done":
                break

        return "".join(response_parts)

    async def list_models(self) -> list[ModelInfo]:
        """List all available models with detailed information.

        Returns:
            list[ModelInfo]: Detailed model information

        Raises:
            RuntimeError: If client is not initialized
            ConnectionError: If request fails

        Example:
            async with OllamaClient() as client:
                models = await client.list_models()
                for model in models:
                    print(f"{model.name}: {model.size:,} bytes")
        """
        return await self._execute_with_retry(
            "List models",
            self._perform_list_models
        )

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of the client and service.

        Returns:
            dict: Health status information with keys:
                - client_status: "healthy", "degraded", or "unhealthy"
                - api_connectivity: "connected", "disconnected", or "error"
                - available_models: list of model names
                - connection_metrics: dict with pool statistics
                - timestamp: Unix timestamp of check

        Example:
            async with OllamaClient() as client:
                health = await client.health_check()
                print(f"Status: {health['client_status']}")
        """
        health_info = {
            "client_status": "healthy" if not self._closed else "closed",
            "timestamp": asyncio.get_event_loop().time(),
        }

        # Test API connectivity
        try:
            connected, models = await self.test_connection()
            health_info["api_connectivity"] = "connected" if connected else "disconnected"
            health_info["available_models"] = models
        except Exception as e:
            health_info["api_connectivity"] = "error"
            health_info["connectivity_error"] = str(e)

        # Add connection metrics if pooling is enabled
        if self.config.connection.enable_pooling and self._connection_pool:
            health_info["connection_metrics"] = self._connection_pool.get_metrics()

        return health_info

    # ========== Configuration and Utility Methods ==========

    def get_config(self) -> ClientConfig:
        """Get current client configuration.

        Returns:
            ClientConfig: Current configuration
        """
        return self.config

    def update_config(self, **kwargs: Any) -> None:
        """Update client configuration.

        Args:
            **kwargs: Configuration parameters to update

        Note:
            Some configuration changes require client reinitialization.
        """
        self.config = self._apply_config_overrides(self.config, kwargs)

    def get_metrics(self) -> Dict[str, Any]:
        """Get client performance metrics.

        Returns:
            dict: Metrics data if enabled, empty dict otherwise

        Example:
            client = OllamaClient(enable_metrics=True)
            metrics = client.get_metrics()
            print(f"Requests made: {metrics['total_requests']}")
        """
        if self._metrics:
            return self._metrics.get_data()
        return {"message": "Metrics collection is disabled"}

    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about current connection state.

        Returns:
            dict: Connection information and statistics

        Example:
            client = OllamaClient()
            info = client.get_connection_info()
            print(f"Pool size: {info['pool_metrics']['total_connections']}")
        """
        info = {
            "base_url": self.config.base_url,
            "mode": self.config.mode.value,
            "connection_pooling": self.config.connection.enable_pooling,
            "session_active": self._session is not None and not self._session.closed,
        }

        if self._connection_pool:
            info["pool_metrics"] = self._connection_pool.get_metrics()

        return info

    # ========== Lifecycle Management ==========

    async def close(self) -> None:
        """Close the client and release all resources.

        This method is called automatically when using the async context
        manager, but can be called manually for explicit cleanup.

        Example:
            client = OllamaClient()
            # ... use client ...
            await client.close()
        """
        if self._closed:
            return

        self._closed = True

        # Close connection pool
        if self._connection_pool:
            await self._connection_pool.close()
            self._connection_pool = None

        # Close session
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

        # Close connector
        if self._connector and not self._connector.closed:
            await self._connector.close()
            self._connector = None

        self.logger.debug("Client resources cleaned up")

    # ========== Internal Implementation ==========

    async def _initialize_resources(self) -> None:
        """Initialize client resources based on configuration."""
        if self.config.connection.enable_pooling:
            await self._initialize_connection_pool()
        else:
            await self._initialize_simple_session()

    async def _initialize_connection_pool(self) -> None:
        """Initialize advanced connection pooling."""
        self._connection_pool = OllamaConnectionPool(
            base_url=self.config.base_url,
            min_connections=self.config.connection.min_connections,
            max_connections=self.config.connection.max_connections,
            keepalive_timeout=self.config.connection.keepalive_timeout,
            health_check_interval=self.config.connection.health_check_interval,
            max_idle_time=self.config.connection.max_idle_time,
            max_failures=self.config.connection.max_failures,
        )

        await self._connection_pool.__aenter__()
        self.logger.debug(f"Connection pool initialized: {self.config.base_url}")

    async def _initialize_simple_session(self) -> None:
        """Initialize simple aiohttp session without pooling."""
        self._connector = aiohttp.TCPConnector(
            limit=1,
            enable_cleanup_closed=True,
            keepalive_timeout=self.config.connection.keepalive_timeout,
        )

        timeout = aiohttp.ClientTimeout(
            total=self.config.timeout.total,
            sock_read=self.config.timeout.read,
            sock_connect=self.config.timeout.connect,
        )

        self._session = aiohttp.ClientSession(
            connector=self._connector,
            timeout=timeout,
            connector_owner=True,
        )

        self.logger.debug(f"Simple session initialized: {self.config.base_url}")

    async def _execute_with_retry(
        self,
        operation: str,
        func,
        *args,
        **kwargs
    ) -> Any:
        """Execute an operation with retry logic."""
        last_exception = None

        for attempt in range(self.config.retry.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e

                if attempt < self.config.retry.max_retries:
                    if self.config.retry.exponential_backoff:
                        wait_time = self.config.retry.retry_delay * (2 ** attempt)
                    else:
                        wait_time = self.config.retry.retry_delay

                    self.logger.warning(
                        f"{operation} failed (attempt {attempt + 1}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"{operation} failed after {self.config.retry.max_retries + 1} attempts: {e}")
            except Exception:
                # Non-retryable error
                raise

        raise last_exception if last_exception else Exception("Operation failed")

    async def _execute_stream_with_retry(
        self,
        operation: str,
        func,
        *args,
        **kwargs
    ) -> AsyncGenerator[Any, None]:
        """Execute a streaming operation with retry logic for initial connection."""
        for attempt in range(self.config.retry.max_retries + 1):
            try:
                async for item in func(*args, **kwargs):
                    yield item
                return
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < self.config.retry.max_retries:
                    if self.config.retry.exponential_backoff:
                        wait_time = self.config.retry.retry_delay * (2 ** attempt)
                    else:
                        wait_time = self.config.retry.retry_delay

                    self.logger.warning(
                        f"{operation} failed (attempt {attempt + 1}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    yield {"type": "error", "content": f"Stream failed after retries: {e}"}
                    return
            except Exception as e:
                yield {"type": "error", "content": f"Stream failed: {e}"}
                return

    # ... Additional internal methods for specific operations
    # These would be implemented in the actual client code

    def _apply_config_overrides(self, config: ClientConfig, overrides: Dict[str, Any]) -> ClientConfig:
        """Apply configuration overrides from kwargs."""
        # Implementation would handle nested config updates
        return config
```

### Streamlit Compatibility Layer

```python
class StreamlitOllamaClient:
    """Streamlit-safe wrapper for the unified Ollama client.

    This wrapper provides a synchronous interface that safely integrates
    with Streamlit's event loop management while leveraging all the
    advanced features of the unified async client.

    Key features:
    - Thread-based async execution to avoid event loop corruption
    - Synchronous generator interface for streaming
    - All advanced features from the unified client
    - Error handling that doesn't crash Streamlit apps

    Example:
        client = StreamlitOllamaClient()
        connected, models = client.test_connection()

        for chunk in client.generate_stream("llama2", "Hello"):
            if chunk["type"] == "response":
                st.write(chunk["content"])
    """

    def __init__(
        self,
        config: Optional[ClientConfig] = None,
        **kwargs: Any
    ) -> None:
        """Initialize Streamlit-safe client."""
        # Force streamlit-safe mode
        if config is None:
            config = ClientConfig()
        config.mode = ClientMode.STREAMLIT_SAFE

        self.config = config
        self._client_kwargs = kwargs

    def test_connection(self) -> Tuple[bool, list[str]]:
        """Test connection safely in Streamlit context."""
        async def _test():
            async with OllamaClient(config=self.config, **self._client_kwargs) as client:
                return await client.test_connection()

        return safe_async_call(_test())

    def generate_stream(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
        think: bool = False,
        timeout: Optional[int] = None,
        **kwargs: Any
    ) -> Generator[Dict[str, Any], None, None]:
        """Generate streaming response safely in Streamlit context."""
        async def _generate():
            async with OllamaClient(config=self.config, **self._client_kwargs) as client:
                async for chunk in client.generate_stream(
                    model=model,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    options=options,
                    think=think,
                    timeout=timeout,
                    **kwargs
                ):
                    yield chunk

        return safe_stream_wrapper(_generate())

    def generate(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
        think: bool = False,
        timeout: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """Generate complete response safely in Streamlit context."""
        response_parts = []

        for chunk in self.generate_stream(
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            options=options,
            think=think,
            timeout=timeout,
            **kwargs
        ):
            if chunk["type"] == "response":
                response_parts.append(chunk["content"])
            elif chunk["type"] == "error":
                raise RuntimeError(f"Generation failed: {chunk['content']}")

        return "".join(response_parts)

    # ... Additional methods that delegate to the async client
```

## Configuration System

### Hierarchical Configuration

The configuration system supports multiple levels of overrides:

```python
# 1. Default configuration (built-in)
default_config = ClientConfig()

# 2. Environment-based configuration
env_config = ClientConfig.from_environment()

# 3. File-based configuration
file_config = ClientConfig.from_file("config.json")

# 4. Runtime overrides
runtime_config = ClientConfig(
    base_url="http://custom:11434",
    connection=ConnectionConfig(max_connections=20)
)

# 5. Method-level overrides
client.generate("llama2", "Hello", timeout=60)
```

### Configuration Validation

```python
@dataclass
class ValidatedConfig:
    """Configuration with automatic validation."""

    def __post_init__(self):
        self._validate_config()

    def _validate_config(self):
        """Validate configuration parameters."""
        if self.connection.min_connections < 0:
            raise ValueError("min_connections must be >= 0")

        if self.connection.max_connections < self.connection.min_connections:
            raise ValueError("max_connections must be >= min_connections")

        if self.timeout.connect < 0 or self.timeout.read < 0:
            raise ValueError("Timeouts must be positive")

        if not (0.0 <= self.options.temperature <= 2.0):
            raise ValueError("Temperature must be between 0.0 and 2.0")
```

## Connection Pooling Architecture

### Advanced Pool Features

```python
class OllamaConnectionPool:
    """Advanced connection pool with health monitoring."""

    def __init__(
        self,
        base_url: str,
        min_connections: int = 2,
        max_connections: int = 10,
        health_check_interval: int = 30,
        max_idle_time: int = 600,
        max_failures: int = 3,
    ) -> None:
        """Initialize pool with advanced configuration."""

    # Features:
    # - Automatic health monitoring
    # - Connection lifecycle management
    # - Graceful degradation
    # - Metrics collection
    # - Concurrent health checks
    # - Backpressure handling
```

### Pool Behavior

```
┌─────────────────────────────────────────────────────────────┐
│                    Connection Pool                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │  Active Conns   │  │      Idle Connections            │  │
│  │  (In Use)       │  │      (Available for Reuse)      │  │
│  └─────────────────┘  └──────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │  Health Monitor │  │      Auto-Recovery               │  │
│  │  (Background)   │  │      (Replace Failed Conns)      │  │
│  └─────────────────┘  └──────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Metrics Collection                       │
│  - Connection counts, request rates, failure rates          │
└─────────────────────────────────────────────────────────────┘
```

## Module Organization

### File Structure

```
src/services/
├── ollama_client.py              # Unified client (primary file)
├── ollama_config.py              # Configuration classes
├── ollama_connection_pool.py     # Connection pooling implementation
├── ollama_streamlit.py           # Streamlit compatibility wrapper
├── ollama_metrics.py             # Metrics collection
├── ollama_types.py               # Type definitions and dataclasses
└── ollama_errors.py              # Custom exceptions
```

### Module Dependencies

```
ollama_client.py (Main Module)
├── ollama_config.py (ClientConfig, GenerationOptions)
├── ollama_connection_pool.py (OllamaConnectionPool)
├── ollama_metrics.py (ClientMetrics)
├── ollama_types.py (ModelInfo, ResponseChunk)
└── ollama_errors.py (ClientError, ConnectionError)

ollama_streamlit.py (Streamlit Wrapper)
├── ollama_client.py (OllamaClient)
└── ollama_config.py (ClientConfig)
```

## Implementation Strategy

### Phase 1: Core Implementation (2-3 hours)
1. Create unified `OllamaClient` class
2. Implement configuration system
3. Add connection pooling integration
4. Include basic API methods

### Phase 2: Advanced Features (1-2 hours)
1. Add comprehensive error handling
2. Implement metrics collection
3. Add retry logic with exponential backoff
4. Include health monitoring

### Phase 3: Streamlit Compatibility (1 hour)
1. Create `StreamlitOllamaClient` wrapper
2. Implement thread-safe async execution
3. Add synchronous generator interface
4. Test Streamlit integration

### Phase 4: Migration Support (30-45 minutes)
1. Update all imports in codebase
2. Remove duplicate client files
3. Update tests
4. Add migration documentation

## Testing Strategy

### Unit Tests
```python
class TestOllamaClient:
    """Comprehensive test suite for unified client."""

    async def test_connection_pooling(self):
        """Test connection pooling behavior."""

    async def test_retry_logic(self):
        """Test retry mechanism with various failure modes."""

    async def test_streaming_response(self):
        """Test streaming response handling."""

    async def test_configuration_validation(self):
        """Test configuration validation and overrides."""

    async def test_metrics_collection(self):
        """Test performance metrics gathering."""
```

### Integration Tests
- Test with real Ollama server
- Test connection pool under load
- Test error recovery scenarios
- Test Streamlit compatibility

## Migration Guide

### For Existing Users

**Before:**
```python
from src.services.ollama_client_optimized import OptimizedOllamaClient

async with OptimizedOllamaClient() as client:
    connected, models = await client.test_connection()
```

**After:**
```python
from src.services.ollama_client import OllamaClient, ClientConfig

config = ClientConfig(
    connection=ConnectionConfig(max_connections=10)
)

async with OllamaClient(config=config) as client:
    connected, models = await client.test_connection()
```

### For Streamlit Users

**Before:**
```python
from src.services.streamlit_ollama_client import StreamlitOllamaClient

client = StreamlitOllamaClient()
connected, models = client.test_connection()
```

**After:**
```python
from src.services.ollama_client import StreamlitOllamaClient, ClientConfig

config = ClientConfig(mode=ClientMode.STREAMLIT_SAFE)
client = StreamlitOllamaClient(config=config)
connected, models = client.test_connection()
```

## Performance Optimizations

### Connection Pooling
- Reuse connections for multiple requests
- Maintain minimum connection count
- Automatic health monitoring
- Graceful connection cleanup

### Request Optimization
- Configurable timeouts per operation
- Retry logic with exponential backoff
- Efficient streaming with proper backpressure
- Resource usage monitoring

### Memory Management
- Bounded connection pools
- Automatic resource cleanup
- Metrics with controlled memory usage
- Lazy initialization of components

## Security Considerations

### SSL/TLS Configuration
```python
config = ClientConfig(
    verify_ssl=True,
    ssl_context=create_default_context()
)
```

### Input Validation
- Model name validation
- Prompt length limits
- Parameter validation
- Injection prevention

### Error Information Sanitization
- Remove sensitive URLs from error messages
- Limit stack trace exposure
- Safe error logging

## Monitoring and Observability

### Built-in Metrics
```python
metrics = client.get_metrics()
# {
#     "total_requests": 1250,
#     "successful_requests": 1247,
#     "failed_requests": 3,
#     "average_response_time": 1.234,
#     "connection_pool_stats": {...}
# }
```

### Health Endpoints
```python
health = await client.health_check()
# {
#     "client_status": "healthy",
#     "api_connectivity": "connected",
#     "available_models": ["llama2", "mistral"],
#     "connection_metrics": {...},
#     "timestamp": 1699123456.789
# }
```

### Logging Integration
- Structured logging with correlation IDs
- Configurable log levels
- Performance event logging
- Error tracking integration

## Success Criteria

- [x] Unified API design consolidating all existing implementations
- [x] Comprehensive configuration system with validation
- [x] Advanced connection pooling with health monitoring
- [x] Streamlit compatibility layer
- [x] Type-safe API with comprehensive documentation
- [x] Performance monitoring and metrics
- [x] Clear migration path for existing users
- [x] Production-ready error handling and retry logic

This unified client API design provides a solid foundation for the python-async-client-consolidator to implement the canonical client that consolidates all existing functionality while providing an extensible, production-ready interface.