#!/usr/bin/env python3
"""Test script to verify Streamlit async fixes work correctly.

This script tests the Streamlit-safe async execution patterns
to ensure they work without event loop corruption.
"""

import asyncio
import time
from typing import Generator

from src.services.ollama_client_streamlit import StreamlitOllamaClient
from src.utils.streamlit_async import StreamlitAsyncExecutor, run_async_safely


async def test_async_function():
    """Simple async function for testing."""
    await asyncio.sleep(0.1)
    return "async result"


async def test_async_generator():
    """Simple async generator for testing."""
    for i in range(3):
        await asyncio.sleep(0.05)
        yield f"chunk {i}"


def test_streamlit_async_executor():
    """Test StreamlitAsyncExecutor works correctly."""
    print("Testing StreamlitAsyncExecutor...")

    executor = StreamlitAsyncExecutor()

    # Test basic async execution
    result = executor.run_async(test_async_function())
    assert result == "async result", f"Expected 'async result', got {result}"
    print("✓ Basic async execution works")

    # Test async generator
    results = list(executor.run_async_stream(test_async_generator()))
    expected = ["chunk 0", "chunk 1", "chunk 2"]
    assert results == expected, f"Expected {expected}, got {results}"
    print("✓ Async generator execution works")

    executor.shutdown()
    print("✓ StreamlitAsyncExecutor test passed")


def test_streamlit_ollama_client():
    """Test StreamlitOllamaClient works correctly."""
    print("\nTesting StreamlitOllamaClient...")

    client = StreamlitOllamaClient()

    # Test connection (this may fail if Ollama is not running)
    try:
        connected, models = client.test_connection()
        print(f"✓ Connection test completed: connected={connected}, models={len(models)}")

        if connected and models:
            # Test streaming with actual model (just first few chunks)
            print(f"✓ Testing streaming with model: {models[0]}")
            chunk_count = 0
            for chunk in client.generate_stream(models[0], "Say hello"):
                chunk_count += 1
                print(f"  Chunk {chunk_count}: {chunk['type']}")
                if chunk_count >= 3:  # Just test first few chunks
                    break
            print("✓ Streaming test completed")

    except Exception as e:
        print(f"⚠ Ollama connection test failed (expected if Ollama not running): {e}")


def test_run_async_safely():
    """Test the convenience function works correctly."""
    print("\nTesting run_async_safely...")

    result = run_async_safely(test_async_function())
    assert result == "async result", f"Expected 'async result', got {result}"
    print("✓ run_async_safely works correctly")


def test_no_event_loop_corruption():
    """Test that repeated async operations don't corrupt event loop."""
    print("\nTesting for event loop corruption...")

    for i in range(10):
        result = run_async_safely(test_async_function())
        assert result == "async result", f"Iteration {i}: Expected 'async result', got {result}"

    print("✓ No event loop corruption detected after 10 iterations")


def benchmark_async_execution():
    """Benchmark the performance of async execution."""
    print("\nBenchmarking async execution...")

    async def slow_function():
        await asyncio.sleep(0.1)
        return "slow result"

    # Time the safe execution
    start = time.time()
    for _ in range(5):
        result = run_async_safely(slow_function())
        assert result == "slow result"
    duration = time.time() - start

    print(f"✓ 5 slow async operations completed in {duration:.2f} seconds")
    print(f"✓ Average per operation: {duration/5:.3f} seconds")


if __name__ == "__main__":
    print("🔧 Testing Streamlit Async Fixes")
    print("=" * 50)

    try:
        test_streamlit_async_executor()
        test_streamlit_ollama_client()
        test_run_async_safely()
        test_no_event_loop_corruption()
        benchmark_async_execution()

        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("Streamlit async fixes are working correctly.")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()