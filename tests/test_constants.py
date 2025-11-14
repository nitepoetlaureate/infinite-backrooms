"""Tests for constants and configuration."""

import pytest


class TestConstants:
    """Test constants are properly defined."""

    def test_role_emoji_map_exists(self):
        """Test that ROLE_EMOJI_MAP constant exists and is populated."""
        from src.utils.constants import ROLE_EMOJI_MAP

        assert isinstance(ROLE_EMOJI_MAP, dict)
        assert len(ROLE_EMOJI_MAP) > 0

    def test_role_emoji_map_has_expected_roles(self):
        """Test that ROLE_EMOJI_MAP contains expected roles."""
        from src.utils.constants import ROLE_EMOJI_MAP

        expected_roles = [
            "Explorer", "Analyst", "Scientist", "Philosopher", "Comedian",
            "Optimist", "Skeptic", "Moderator", "Creative Writer"
        ]
        for role in expected_roles:
            assert role in ROLE_EMOJI_MAP
            assert isinstance(ROLE_EMOJI_MAP[role], str)
            assert len(ROLE_EMOJI_MAP[role]) > 0

    def test_default_role_and_emoji_exist(self):
        """Test default role and emoji constants exist."""
        from src.utils.constants import DEFAULT_ROLE, DEFAULT_EMOJI

        assert isinstance(DEFAULT_ROLE, str)
        assert isinstance(DEFAULT_EMOJI, str)
        assert len(DEFAULT_ROLE) > 0
        assert len(DEFAULT_EMOJI) > 0

    def test_ollama_configuration_constants(self):
        """Test Ollama configuration constants are defined."""
        from src.utils.constants import (
            DEFAULT_OLLAMA_URL,
            DEFAULT_TIMEOUT,
            DEFAULT_RESPONSE_TIMEOUT
        )

        assert isinstance(DEFAULT_OLLAMA_URL, str)
        assert "localhost" in DEFAULT_OLLAMA_URL or "127.0.0.1" in DEFAULT_OLLAMA_URL

        assert isinstance(DEFAULT_TIMEOUT, (int, float))
        assert DEFAULT_TIMEOUT > 0

        assert isinstance(DEFAULT_RESPONSE_TIMEOUT, (int, float))
        assert DEFAULT_RESPONSE_TIMEOUT > 0

    def test_logging_configuration_constants(self):
        """Test logging configuration constants are defined."""
        from src.utils.constants import LOG_DIRECTORY, LOG_FILE_PREFIX
        from pathlib import Path

        # LOG_DIRECTORY is a Path object, not a string
        assert isinstance(LOG_DIRECTORY, Path)

        assert isinstance(LOG_FILE_PREFIX, str)
        assert len(LOG_FILE_PREFIX) > 0

    def test_ui_configuration_constants(self):
        """Test UI configuration constants are defined."""
        from src.utils.constants import (
            MIN_CONTEXT_MESSAGES,
            MAX_CONTEXT_MESSAGES,
            DEFAULT_CONTEXT_MESSAGES,
            MIN_TEMPERATURE,
            MAX_TEMPERATURE,
            DEFAULT_TEMPERATURE
        )

        # Context messages
        assert isinstance(MIN_CONTEXT_MESSAGES, int)
        assert isinstance(MAX_CONTEXT_MESSAGES, int)
        assert isinstance(DEFAULT_CONTEXT_MESSAGES, int)
        assert MIN_CONTEXT_MESSAGES > 0
        assert MAX_CONTEXT_MESSAGES > MIN_CONTEXT_MESSAGES
        assert MIN_CONTEXT_MESSAGES <= DEFAULT_CONTEXT_MESSAGES <= MAX_CONTEXT_MESSAGES

        # Temperature
        assert isinstance(MIN_TEMPERATURE, (int, float))
        assert isinstance(MAX_TEMPERATURE, (int, float))
        assert isinstance(DEFAULT_TEMPERATURE, (int, float))
        assert MIN_TEMPERATURE >= 0
        assert MAX_TEMPERATURE > MIN_TEMPERATURE
        assert MIN_TEMPERATURE <= DEFAULT_TEMPERATURE <= MAX_TEMPERATURE

    def test_role_templates_exist(self):
        """Test ROLE_TEMPLATES constant exists and is populated."""
        from src.utils.constants import ROLE_TEMPLATES

        assert isinstance(ROLE_TEMPLATES, dict)
        assert len(ROLE_TEMPLATES) > 0

        # Each role should have a template
        for role, template in ROLE_TEMPLATES.items():
            assert isinstance(role, str)
            assert isinstance(template, str)
            assert len(template) > 0

    def test_role_templates_match_emoji_map(self):
        """Test that roles in ROLE_TEMPLATES match ROLE_EMOJI_MAP."""
        from src.utils.constants import ROLE_TEMPLATES, ROLE_EMOJI_MAP

        # All roles with templates should have emojis (except empty string role)
        for role in ROLE_TEMPLATES.keys():
            if role:  # Skip empty string role
                assert role in ROLE_EMOJI_MAP, f"Role '{role}' has template but no emoji"

    def test_constants_are_immutable_types(self):
        """Test that constants use appropriate immutable types where needed."""
        from src.utils.constants import DEFAULT_OLLAMA_URL, DEFAULT_ROLE

        # String constants should be strings
        assert isinstance(DEFAULT_OLLAMA_URL, str)
        assert isinstance(DEFAULT_ROLE, str)
