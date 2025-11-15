"""Accessibility improvements for the UI."""

import streamlit as st

from src.utils.html_sanitizer import secure_renderer


def accessible_button(
    label: str,
    key: str | None = None,
    help_text: str | None = None,
    shortcut: str | None = None,
    **kwargs,
) -> bool:
    """Create an accessible button with additional help text.

    Args:
        label: Button label
        key: Unique key for the button
        help_text: Additional help text
        shortcut: Keyboard shortcut hint (e.g., "Ctrl+Enter")
        **kwargs: Additional arguments passed to st.button

    Returns:
        True if button was clicked

    Example:
        >>> if accessible_button("Start", help_text="Begin conversation", shortcut="Ctrl+S"):
        ...     start_conversation()
    """
    # Add shortcut to help text if provided
    full_help = help_text or ""
    if shortcut:
        full_help = f"{full_help} [Shortcut: {shortcut}]" if full_help else f"Keyboard shortcut: {shortcut}"

    # Pass help text to button
    if full_help:
        kwargs["help"] = full_help

    return st.button(label, key=key, **kwargs)


def screen_reader_text(text: str) -> None:
    """Add screen reader only text using secure CSS.

    Args:
        text: Text visible only to screen readers

    Example:
        >>> screen_reader_text("This section contains conversation controls")
    """
    # Create screen reader only HTML
    sr_html = f'''
    <span class="sr-only" style="
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0,0,0,0);
        white-space: nowrap;
        border-width: 0;
    ">{text}</span>
    '''

    # Sanitize the HTML and render securely
    safe_sr_html = secure_renderer.render_with_fallback(
        sr_html,
        fallback_text=""  # Screen reader text should be invisible if rendering fails
    )

    if safe_sr_html:
        st.markdown(safe_sr_html, unsafe_allow_html=True)  # Safe since we've sanitized it


def accessible_header(title: str, level: int = 1, help_text: str | None = None) -> None:
    """Create an accessible header with optional help text.

    Args:
        title: Header text
        level: Header level (1-6)
        help_text: Additional help text for accessibility

    Example:
        >>> accessible_header("Conversation Settings", level=2, help_text="Configure conversation parameters")
    """
    if level < 1 or level > 6:
        level = 1

    # Create header with optional help
    header_content = title
    if help_text:
        header_content = f"{title} <span class='header-help' style='font-size: 0.8em; color: #666;'>({help_text})</span>"

    # Sanitize and render
    safe_header = secure_renderer.render_with_fallback(
        f"<h{level}>{header_content}</h{level}>",
        fallback_text=f"{'#' * level} {title}" + (f" ({help_text})" if help_text else "")
    )

    if safe_header:
        st.markdown(safe_header, unsafe_allow_html=True)  # Safe since we've sanitized it


def accessible_label(text: str, for_input: str | None = None) -> None:
    """Create an accessible label for form inputs.

    Args:
        text: Label text
        for_input: ID of the input this label is for

    Example:
        >>> accessible_label("Persona Name", for_input="persona_name_input")
        >>> st.text_input("", key="persona_name_input")
    """
    label_attrs = f' for="{for_input}"' if for_input else ""
    label_html = f'<label{label_attrs}>{text}</label>'

    # Sanitize and render
    safe_label = secure_renderer.render_with_fallback(
        label_html,
        fallback_text=f"{text}:"
    )

    if safe_label:
        st.markdown(safe_label, unsafe_allow_html=True)  # Safe since we've sanitized it


def add_accessibility_attributes():
    """Add accessibility attributes to the page using secure HTML."""
    accessibility_html = """
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="AI conversation platform with multiple personas">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">

    <style>
        /* Focus styles for keyboard navigation */
        *:focus {
            outline: 2px solid #4CAF50 !important;
            outline-offset: 2px !important;
        }

        /* Skip to main content link */
        .skip-link {
            position: absolute;
            top: -40px;
            left: 6px;
            background: #4CAF50;
            color: white;
            padding: 8px;
            text-decoration: none;
            border-radius: 4px;
            z-index: 1000;
        }

        .skip-link:focus {
            top: 6px;
        }

        /* Screen reader only text */
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0,0,0,0);
            white-space: nowrap;
            border-width: 0;
        }

        /* High contrast mode support */
        @media (prefers-contrast: high) {
            * {
                border-width: 2px !important;
            }
        }

        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
    </style>

    <!-- Skip to main content -->
    <a href="#main-content" class="skip-link">Skip to main content</a>

    <!-- Main content landmark -->
    <main id="main-content" role="main">
    """

    # Sanitize the accessibility HTML
    safe_accessibility = secure_renderer.render_with_fallback(
        accessibility_html,
        fallback_text=""
    )

    if safe_accessibility:
        st.markdown(safe_accessibility, unsafe_allow_html=True)  # Safe since we've sanitized it


def accessible_status(message: str, status_type: str = "info") -> None:
    """Create an accessible status message.

    Args:
        message: Status message text
        status_type: Type of status ("info", "success", "warning", "error")

    Example:
        >>> accessible_status("Conversation saved successfully", "success")
        >>> accessible_status("No personas enabled", "warning")
    """
    # Define status colors and icons
    status_config = {
        "info": {"icon": "ℹ️", "color": "#2196F3"},
        "success": {"icon": "✅", "color": "#4CAF50"},
        "warning": {"icon": "⚠️", "color": "#FF9800"},
        "error": {"icon": "❌", "color": "#F44336"}
    }

    config = status_config.get(status_type, status_config["info"])
    icon = config["icon"]
    color = config["color"]

    # Create accessible status HTML
    status_html = f'''
    <div role="alert" aria-live="polite" style="
        background-color: {color}20;
        border: 1px solid {color};
        border-radius: 4px;
        padding: 12px;
        margin: 10px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    ">
        <span aria-hidden="true">{icon}</span>
        <span>{message}</span>
    </div>
    '''

    # Sanitize and render
    safe_status = secure_renderer.render_with_fallback(
        status_html,
        fallback_text=f"{icon} {message}"
    )

    if safe_status:
        st.markdown(safe_status, unsafe_allow_html=True)  # Safe since we've sanitized it