"""Tests for ConversationLogger."""

# Import from the main module - adjust if needed based on final structure
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from streamlit_backroom import ConversationLogger


class TestConversationLogger:
    """Test ConversationLogger functionality."""

    def test_logger_initialization(self):
        """Test logger creates directory on initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)
            assert logger.log_dir.exists()
            assert logger.log_dir.is_dir()

    def test_clean_message_removes_thinking_tags(self):
        """Test that thinking tags are properly removed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)

            # Test simple thinking tag
            message = "Hello <think>internal thought</think> world!"
            cleaned = logger.clean_message(message)
            assert "<think>" not in cleaned
            assert "</think>" not in cleaned
            assert "Hello world!" in cleaned

            # Test nested thinking tags
            message_nested = "<think>outer <think>inner</think> thought</think> text"
            cleaned_nested = logger.clean_message(message_nested)
            assert "<think>" not in cleaned_nested
            assert "text" in cleaned_nested

    def test_log_message_creates_file(self):
        """Test that log_message creates a file and writes content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)
            logger.log_message("TestPersona", "Test message")

            log_file = logger.get_daily_log_file()
            assert log_file.exists()

            content = log_file.read_text()
            assert "TestPersona$" in content
            assert "Test message" in content

    def test_log_message_skips_empty_content(self):
        """Test that empty messages after cleaning are not logged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)

            # Message that becomes empty after cleaning
            logger.log_message("TestPersona", "<think>only thinking</think>")

            log_file = logger.get_daily_log_file()
            # File should not exist or be empty
            if log_file.exists():
                content = log_file.read_text()
                assert content.strip() == ""

    def test_daily_log_file_naming(self):
        """Test that log files are named correctly with date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)
            log_file = logger.get_daily_log_file()

            today = datetime.now().strftime("%Y-%m-%d")
            expected_name = f"streamlit_backroom_{today}.txt"

            assert log_file.name == expected_name
