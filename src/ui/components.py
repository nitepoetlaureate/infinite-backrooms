"""Reusable UI components for the Streamlit app."""

from __future__ import annotations

import streamlit as st

from src.models.persona import AIPersona
from src.utils.constants import DEFAULT_FALLBACK_EMOJI, ROLE_EMOJI_MAP
try:
    from src.utils.html_sanitizer import secure_renderer
except ImportError:
    from src.utils.html_sanitizer_simple import secure_renderer


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

    Security:
        - Uses secure HTML renderer to prevent XSS
        - Validates color format to prevent CSS injection
        - Provides fallback mechanisms for rendering failures
    """
    # Sanitize inputs using secure renderer
    safe_name = secure_renderer.sanitize_text(persona.name)
    safe_color = secure_renderer._sanitize_color(persona.color)

    # Create persona name styling
    persona_name_html = (
        f'<span style="background-color: {safe_color}; color: white; '
        f'padding: 2px 8px; border-radius: 4px; font-weight: bold;">'
        f"{safe_name}</span>"
    )

    # Add role information if requested
    if show_role and persona.role:
        role_emoji = ROLE_EMOJI_MAP.get(persona.role, "")
        safe_role = secure_renderer.sanitize_text(persona.role)
        persona_html = f"{persona_name_html} {role_emoji} _{safe_role}_"
    else:
        persona_html = persona_name_html

    # Render using secure HTML renderer with fallback
    safe_display = secure_renderer.render_with_fallback(
        persona_html,
        fallback_text=f"{safe_name} ({persona.role})" if show_role and persona.role else safe_name
    )

    st.markdown(safe_display, unsafe_allow_html=False)


def render_persona_list_item(persona: AIPersona) -> None:
    """Render a single persona in a list with colored badge.

    Args:
        persona: Persona to render

    Security:
        - Uses secure HTML renderer to prevent XSS
        - Validates color format to prevent CSS injection
        - Provides fallback mechanisms for rendering failures
    """
    role_emoji = ROLE_EMOJI_MAP.get(persona.role, DEFAULT_FALLBACK_EMOJI) if persona.role else DEFAULT_FALLBACK_EMOJI
    safe_role = secure_renderer.sanitize_text(persona.role) if persona.role else ""
    role_text = f" ({safe_role})" if safe_role else ""

    # Sanitize inputs
    safe_name = secure_renderer.sanitize_text(persona.name)
    safe_color = secure_renderer._sanitize_color(persona.color)

    # Create persona styling
    persona_name_html = (
        f'<span style="background-color: {safe_color}; color: white; '
        f'padding: 2px 6px; border-radius: 3px; font-weight: bold; font-size: 0.9em;">'
        f"{safe_name}</span>"
    )

    persona_html = f"{role_emoji} {persona_name_html}{role_text}"

    # Render using secure HTML renderer with fallback
    safe_display = secure_renderer.render_with_fallback(
        persona_html,
        fallback_text=f"{safe_name}{role_text}"
    )

    st.markdown(safe_display, unsafe_allow_html=False)


def highlight_mentions(content: str, personas: list[AIPersona]) -> str:
    """Highlight @mentions in message content with persona colors.

    Args:
        content: Message content potentially containing @mentions
        personas: List of personas to check for mentions

    Returns:
        Content with securely highlighted @mentions

    Security:
        - Uses secure HTML renderer for all content processing
        - Only highlights exact @mention matches
        - Validates colors before use
        - Provides comprehensive fallback mechanisms
    """
    # Use secure renderer for mention highlighting
    return secure_renderer.render_content_with_mentions(content, personas)


def render_markdown_content(content: str, allow_mentions: bool = True, personas: list[AIPersona] | None = None) -> None:
    """Render markdown content with optional @mention highlighting.

    Args:
        content: Markdown content to render
        allow_mentions: Whether to highlight @mentions
        personas: List of personas for mention highlighting

    Security:
        - Uses secure HTML rendering
        - Prevents XSS through comprehensive sanitization
        - Provides fallback for rendering failures
    """
    if not content:
        st.write("")
        return

    try:
        # Process mentions if requested and personas provided
        if allow_mentions and personas:
            processed_content = highlight_mentions(content, personas)
        else:
            # Sanitize plain content
            processed_content = secure_renderer.sanitize_text(content)

        # Render with fallback
        safe_content = secure_renderer.render_with_fallback(
            processed_content,
            fallback_text=content,
            enable_markdown=True
        )

        st.markdown(safe_content, unsafe_allow_html=False)

    except Exception as e:
        # Ultimate fallback: plain text
        import logging
        logging.error(f"Markdown rendering failed: {e}")
        st.write(content)


def create_safe_html_element(
    tag: str,
    content: str,
    style: str | None = None,
    css_class: str | None = None,
    **attributes
) -> str:
    """Create a safe HTML element with sanitized content and attributes.

    Args:
        tag: HTML tag name
        content: Content for the element
        style: Optional CSS style
        css_class: Optional CSS class
        **attributes: Additional HTML attributes

    Returns:
        Sanitized HTML element string

    Security:
        - Sanitizes all content and attributes
        - Validates CSS properties
        - Uses secure HTML renderer for final output
    """
    # Sanitize content
    safe_content = secure_renderer.sanitize_text(content)

    # Build attributes
    attrs = []
    if style:
        safe_style = secure_renderer._sanitize_css(style) if hasattr(secure_renderer, '_sanitize_css') else ""
        if safe_style:
            attrs.append(f'style="{safe_style}"')
    if css_class:
        safe_class = secure_renderer.sanitize_text(css_class)
        attrs.append(f'class="{safe_class}"')

    # Add other attributes
    for key, value in attributes.items():
        if value is not None:
            safe_key = secure_renderer.sanitize_text(str(key))
            safe_value = secure_renderer.sanitize_text(str(value))
            attrs.append(f'{safe_key}="{safe_value}"')

    attr_string = ' ' + ' '.join(attrs) if attrs else ''
    html_element = f'<{tag}{attr_string}>{safe_content}</{tag}>'

    # Final sanitization using secure renderer
    return secure_renderer.sanitize_html(html_element)