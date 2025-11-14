"""Tests for ConversationLogger class."""

from datetime import datetime

from src.services.logger import ConversationLogger


class TestConversationLogger:
    """Test ConversationLogger functionality."""

    def test_logger_initialization(self, temp_log_dir):
        """Test logger initialization creates directory."""
        logger = ConversationLogger(log_dir=str(temp_log_dir))
        assert logger.log_dir == temp_log_dir
        assert temp_log_dir.exists()

    def test_logger_creates_directory_if_not_exists(self, tmp_path):
        """Test logger creates log directory if it doesn't exist."""
        log_dir = tmp_path / "new_logs"
        assert not log_dir.exists()

        _logger = ConversationLogger(log_dir=str(log_dir))
        assert log_dir.exists()

    def test_get_daily_log_file(self, conversation_logger):
        """Test getting daily log file path."""
        log_file = conversation_logger.get_daily_log_file()
        today = datetime.now().strftime("%Y-%m-%d")
        expected_name = f"streamlit_backroom_{today}.txt"

        assert log_file.name == expected_name
        assert log_file.parent == conversation_logger.log_dir

    def test_log_message_creates_file(self, conversation_logger, temp_log_dir):
        """Test logging a message creates the log file."""
        conversation_logger.log_message("TestBot", "Hello world")

        log_files = list(temp_log_dir.glob("*.txt"))
        assert len(log_files) == 1

    def test_log_message_content(self, conversation_logger, temp_log_dir):
        """Test logged message has correct format."""
        test_time = datetime(2024, 1, 1, 12, 30, 45)
        conversation_logger.log_message("TestBot", "Hello world", timestamp=test_time)

        log_file = conversation_logger.get_daily_log_file()
        content = log_file.read_text()

        assert "TestBot" in content
        assert "Hello world" in content
        assert "12:30:45" in content
        assert "$" in content  # Format separator

    def test_log_multiple_messages(self, conversation_logger, temp_log_dir):
        """Test logging multiple messages appends to same file."""
        conversation_logger.log_message("Alice", "First message")
        conversation_logger.log_message("Bob", "Second message")
        conversation_logger.log_message("Charlie", "Third message")

        log_file = conversation_logger.get_daily_log_file()
        content = log_file.read_text()
        lines = content.strip().split("\n")

        assert len(lines) == 3
        assert "Alice" in lines[0]
        assert "Bob" in lines[1]
        assert "Charlie" in lines[2]

    def test_clean_message_removes_thinking_tags(self, conversation_logger):
        """Test that thinking tags are removed from messages."""
        message_with_thinking = (
            "Here is my thought: <think>internal reasoning</think> And my conclusion."
        )
        cleaned = conversation_logger.clean_message(message_with_thinking)

        assert "<think>" not in cleaned
        assert "</think>" not in cleaned
        assert "internal reasoning" not in cleaned
        assert "Here is my thought:" in cleaned
        assert "And my conclusion." in cleaned

    def test_clean_message_removes_nested_thinking_tags(self, conversation_logger):
        """Test that nested thinking tags are removed."""
        message = "Start <think>outer <think>inner</think> content</think> end"
        cleaned = conversation_logger.clean_message(message)

        assert "<think>" not in cleaned
        assert "Start" in cleaned
        assert "end" in cleaned

    def test_clean_message_handles_multiline_thinking(self, conversation_logger):
        """Test cleaning thinking tags across multiple lines."""
        message = """Before thinking
        <think>
        Line 1 of thinking
        Line 2 of thinking
        </think>
        After thinking"""

        cleaned = conversation_logger.clean_message(message)

        assert "<think>" not in cleaned
        assert "Line 1 of thinking" not in cleaned
        assert "Before thinking" in cleaned
        assert "After thinking" in cleaned

    def test_clean_message_removes_extra_whitespace(self, conversation_logger):
        """Test that extra whitespace is normalized."""
        message = "Hello    world   with    spaces"
        cleaned = conversation_logger.clean_message(message)

        assert cleaned == "Hello world with spaces"

    def test_clean_message_preserves_normal_text(self, conversation_logger):
        """Test that normal text without tags is preserved."""
        message = "This is a normal message without any special tags."
        cleaned = conversation_logger.clean_message(message)

        assert cleaned == message

    def test_log_empty_message_after_cleaning(self, conversation_logger, temp_log_dir):
        """Test that messages that are empty after cleaning are not logged."""
        # Message with only thinking tags
        conversation_logger.log_message("TestBot", "<think>only thinking</think>")

        log_file = conversation_logger.get_daily_log_file()

        # File may exist but should be empty or not created
        if log_file.exists():
            content = log_file.read_text().strip()
            assert content == ""
        else:
            # File not created is also acceptable
            assert True

    def test_log_message_with_unicode(self, conversation_logger, temp_log_dir):
        """Test logging messages with unicode characters."""
        conversation_logger.log_message("TestBot", "Hello 世界 🌍 café")

        log_file = conversation_logger.get_daily_log_file()
        content = log_file.read_text(encoding="utf-8")

        assert "世界" in content
        assert "🌍" in content
        assert "café" in content

    def test_log_message_with_special_characters(self, conversation_logger, temp_log_dir):
        """Test logging messages with special characters."""
        special_message = "Special chars: @#$%^&*() [] {} <> | \\ / ?"
        conversation_logger.log_message("TestBot", special_message)

        log_file = conversation_logger.get_daily_log_file()
        content = log_file.read_text()

        # Note: angle brackets in thinking tags would be removed, but we're not using them as tags
        assert "Special chars:" in content
        assert "@#$%^&*()" in content

    def test_multiple_loggers_same_directory(self, temp_log_dir):
        """Test multiple logger instances can write to same directory."""
        logger1 = ConversationLogger(log_dir=str(temp_log_dir))
        logger2 = ConversationLogger(log_dir=str(temp_log_dir))

        logger1.log_message("Logger1", "Message from logger 1")
        logger2.log_message("Logger2", "Message from logger 2")

        log_file = logger1.get_daily_log_file()
        content = log_file.read_text()

        assert "Logger1" in content
        assert "Logger2" in content

    def test_parse_log_file_with_valid_messages(self, temp_log_dir):
        """Test parsing log file with valid message format."""
        conversation_logger = ConversationLogger(log_dir=str(temp_log_dir))

        # Log some messages
        conversation_logger.log_message("Alice", "Hello there")
        conversation_logger.log_message("Bob", "Hi Alice!")

        log_file = conversation_logger.get_daily_log_file()

        # Parse the log file
        messages = conversation_logger.parse_log_file(log_file)

        assert len(messages) == 2
        assert messages[0]["persona"] == "Alice"
        assert messages[0]["content"] == "Hello there"
        assert messages[1]["persona"] == "Bob"
        assert messages[1]["content"] == "Hi Alice!"
        assert "timestamp" in messages[0]

    def test_parse_log_file_nonexistent_file(self, temp_log_dir):
        """Test parsing nonexistent log file returns empty list."""
        conversation_logger = ConversationLogger(log_dir=str(temp_log_dir))

        messages = conversation_logger.parse_log_file(temp_log_dir / "nonexistent.txt")

        assert messages == []

    def test_parse_log_file_with_empty_file(self, temp_log_dir):
        """Test parsing empty log file."""
        empty_file = temp_log_dir / "empty.txt"
        empty_file.write_text("")

        conversation_logger = ConversationLogger(log_dir=str(temp_log_dir))
        messages = conversation_logger.parse_log_file(empty_file)

        assert messages == []

    def test_parse_log_file_with_malformed_lines(self, temp_log_dir):
        """Test parsing log file with malformed lines."""
        malformed_file = temp_log_dir / "malformed.txt"
        malformed_file.write_text(
            "[12:34:56] Persona$ Valid message\n"
            "Invalid line without timestamp\n"
            "[12:34:57] Missing dollar sign\n"
            "[12:34:58] Another$ Valid message\n"
        )

        conversation_logger = ConversationLogger(log_dir=str(temp_log_dir))
        messages = conversation_logger.parse_log_file(malformed_file)

        # Should only parse valid messages
        assert len(messages) == 2
        assert messages[0]["content"] == "Valid message"
        assert messages[1]["content"] == "Valid message"

    def test_parse_log_file_with_special_characters(self, temp_log_dir):
        """Test parsing log file with special characters in content."""
        conversation_logger = ConversationLogger(log_dir=str(temp_log_dir))

        conversation_logger.log_message("Bot", "Message with @#$%^&*() special chars")

        log_file = conversation_logger.get_daily_log_file()
        messages = conversation_logger.parse_log_file(log_file)

        assert len(messages) == 1
        assert "@#$%^&*()" in messages[0]["content"]

    def test_parse_log_file_with_unicode(self, temp_log_dir):
        """Test parsing log file with Unicode characters."""
        conversation_logger = ConversationLogger(log_dir=str(temp_log_dir))

        conversation_logger.log_message("Bot", "Hello 世界 🌍")

        log_file = conversation_logger.get_daily_log_file()
        messages = conversation_logger.parse_log_file(log_file)

        assert len(messages) == 1
        assert "世界" in messages[0]["content"]
        assert "🌍" in messages[0]["content"]
