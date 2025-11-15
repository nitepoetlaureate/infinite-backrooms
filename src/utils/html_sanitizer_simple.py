"""Simple HTML sanitizer fallback without external dependencies."""

from __future__ import annotations

import re
from typing import Any

import streamlit as st


class SimpleSecureRenderer:
    """Simple HTML sanitizer for safe rendering without external dependencies."""

    def sanitize_text(self, text: str) -> str:
        """Sanitize text content by removing HTML tags.

        Args:
            text: Input text that may contain HTML

        Returns:
            Sanitized text with HTML tags removed
        """
        if not text:
            return ""

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Handle HTML entities
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&apos;': "'",
        }

        for entity, char in html_entities.items():
            text = text.replace(entity, char)

        return text.strip()

    def _sanitize_color(self, color: str) -> str:
        """Sanitize color values.

        Args:
            color: Color value (hex, rgb, or named color)

        Returns:
            Sanitized color value or default
        """
        if not color:
            return "#000000"

        # Allow hex colors
        if re.match(r'^#[0-9A-Fa-f]{6}$', color):
            return color

        # Allow rgb colors
        if re.match(r'^rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)$', color):
            return color

        # Default to black for invalid colors
        return "#000000"

    def render_with_fallback(self, content: str, fallback: str = "") -> str:
        """Render content with fallback if empty.

        Args:
            content: Content to render
            fallback: Fallback content if main content is empty

        Returns:
            Rendered content or fallback
        """
        if not content or not content.strip():
            return fallback
        return self.sanitize_text(content)

    def render_content_with_mentions(self, content: str, personas: list[Any]) -> str:
        """Render content with @mentions highlighting.

        Args:
            content: Content with @mentions
            personas: List of persona objects

        Returns:
            Content with mentions highlighted
        """
        if not content:
            return ""

        # Simple mention highlighting without external dependencies
        safe_content = self.sanitize_text(content)

        # Find persona names and highlight them
        persona_names = [p.name for p in personas if hasattr(p, 'name')]

        for name in persona_names:
            # Simple regex to find @mentions
            pattern = rf'@{re.escape(name)}\b'
            safe_content = re.sub(
                pattern,
                f'<span style="color: #0066cc; font-weight: bold;">@{name}</span>',
                safe_content
            )

        return safe_content

    def sanitize_html(self, html: str) -> str:
        """Sanitize HTML by removing dangerous elements.

        Args:
            html: HTML content to sanitize

        Returns:
            Sanitized HTML (tags removed in this simple version)
        """
        return self.sanitize_text(html)


# Create global instance
secure_renderer = SimpleSecureRenderer()