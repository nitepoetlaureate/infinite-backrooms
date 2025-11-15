#!/usr/bin/env python3
"""Performance benchmarking script for Infinite Backrooms.

This script tests various performance aspects of the application:
- CSS loading time
- Constants caching
- Message rendering
- Ollama client connection pooling
- Overall application startup time
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.ollama_client import OllamaClient
from src.services.ollama_client_optimized import OllamaClientOptimized, OllamaSessionManager
from src.utils.constants import DEFAULT_OLLAMA_URL, ROLE_TEMPLATES, ROLE_EMOJI_MAP
from src.utils.performance import PerformanceTimer, get_metrics


def benchmark_css_loading() -> None:
    """Benchmark CSS file loading."""
    print("\n=== CSS Loading Benchmark ===")

    css_file = project_root / "static" / "css" / "system.css"
    if not css_file.exists():
        print(f"WARNING: CSS file not found at {css_file}")
        return

    # Test uncached loading
    with PerformanceTimer("css_load_uncached") as timer:
        with open(css_file, "r") as f:
            content = f.read()
    print(f"Uncached CSS load: {timer.duration * 1000:.2f}ms ({len(content)} bytes)")

    # Test cached loading (simulate)
    loads = []
    for i in range(10):
        start = time.perf_counter()
        with open(css_file, "r") as f:
            _ = f.read()
        loads.append(time.perf_counter() - start)

    avg_time = sum(loads) / len(loads) * 1000
    print(f"Average load time (10 runs): {avg_time:.2f}ms")


def benchmark_constants_access() -> None:
    """Benchmark constants and template access."""
    print("\n=== Constants Access Benchmark ===")

    # Test role templates access
    iterations = 10000
    with PerformanceTimer("role_templates_access") as timer:
        for _ in range(iterations):
            _ = ROLE_TEMPLATES.copy()

    per_access = timer.duration / iterations * 1000000
    print(f"Role templates copy ({iterations} times): {timer.duration * 1000:.2f}ms")
    print(f"Per-access time: {per_access:.2f}μs")

    # Test emoji map access
    with PerformanceTimer("emoji_map_access") as timer:
        for _ in range(iterations):
            _ = ROLE_EMOJI_MAP.copy()

    per_access = timer.duration / iterations * 1000000
    print(f"Emoji map copy ({iterations} times): {timer.duration * 1000:.2f}ms")
    print(f"Per-access time: {per_access:.2f}μs")


async def benchmark_ollama_client_original() -> None:
    """Benchmark original Ollama client."""
    print("\n=== Original Ollama Client Benchmark ===")

    # Test connection establishment
    with PerformanceTimer("original_client_connect") as timer:
        async with OllamaClient(DEFAULT_OLLAMA_URL) as client:
            connected, models = await client.test_connection()

    print(f"Connection + test: {timer.duration * 1000:.2f}ms")
    print(f"Connected: {connected}, Models: {len(models) if connected else 0}")

    if not connected:
        print("WARNING: Cannot connect to Ollama. Skipping client benchmarks.")
        return

    # Test multiple sequential connections
    times = []
    for i in range(5):
        start = time.perf_counter()
        async with OllamaClient(DEFAULT_OLLAMA_URL) as client:
            await client.test_connection()
        times.append(time.perf_counter() - start)

    avg_time = sum(times) / len(times) * 1000
    print(f"Average connection time (5 runs): {avg_time:.2f}ms")


async def benchmark_ollama_client_optimized() -> None:
    """Benchmark optimized Ollama client."""
    print("\n=== Optimized Ollama Client Benchmark ===")

    # Test connection establishment
    with PerformanceTimer("optimized_client_connect") as timer:
        async with OllamaClientOptimized(DEFAULT_OLLAMA_URL) as client:
            connected, models = await client.test_connection()

    print(f"Connection + test: {timer.duration * 1000:.2f}ms")
    print(f"Connected: {connected}, Models: {len(models) if connected else 0}")

    if not connected:
        print("WARNING: Cannot connect to Ollama. Skipping optimized client benchmarks.")
        return

    # Test multiple sequential connections
    times = []
    for i in range(5):
        start = time.perf_counter()
        async with OllamaClientOptimized(DEFAULT_OLLAMA_URL) as client:
            await client.test_connection()
        times.append(time.perf_counter() - start)

    avg_time = sum(times) / len(times) * 1000
    print(f"Average connection time (5 runs): {avg_time:.2f}ms")

    # Test session manager (best performance)
    print("\n--- Session Manager (Reused Connection) ---")
    client = await OllamaSessionManager.get_client(DEFAULT_OLLAMA_URL)

    times = []
    for i in range(10):
        start = time.perf_counter()
        await client.test_connection()
        times.append(time.perf_counter() - start)

    avg_time = sum(times) / len(times) * 1000
    print(f"Average test_connection time with reused session (10 runs): {avg_time:.2f}ms")

    await OllamaSessionManager.cleanup()


def benchmark_message_rendering_simulation() -> None:
    """Simulate message rendering performance."""
    print("\n=== Message Rendering Simulation ===")

    # Create mock messages
    messages = []
    for i in range(100):
        messages.append({
            "role": "assistant" if i % 2 == 0 else "user",
            "content": f"This is message {i} with some content that might include @mentions and other text.",
            "timestamp": "2024-01-01 12:00:00",
            "persona_name": f"Persona{i % 3}",
            "model": "test-model",
        })

    # Simulate rendering time (just string operations)
    with PerformanceTimer("render_100_messages") as timer:
        for msg in messages:
            # Simulate what happens in rendering
            _ = msg["content"]
            _ = msg["timestamp"]
            if msg["role"] == "assistant":
                _ = msg["persona_name"]
                _ = msg["model"]

    print(f"Render 100 messages: {timer.duration * 1000:.2f}ms")
    print(f"Per-message time: {timer.duration / len(messages) * 1000:.2f}ms")

    # Test with 500 messages
    large_messages = messages * 5
    with PerformanceTimer("render_500_messages") as timer:
        for msg in large_messages:
            _ = msg["content"]
            _ = msg["timestamp"]
            if msg["role"] == "assistant":
                _ = msg["persona_name"]
                _ = msg["model"]

    print(f"Render 500 messages: {timer.duration * 1000:.2f}ms")
    print(f"Per-message time: {timer.duration / len(large_messages) * 1000:.2f}ms")


def print_performance_summary() -> None:
    """Print summary of all performance metrics."""
    print("\n" + "=" * 60)
    print("PERFORMANCE METRICS SUMMARY")
    print("=" * 60)

    metrics = get_metrics()
    stats = metrics.get_stats()

    if not stats["timings"]:
        print("No metrics collected.")
        return

    print("\nOperation Timings:")
    print("-" * 60)

    for operation, data in sorted(stats["timings"].items()):
        print(f"\n{operation}:")
        print(f"  Total calls: {data['count']}")
        print(f"  Average:     {data['average'] * 1000:.2f}ms")
        print(f"  Min:         {data['min'] * 1000:.2f}ms")
        print(f"  Max:         {data['max'] * 1000:.2f}ms")
        print(f"  Total time:  {data['total'] * 1000:.2f}ms")

    if stats["counters"]:
        print("\nCounters:")
        print("-" * 60)
        for counter, value in sorted(stats["counters"].items()):
            print(f"  {counter}: {value}")


async def main() -> None:
    """Run all benchmarks."""
    print("=" * 60)
    print("INFINITE BACKROOMS PERFORMANCE BENCHMARK")
    print("=" * 60)
    print(f"Project root: {project_root}")

    # Run synchronous benchmarks
    benchmark_css_loading()
    benchmark_constants_access()
    benchmark_message_rendering_simulation()

    # Run async benchmarks
    await benchmark_ollama_client_original()
    await benchmark_ollama_client_optimized()

    # Print summary
    print_performance_summary()

    print("\n" + "=" * 60)
    print("BENCHMARK COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
