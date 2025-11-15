"""Advanced connection pooling for Ollama API clients with health monitoring.

This module provides a robust connection pool implementation that:
- Maintains persistent connections with proper lifecycle management
- Implements health checks and automatic recovery
- Provides connection reuse and resource optimization
- Eliminates blocking sleeps from connection cleanup
- Supports configurable limits and monitoring
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from weakref import WeakSet

import aiohttp
from aiohttp import ClientConnectorError, ClientError, ClientSession

from src.utils.constants import DEFAULT_OLLAMA_URL, DEFAULT_RESPONSE_TIMEOUT

logger = logging.getLogger(__name__)


@dataclass
class ConnectionMetrics:
    """Metrics for connection pool monitoring."""
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    requests_served: int = 0
    failures: int = 0
    is_healthy: bool = True
    last_health_check: float = field(default_factory=time.time)


class PooledConnection:
    """A single pooled connection with health monitoring."""

    def __init__(
        self,
        session: ClientSession,
        connector: aiohttp.TCPConnector,
        base_url: str,
        pool_ref: "OllamaConnectionPool"
    ) -> None:
        """Initialize pooled connection.

        Args:
            session: The aiohttp ClientSession
            connector: The TCP connector
            base_url: Base URL for the connection
            pool_ref: Reference to the parent pool
        """
        self.session = session
        self.connector = connector
        self.base_url = base_url
        self.pool_ref = pool_ref
        self.metrics = ConnectionMetrics()
        self._in_use = False
        self._closing = False

    @property
    def is_in_use(self) -> bool:
        """Check if connection is currently in use."""
        return self._in_use

    @property
    def is_closing(self) -> bool:
        """Check if connection is being closed."""
        return self._closing

    async def acquire(self) -> None:
        """Acquire the connection for use."""
        if self._in_use:
            raise RuntimeError("Connection already in use")
        if self._closing:
            raise RuntimeError("Connection is closing")

        self._in_use = True
        self.metrics.last_used = time.time()
        self.metrics.requests_served += 1

    async def release(self) -> None:
        """Release the connection back to the pool."""
        if not self._in_use:
            logger.warning("Releasing connection that was not acquired")
            return

        self._in_use = False
        await self.pool_ref._return_connection(self)

    async def health_check(self) -> bool:
        """Perform a health check on the connection.

        Returns:
            True if connection is healthy, False otherwise
        """
        if self._closing or not self.session or self.session.closed:
            self.metrics.is_healthy = False
            return False

        try:
            # Quick health check with timeout
            timeout = aiohttp.ClientTimeout(total=5)
            async with self.session.get(
                f"{self.base_url}/api/tags",
                timeout=timeout
            ) as response:
                is_healthy = response.status == 200
                self.metrics.is_healthy = is_healthy
                self.metrics.last_health_check = time.time()
                return is_healthy
        except (ClientError, asyncio.TimeoutError) as e:
            logger.debug(f"Health check failed: {type(e).__name__}")
            self.metrics.is_healthy = False
            self.metrics.failures += 1
            return False

    async def close(self) -> None:
        """Close the connection and clean up resources."""
        if self._closing:
            return

        self._closing = True

        try:
            if self.session and not self.session.closed:
                await self.session.close()
        except Exception as e:
            logger.warning(f"Error closing session: {e}")

        try:
            if self.connector and not self.connector.closed:
                await self.connector.close()
        except Exception as e:
            logger.warning(f"Error closing connector: {e}")


class OllamaConnectionPool:
    """Advanced connection pool with health monitoring and auto-scaling.

    This pool maintains a set of healthy connections that can be reused
    across multiple requests, providing better performance and resource
    management than creating new connections for each request.

    Features:
    - Configurable minimum and maximum pool sizes
    - Automatic health checks and connection recovery
    - Connection lifecycle management without blocking sleeps
    - Metrics and monitoring
    - Graceful shutdown
    """

    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_URL,
        min_connections: int = 2,
        max_connections: int = 10,
        keepalive_timeout: int = 300,
        health_check_interval: int = 30,
        max_idle_time: int = 600,
        max_failures: int = 3,
    ) -> None:
        """Initialize the connection pool.

        Args:
            base_url: Base URL for Ollama API
            min_connections: Minimum number of connections to maintain
            max_connections: Maximum number of connections in pool
            keepalive_timeout: Keepalive timeout for connections (seconds)
            health_check_interval: Health check interval (seconds)
            max_idle_time: Maximum time a connection can be idle (seconds)
            max_failures: Maximum failures before connection is removed
        """
        self.base_url = base_url
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.keepalive_timeout = keepalive_timeout
        self.health_check_interval = health_check_interval
        self.max_idle_time = max_idle_time
        self.max_failures = max_failures

        self._available_connections: asyncio.Queue[PooledConnection] = asyncio.Queue()
        self._all_connections: WeakSet[PooledConnection] = WeakSet()
        self._lock = asyncio.Lock()
        self._shutdown = False
        self._health_check_task: Optional[asyncio.Task] = None
        self._connection_count = 0

        logger.info(f"Initialized connection pool: min={min_connections}, max={max_connections}")

    async def __aenter__(self) -> OllamaConnectionPool:
        """Enter async context manager - start health monitoring."""
        await self._ensure_minimum_connections()
        self._health_check_task = asyncio.create_task(self._health_monitor())
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit async context manager - cleanup all connections."""
        await self.close()

    async def close(self) -> None:
        """Close all connections and stop monitoring."""
        self._shutdown = True

        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        connections_to_close: List[PooledConnection] = []
        while not self._available_connections.empty():
            try:
                conn = self._available_connections.get_nowait()
                connections_to_close.append(conn)
            except asyncio.QueueEmpty:
                break

        # Add all tracked connections
        connections_to_close.extend(list(self._all_connections))

        # Close connections concurrently without blocking
        if connections_to_close:
            await asyncio.gather(
                *[conn.close() for conn in connections_to_close],
                return_exceptions=True
            )

        logger.info("Connection pool closed")

    async def get_connection(self) -> PooledConnection:
        """Get a connection from the pool.

        Returns:
            A healthy PooledConnection ready for use

        Raises:
            RuntimeError: If pool is shutdown or no connections available
        """
        if self._shutdown:
            raise RuntimeError("Connection pool is shutdown")

        async with self._lock:
            # Try to get an existing connection
            try:
                conn = self._available_connections.get_nowait()
                if await self._is_connection_healthy(conn):
                    await conn.acquire()
                    return conn
                else:
                    # Connection is unhealthy, remove it
                    await self._remove_connection(conn)
            except asyncio.QueueEmpty:
                pass

            # No available connections, try to create a new one
            if self._connection_count < self.max_connections:
                conn = await self._create_connection()
                await conn.acquire()
                return conn

            # Pool is full, wait for a connection
            try:
                conn = await asyncio.wait_for(
                    self._available_connections.get(),
                    timeout=5.0
                )
                if await self._is_connection_healthy(conn):
                    await conn.acquire()
                    return conn
                else:
                    await self._remove_connection(conn)
                    raise RuntimeError("No healthy connections available")
            except asyncio.TimeoutError:
                raise RuntimeError("Connection pool timeout - no connections available")

    async def _return_connection(self, conn: PooledConnection) -> None:
        """Return a connection to the pool."""
        if self._shutdown or conn.is_closing:
            await self._remove_connection(conn)
            return

        # Check if connection is still healthy
        if not await self._is_connection_healthy(conn):
            await self._remove_connection(conn)
            return

        try:
            self._available_connections.put_nowait(conn)
        except asyncio.QueueFull:
            # Pool is full, close this connection
            await self._remove_connection(conn)

    async def _create_connection(self) -> PooledConnection:
        """Create a new connection."""
        connector = aiohttp.TCPConnector(
            limit=1,  # One connection per pooled connection
            ttl_dns_cache=300,
            force_close=False,
            enable_cleanup_closed=True,
            keepalive_timeout=self.keepalive_timeout,
            limit_per_host=1,
        )

        timeout = aiohttp.ClientTimeout(
            total=None,  # No total timeout for streaming
            sock_read=DEFAULT_RESPONSE_TIMEOUT,
            sock_connect=10,
        )

        session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            connector_owner=True,
        )

        conn = PooledConnection(session, connector, self.base_url, self)
        self._all_connections.add(conn)
        self._connection_count += 1

        # Perform initial health check
        if not await conn.health_check():
            await conn.close()
            self._connection_count -= 1
            raise RuntimeError("Failed to create healthy connection")

        logger.debug(f"Created new connection (total: {self._connection_count})")
        return conn

    async def _remove_connection(self, conn: PooledConnection) -> None:
        """Remove a connection from the pool."""
        if conn not in self._all_connections:
            return

        self._all_connections.discard(conn)
        self._connection_count = max(0, self._connection_count - 1)

        # Close the connection without blocking
        asyncio.create_task(conn.close())
        logger.debug(f"Removed connection (total: {self._connection_count})")

    async def _is_connection_healthy(self, conn: PooledConnection) -> bool:
        """Check if a connection is healthy."""
        if conn.is_closing or conn.metrics.failures >= self.max_failures:
            return False

        # Check if connection has been idle too long
        idle_time = time.time() - conn.metrics.last_used
        if idle_time > self.max_idle_time:
            return False

        # Check last health check
        health_check_age = time.time() - conn.metrics.last_health_check
        if health_check_age > self.health_check_interval:
            return await conn.health_check()

        return conn.metrics.is_healthy

    async def _ensure_minimum_connections(self) -> None:
        """Ensure minimum number of connections are available."""
        for _ in range(self.min_connections):
            if self._connection_count >= self.min_connections:
                break

            try:
                conn = await self._create_connection()
                self._available_connections.put_nowait(conn)
            except Exception as e:
                logger.warning(f"Failed to create minimum connection: {e}")
                break

    async def _health_monitor(self) -> None:
        """Background task to monitor connection health."""
        logger.info("Starting connection health monitor")

        while not self._shutdown:
            try:
                await asyncio.sleep(self.health_check_interval)

                if self._shutdown:
                    break

                await self._perform_health_checks()
                await self._ensure_minimum_connections()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(5)  # Brief pause on error

        logger.info("Connection health monitor stopped")

    async def _perform_health_checks(self) -> None:
        """Perform health checks on all connections."""
        connections_to_check = list(self._all_connections)

        # Check connections concurrently
        check_tasks = [
            self._check_single_connection(conn)
            for conn in connections_to_check
            if not conn.is_in_use
        ]

        if check_tasks:
            await asyncio.gather(*check_tasks, return_exceptions=True)

    async def _check_single_connection(self, conn: PooledConnection) -> None:
        """Check a single connection and handle cleanup if needed."""
        try:
            if not await self._is_connection_healthy(conn):
                await self._remove_connection(conn)
        except Exception as e:
            logger.debug(f"Health check error for connection: {e}")
            await self._remove_connection(conn)

    def get_metrics(self) -> Dict[str, Any]:
        """Get pool metrics.

        Returns:
            Dictionary with pool statistics
        """
        connections = list(self._all_connections)
        healthy_count = sum(1 for conn in connections if conn.metrics.is_healthy)

        return {
            "total_connections": len(connections),
            "healthy_connections": healthy_count,
            "available_connections": self._available_connections.qsize(),
            "in_use_connections": sum(1 for conn in connections if conn.is_in_use),
            "min_connections": self.min_connections,
            "max_connections": self.max_connections,
            "shutdown": self._shutdown,
        }


# Global connection pool instance
_global_pool: Optional[OllamaConnectionPool] = None
_pool_lock = asyncio.Lock()


async def get_connection_pool(
    base_url: str = DEFAULT_OLLAMA_URL,
    **kwargs: Any,
) -> OllamaConnectionPool:
    """Get or create the global connection pool.

    Args:
        base_url: Base URL for Ollama API
        **kwargs: Additional arguments for pool initialization

    Returns:
        Global OllamaConnectionPool instance
    """
    async with _pool_lock:
        global _global_pool
        if _global_pool is None:
            _global_pool = OllamaConnectionPool(base_url, **kwargs)
            await _global_pool.__aenter__()
        return _global_pool


async def cleanup_global_pool() -> None:
    """Clean up the global connection pool."""
    async with _pool_lock:
        global _global_pool
        if _global_pool is not None:
            await _global_pool.close()
            _global_pool = None