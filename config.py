"""Configuration management for Infinite Backrooms application

This module provides centralized configuration management with support for:
- Environment variables
- Default values
- Type-safe configuration access
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class OllamaConfig:
    """Configuration for Ollama API client"""
    base_url: str = "http://localhost:11434"
    connection_timeout: int = 10  # seconds
    response_timeout: int = 300  # seconds (5 minutes)

    @classmethod
    def from_env(cls) -> "OllamaConfig":
        """Create configuration from environment variables"""
        return cls(
            base_url=os.getenv("OLLAMA_BASE_URL", cls.base_url),
            connection_timeout=int(os.getenv("OLLAMA_CONNECTION_TIMEOUT", str(cls.connection_timeout))),
            response_timeout=int(os.getenv("OLLAMA_RESPONSE_TIMEOUT", str(cls.response_timeout))),
        )


@dataclass
class ConversationConfig:
    """Configuration for conversation settings"""
    max_history: int = 50
    context_messages: int = 10
    response_delay_min: int = 2  # seconds
    response_delay_max: int = 8  # seconds
    auto_advance: bool = True
    enable_thinking: bool = True

    @classmethod
    def from_env(cls) -> "ConversationConfig":
        """Create configuration from environment variables"""
        return cls(
            max_history=int(os.getenv("MAX_HISTORY", str(cls.max_history))),
            context_messages=int(os.getenv("CONTEXT_MESSAGES", str(cls.context_messages))),
            response_delay_min=int(os.getenv("RESPONSE_DELAY_MIN", str(cls.response_delay_min))),
            response_delay_max=int(os.getenv("RESPONSE_DELAY_MAX", str(cls.response_delay_max))),
            auto_advance=os.getenv("AUTO_ADVANCE", str(cls.auto_advance)).lower() in ("true", "1", "yes"),
            enable_thinking=os.getenv("ENABLE_THINKING", str(cls.enable_thinking)).lower() in ("true", "1", "yes"),
        )


@dataclass
class LoggingConfig:
    """Configuration for logging"""
    log_dir: str = "conversations"
    log_file_prefix: str = "streamlit_backroom"

    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """Create configuration from environment variables"""
        return cls(
            log_dir=os.getenv("LOG_DIR", cls.log_dir),
            log_file_prefix=os.getenv("LOG_FILE_PREFIX", cls.log_file_prefix),
        )


@dataclass
class AppConfig:
    """Main application configuration"""
    ollama: OllamaConfig
    conversation: ConversationConfig
    logging: LoggingConfig

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create configuration from environment variables"""
        return cls(
            ollama=OllamaConfig.from_env(),
            conversation=ConversationConfig.from_env(),
            logging=LoggingConfig.from_env(),
        )


# Global configuration instance
config = AppConfig.from_env()
