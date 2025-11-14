#!/usr/bin/env python3
"""
Input validation utilities for security and data integrity
Prevents injection attacks and ensures data quality
"""

import re
from constants import (
    MAX_PERSONA_NAME_LENGTH,
    MAX_SYSTEM_PROMPT_LENGTH,
    MAX_MESSAGE_LENGTH
)


class ValidationError(Exception):
    """Raised when validation fails"""
    pass


def validate_persona_name(name: str) -> str:
    """
    Validate and sanitize persona name.

    Args:
        name: The persona name to validate

    Returns:
        The validated and sanitized name

    Raises:
        ValidationError: If validation fails
    """
    name = name.strip()

    if not name:
        raise ValidationError("Persona name cannot be empty")

    if len(name) > MAX_PERSONA_NAME_LENGTH:
        raise ValidationError(
            f"Persona name too long (max {MAX_PERSONA_NAME_LENGTH} characters)"
        )

    # Allow letters, numbers, spaces, hyphens, and underscores
    if not re.match(r'^[a-zA-Z0-9_\- ]+$', name):
        raise ValidationError(
            "Persona name can only contain letters, numbers, spaces, hyphens, and underscores"
        )

    return name


def validate_system_prompt(prompt: str) -> str:
    """
    Validate and sanitize system prompt.

    Args:
        prompt: The system prompt to validate

    Returns:
        The validated and sanitized prompt

    Raises:
        ValidationError: If validation fails
    """
    prompt = prompt.strip()

    if len(prompt) > MAX_SYSTEM_PROMPT_LENGTH:
        raise ValidationError(
            f"System prompt too long (max {MAX_SYSTEM_PROMPT_LENGTH} characters)"
        )

    # Check for potential injection attempts
    dangerous_patterns = [
        (r'<script', "Script tags are not allowed"),
        (r'javascript:', "JavaScript protocol is not allowed"),
        (r'onerror\s*=', "Event handlers are not allowed"),
        (r'onclick\s*=', "Event handlers are not allowed"),
        (r'onload\s*=', "Event handlers are not allowed"),
    ]

    for pattern, error_msg in dangerous_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            raise ValidationError(f"Security violation: {error_msg}")

    return prompt


def validate_message(message: str) -> str:
    """
    Validate message content.

    Args:
        message: The message to validate

    Returns:
        The validated message

    Raises:
        ValidationError: If validation fails
    """
    if len(message) > MAX_MESSAGE_LENGTH:
        raise ValidationError(
            f"Message too long (max {MAX_MESSAGE_LENGTH} characters)"
        )

    return message


def validate_color(color: str) -> str:
    """
    Validate hex color code.

    Args:
        color: The color code to validate (e.g., "#1f77b4")

    Returns:
        The validated color code

    Raises:
        ValidationError: If validation fails
    """
    color = color.strip()

    if not re.match(r'^#[0-9a-fA-F]{6}$', color):
        raise ValidationError(
            "Invalid color code. Must be in format #RRGGBB (e.g., #1f77b4)"
        )

    return color


def validate_model_name(model: str) -> str:
    """
    Validate Ollama model name.

    Args:
        model: The model name to validate

    Returns:
        The validated model name

    Raises:
        ValidationError: If validation fails
    """
    model = model.strip()

    if not model:
        raise ValidationError("Model name cannot be empty")

    # Model names should contain only alphanumeric, dots, hyphens, colons, and underscores
    if not re.match(r'^[a-zA-Z0-9._:\-]+$', model):
        raise ValidationError(
            "Invalid model name. Can only contain letters, numbers, dots, hyphens, colons, and underscores"
        )

    return model


def validate_url(url: str) -> str:
    """
    Validate URL format.

    Args:
        url: The URL to validate

    Returns:
        The validated URL

    Raises:
        ValidationError: If validation fails
    """
    url = url.strip()

    if not url:
        raise ValidationError("URL cannot be empty")

    # Basic URL pattern matching
    if not re.match(r'^https?://[a-zA-Z0-9.\-]+(:[0-9]+)?(/.*)?$', url):
        raise ValidationError(
            "Invalid URL format. Must start with http:// or https://"
        )

    return url


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.

    Args:
        filename: The filename to sanitize

    Returns:
        The sanitized filename

    Raises:
        ValidationError: If validation fails
    """
    filename = filename.strip()

    # Remove any path separators
    filename = filename.replace('/', '').replace('\\', '')

    # Remove parent directory references
    filename = filename.replace('..', '')

    # Only allow safe characters
    if not re.match(r'^[a-zA-Z0-9._\-]+$', filename):
        raise ValidationError(
            "Invalid filename. Can only contain letters, numbers, dots, hyphens, and underscores"
        )

    if not filename:
        raise ValidationError("Filename cannot be empty after sanitization")

    return filename
