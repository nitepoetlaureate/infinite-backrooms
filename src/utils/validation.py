"""Input validation utilities for Infinite Backrooms.

This module provides comprehensive input validation functions to prevent
security vulnerabilities and ensure data integrity.
"""

import re
from typing import Optional


def validate_persona_name(name: str) -> tuple[bool, Optional[str]]:
    """Validate persona name.

    Args:
        name: Persona name to validate

    Returns:
        Tuple of (is_valid, error_message)

    Security:
        - Prevents empty names
        - Limits length to prevent DoS
        - Restricts to safe characters to prevent injection attacks
    """
    if not name or not name.strip():
        return False, "Persona name cannot be empty"

    if len(name) > 50:
        return False, "Persona name must be 50 characters or less"

    # Allow letters, numbers, spaces, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
        return False, "Persona name can only contain letters, numbers, spaces, hyphens, and underscores"

    return True, None


def validate_model_name(model: str) -> tuple[bool, Optional[str]]:
    """Validate Ollama model name.

    Args:
        model: Model name to validate

    Returns:
        Tuple of (is_valid, error_message)

    Security:
        - Validates Ollama model naming convention
        - Prevents command injection via model names
    """
    if not model or not model.strip():
        return False, "Model name cannot be empty"

    # Ollama models follow pattern: name[:tag]
    # Example: llama2, llama2:latest, granite3.3:8b
    if not re.match(r'^[a-zA-Z0-9\-_\.]+(?::[a-zA-Z0-9\-_\.]+)?$', model):
        return False, "Invalid model name format. Expected format: name or name:tag"

    return True, None


def validate_url(url: str) -> tuple[bool, Optional[str]]:
    """Validate URL format.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, error_message)

    Security:
        - Validates URL format to prevent SSRF attacks
        - Ensures only http/https protocols
        - Supports localhost and IP addresses
    """
    if not url or not url.strip():
        return False, "URL cannot be empty"

    # Basic URL validation - must be http or https
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    if not url_pattern.match(url):
        return False, "Invalid URL format. Must be http:// or https:// followed by a valid domain, localhost, or IP address"

    return True, None


def sanitize_log_filename(filename: str) -> str:
    """Sanitize filename for log files.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem operations

    Security:
        - Removes path traversal attempts (..)
        - Removes directory separators
        - Replaces unsafe characters with underscores
    """
    # Remove any path traversal attempts
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')

    # Allow only safe characters: alphanumeric, hyphen, underscore, period
    filename = re.sub(r'[^a-zA-Z0-9\-_\.]', '_', filename)

    # Ensure filename isn't empty after sanitization
    if not filename or filename == '.':
        filename = 'sanitized_log.txt'

    return filename


def validate_system_prompt(prompt: str, max_length: int = 10000) -> tuple[bool, Optional[str]]:
    """Validate system prompt length.

    Args:
        prompt: System prompt to validate
        max_length: Maximum allowed length

    Returns:
        Tuple of (is_valid, error_message)

    Security:
        - Prevents excessively long prompts that could cause DoS
    """
    if len(prompt) > max_length:
        return False, f"System prompt must be {max_length} characters or less (current: {len(prompt)})"

    return True, None


def validate_timeout(timeout: int, min_timeout: int = 10, max_timeout: int = 600) -> tuple[bool, Optional[str]]:
    """Validate timeout value.

    Args:
        timeout: Timeout value in seconds
        min_timeout: Minimum allowed timeout
        max_timeout: Maximum allowed timeout

    Returns:
        Tuple of (is_valid, error_message)

    Security:
        - Prevents unreasonably short or long timeouts
        - Ensures timeout is within safe operational bounds
    """
    if timeout < min_timeout:
        return False, f"Timeout must be at least {min_timeout} seconds"

    if timeout > max_timeout:
        return False, f"Timeout must be at most {max_timeout} seconds"

    return True, None


def validate_integer_range(value: int, min_val: int, max_val: int, field_name: str = "Value") -> tuple[bool, Optional[str]]:
    """Validate an integer is within a specified range.

    Args:
        value: Integer value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        field_name: Name of field for error messages

    Returns:
        Tuple of (is_valid, error_message)
    """
    if value < min_val:
        return False, f"{field_name} must be at least {min_val}"

    if value > max_val:
        return False, f"{field_name} must be at most {max_val}"

    return True, None
