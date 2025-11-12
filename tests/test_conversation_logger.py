"""Tests for ConversationLogger class"""

import pytest
from pathlib import Path
from datetime import datetime
from streamlit_backroom import ConversationLogger
import tempfile
import shutil


class TestConversationLogger:
    """Test conversation logging functionality"""

    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory for test logs"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def logger(self, temp_log_dir):
        """Create a logger instance with temp directory"""
        return ConversationLogger(log_dir=temp_log_dir)

    def test_logger_creates_directory(self, temp_log_dir):
        """Ensure log directory is created if it doesn't exist"""
        log_dir = Path(temp_log_dir) / "new_logs"
        assert not log_dir.exists()

        logger = ConversationLogger(log_dir=str(log_dir))
        assert log_dir.exists()
        assert log_dir.is_dir()

    def test_get_daily_log_file(self, logger):
        """Test that daily log file path is generated correctly"""
        log_file = logger.get_daily_log_file()
        today = datetime.now().strftime("%Y-%m-%d")

        assert isinstance(log_file, Path)
        assert f"streamlit_backroom_{today}.txt" in str(log_file)

    def test_clean_message_removes_thinking_tags(self, logger):
        """Test that <think> tags are removed from messages"""
        message_with_thinking = "Start <think>internal thoughts</think> End"
        cleaned = logger.clean_message(message_with_thinking)

        assert '<think>' not in cleaned
        assert '</think>' not in cleaned
        assert 'internal thoughts' not in cleaned
        assert 'Start' in cleaned
        assert 'End' in cleaned

    def test_clean_message_handles_nested_thinking_tags(self, logger):
        """Test cleaning of nested thinking tags"""
        message = "Text <think>outer <think>inner</think> outer</think> more text"
        cleaned = logger.clean_message(message)

        assert '<think>' not in cleaned
        assert '</think>' not in cleaned
        assert 'Text' in cleaned
        assert 'more text' in cleaned

    def test_clean_message_normalizes_whitespace(self, logger):
        """Test that excessive whitespace is normalized"""
        message = "Hello    world   with   spaces"
        cleaned = logger.clean_message(message)

        assert '    ' not in cleaned
        assert 'Hello world with spaces' == cleaned

    def test_log_message_writes_to_file(self, logger):
        """Test that messages are written to log file"""
        test_persona = "TestBot"
        test_message = "Hello, this is a test message"

        logger.log_message(test_persona, test_message)

        log_file = logger.get_daily_log_file()
        assert log_file.exists()

        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()

        assert test_persona in content
        assert test_message in content
        assert '$' in content  # Message delimiter

    def test_log_message_includes_timestamp(self, logger):
        """Test that log messages include timestamps"""
        test_persona = "TimestampBot"
        test_message = "Testing timestamp"
        test_time = datetime(2025, 1, 15, 14, 30, 45)

        logger.log_message(test_persona, test_message, timestamp=test_time)

        log_file = logger.get_daily_log_file()
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()

        assert '[14:30:45]' in content

    def test_log_message_cleans_before_logging(self, logger):
        """Test that messages are cleaned before being logged"""
        test_persona = "ThinkingBot"
        test_message = "Message <think>should not appear</think> visible"

        logger.log_message(test_persona, test_message)

        log_file = logger.get_daily_log_file()
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()

        assert '<think>' not in content
        assert 'should not appear' not in content
        assert 'visible' in content

    def test_log_message_skips_empty_cleaned_messages(self, logger):
        """Test that empty messages after cleaning are not logged"""
        test_persona = "EmptyBot"
        test_message = "<think>only thinking, no content</think>"

        logger.log_message(test_persona, test_message)

        log_file = logger.get_daily_log_file()

        # File might not exist if this is the only message
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            assert test_persona not in content

    def test_log_message_appends_to_existing_file(self, logger):
        """Test that multiple messages are appended to the same file"""
        persona1 = "Bot1"
        persona2 = "Bot2"
        message1 = "First message"
        message2 = "Second message"

        logger.log_message(persona1, message1)
        logger.log_message(persona2, message2)

        log_file = logger.get_daily_log_file()
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()

        assert persona1 in content
        assert persona2 in content
        assert message1 in content
        assert message2 in content

    def test_log_message_handles_unicode(self, logger):
        """Test that unicode characters are properly logged"""
        test_persona = "UnicodeBot"
        test_message = "Hello 世界 🌍 Привет"

        logger.log_message(test_persona, test_message)

        log_file = logger.get_daily_log_file()
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()

        assert '世界' in content
        assert '🌍' in content
        assert 'Привет' in content
