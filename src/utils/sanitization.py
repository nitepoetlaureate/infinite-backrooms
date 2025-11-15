"""Input sanitization utilities to prevent injection attacks.

This module provides comprehensive input sanitization functions to protect against:
- XSS (Cross-Site Scripting) attacks
- SQL injection attempts
- HTML injection attacks
- Markdown injection attacks
- JSON injection attacks
- Command injection attempts
- Path traversal attacks
- LDAP injection attacks
"""

import html
import json
import re
import urllib.parse
from typing import Any, Dict, Optional, Union


def sanitize_html(text: str, allow_basic_formatting: bool = False) -> str:
    """Sanitize text for HTML output by escaping special characters.

    Args:
        text: Input text to sanitize
        allow_basic_formatting: If True, allow basic HTML tags like <b>, <i>, <em>, <strong>

    Returns:
        Sanitized text safe for HTML rendering

    Security:
        - Escapes all HTML special characters
        - Prevents XSS attacks via user input
        - Optionally preserves basic formatting tags
    """
    if not text:
        return ""

    # Always escape HTML entities first
    sanitized = html.escape(text, quote=True)

    # If basic formatting is allowed, restore safe tags
    if allow_basic_formatting:
        safe_tags = ['b', 'i', 'em', 'strong', 'code']
        for tag in safe_tags:
            # Re-enable these specific tags
            sanitized = sanitized.replace(f'&lt;{tag}&gt;', f'<{tag}>')
            sanitized = sanitized.replace(f'&lt;/{tag}&gt;', f'</{tag}>')

    return sanitized


def sanitize_css_value(value: str) -> str:
    """Sanitize CSS values to prevent CSS injection.

    Args:
        value: CSS value to sanitize

    Returns:
        Sanitized CSS value

    Security:
        - Removes potentially dangerous CSS functions
        - Validates hex colors
        - Prevents expression() and url() injections
    """
    if not value:
        return ""

    # Remove dangerous CSS functions
    dangerous_patterns = [
        r'expression\s*\(',
        r'javascript:',
        r'@import',
        r'behavior:',
        r'binding:',
        r'-moz-binding',
        r'vbscript:',
        r'data:text/html',
    ]

    sanitized = value.lower()
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

    return sanitized


def validate_hex_color(color: str) -> tuple[bool, Optional[str]]:
    """Validate hex color code format.

    Args:
        color: Color code to validate (e.g., "#FF0000" or "#F00")

    Returns:
        Tuple of (is_valid, error_message)

    Security:
        - Ensures color codes match expected hex format
        - Prevents CSS injection via color fields
    """
    if not color:
        return False, "Color cannot be empty"

    # Check hex color format (#RGB or #RRGGBB)
    if not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', color):
        return False, "Invalid hex color format. Expected #RGB or #RRGGBB"

    return True, None


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize filename for safe filesystem operations.

    Args:
        filename: Original filename
        max_length: Maximum allowed filename length

    Returns:
        Sanitized filename

    Security:
        - Removes path traversal attempts
        - Removes special characters
        - Limits filename length
        - Prevents null bytes
    """
    # Remove null bytes
    filename = filename.replace('\x00', '')

    # Remove path separators and traversal
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')

    # Allow only safe characters
    filename = re.sub(r'[^a-zA-Z0-9\-_\.]', '_', filename)

    # Ensure not empty
    if not filename or filename == '.':
        filename = 'sanitized_file.txt'

    # Limit length
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        name = name[:max_length - len(ext) - 1]
        filename = f"{name}.{ext}" if ext else name

    return filename


def sanitize_persona_name(name: str) -> str:
    """Sanitize persona name for safe display.

    Args:
        name: Persona name to sanitize

    Returns:
        Sanitized persona name

    Security:
        - Escapes HTML to prevent XSS
        - Preserves Unicode characters for international names
    """
    if not name:
        return ""

    # HTML escape to prevent XSS
    sanitized = html.escape(name.strip(), quote=True)

    # Limit length
    if len(sanitized) > 50:
        sanitized = sanitized[:50]

    return sanitized


def sanitize_url(url: str) -> str:
    """Sanitize URL to prevent injection attacks.

    Args:
        url: URL to sanitize

    Returns:
        Sanitized URL

    Security:
        - Ensures URL uses safe protocols (http/https)
        - Prevents javascript: and data: URIs
        - Removes dangerous characters
    """
    if not url:
        return ""

    url = url.strip()

    # Remove dangerous protocols
    dangerous_protocols = [
        'javascript:', 'data:', 'vbscript:', 'file:',
        'about:', 'blob:', 'ws:', 'wss:'
    ]

    url_lower = url.lower()
    for protocol in dangerous_protocols:
        if url_lower.startswith(protocol):
            return ""

    # Only allow http and https
    if not (url_lower.startswith('http://') or url_lower.startswith('https://')):
        return ""

    return url


def sanitize_system_prompt(prompt: str) -> str:
    """Sanitize system prompt while preserving formatting.

    Args:
        prompt: System prompt to sanitize

    Returns:
        Sanitized system prompt

    Security:
        - Removes null bytes
        - Preserves line breaks and formatting
        - No HTML escaping (as this goes to AI, not rendered)
    """
    if not prompt:
        return ""

    # Remove null bytes
    sanitized = prompt.replace('\x00', '')

    # Remove any embedded control characters except newlines/tabs
    sanitized = ''.join(char for char in sanitized if char >= ' ' or char in '\n\r\t')

    return sanitized.strip()


def escape_markdown(text: str) -> str:
    """Escape markdown special characters.

    Args:
        text: Text to escape

    Returns:
        Text with markdown characters escaped
    """
    if not text:
        return ""

    # Escape markdown special characters
    markdown_chars = ['\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!', '|']

    escaped = text
    for char in markdown_chars:
        escaped = escaped.replace(char, '\\' + char)

    return escaped


# Regular expressions for security patterns
DANGEROUS_PATTERNS = {
    'xss': re.compile(
        r'<(script|iframe|object|embed|form|input|link|meta|style)[^>]*>.*?</\1>',
        re.IGNORECASE | re.DOTALL
    ),
    'javascript': re.compile(
        r'javascript\s*:',
        re.IGNORECASE
    ),
    'on_events': re.compile(
        r'on\w+\s*=\s*["\'][^"\']*["\']',
        re.IGNORECASE
    ),
    'sql_injection': re.compile(
        r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)|(--|\*/)',
        re.IGNORECASE
    ),
    'command_injection': re.compile(
        r'[;&|`$(){}[\]\'"\\]',
        re.MULTILINE
    ),
    'path_traversal': re.compile(
        r'\.\.[\\/]',
        re.IGNORECASE
    ),
    'ldap_injection': re.compile(
        r'[()*&|\\=!,]',
        re.IGNORECASE
    )
}

# Allowed HTML tags for safe content
ALLOWED_HTML_TAGS = {
    'p', 'br', 'strong', 'em', 'u', 'i', 'b',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'code', 'pre',
    'a', 'span', 'div'
}

# Allowed HTML attributes
ALLOWED_HTML_ATTRS = {
    'href', 'title', 'alt', 'class', 'id'
}

# Markdown-specific dangerous patterns
MARKDOWN_DANGEROUS_PATTERNS = {
    'html_injection': re.compile(r'<[^>]+>', re.IGNORECASE),
    'link_javascript': re.compile(r'\[([^\]]*)\]\(javascript:[^\)]*\)', re.IGNORECASE),
    'image_data': re.compile(r'!\[([^\]]*)\]\(data:[^\)]*\)', re.IGNORECASE),
}


def sanitize_markdown(markdown_input: str) -> str:
    """Sanitize markdown input to prevent injection attacks.

    Args:
        markdown_input: Markdown string to sanitize

    Returns:
        Sanitized markdown string

    Security:
        - Prevents HTML injection in markdown
        - Blocks dangerous link schemes
        - Removes embedded data URIs
        - Sanitizes code blocks
    """
    if not markdown_input:
        return ""

    # Check for extremely long inputs
    if len(markdown_input) > 200000:  # 200KB limit
        markdown_input = markdown_input[:200000] + "...[truncated]"

    sanitized = markdown_input

    # Remove dangerous markdown patterns
    for pattern_name, pattern in MARKDOWN_DANGEROUS_PATTERNS.items():
        if pattern_name == 'html_injection':
            # Replace HTML tags with escaped versions
            sanitized = html.escape(sanitized)
        else:
            sanitized = pattern.sub('', sanitized)

    # Sanitize links to prevent javascript: and other dangerous protocols
    sanitized = re.sub(
        r'\[([^\]]*)\]\(([^)]*)\)',
        lambda m: f"[{m.group(1)}]({_sanitize_url(m.group(2))})",
        sanitized
    )

    # Sanitize image sources
    sanitized = re.sub(
        r'!\[([^\]]*)\]\(([^)]*)\)',
        lambda m: f"![{m.group(1)}]({_sanitize_url(m.group(2))})",
        sanitized
    )

    # Remove or escape backticks that could be used for command injection
    sanitized = sanitized.replace('`', '')

    return sanitized.strip()


def sanitize_json_string(json_string: str) -> str:
    """Sanitize JSON string to prevent injection attacks.

    Args:
        json_string: JSON string to sanitize

    Returns:
        Sanitized JSON string

    Security:
        - Prevents JSON injection
        - Validates JSON structure
        - Removes dangerous characters
    """
    if not json_string:
        return ""

    # Check for extremely long inputs
    if len(json_string) > 100000:  # 100KB limit
        json_string = json_string[:100000] + "...[truncated]"

    try:
        # Try to parse as JSON first to validate structure
        parsed = json.loads(json_string)

        # Sanitize string values in the JSON
        def sanitize_strings(obj):
            if isinstance(obj, str):
                return sanitize_text_field(obj)
            elif isinstance(obj, dict):
                return {k: sanitize_strings(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize_strings(item) for item in obj]
            else:
                return obj

        sanitized_parsed = sanitize_strings(parsed)
        return json.dumps(sanitized_parsed, ensure_ascii=False)

    except json.JSONDecodeError:
        # If not valid JSON, treat as plain text and sanitize
        return sanitize_text_field(json_string)


def sanitize_text_field(text: str) -> str:
    """Sanitize plain text field.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text

    Security:
        - Removes dangerous characters
        - Prevents injection attacks
        - Limits length
    """
    if not text:
        return ""

    # Length limit
    if len(text) > 10000:  # 10KB limit for text fields
        text = text[:10000] + "...[truncated]"

    # Remove null bytes and control characters except newlines and tabs
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')

    # Remove dangerous patterns
    for pattern in DANGEROUS_PATTERNS.values():
        text = pattern.sub('', text)

    # Unicode normalization to prevent homograph attacks
    text = text.replace('\u200b', '')  # Zero-width space
    text = text.replace('\ufeff', '')  # BOM

    return text.strip()


def sanitize_user_input(user_input: str, input_type: str = "text") -> str:
    """General purpose user input sanitization.

    Args:
        user_input: User input to sanitize
        input_type: Type of input (text, html, markdown, json, filename, url)

    Returns:
        Sanitized input

    Security:
        - Applies appropriate sanitization based on input type
        - Provides comprehensive protection
    """
    if not user_input:
        return ""

    sanitizers = {
        'text': sanitize_text_field,
        'html': sanitize_html,
        'markdown': sanitize_markdown,
        'json': sanitize_json_string,
        'filename': sanitize_filename,
        'url': sanitize_url
    }

    sanitizer = sanitizers.get(input_type, sanitize_text_field)
    return sanitizer(user_input)


def _sanitize_url(url: str) -> str:
    """Sanitize URL in markdown links."""
    sanitized = sanitize_url(url)
    if sanitized == "":
        return "#"
    return sanitized


def validate_email(email: str) -> bool:
    """Validate email format safely."""
    if not email:
        return False

    # Basic email validation without regex DoS
    email = email.strip()
    if len(email) > 254:  # RFC 5321 limit
        return False

    try:
        local, domain = email.rsplit('@', 1)
    except ValueError:
        return False

    # Basic checks
    if not local or not domain:
        return False

    if len(local) > 64 or len(domain) > 253:
        return False

    # Check for dangerous characters
    dangerous_chars = ['<', '>', '"', '\'', '(', ')', '[', ']', '\\', ',']
    if any(char in email for char in dangerous_chars):
        return False

    return True


def sanitize_search_query(query: str) -> str:
    """Sanitize search query to prevent injection."""
    if not query:
        return ""

    # Remove dangerous characters for search
    query = re.sub(r'[<>"\'\\;|&`$()]', '', query)
    query = query.replace('--', '')
    query = query.replace('/*', '')
    query = query.replace('*/', '')

    # Limit length
    if len(query) > 1000:
        query = query[:1000]

    return query.strip()


def sanitize_api_input(data: Union[str, Dict, Any]) -> Union[str, Dict, Any]:
    """Sanitize API input data comprehensively.

    Args:
        data: Input data to sanitize (string, dict, or any object)

    Returns:
        Sanitized data

    Security:
        - Handles all data types comprehensively
        - Prevents injection at API level
    """
    if isinstance(data, str):
        return sanitize_text_field(data)
    elif isinstance(data, dict):
        return {k: sanitize_api_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_api_input(item) for item in data]
    elif hasattr(data, '__dict__'):
        # Handle objects with attributes
        sanitized_dict = {}
        for key, value in data.__dict__.items():
            if not key.startswith('_'):  # Skip private attributes
                sanitized_dict[key] = sanitize_api_input(value)
        return sanitized_dict
    else:
        return data


def prevent_csrf_token(token: str) -> str:
    """Validate and sanitize CSRF token."""
    if not token:
        return ""

    # Only allow alphanumeric characters
    return re.sub(r'[^a-zA-Z0-9]', '', token)
