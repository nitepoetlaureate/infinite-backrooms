"""Tests for UI components module."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.models.persona import AIPersona
from src.ui.components import (
    get_persona_avatar,
    highlight_mentions,
    render_persona_header,
    render_persona_list_item,
)


class TestGetPersonaAvatar:
    """Test get_persona_avatar function."""

    def test_get_avatar_with_none_persona(self):
        """Test avatar retrieval with None persona returns fallback."""
        avatar = get_persona_avatar(None)
        assert avatar == "🤖"  # DEFAULT_FALLBACK_EMOJI

    def test_get_avatar_with_known_role(self):
        """Test avatar retrieval with known role."""
        persona = AIPersona(
            id="test-1",
            name="TestBot",
            model="llama2:latest",
            role="creative",
            system_prompt="",
            color="#FF5733",
            enabled=True,
        )
        avatar = get_persona_avatar(persona)
        assert avatar == "🎨"  # creative role emoji

    def test_get_avatar_with_unknown_role(self):
        """Test avatar retrieval with unknown role returns fallback."""
        persona = AIPersona(
            id="test-1",
            name="TestBot",
            model="llama2:latest",
            role="unknown_role",
            system_prompt="",
            color="#FF5733",
            enabled=True,
        )
        avatar = get_persona_avatar(persona)
        assert avatar == "🤖"  # DEFAULT_FALLBACK_EMOJI

    def test_get_avatar_with_no_role(self):
        """Test avatar retrieval with empty role."""
        persona = AIPersona(
            id="test-1",
            name="TestBot",
            model="llama2:latest",
            role="",
            system_prompt="",
            color="#FF5733",
            enabled=True,
        )
        avatar = get_persona_avatar(persona)
        assert avatar == "🤖"  # DEFAULT_FALLBACK_EMOJI

    def test_get_avatar_with_analyst_role(self):
        """Test avatar for analyst role."""
        persona = AIPersona(
            id="test-1",
            name="Analyst",
            model="llama2:latest",
            role="analyst",
            system_prompt="",
            color="#FF5733",
            enabled=True,
        )
        avatar = get_persona_avatar(persona)
        assert avatar == "📊"

    def test_get_avatar_with_moderator_role(self):
        """Test avatar for moderator role."""
        persona = AIPersona(
            id="test-1",
            name="Moderator",
            model="llama2:latest",
            role="Moderator",
            system_prompt="",
            color="#FF5733",
            enabled=True,
        )
        avatar = get_persona_avatar(persona)
        assert avatar == "🎯"


class TestRenderPersonaHeader:
    """Test render_persona_header function."""

    @patch("src.ui.components.st")
    def test_render_header_with_role(self, mock_st):
        """Test rendering persona header with role displayed."""
        persona = AIPersona(
            id="test-1",
            name="TestBot",
            model="llama2:latest",
            role="creative",
            system_prompt="",
            color="#FF5733",
            enabled=True,
        )

        render_persona_header(persona, show_role=True)

        # Verify st.markdown was called
        mock_st.markdown.assert_called_once()
        call_args = mock_st.markdown.call_args

        # Check that the HTML contains the persona name
        assert "TestBot" in call_args[0][0]
        # Check that the color is in the style
        assert "#FF5733" in call_args[0][0]
        # Check that role is included
        assert "creative" in call_args[0][0]
        # Check unsafe_allow_html is True
        assert call_args[1]["unsafe_allow_html"] is True

    @patch("src.ui.components.st")
    def test_render_header_without_role(self, mock_st):
        """Test rendering persona header without role displayed."""
        persona = AIPersona(
            id="test-1",
            name="TestBot",
            model="llama2:latest",
            role="creative",
            system_prompt="",
            color="#FF5733",
            enabled=True,
        )

        render_persona_header(persona, show_role=False)

        mock_st.markdown.assert_called_once()
        call_args = mock_st.markdown.call_args

        # Check that the HTML contains the persona name but not role text
        assert "TestBot" in call_args[0][0]
        assert "creative" not in call_args[0][0].split("</span>")[-1]  # Role not after the span

    @patch("src.ui.components.st")
    def test_render_header_with_empty_role(self, mock_st):
        """Test rendering persona header with empty role."""
        persona = AIPersona(
            id="test-1",
            name="TestBot",
            model="llama2:latest",
            role="",
            system_prompt="",
            color="#FF5733",
            enabled=True,
        )

        render_persona_header(persona, show_role=True)

        mock_st.markdown.assert_called_once()
        call_args = mock_st.markdown.call_args

        # Should not include role emoji or text when role is empty
        assert "TestBot" in call_args[0][0]

    @patch("src.ui.components.st")
    def test_render_header_with_special_chars_in_name(self, mock_st):
        """Test rendering persona header with special characters in name."""
        persona = AIPersona(
            id="test-1",
            name="Test-Bot_123",
            model="llama2:latest",
            role="analyst",
            system_prompt="",
            color="#00FF00",
            enabled=True,
        )

        render_persona_header(persona, show_role=True)

        mock_st.markdown.assert_called_once()
        call_args = mock_st.markdown.call_args
        assert "Test-Bot_123" in call_args[0][0]


class TestRenderPersonaListItem:
    """Test render_persona_list_item function."""

    @patch("src.ui.components.st")
    def test_render_list_item_with_role(self, mock_st):
        """Test rendering persona list item with role."""
        persona = AIPersona(
            id="test-1",
            name="TestBot",
            model="llama2:latest",
            role="creative",
            system_prompt="",
            color="#FF5733",
            enabled=True,
        )

        render_persona_list_item(persona)

        mock_st.markdown.assert_called_once()
        call_args = mock_st.markdown.call_args

        # Check that the HTML contains persona name and role
        assert "TestBot" in call_args[0][0]
        assert "creative" in call_args[0][0]
        assert "#FF5733" in call_args[0][0]

    @patch("src.ui.components.st")
    def test_render_list_item_without_role(self, mock_st):
        """Test rendering persona list item without role."""
        persona = AIPersona(
            id="test-1",
            name="TestBot",
            model="llama2:latest",
            role="",
            system_prompt="",
            color="#FF5733",
            enabled=True,
        )

        render_persona_list_item(persona)

        mock_st.markdown.assert_called_once()
        call_args = mock_st.markdown.call_args

        # Check that it renders without role text
        assert "TestBot" in call_args[0][0]
        # Should not have role text in parentheses when role is empty
        assert "()" not in call_args[0][0]

    @patch("src.ui.components.st")
    def test_render_list_item_with_emoji(self, mock_st):
        """Test that list item includes emoji for role."""
        persona = AIPersona(
            id="test-1",
            name="Analyst",
            model="llama2:latest",
            role="analyst",
            system_prompt="",
            color="#0000FF",
            enabled=True,
        )

        render_persona_list_item(persona)

        mock_st.markdown.assert_called_once()
        call_args = mock_st.markdown.call_args

        # Should include the analyst emoji
        assert "📊" in call_args[0][0] or "🤖" in call_args[0][0]


class TestHighlightMentions:
    """Test highlight_mentions function."""

    def test_highlight_single_mention(self):
        """Test highlighting a single @mention."""
        personas = [
            AIPersona(
                id="alice-1",
                name="Alice",
                model="llama2:latest",
                role="creative",
                system_prompt="",
                color="#FF5733",
                enabled=True,
            )
        ]

        content = "Hey @Alice, what do you think?"
        result = highlight_mentions(content, personas)

        # Check that @Alice is highlighted with her color
        assert "#FF5733" in result
        assert "@Alice" in result
        assert "<span" in result

    def test_highlight_multiple_mentions(self):
        """Test highlighting multiple @mentions."""
        personas = [
            AIPersona(
                id="alice-1",
                name="Alice",
                model="llama2:latest",
                role="creative",
                system_prompt="",
                color="#FF5733",
                enabled=True,
            ),
            AIPersona(
                id="bob-1",
                name="Bob",
                model="llama2:latest",
                role="analyst",
                system_prompt="",
                color="#33C3FF",
                enabled=True,
            ),
        ]

        content = "@Alice and @Bob, let's discuss this."
        result = highlight_mentions(content, personas)

        # Check that both are highlighted
        assert "#FF5733" in result
        assert "#33C3FF" in result
        assert "@Alice" in result
        assert "@Bob" in result

    def test_highlight_no_mentions(self):
        """Test content with no @mentions."""
        personas = [
            AIPersona(
                id="alice-1",
                name="Alice",
                model="llama2:latest",
                role="creative",
                system_prompt="",
                color="#FF5733",
                enabled=True,
            )
        ]

        content = "This is a regular message without mentions."
        result = highlight_mentions(content, personas)

        # Content should be unchanged
        assert result == content

    def test_highlight_empty_personas_list(self):
        """Test highlighting with empty personas list."""
        personas = []
        content = "@Alice, are you there?"
        result = highlight_mentions(content, personas)

        # Content should be unchanged
        assert result == content

    def test_highlight_partial_match_not_highlighted(self):
        """Test that partial matches are not highlighted."""
        personas = [
            AIPersona(
                id="alice-1",
                name="Alice",
                model="llama2:latest",
                role="creative",
                system_prompt="",
                color="#FF5733",
                enabled=True,
            )
        ]

        # "Alicia" contains "Alice" but should not be highlighted
        content = "Alicia is a different person from @Alice."
        result = highlight_mentions(content, personas)

        # Only @Alice should be highlighted
        assert result.count("<span") == 1

    def test_highlight_case_sensitive(self):
        """Test that mentions are case-sensitive."""
        personas = [
            AIPersona(
                id="alice-1",
                name="Alice",
                model="llama2:latest",
                role="creative",
                system_prompt="",
                color="#FF5733",
                enabled=True,
            )
        ]

        content = "@Alice is here but @alice is not the same."
        result = highlight_mentions(content, personas)

        # Only @Alice should be highlighted (case-sensitive)
        assert result.count("<span") == 1

    def test_highlight_multiple_mentions_same_persona(self):
        """Test highlighting multiple mentions of the same persona."""
        personas = [
            AIPersona(
                id="alice-1",
                name="Alice",
                model="llama2:latest",
                role="creative",
                system_prompt="",
                color="#FF5733",
                enabled=True,
            )
        ]

        content = "@Alice, I agree with @Alice completely."
        result = highlight_mentions(content, personas)

        # Both mentions should be highlighted
        assert result.count("<span") == 2
        assert result.count("#FF5733") == 2

    def test_highlight_preserves_surrounding_text(self):
        """Test that highlighting preserves surrounding text."""
        personas = [
            AIPersona(
                id="alice-1",
                name="Alice",
                model="llama2:latest",
                role="creative",
                system_prompt="",
                color="#FF5733",
                enabled=True,
            )
        ]

        content = "Hello @Alice, how are you today?"
        result = highlight_mentions(content, personas)

        # Check that surrounding text is preserved
        assert "Hello" in result
        assert "how are you today?" in result

    def test_highlight_with_special_html_chars(self):
        """Test highlighting doesn't break with special HTML characters."""
        personas = [
            AIPersona(
                id="alice-1",
                name="Alice",
                model="llama2:latest",
                role="creative",
                system_prompt="",
                color="#FF5733",
                enabled=True,
            )
        ]

        content = "@Alice, what about <html> & entities?"
        result = highlight_mentions(content, personas)

        # Should contain the highlight
        assert "@Alice" in result
        assert "#FF5733" in result
        # Original special chars should be preserved
        assert "<html>" in result
        assert "&" in result
