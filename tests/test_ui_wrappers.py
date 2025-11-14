"""Tests for UI wrapper modules."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.ui.conversation_ui import render_conversation
from src.ui.persona_ui import render_persona_management
from src.ui.settings_ui import render_export, render_settings


class TestPersonaUI:
    """Tests for persona_ui module."""

    def test_render_persona_management_calls_app_method(self) -> None:
        """Test that render_persona_management delegates to app.persona_management_ui()."""
        mock_app = MagicMock()

        render_persona_management(mock_app)

        mock_app.persona_management_ui.assert_called_once()

    def test_render_persona_management_with_different_app(self) -> None:
        """Test render_persona_management with different app instances."""
        mock_app1 = MagicMock()
        mock_app2 = MagicMock()

        render_persona_management(mock_app1)
        render_persona_management(mock_app2)

        mock_app1.persona_management_ui.assert_called_once()
        mock_app2.persona_management_ui.assert_called_once()


class TestConversationUI:
    """Tests for conversation_ui module."""

    def test_render_conversation_calls_app_method(self) -> None:
        """Test that render_conversation delegates to app.conversation_ui()."""
        mock_app = MagicMock()

        render_conversation(mock_app)

        mock_app.conversation_ui.assert_called_once()

    def test_render_conversation_with_different_app(self) -> None:
        """Test render_conversation with different app instances."""
        mock_app1 = MagicMock()
        mock_app2 = MagicMock()

        render_conversation(mock_app1)
        render_conversation(mock_app2)

        mock_app1.conversation_ui.assert_called_once()
        mock_app2.conversation_ui.assert_called_once()


class TestSettingsUI:
    """Tests for settings_ui module."""

    def test_render_settings_calls_app_method(self) -> None:
        """Test that render_settings delegates to app.settings_ui()."""
        mock_app = MagicMock()

        render_settings(mock_app)

        mock_app.settings_ui.assert_called_once()

    def test_render_settings_with_different_app(self) -> None:
        """Test render_settings with different app instances."""
        mock_app1 = MagicMock()
        mock_app2 = MagicMock()

        render_settings(mock_app1)
        render_settings(mock_app2)

        mock_app1.settings_ui.assert_called_once()
        mock_app2.settings_ui.assert_called_once()

    def test_render_export_calls_app_method(self) -> None:
        """Test that render_export delegates to app.export_ui()."""
        mock_app = MagicMock()

        render_export(mock_app)

        mock_app.export_ui.assert_called_once()

    def test_render_export_with_different_app(self) -> None:
        """Test render_export with different app instances."""
        mock_app1 = MagicMock()
        mock_app2 = MagicMock()

        render_export(mock_app1)
        render_export(mock_app2)

        mock_app1.export_ui.assert_called_once()
        mock_app2.export_ui.assert_called_once()
