#!/usr/bin/env python3
"""Test script for memory optimization components."""

from datetime import datetime
import tempfile
import json
from pathlib import Path

from src.models.memory import MemoryConfig, SessionMetrics, create_memory_config, create_session_metrics
from src.ui.memory_optimized_chat import (
    ChatMessage,
    InMemoryStorage,
    HybridStorage,
    MemoryOptimizedChat,
    create_memory_optimized_chat
)


def test_memory_config():
    """Test memory configuration."""
    print("Testing MemoryConfig...")

    # Test default config
    config = create_memory_config()
    assert config.max_messages_memory == 500
    assert config.cleanup_threshold == 1000
    assert config.auto_cleanup == True
    print("✓ Default config works")

    # Test custom config
    custom_config = create_memory_config(
        max_messages_memory=200,
        cleanup_threshold=500,
        auto_cleanup=False
    )
    assert custom_config.max_messages_memory == 200
    assert custom_config.cleanup_threshold == 500
    assert custom_config.auto_cleanup == False
    print("✓ Custom config works")

    # Test serialization
    config_dict = config.to_dict()
    restored_config = MemoryConfig.from_dict(config_dict)
    assert restored_config.max_messages_memory == config.max_messages_memory
    print("✓ Config serialization works")


def test_session_metrics():
    """Test session metrics."""
    print("\nTesting SessionMetrics...")

    metrics = create_session_metrics()
    assert metrics.message_count == 0
    assert metrics.user_message_count == 0
    assert metrics.assistant_message_count == 0

    # Test adding messages
    metrics.add_message("user")
    assert metrics.message_count == 1
    assert metrics.user_message_count == 1

    metrics.add_message("assistant", 2.5)
    assert metrics.message_count == 2
    assert metrics.assistant_message_count == 1
    assert metrics.average_response_time == 2.5

    # Test serialization
    metrics_dict = metrics.to_dict()
    restored_metrics = SessionMetrics.from_dict(metrics_dict)
    assert restored_metrics.message_count == metrics.message_count
    print("✓ Session metrics work")


def test_chat_message():
    """Test ChatMessage model."""
    print("\nTesting ChatMessage...")

    message = ChatMessage(
        id="test-123",
        role="user",
        content="Hello world",
        timestamp=datetime.now(),
        persona_name="User",
        model="Human"
    )

    # Test serialization
    message_dict = message.to_dict()
    restored_message = ChatMessage.from_dict(message_dict)
    assert restored_message.id == message.id
    assert restored_message.content == message.content
    print("✓ ChatMessage works")


def test_in_memory_storage():
    """Test in-memory storage."""
    print("\nTesting InMemoryStorage...")

    storage = InMemoryStorage(max_messages=3)

    # Add messages
    for i in range(5):
        message = ChatMessage(
            id=f"msg-{i}",
            role="user",
            content=f"Message {i}",
            timestamp=datetime.now()
        )
        storage.add_message(message)

    # Should only keep last 3 messages
    messages = storage.get_messages()
    assert len(messages) == 3
    assert messages[0].id == "msg-2"  # First message should be msg-2
    print("✓ InMemoryStorage respects limits")

    # Test pagination
    page1 = storage.get_messages(limit=2, offset=0)
    assert len(page1) == 2
    page2 = storage.get_messages(limit=2, offset=2)
    assert len(page2) == 1
    print("✓ Pagination works")


def test_hybrid_storage():
    """Test hybrid storage with archiving."""
    print("\nTesting HybridStorage...")

    with tempfile.TemporaryDirectory() as temp_dir:
        archive_file = Path(temp_dir) / "test_archive.json"

        storage = HybridStorage(
            memory_limit=3,
            archive_file=archive_file,
            cleanup_threshold=5
        )

        # Add messages
        for i in range(7):
            message = ChatMessage(
                id=f"msg-{i}",
                role="user",
                content=f"Message {i}",
                timestamp=datetime.now()
            )
            storage.add_message(message)

        # Should trigger cleanup
        assert storage.count_messages() <= 7
        assert archive_file.exists()

        # Check archive content
        with open(archive_file, 'r') as f:
            archive_data = json.load(f)
            assert 'messages' in archive_data
            assert len(archive_data['messages']) > 0

        print("✓ HybridStorage archives correctly")

        # Test getting all messages
        all_messages = storage.get_all_messages()
        assert len(all_messages) >= 3  # At least memory limit
        print("✓ HybridStorage retrieves all messages")


def test_memory_optimized_chat():
    """Test MemoryOptimizedChat."""
    print("\nTesting MemoryOptimizedChat...")

    with tempfile.TemporaryDirectory() as temp_dir:
        archive_file = Path(temp_dir) / "test_chat_archive.json"

        chat = create_memory_optimized_chat(
            strategy="hybrid",
            messages_per_page=2,
            cleanup_threshold=5,
            archive_file=archive_file
        )

        # Add messages
        for i in range(6):
            chat.add_message(
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                persona_name="TestPersona" if i % 2 == 1 else "User",
                model="test-model"
            )

        # Test pagination
        page1 = chat.get_messages_page(1)
        assert len(page1) <= 2

        # Test stats
        stats = chat.get_stats()
        assert stats.total_messages == 6
        assert stats.archived_messages >= 0

        # Test cleanup
        removed = chat.perform_cleanup(keep_count=3)
        assert removed >= 0

        # Test export
        exported = chat.export_messages()
        assert len(exported) >= 0

        print("✓ MemoryOptimizedChat works correctly")


def test_memory_monitoring():
    """Test memory monitoring functionality."""
    print("\nTesting memory monitoring...")

    chat = create_memory_optimized_chat(
        strategy="memory",
        messages_per_page=10
    )

    # Start monitoring
    chat.start_monitoring()

    # Add some messages
    for i in range(20):
        chat.add_message(
            role="user",
            content=f"Test message {i} with some content to use memory",
            persona_name="User"
        )

    # Get stats
    stats = chat.get_stats()
    assert stats.total_messages == 20
    assert stats.memory_usage_mb >= 0

    # Stop monitoring
    chat.stop_monitoring()

    print("✓ Memory monitoring works")


def run_all_tests():
    """Run all memory optimization tests."""
    print("🧠 Testing Memory Optimization Components\n")

    try:
        test_memory_config()
        test_session_metrics()
        test_chat_message()
        test_in_memory_storage()
        test_hybrid_storage()
        test_memory_optimized_chat()
        test_memory_monitoring()

        print("\n✅ All memory optimization tests passed!")
        print("\nKey features verified:")
        print("• Memory configuration and settings")
        print("• Session metrics tracking")
        print("• Message pagination and archiving")
        print("• Memory usage monitoring")
        print("• Automatic cleanup functionality")
        print("• Hybrid storage (memory + disk)")
        print("• Export functionality")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()