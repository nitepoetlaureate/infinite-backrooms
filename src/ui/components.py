"""Reusable UI components for the Streamlit app."""

from __future__ import annotations

import streamlit as st

from src.models.persona import AIPersona
from src.utils.constants import DEFAULT_FALLBACK_EMOJI, ROLE_EMOJI_MAP


def get_persona_avatar(persona: AIPersona | None) -> str:
    """Get avatar emoji for persona based on role.

    Args:
        persona: AI persona (can be None for fallback)

    Returns:
        Emoji string to use as avatar
    """
    if persona is None:
        return DEFAULT_FALLBACK_EMOJI

    if persona.role in ROLE_EMOJI_MAP:
        return ROLE_EMOJI_MAP[persona.role]
    else:
        return DEFAULT_FALLBACK_EMOJI


def render_persona_header(persona: AIPersona, show_role: bool = True) -> None:
    """Render persona header with name, role, and styling.

    Args:
        persona: AI persona to display
        show_role: Whether to show role text
    """
    persona_name_styled = (
        f'<span style="background-color: {persona.color}; color: white; '
        f'padding: 2px 8px; border-radius: 4px; font-weight: bold;">'
        f"{persona.name}</span>"
    )

    if show_role and persona.role:
        role_emoji = ROLE_EMOJI_MAP.get(persona.role, "")
        persona_display = f"{persona_name_styled} {role_emoji} _{persona.role}_"
    else:
        persona_display = persona_name_styled

    st.markdown(persona_display, unsafe_allow_html=True)


def render_persona_list_item(persona: AIPersona) -> None:
    """Render a single persona in a list with colored badge.

    Args:
        persona: Persona to render
    """
    role_emoji = ROLE_EMOJI_MAP.get(persona.role, DEFAULT_FALLBACK_EMOJI) if persona.role else DEFAULT_FALLBACK_EMOJI
    role_text = f" ({persona.role})" if persona.role else ""

    persona_name_styled = (
        f'<span style="background-color: {persona.color}; color: white; '
        f'padding: 2px 6px; border-radius: 3px; font-weight: bold; font-size: 0.9em;">'
        f"{persona.name}</span>"
    )
    persona_display = f"{role_emoji} {persona_name_styled}{role_text}"

    st.markdown(persona_display, unsafe_allow_html=True)


def highlight_mentions(content: str, personas: list[AIPersona]) -> str:
    """Highlight @mentions in message content with persona colors.

    Args:
        content: Message content potentially containing @mentions
        personas: List of personas to check for mentions

    Returns:
        Content with HTML-highlighted @mentions
    """
    for persona in personas:
        mention_pattern = f"@{persona.name}"
        if mention_pattern in content:
            highlighted_mention = (
                f'<span style="background-color: {persona.color}; color: white; '
                f'padding: 1px 4px; border-radius: 3px; font-weight: bold;">@{persona.name}</span>'
            )
            content = content.replace(mention_pattern, highlighted_mention)
    return content
