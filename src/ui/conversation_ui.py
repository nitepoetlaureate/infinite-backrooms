"""Conversation UI module.

This module contains UI components for displaying and managing the conversation interface.
Currently wraps the StreamlitBackroomApp.conversation_ui() method.

Future refactoring will extract this into standalone functions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def render_conversation(app: Any) -> None:
    """Render the conversation UI.

    Args:
        app: StreamlitBackroomApp instance

    Note:
        This is currently a wrapper that delegates to the app's conversation_ui() method.
        Future versions will extract this logic into standalone, testable functions.
    """
    app.conversation_ui()
