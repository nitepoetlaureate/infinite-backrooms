"""Conversation logging service."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from src.utils.constants import LOG_DIRECTORY, LOG_FILE_PREFIX


class ConversationLogger:
    """Handles logging conversations to daily text files.

    Logs are stored in the configured directory with one file per day.
    Thinking tags are automatically removed from messages before logging.
    """

    def __init__(self, log_dir: str | Path = LOG_DIRECTORY) -> None:
        """Initialize conversation logger.

        Args:
            log_dir: Directory to store log files (default: "conversations")
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

    def get_daily_log_file(self) -> Path:
        """Get the log file path for today.

        Returns:
            Path object for today's log file
        """
        today = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"{LOG_FILE_PREFIX}_{today}.txt"

    def clean_message(self, message: str) -> str:
        """Remove thinking tags and content from message.

        Args:
            message: Raw message text potentially containing <think>...</think> tags

        Returns:
            Cleaned message with thinking tags removed
        """
        # Remove <think>...</think> blocks (including nested ones)
        cleaned = re.sub(r"<think>.*?</think>", "", message, flags=re.DOTALL | re.IGNORECASE)
        # Clean up any extra whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def log_message(self, persona: str, message: str, timestamp: datetime | None = None) -> None:
        """Log a message to today's file.

        Args:
            persona: Name of the persona sending the message
            message: Message content
            timestamp: Optional timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Clean the message before logging
        cleaned_message = self.clean_message(message)

        # Only log if there's content after cleaning
        if cleaned_message:
            log_file = self.get_daily_log_file()
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp.strftime('%H:%M:%S')}] {persona}$ {cleaned_message}\n")

    def parse_log_file(self, log_file_path: Path | str) -> list[dict[str, str]]:
        """Parse a log file and return structured message data.

        Args:
            log_file_path: Path to the log file to parse

        Returns:
            List of dictionaries with keys: persona, content, timestamp
        """
        log_file_path = Path(log_file_path)
        if not log_file_path.exists():
            return []

        messages = []
        with open(log_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Parse format: [HH:MM:SS] PersonaName$ message content
                if line.startswith("[") and "]" in line and "$" in line:
                    try:
                        # Extract timestamp
                        timestamp_end = line.index("]")
                        timestamp = line[1:timestamp_end]

                        # Extract persona and content
                        rest = line[timestamp_end + 1 :].strip()
                        if "$" in rest:
                            persona_end = rest.index("$")
                            persona = rest[:persona_end].strip()
                            content = rest[persona_end + 1 :].strip()

                            messages.append(
                                {"timestamp": timestamp, "persona": persona, "content": content}
                            )
                    except (ValueError, IndexError):
                        # Skip malformed lines
                        continue

        return messages
