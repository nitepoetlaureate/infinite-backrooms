"""Accessibility improvements for the UI."""

from typing import Any

import streamlit as st


def accessible_button(
    label: str,
    key: str | None = None,
    help_text: str | None = None,
    shortcut: str | None = None,
    **kwargs: Any,
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
        full_help = (
            f"{full_help} [Shortcut: {shortcut}]" if full_help else f"Keyboard shortcut: {shortcut}"
        )

    # Pass help text to button
    if full_help:
        kwargs["help"] = full_help

    return bool(st.button(label, key=key, **kwargs))


def screen_reader_text(text: str) -> None:
    """Add screen reader only text using CSS.

    Args:
        text: Text visible only to screen readers

    Example:
        >>> screen_reader_text("This section contains conversation controls")
    """
    st.markdown(
        f"""
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
        """,
        unsafe_allow_html=True,
    )


def accessible_header(title: str, level: int = 1, help_text: str | None = None) -> None:
    """Create an accessible header with optional help text.

    Args:
        title: Header text
        level: Header level (1-6)
        help_text: Optional help text to display

    Example:
        >>> accessible_header("Conversation Settings", level=2, help_text="Configure your chat")
    """
    # Create header
    header_func = getattr(st, "header" if level == 1 else "subheader" if level == 2 else "markdown")

    if level <= 2:
        header_func(title)
    else:
        st.markdown(f"{'#' * level} {title}")

    # Add help text if provided
    if help_text:
        st.caption(help_text)


def accessible_form_field(
    field_type: str,
    label: str,
    key: str,
    help_text: str | None = None,
    required: bool = False,
    **kwargs: Any,
) -> Any:
    """Create an accessible form field with consistent labeling.

    Args:
        field_type: Type of field ("text_input", "number_input", "selectbox", etc.)
        label: Field label
        key: Unique key
        help_text: Help text for the field
        required: Whether field is required
        **kwargs: Additional arguments for the field

    Returns:
        Field value

    Example:
        >>> name = accessible_form_field("text_input", "Name", "persona_name", required=True)
    """
    # Add required indicator to label
    if required:
        display_label = f"{label} *"
    else:
        display_label = label

    # Get the appropriate Streamlit function
    field_func = getattr(st, field_type)

    # Add help text if provided
    if help_text:
        kwargs["help"] = help_text

    # Create the field
    return field_func(display_label, key=key, **kwargs)


def add_keyboard_navigation_hints() -> None:
    """Display keyboard navigation hints for the application."""
    with st.expander("⌨️ Keyboard Navigation & Accessibility", expanded=False):
        st.markdown(
            """
            ### Keyboard Shortcuts

            - **Tab** - Navigate between interactive elements
            - **Shift+Tab** - Navigate backwards
            - **Enter** - Activate focused button or submit form
            - **Space** - Toggle checkboxes and buttons
            - **Esc** - Close dialogs and expanders
            - **Ctrl+Enter** - Submit chat input

            ### Screen Reader Support

            This application is designed to work with screen readers:
            - All buttons have descriptive labels
            - Form fields have associated labels
            - Status messages are announced
            - Interactive elements are keyboard accessible

            ### Accessibility Features

            - ✅ High contrast text and UI elements
            - ✅ Keyboard-only navigation
            - ✅ Descriptive button labels
            - ✅ Help text for all controls
            - ✅ Consistent navigation structure
            - ✅ Skip to main content (implicit via tabs)

            ### Tips for Better Experience

            - Use **Tab** to quickly navigate forms
            - Listen for status announcements when actions complete
            - Use expanders to manage information density
            - Adjust text size in your browser (Ctrl +/-)
            """
        )


def add_color_contrast_info() -> None:
    """Display information about color contrast and theme support."""
    st.caption(
        """
        💡 **Tip:** This app respects your system theme (light/dark mode).
        Adjust your browser or system theme settings for optimal viewing.
        """
    )


def accessible_status_message(
    message: str, status_type: str = "info", icon: str | None = None
) -> None:
    """Display an accessible status message.

    Args:
        message: Message text
        status_type: Type of message ("success", "info", "warning", "error")
        icon: Optional icon override

    Example:
        >>> accessible_status_message("Connection successful!", "success")
    """
    # Map status types to Streamlit functions and default icons
    status_map = {
        "success": (st.success, "✅"),
        "info": (st.info, "ℹ️"),
        "warning": (st.warning, "⚠️"),
        "error": (st.error, "❌"),
    }

    func, default_icon = status_map.get(status_type, (st.info, "ℹ️"))
    display_icon = icon or default_icon

    func(f"{display_icon} {message}")


def add_accessibility_statement() -> None:
    """Display accessibility statement for the application."""
    with st.expander("♿ Accessibility Statement"):
        st.markdown(
            """
            ### Our Commitment to Accessibility

            Infinite AI Backrooms is committed to ensuring digital accessibility
            for people with disabilities. We are continually improving the user
            experience for everyone and applying relevant accessibility standards.

            ### Conformance Status

            We aim to conform with WCAG 2.1 Level AA standards. This includes:

            - **Perceivable**: Information and UI components are presentable to users
            - **Operable**: UI components and navigation are operable
            - **Understandable**: Information and UI operation are understandable
            - **Robust**: Content is robust enough for assistive technologies

            ### Features

            - Keyboard navigation throughout the application
            - Screen reader compatibility
            - High contrast UI elements
            - Descriptive labels and help text
            - Consistent navigation structure

            ### Feedback

            We welcome feedback on the accessibility of Infinite AI Backrooms.
            If you encounter accessibility barriers, please let us know:

            - GitHub Issues: Report accessibility issues
            - Email: Contact the maintainers

            We will work to resolve the issue as quickly as possible.

            ### Technical Specifications

            - Built with Streamlit (web framework)
            - Compatible with modern browsers
            - Works with screen readers (NVDA, JAWS, VoiceOver)
            - Keyboard accessible
            """
        )
