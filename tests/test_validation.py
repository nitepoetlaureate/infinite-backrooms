"""Tests for input validation utilities."""

import pytest


class TestValidation:
    """Test input validation functions."""

    def test_validate_persona_name_valid(self):
        """Test valid persona names are accepted."""
        from src.utils.validation import validate_persona_name

        valid_names = ["Alice", "Bot_123", "AI-Assistant", "Test Bot"]
        for name in valid_names:
            is_valid, error = validate_persona_name(name)
            assert is_valid is True
            assert error is None

    def test_validate_persona_name_invalid_empty(self):
        """Test empty persona name is rejected."""
        from src.utils.validation import validate_persona_name

        is_valid, error = validate_persona_name("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_validate_persona_name_invalid_too_long(self):
        """Test persona name exceeding length limit is rejected."""
        from src.utils.validation import validate_persona_name

        long_name = "A" * 51
        is_valid, error = validate_persona_name(long_name)
        assert is_valid is False
        assert "50" in error

    def test_validate_persona_name_invalid_special_chars(self):
        """Test persona name with invalid characters is rejected."""
        from src.utils.validation import validate_persona_name

        invalid_names = ["Bob<script>", "Alice';DROP TABLE", "Bot&&&"]
        for name in invalid_names:
            is_valid, error = validate_persona_name(name)
            assert is_valid is False

    def test_validate_model_name_valid(self):
        """Test valid model names are accepted."""
        from src.utils.validation import validate_model_name

        valid_models = ["llama2:latest", "mistral:7b", "granite3.3:8b"]
        for model in valid_models:
            is_valid, error = validate_model_name(model)
            assert is_valid is True
            assert error is None

    def test_validate_model_name_invalid(self):
        """Test invalid model names are rejected."""
        from src.utils.validation import validate_model_name

        is_valid, error = validate_model_name("")
        assert is_valid is False

    def test_validate_url_valid(self):
        """Test valid URLs are accepted."""
        from src.utils.validation import validate_url

        valid_urls = [
            "http://localhost:11434",
            "https://example.com:8080",
            "http://192.168.1.1:11434"
        ]
        for url in valid_urls:
            is_valid, error = validate_url(url)
            assert is_valid is True
            assert error is None

    def test_validate_url_invalid(self):
        """Test invalid URLs are rejected."""
        from src.utils.validation import validate_url

        invalid_urls = ["not-a-url", "ftp://wrong-protocol", ""]
        for url in invalid_urls:
            is_valid, error = validate_url(url)
            assert is_valid is False

    def test_sanitize_log_filename(self):
        """Test filename sanitization removes dangerous characters."""
        from src.utils.validation import sanitize_log_filename

        dangerous = "../../../etc/passwd"
        safe = sanitize_log_filename(dangerous)
        assert ".." not in safe
        assert "/" not in safe
        assert "\\" not in safe

    def test_sanitize_log_filename_preserves_safe_chars(self):
        """Test filename sanitization preserves safe characters."""
        from src.utils.validation import sanitize_log_filename

        safe_name = "valid_log_2024-01-01.txt"
        result = sanitize_log_filename(safe_name)
        # Hyphens are safe characters, so they're preserved
        assert result == safe_name
