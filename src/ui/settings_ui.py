"""Settings UI module.

This module contains UI components for application settings and configuration.
Currently wraps the StreamlitBackroomApp.settings_ui() method.

Future refactoring will extract this into standalone functions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def render_settings(app: Any) -> None:
    """Render the settings UI.

    Args:
        app: StreamlitBackroomApp instance

    Note:
        This is currently a wrapper that delegates to the app's settings_ui() method.
        Future versions will extract this logic into standalone, testable functions.
    """
    app.settings_ui()


def render_export(app: Any) -> None:
    """Render the export and logs UI.

    Args:
        app: StreamlitBackroomApp instance

    Note:
        This is currently a wrapper that delegates to the app's export_ui() method.
        Future versions will extract this logic into standalone, testable functions.
    """
    app.export_ui()
