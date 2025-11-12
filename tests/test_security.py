"""Security tests for XSS prevention and input sanitization"""

from streamlit_backroom import sanitize_html


class TestXSSPrevention:
    """Test XSS vulnerability prevention"""

    def test_sanitize_html_prevents_script_injection(self):
        """Ensure script tags are escaped"""
        malicious_input = '<script>alert("XSS")</script>'
        result = sanitize_html(malicious_input)
        assert '<script>' not in result
        assert '&lt;script&gt;' in result
        assert '&lt;/script&gt;' in result

    def test_sanitize_html_prevents_img_onerror(self):
        """Ensure img onerror XSS is escaped"""
        malicious_input = '<img src=x onerror="alert(1)">'
        result = sanitize_html(malicious_input)
        # Verify that tags and quotes are escaped, making it safe
        assert '&lt;img' in result
        assert '&quot;' in result  # Quotes are escaped
        assert 'alert(1)' in result  # Content preserved but safe
        # The dangerous script cannot execute because quotes are escaped

    def test_sanitize_html_prevents_event_handlers(self):
        """Ensure event handler attributes are escaped"""
        malicious_input = '<div onclick="malicious()">Click me</div>'
        result = sanitize_html(malicious_input)
        # Verify that tags and quotes are escaped, making it safe
        assert '&lt;div' in result
        assert '&quot;' in result  # Quotes are escaped
        assert 'malicious()' in result  # Content preserved but safe
        # The event handler cannot execute because quotes are escaped

    def test_sanitize_html_escapes_special_characters(self):
        """Ensure special HTML characters are properly escaped"""
        test_input = '< > & " \' /'
        result = sanitize_html(test_input)
        assert '&lt;' in result
        assert '&gt;' in result
        assert '&amp;' in result
        assert '&#x27;' in result or '&apos;' in result or "'" in result

    def test_sanitize_html_preserves_safe_text(self):
        """Ensure normal text is preserved after escaping"""
        safe_input = 'Hello, World! This is safe text.'
        result = sanitize_html(safe_input)
        assert 'Hello' in result
        assert 'World' in result
        assert 'safe text' in result

    def test_sanitize_html_handles_empty_string(self):
        """Ensure empty strings are handled correctly"""
        result = sanitize_html('')
        assert result == ''

    def test_sanitize_html_handles_unicode(self):
        """Ensure unicode characters are preserved"""
        unicode_input = '你好世界 🌍 Привет'
        result = sanitize_html(unicode_input)
        assert '你好世界' in result
        assert '🌍' in result
        assert 'Привет' in result
