"""Tests for the HTML sanitizer module."""

import pytest
from src.utils.html_sanitizer import SecureHTMLRenderer, secure_renderer


class TestSecureHTMLRenderer:
    """Test cases for SecureHTMLRenderer."""

    def test_basic_html_sanitization(self):
        """Test basic HTML sanitization removes dangerous content."""
        dangerous_html = "<script>alert('xss')</script><p>Safe content</p>"
        renderer = SecureHTMLRenderer()
        result = renderer.sanitize_html(dangerous_html)

        # Script tag should be removed
        assert "<script>" not in result
        assert "alert('xss')" not in result
        # Safe content should remain
        assert "Safe content" in result

    def test_css_sanitization(self):
        """Test CSS sanitization removes dangerous CSS."""
        dangerous_css = "background-color: red; javascript:alert('xss')"
        renderer = SecureHTMLRenderer()
        result = renderer._sanitize_css(dangerous_css)

        # Dangerous CSS should be removed
        assert "javascript:" not in result
        # Safe CSS should remain
        assert "background-color: red" in result

    def test_text_sanitization(self):
        """Test text sanitization escapes HTML."""
        dangerous_text = "<script>alert('xss')</script>"
        renderer = SecureHTMLRenderer()
        result = renderer.sanitize_text(dangerous_text)

        # Should be HTML escaped
        assert "&lt;script&gt;" in result
        assert "<script>" not in result

    def test_mention_highlighting(self):
        """Test secure @mention highlighting."""
        from src.models.persona import AIPersona

        persona = AIPersona(
            name="TestPersona",
            role="assistant",
            color="#FF0000"
        )
        content = "Hello @TestPersona, how are you?"
        personas = [persona]

        renderer = SecureHTMLRenderer()
        result = renderer.render_content_with_mentions(content, personas)

        # Should contain highlighted mention
        assert "@TestPersona" in result
        assert "background-color" in result
        assert "#FF0000" in result

    def test_render_with_fallback(self):
        """Test render_with_fallback provides fallback on error."""
        malicious_html = "<img src=x onerror=alert('xss')>"
        renderer = SecureHTMLRenderer()
        result = renderer.render_with_fallback(
            malicious_html,
            fallback_text="Safe fallback"
        )

        # Should provide safe fallback
        assert "Safe fallback" in result or "&lt;img" in result
        assert "onerror" not in result

    def test_global_secure_renderer(self):
        """Test the global secure_renderer instance."""
        assert isinstance(secure_renderer, SecureHTMLRenderer)

        # Test basic functionality
        result = secure_renderer.sanitize_text("<script>alert('test')</script>")
        assert "&lt;script&gt;" in result
        assert "<script>" not in result


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_sanitize_html_content(self):
        """Test sanitize_html_content convenience function."""
        from src.utils.html_sanitizer import sanitize_html_content

        result = sanitize_html_content("<script>alert('xss')</script><p>Safe</p>")
        assert "<script>" not in result
        assert "Safe" in result

    def test_render_secure_content_with_mentions(self):
        """Test render_secure_content_with_mentions convenience function."""
        from src.utils.html_sanitizer import render_secure_content_with_mentions
        from src.models.persona import AIPersona

        persona = AIPersona(name="Test", role="assistant", color="#FF0000")
        content = "Hello @Test"
        result = render_secure_content_with_mentions(content, [persona])

        assert "@Test" in result
        assert "background-color" in result

    def test_create_secure_html_renderer(self):
        """Test create_secure_html_renderer convenience function."""
        from src.utils.html_sanitizer import create_secure_html_renderer

        custom_renderer = create_secure_html_renderer(
            allowed_tags={"b", "i"},
            allowed_css_properties={"color"}
        )

        assert isinstance(custom_renderer, SecureHTMLRenderer)
        assert "b" in custom_renderer.ALLOWED_TAGS
        assert "script" not in custom_renderer.ALLOWED_TAGS


if __name__ == "__main__":
    pytest.main([__file__])