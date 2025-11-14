"""Persona management UI module.

This module contains UI components for creating, managing, and configuring AI personas.
Currently wraps the StreamlitBackroomApp.persona_management_ui() method.

Future refactoring will extract this into standalone functions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def render_persona_management(app: Any) -> None:
    """Render the persona management UI.

    Args:
        app: StreamlitBackroomApp instance

    Note:
        This is currently a wrapper that delegates to the app's persona_management_ui() method.
        Future versions will extract this logic into standalone, testable functions.
    """
    app.persona_management_ui()
