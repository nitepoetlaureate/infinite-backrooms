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

    def test_validate_system_prompt_valid(self):
        """Test valid system prompts are accepted."""
        from src.utils.validation import validate_system_prompt

        valid_prompts = [
            "You are a helpful assistant.",
            "A" * 1000,  # Within limit
            "",  # Empty is valid
        ]
        for prompt in valid_prompts:
            is_valid, error = validate_system_prompt(prompt)
            assert is_valid is True
            assert error is None

    def test_validate_system_prompt_too_long(self):
        """Test system prompt exceeding length limit is rejected."""
        from src.utils.validation import validate_system_prompt

        long_prompt = "A" * 10001  # Exceeds default limit
        is_valid, error = validate_system_prompt(long_prompt)
        assert is_valid is False
        assert "10000" in error

    def test_validate_system_prompt_custom_max_length(self):
        """Test system prompt validation with custom max length."""
        from src.utils.validation import validate_system_prompt

        prompt = "A" * 100
        is_valid, error = validate_system_prompt(prompt, max_length=50)
        assert is_valid is False
        assert "50" in error

        is_valid2, error2 = validate_system_prompt(prompt, max_length=200)
        assert is_valid2 is True
        assert error2 is None

    def test_validate_timeout_valid(self):
        """Test valid timeout values are accepted."""
        from src.utils.validation import validate_timeout

        valid_timeouts = [10, 30, 60, 300, 600]
        for timeout in valid_timeouts:
            is_valid, error = validate_timeout(timeout)
            assert is_valid is True
            assert error is None

    def test_validate_timeout_too_short(self):
        """Test timeout below minimum is rejected."""
        from src.utils.validation import validate_timeout

        is_valid, error = validate_timeout(5)
        assert is_valid is False
        assert "at least 10" in error

    def test_validate_timeout_too_long(self):
        """Test timeout above maximum is rejected."""
        from src.utils.validation import validate_timeout

        is_valid, error = validate_timeout(700)
        assert is_valid is False
        assert "at most 600" in error

    def test_validate_timeout_custom_bounds(self):
        """Test timeout validation with custom bounds."""
        from src.utils.validation import validate_timeout

        is_valid, error = validate_timeout(25, min_timeout=30, max_timeout=100)
        assert is_valid is False
        assert "at least 30" in error

        is_valid2, error2 = validate_timeout(150, min_timeout=30, max_timeout=100)
        assert is_valid2 is False
        assert "at most 100" in error2

        is_valid3, error3 = validate_timeout(50, min_timeout=30, max_timeout=100)
        assert is_valid3 is True
        assert error3 is None

    def test_validate_integer_range_valid(self):
        """Test valid integer ranges are accepted."""
        from src.utils.validation import validate_integer_range

        is_valid, error = validate_integer_range(50, 0, 100)
        assert is_valid is True
        assert error is None

        is_valid2, error2 = validate_integer_range(0, 0, 100)
        assert is_valid2 is True
        assert error2 is None

        is_valid3, error3 = validate_integer_range(100, 0, 100)
        assert is_valid3 is True
        assert error3 is None

    def test_validate_integer_range_below_minimum(self):
        """Test integer below minimum is rejected."""
        from src.utils.validation import validate_integer_range

        is_valid, error = validate_integer_range(5, 10, 100, "TestValue")
        assert is_valid is False
        assert "TestValue" in error
        assert "at least 10" in error

    def test_validate_integer_range_above_maximum(self):
        """Test integer above maximum is rejected."""
        from src.utils.validation import validate_integer_range

        is_valid, error = validate_integer_range(150, 10, 100, "TestValue")
        assert is_valid is False
        assert "TestValue" in error
        assert "at most 100" in error

    def test_validate_integer_range_custom_field_name(self):
        """Test integer range validation uses custom field name in errors."""
        from src.utils.validation import validate_integer_range

        is_valid, error = validate_integer_range(5, 10, 100, "CustomField")
        assert is_valid is False
        assert "CustomField" in error

    def test_validate_integer_range_default_field_name(self):
        """Test integer range validation uses default field name."""
        from src.utils.validation import validate_integer_range

        is_valid, error = validate_integer_range(5, 10, 100)
        assert is_valid is False
        assert "Value" in error

    def test_validate_persona_name_whitespace_only(self):
        """Test persona name with only whitespace is rejected."""
        from src.utils.validation import validate_persona_name

        is_valid, error = validate_persona_name("   ")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_validate_model_name_whitespace_only(self):
        """Test model name with only whitespace is rejected."""
        from src.utils.validation import validate_model_name

        is_valid, error = validate_model_name("   ")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_validate_url_whitespace_only(self):
        """Test URL with only whitespace is rejected."""
        from src.utils.validation import validate_url

        is_valid, error = validate_url("   ")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_sanitize_log_filename_empty_string(self):
        """Test filename sanitization with empty string."""
        from src.utils.validation import sanitize_log_filename

        result = sanitize_log_filename("")
        assert result == "sanitized_log.txt"

    def test_sanitize_log_filename_only_dots(self):
        """Test filename sanitization with only dots."""
        from src.utils.validation import sanitize_log_filename

        result = sanitize_log_filename(".")
        assert result == "sanitized_log.txt"

    def test_sanitize_log_filename_mixed_separators(self):
        """Test filename sanitization with mixed path separators."""
        from src.utils.validation import sanitize_log_filename

        dangerous = "..\\..\\../etc/passwd"
        result = sanitize_log_filename(dangerous)
        assert ".." not in result
        assert "/" not in result
        assert "\\" not in result

    def test_validate_model_name_with_multiple_colons(self):
        """Test model name with multiple colons is rejected."""
        from src.utils.validation import validate_model_name

        is_valid, error = validate_model_name("model:tag:extra")
        assert is_valid is False

    def test_validate_model_name_valid_formats(self):
        """Test various valid model name formats."""
        from src.utils.validation import validate_model_name

        valid_models = [
            "llama2",
            "llama2:latest",
            "granite3.3:8b",
            "model-name:tag-name",
            "model_name:tag_name",
            "model.name:1.0",
        ]
        for model in valid_models:
            is_valid, error = validate_model_name(model)
            assert is_valid is True, f"Model {model} should be valid"
            assert error is None

    def test_validate_url_various_ports(self):
        """Test URL validation with various port numbers."""
        from src.utils.validation import validate_url

        valid_urls = [
            "http://localhost:11434",
            "http://localhost:80",
            "http://localhost:8080",
            "http://example.com:3000",
            "https://example.com:443",
        ]
        for url in valid_urls:
            is_valid, error = validate_url(url)
            assert is_valid is True, f"URL {url} should be valid"
            assert error is None

    def test_validate_url_without_port(self):
        """Test URL validation without port number."""
        from src.utils.validation import validate_url

        valid_urls = ["http://localhost", "https://example.com", "http://192.168.1.1"]
        for url in valid_urls:
            is_valid, error = validate_url(url)
            assert is_valid is True, f"URL {url} should be valid"
            assert error is None
