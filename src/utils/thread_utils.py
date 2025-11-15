"""Thread utility functions for the Infinite Backrooms application.

Provides thread-safe operations, thread pool management,
and async-to-sync bridging utilities.
"""

from __future__ import annotations

import concurrent.futures
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, Future
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, Union
from queue import Queue, Empty
import weakref


class ThreadSafeCounter:
    """Thread-safe counter for tracking shared state."""

    def __init__(self, initial_value: int = 0):
        """Initialize thread-safe counter.

        Args:
            initial_value: Initial counter value
        """
        self._value = initial_value
        self._lock = threading.Lock()

    def increment(self, amount: int = 1) -> int:
        """Increment counter by specified amount.

        Args:
            amount: Amount to increment by

        Returns:
            New counter value
        """
        with self._lock:
            self._value += amount
            return self._value

    def decrement(self, amount: int = 1) -> int:
        """Decrement counter by specified amount.

        Args:
            amount: Amount to decrement by

        Returns:
            New counter value
        """
        with self._lock:
            self._value -= amount
            return self._value

    def get(self) -> int:
        """Get current counter value.

        Returns:
            Current counter value
        """
        with self._lock:
            return self._value

    def set(self, value: int) -> None:
        """Set counter to specific value.

        Args:
            value: Value to set
        """
        with self._lock:
            self._value = value


class ThreadSafeDict:
    """Thread-safe dictionary for shared state."""

    def __init__(self, initial_dict: Optional[Dict] = None):
        """Initialize thread-safe dictionary.

        Args:
            initial_dict: Initial dictionary data
        """
        self._data = initial_dict or {}
        self._lock = threading.Lock()

    def get(self, key: str, default: Any = None) -> Any:
        """Get value by key.

        Args:
            key: Dictionary key
            default: Default value if key not found

        Returns:
            Value or default
        """
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set value by key.

        Args:
            key: Dictionary key
            value: Value to set
        """
        with self._lock:
            self._data[key] = value

    def delete(self, key: str) -> None:
        """Delete key from dictionary.

        Args:
            key: Key to delete
        """
        with self._lock:
            self._data.pop(key, None)

    def keys(self) -> List[str]:
        """Get all keys.

        Returns:
            List of keys
        """
        with self._lock:
            return list(self._data.keys())

    def values(self) -> List[Any]:
        """Get all values.

        Returns:
            List of values
        """
        with self._lock:
            return list(self._data.values())

    def items(self) -> List[tuple]:
        """Get all key-value pairs.

        Returns:
            List of (key, value) tuples
        """
        with self._lock:
            return list(self._data.items())

    def clear(self) -> None:
        """Clear all data."""
        with self._lock:
            self._data.clear()


class ThreadPoolManager:
    """Manager for thread pool lifecycle and resource management."""

    def __init__(self, max_workers: int = 4):
        """Initialize thread pool manager.

        Args:
            max_workers: Maximum number of worker threads
        """
        self.max_workers = max_workers
        self._executor: Optional[ThreadPoolExecutor] = None
        self._active_futures: List[Future] = []
        self._lock = threading.Lock()
        self._shutdown_event = threading.Event()

    def get_executor(self) -> ThreadPoolExecutor:
        """Get or create thread pool executor.

        Returns:
            ThreadPoolExecutor instance
        """
        if self._executor is None or self._executor._shutdown:
            with self._lock:
                if self._executor is None or self._executor._shutdown:
                    self._executor = ThreadPoolExecutor(
                        max_workers=self.max_workers,
                        thread_name_prefix="backroom_worker"
                    )
        return self._executor

    def submit_task(
        self,
        func: Callable,
        *args,
        callback: Optional[Callable] = None,
        **kwargs
    ) -> Future:
        """Submit task to thread pool.

        Args:
            func: Function to execute
            *args: Arguments to pass to function
            callback: Optional callback for completion
            **kwargs: Keyword arguments to pass to function

        Returns:
            Future representing the task
        """
        executor = self.get_executor()

        def wrapped_func():
            try:
                result = func(*args, **kwargs)
                if callback:
                    callback(result)
                return result
            except Exception as e:
                if callback:
                    callback(e)
                raise

        future = executor.submit(wrapped_func)

        with self._lock:
            self._active_futures.append(future)

        return future

    def wait_for_completion(
        self,
        timeout: Optional[float] = None,
        return_when: str = "ALL_COMPLETED"
    ) -> List[Future]:
        """Wait for active tasks to complete.

        Args:
            timeout: Maximum time to wait
            return_when: When to return (ALL_COMPLETED, FIRST_COMPLETED, FIRST_EXCEPTION)

        Returns:
            List of completed futures
        """
        with self._lock:
            futures = self._active_futures.copy()

        if not futures:
            return []

        try:
            completed = concurrent.futures.wait(
                futures,
                timeout=timeout,
                return_when=getattr(concurrent.futures, return_when, concurrent.futures.ALL_COMPLETED)
            )
            return list(completed.done)
        except Exception as e:
            print(f"Error waiting for futures: {e}")
            return []

    def cancel_all_tasks(self) -> int:
        """Cancel all active tasks.

        Returns:
            Number of tasks cancelled
        """
        cancelled_count = 0
        with self._lock:
            for future in self._active_futures:
                if future.cancel():
                    cancelled_count += 1
            self._active_futures.clear()
        return cancelled_count

    def cleanup_completed_tasks(self) -> int:
        """Remove completed tasks from active list.

        Returns:
            Number of tasks removed
        """
        removed_count = 0
        with self._lock:
            remaining_futures = []
            for future in self._active_futures:
                if future.done():
                    removed_count += 1
                else:
                    remaining_futures.append(future)
            self._active_futures = remaining_futures
        return removed_count

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown thread pool manager.

        Args:
            wait: Whether to wait for tasks to complete
        """
        self._shutdown_event.set()
        if self._executor:
            self._executor.shutdown(wait=wait)

    def get_active_task_count(self) -> int:
        """Get number of active tasks.

        Returns:
            Number of active tasks
        """
        with self._lock:
            return len(self._active_futures)

    def get_thread_info(self) -> Dict[str, Any]:
        """Get thread pool information.

        Returns:
            Dictionary with thread pool info
        """
        active_threads = threading.active_count()
        current_thread = threading.current_thread().name

        return {
            "active_threads": active_threads,
            "current_thread": current_thread,
            "max_workers": self.max_workers,
            "active_tasks": self.get_active_task_count(),
            "executor_exists": self._executor is not None and not self._executor._shutdown
        }


# Global thread pool manager
_thread_pool_manager = ThreadPoolManager()


def get_thread_pool_manager() -> ThreadPoolManager:
    """Get global thread pool manager.

    Returns:
        ThreadPoolManager instance
    """
    return _thread_pool_manager


class EventLoopManager:
    """Manager for handling async operations in threaded environment."""

    def __init__(self):
        """Initialize event loop manager."""
        self._loops: Dict[int, asyncio.AbstractEventLoop] = {}
        self._lock = threading.Lock()

    def get_loop_for_thread(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop for current thread.

        Returns:
            Event loop for current thread
        """
        thread_id = threading.get_ident()

        with self._lock:
            if thread_id not in self._loops:
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                self._loops[thread_id] = loop

            return self._loops[thread_id]

    def run_async_in_thread(
        self,
        coro,
        timeout: Optional[float] = None
    ) -> Any:
        """Run coroutine in thread with event loop.

        Args:
            coro: Coroutine to run
            timeout: Optional timeout

        Returns:
            Result of coroutine
        """
        loop = self.get_loop_for_thread()

        if timeout:
            return loop.run_until_complete(asyncio.wait_for(coro, timeout=timeout))
        else:
            return loop.run_until_complete(coro)

    def cleanup_thread_loop(self) -> None:
        """Cleanup event loop for current thread."""
        thread_id = threading.get_ident()

        with self._lock:
            if thread_id in self._loops:
                loop = self._loops[thread_id]
                if not loop.is_closed():
                    loop.close()
                del self._loops[thread_id]


# Global event loop manager
_event_loop_manager = EventLoopManager()


def get_event_loop_manager() -> EventLoopManager:
    """Get global event loop manager.

    Returns:
        EventLoopManager instance
    """
    return _event_loop_manager


class BackgroundTask:
    """Background task with progress tracking and cancellation support."""

    def __init__(
        self,
        func: Callable,
        *args,
        name: str = "BackgroundTask",
        progress_callback: Optional[Callable] = None,
        **kwargs
    ):
        """Initialize background task.

        Args:
            func: Function to run in background
            *args: Arguments for function
            name: Task name for identification
            progress_callback: Optional progress callback
            **kwargs: Keyword arguments for function
        """
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.name = name
        self.progress_callback = progress_callback
        self.future: Optional[Future] = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self._cancelled = False
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start the background task."""
        def wrapped_func():
            try:
                with self._lock:
                    if self._cancelled:
                        raise concurrent.futures.CancelledError("Task was cancelled")
                    self.start_time = time.time()

                result = self.func(*self.args, **self.kwargs)

                with self._lock:
                    self.end_time = time.time()

                return result
            except Exception as e:
                with self._lock:
                    self.end_time = time.time()
                raise e

        manager = get_thread_pool_manager()
        self.future = manager.submit_task(wrapped_func)

    def cancel(self) -> bool:
        """Cancel the background task.

        Returns:
            True if cancelled successfully
        """
        with self._lock:
            if self._cancelled:
                return True

            if self.future and not self.future.done():
                self._cancelled = True
                return self.future.cancel()

        self._cancelled = True
        return False

    def is_cancelled(self) -> bool:
        """Check if task was cancelled.

        Returns:
            True if cancelled
        """
        return self._cancelled or (self.future and self.future.cancelled())

    def is_done(self) -> bool:
        """Check if task is completed.

        Returns:
            True if completed
        """
        return self.future is not None and self.future.done()

    def result(self, timeout: Optional[float] = None) -> Any:
        """Get task result.

        Args:
            timeout: Maximum time to wait for result

        Returns:
            Task result
        """
        if not self.future:
            raise RuntimeError("Task not started")
        return self.future.result(timeout=timeout)

    def progress(self) -> float:
        """Get task progress (0.0 to 1.0).

        Returns:
            Progress percentage
        """
        if self.progress_callback:
            try:
                return self.progress_callback()
            except:
                pass
        return 0.0

    def elapsed_time(self) -> float:
        """Get elapsed time since task started.

        Returns:
            Elapsed time in seconds
        """
        if self.start_time:
            if self.end_time:
                return self.end_time - self.start_time
            else:
                return time.time() - self.start_time
        return 0.0


class TaskQueue:
    """Thread-safe task queue for background processing."""

    def __init__(self, max_size: int = 100):
        """Initialize task queue.

        Args:
            max_size: Maximum queue size
        """
        self._queue = Queue(maxsize=max_size)
        self._workers: List[threading.Thread] = []
        self._shutdown_event = threading.Event()
        self._lock = threading.Lock()

    def add_task(
        self,
        func: Callable,
        *args,
        priority: int = 0,
        **kwargs
    ) -> None:
        """Add task to queue.

        Args:
            func: Function to execute
            *args: Function arguments
            priority: Task priority (higher = more important)
            **kwargs: Function keyword arguments
        """
        task = {
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "priority": priority,
            "timestamp": time.time()
        }

        try:
            self._queue.put(task, timeout=1.0)
        except:
            raise RuntimeError("Task queue is full")

    def start_workers(self, num_workers: int = 2) -> None:
        """Start worker threads.

        Args:
            num_workers: Number of worker threads to start
        """
        with self._lock:
            for _ in range(num_workers):
                worker = threading.Thread(
                    target=self._worker_loop,
                    name=f"TaskQueueWorker-{len(self._workers)}"
                )
                worker.daemon = True
                worker.start()
                self._workers.append(worker)

    def stop_workers(self) -> None:
        """Stop all worker threads."""
        self._shutdown_event.set()
        for worker in self._workers:
            worker.join(timeout=5.0)
        self._workers.clear()

    def _worker_loop(self) -> None:
        """Worker thread main loop."""
        while not self._shutdown_event.is_set():
            try:
                task = self._queue.get(timeout=1.0)
                try:
                    func = task["func"]
                    args = task["args"]
                    kwargs = task["kwargs"]
                    func(*args, **kwargs)
                except Exception as e:
                    print(f"Task execution error: {e}")
                    traceback.print_exc()
                finally:
                    self._queue.task_done()
            except Empty:
                continue

    def get_queue_size(self) -> int:
        """Get current queue size.

        Returns:
            Number of tasks in queue
        """
        return self._queue.qsize()

    def get_worker_count(self) -> int:
        """Get number of active workers.

        Returns:
            Number of worker threads
        """
        with self._lock:
            return len(self._workers)


@contextmanager
def background_thread_context():
    """Context manager for background thread operations."""
    manager = get_thread_pool_manager()
    try:
        yield manager
    finally:
        manager.cleanup_completed_tasks()


def run_in_background(
    func: Callable,
    *args,
    timeout: Optional[float] = None,
    **kwargs
) -> Any:
    """Run function in background thread and wait for result.

    Args:
        func: Function to run
        *args: Function arguments
        timeout: Optional timeout
        **kwargs: Function keyword arguments

    Returns:
        Function result
    """
    task = BackgroundTask(func, *args, **kwargs)
    task.start()
    return task.result(timeout=timeout)


def debounce(
    delay: float,
    key: Optional[str] = None
) -> Callable:
    """Decorator to debounce function calls.

    Args:
        delay: Delay in seconds
        key: Optional key for debouncing (defaults to function name)

    Returns:
        Decorated function
    """
    if key is None:
        key = "debounce_default"

    last_call_time = ThreadSafeDict()

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            current_time = time.time()
            last_time = last_call_time.get(key, 0)

            if current_time - last_time >= delay:
                last_call_time.set(key, current_time)
                return func(*args, **kwargs)

        return wrapper
    return decorator


def throttle(
    calls_per_second: float,
    key: Optional[str] = None
) -> Callable:
    """Decorator to throttle function calls.

    Args:
        calls_per_second: Maximum calls per second
        key: Optional key for throttling (defaults to function name)

    Returns:
        Decorated function
    """
    if key is None:
        key = "throttle_default"

    call_times = ThreadSafeDict()

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            current_time = time.time()
            min_interval = 1.0 / calls_per_second

            last_time = call_times.get(key, 0)
            if current_time - last_time >= min_interval:
                call_times.set(key, current_time)
                return func(*args, **kwargs)

        return wrapper
    return decorator


def get_thread_dump() -> Dict[str, Any]:
    """Get current thread dump for debugging.

    Returns:
        Dictionary with thread information
    """
    threads = {}
    for thread in threading.enumerate():
        threads[thread.name] = {
            "id": thread.ident,
            "alive": thread.is_alive(),
            "daemon": thread.daemon,
            "native_id": getattr(thread, 'native_id', None)
        }

    return {
        "active_count": threading.active_count(),
        "current_thread": threading.current_thread().name,
        "main_thread": threading.main_thread().name,
        "threads": threads
    }


def cleanup_thread_resources() -> None:
    """Cleanup thread-related resources."""
    # Cleanup event loops
    get_event_loop_manager().cleanup_thread_loop()

    # Cleanup thread pool
    get_thread_pool_manager().cleanup_completed_tasks()


# Thread cleanup at exit
import atexit
atexit.register(cleanup_thread_resources)