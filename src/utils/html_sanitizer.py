"""HTML sanitization utilities using bleach for secure content rendering.

This module provides a SecureHTMLRenderer class for safe HTML processing
and content rendering with comprehensive XSS protection.
"""

import logging
from typing import Dict, List, Optional, Set
import bleach

from src.utils.sanitization import sanitize_css_value, validate_hex_color

# Configure logging
logger = logging.getLogger(__name__)


class SecureHTMLRenderer:
    """
    Provides secure HTML rendering with comprehensive XSS protection.

    Uses the bleach library for HTML sanitization and provides methods
    for safe content rendering, mention highlighting, and fallback mechanisms.
    """

    # Whitelist of safe HTML tags for basic formatting
    ALLOWED_TAGS: Set[str] = {
        'b', 'i', 'em', 'strong', 'code', 'pre', 'p', 'br',
        'span', 'div', 'ul', 'ol', 'li', 'blockquote'
    }

    # Whitelist of safe HTML attributes
    ALLOWED_ATTRIBUTES: Dict[str, Set[str]] = {
        '*': {'class'},
        'a': {'href', 'title'},
        'span': {'style'},
        'div': {'style'},
        'p': {'style'},
        'li': {'style'},
        'code': {'class'},
        'pre': {'class'}
    }

    # Whitelist of safe CSS properties
    ALLOWED_CSS_PROPERTIES: Set[str] = {
        'color', 'background-color', 'font-weight', 'font-style',
        'text-decoration', 'padding', 'margin', 'border', 'border-radius',
        'font-size', 'text-align', 'display', 'width', 'height'
    }

    # Allowlist of safe URL protocols
    ALLOWED_PROTOCOLS: Set[str] = {'http', 'https', 'mailto'}

    def __init__(
        self,
        allowed_tags: Optional[Set[str]] = None,
        allowed_attributes: Optional[Dict[str, Set[str]]] = None,
        allowed_css_properties: Optional[Set[str]] = None
    ):
        """Initialize the SecureHTMLRenderer with optional custom configurations.

        Args:
            allowed_tags: Custom whitelist of allowed HTML tags
            allowed_attributes: Custom whitelist of allowed HTML attributes
            allowed_css_properties: Custom whitelist of allowed CSS properties
        """
        if allowed_tags:
            self.ALLOWED_TAGS = allowed_tags
        if allowed_attributes:
            self.ALLOWED_ATTRIBUTES = allowed_attributes
        if allowed_css_properties:
            self.ALLOWED_CSS_PROPERTIES = allowed_css_properties

        # Configure bleach CSS sanitizer
        self.css_sanitizer = bleach.CSSSanitizer(
            allowed_css_properties=self.ALLOWED_CSS_PROPERTIES,
            allowed_svg_properties=set()
        )

    def sanitize_html(self, html_content: str) -> str:
        """
        Sanitize HTML content using bleach with comprehensive XSS protection.

        Args:
            html_content: Raw HTML content to sanitize

        Returns:
            Sanitized HTML content safe for rendering

        Security:
            - Removes all dangerous tags and attributes
            - Strips event handlers and javascript
            - Validates CSS properties
            - Prevents protocol injection
        """
        if not html_content:
            return ""

        try:
            # First pass: Remove dangerous content
            clean_content = bleach.clean(
                html_content,
                tags=self.ALLOWED_TAGS,
                attributes=self.ALLOWED_ATTRIBUTES,
                strip=True,  # Remove disallowed tags completely
                strip_comments=True
            )

            # Second pass: Clean CSS in style attributes
            clean_content = bleach.clean(
                clean_content,
                tags=self.ALLOWED_TAGS,
                attributes=self.ALLOWED_ATTRIBUTES,
                css_sanitizer=self.css_sanitizer,
                protocols=self.ALLOWED_PROTOCOLS,
                strip=True,
                strip_comments=True
            )

            return clean_content

        except Exception as e:
            logger.error(f"HTML sanitization failed: {e}")
            # Return empty string as fallback
            return ""

    def render_content_with_mentions(
        self,
        content: str,
        personas: List,
        fallback: bool = True
    ) -> str:
        """
        Render content with secure @mention highlighting.

        Args:
            content: Text content potentially containing @mentions
            personas: List of persona objects with name and color attributes
            fallback: Whether to use fallback rendering on error

        Returns:
            Content with securely highlighted mentions
        """
        if not content:
            return ""

        try:
            # First sanitize the base content
            safe_content = self.sanitize_text(content)

            # Process mentions if personas provided
            if personas:
                safe_content = self._highlight_mentions_secure(safe_content, personas)

            return safe_content

        except Exception as e:
            logger.error(f"Content rendering failed: {e}")
            if fallback:
                # Fallback: return plain escaped content
                import html
                return html.escape(content, quote=True)
            return ""

    def _highlight_mentions_secure(self, content: str, personas: List) -> str:
        """
        Securely highlight @mentions with persona colors.

        Args:
            content: Sanitized content
            personas: List of persona objects

        Returns:
            Content with securely highlighted mentions
        """
        if not content or not personas:
            return content

        for persona in personas:
            try:
                # Get persona attributes safely
                persona_name = getattr(persona, 'name', '')
                persona_color = getattr(persona, 'color', '#1f77b4')

                if not persona_name:
                    continue

                # Sanitize persona name and color
                safe_name = self.sanitize_text(persona_name)
                safe_color = self._sanitize_color(persona_color)

                # Create mention pattern
                mention_pattern = f"@{safe_name}"

                if mention_pattern in content:
                    # Create safe highlighted mention
                    highlighted_mention = self._create_safe_mention_span(safe_name, safe_color)
                    content = content.replace(mention_pattern, highlighted_mention)

            except Exception as e:
                logger.warning(f"Failed to process mention for persona: {e}")
                continue

        return content

    def _sanitize_color(self, color: str) -> str:
        """
        Sanitize and validate color values.

        Args:
            color: Color value to sanitize

        Returns:
            Sanitized, valid color or fallback color
        """
        try:
            # Use existing sanitization utilities
            safe_color = sanitize_css_value(color)
            is_valid, _ = validate_hex_color(safe_color)

            if is_valid:
                return safe_color
            else:
                return "#1f77b4"  # Fallback color

        except Exception:
            return "#1f77b4"  # Fallback color on error

    def _sanitize_css(self, css: str) -> str:
        """
        Sanitize CSS values using bleach CSS sanitizer.

        Args:
            css: CSS value to sanitize

        Returns:
            Sanitized CSS or fallback value
        """
        try:
            if not css:
                return ""

            # Use bleach CSS sanitizer to clean the CSS
            clean_css = self.css_sanitizer.sanitize(css)
            return clean_css if clean_css else ""

        except Exception:
            return ""

    def _create_safe_mention_span(self, name: str, color: str) -> str:
        """
        Create a safe HTML span for highlighted mentions.

        Args:
            name: Sanitized persona name
            color: Validated color

        Returns:
            Safe HTML span element
        """
        safe_name = self.sanitize_text(name)
        safe_color = self._sanitize_color(color)

        # Create span with inline styles
        span_html = (
            f'<span style="background-color: {safe_color}; color: white; '
            f'padding: 1px 4px; border-radius: 3px; font-weight: bold;">'
            f'@{safe_name}</span>'
        )

        # Sanitize the generated HTML
        return self.sanitize_html(span_html)

    def sanitize_text(self, text: str) -> str:
        """
        Sanitize plain text content.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        try:
            # HTML escape the text
            import html
            return html.escape(str(text), quote=True)
        except Exception as e:
            logger.error(f"Text sanitization failed: {e}")
            return ""

    def render_with_fallback(
        self,
        html_content: str,
        fallback_text: Optional[str] = None,
        enable_markdown: bool = False
    ) -> str:
        """
        Render HTML content with comprehensive fallback mechanisms.

        Args:
            html_content: HTML content to render
            fallback_text: Optional fallback text if rendering fails
            enable_markdown: Whether to preserve markdown formatting

        Returns:
            Safely rendered content or fallback
        """
        if not html_content:
            return ""

        try:
            # Primary sanitization
            clean_content = self.sanitize_html(html_content)

            if clean_content:
                return clean_content
            else:
                # Fallback to plain text
                return self.sanitize_text(fallback_text or html_content)

        except Exception as e:
            logger.error(f"Secure rendering failed: {e}")

            # Final fallback: plain escaped text
            try:
                import html
                return html.escape(fallback_text or html_content, quote=True)
            except Exception:
                return "Content unavailable"


# Global instance for convenient usage
secure_renderer = SecureHTMLRenderer()


def sanitize_html_content(html_content: str) -> str:
    """
    Convenience function to sanitize HTML content using the global renderer.

    Args:
        html_content: HTML content to sanitize

    Returns:
        Sanitized HTML content
    """
    return secure_renderer.sanitize_html(html_content)


def render_secure_content_with_mentions(content: str, personas: List) -> str:
    """
    Convenience function to render content with secure mention highlighting.

    Args:
        content: Content with potential @mentions
        personas: List of persona objects

    Returns:
        Securely rendered content
    """
    return secure_renderer.render_content_with_mentions(content, personas)


def create_secure_html_renderer(
    allowed_tags: Optional[Set[str]] = None,
    allowed_attributes: Optional[Dict[str, Set[str]]] = None,
    allowed_css_properties: Optional[Set[str]] = None
) -> SecureHTMLRenderer:
    """
    Create a new SecureHTMLRenderer instance with custom configuration.

    Args:
        allowed_tags: Custom whitelist of HTML tags
        allowed_attributes: Custom whitelist of HTML attributes
        allowed_css_properties: Custom whitelist of CSS properties

    Returns:
        Configured SecureHTMLRenderer instance
    """
    return SecureHTMLRenderer(
        allowed_tags=allowed_tags,
        allowed_attributes=allowed_attributes,
        allowed_css_properties=allowed_css_properties
    )