"""
System.css Design Tokens for Infinite Backrooms
==============================================

Retro Apple System OS aesthetic (1984-1991) adapted for Streamlit.

This module provides centralized design tokens and style generator functions
to ensure consistency with system.css standards throughout the application.

Reference: https://github.com/sakofchit/system.css

Usage:
    from ui_design_tokens import SYSTEM_COLORS, SPACING, persona_badge_style

    # Use color tokens
    bg_color = SYSTEM_COLORS["window_bg"]

    # Generate component styles
    badge_html = f'<span style="{persona_badge_style("Philosopher", "#9b59b6")}">Philosopher</span>'
"""

# ==============================================================================
# COLOR PALETTE
# ==============================================================================

SYSTEM_COLORS = {
    # Primary monochrome palette (System OS classic)
    "black": "#000000",
    "white": "#FFFFFF",
    "gray_light": "#C0C0C0",
    "gray_medium": "#808080",
    "gray_dark": "#404040",

    # System accent (used sparingly)
    "system_blue": "#0000FF",  # Classic Mac blue

    # UI element colors
    "window_bg": "#FFFFFF",
    "window_border": "#000000",
    "title_bar_active": "#000000",
    "title_bar_inactive": "#FFFFFF",
    "button_bg": "#DDDDDD",
    "button_border": "#000000",
    "input_bg": "#FFFFFF",
    "input_border": "#000000",

    # Text colors
    "text_primary": "#000000",
    "text_secondary": "#404040",
    "text_disabled": "#808080",
    "text_inverse": "#FFFFFF",
}

# Persona colors (muted/desaturated to match system.css aesthetic)
PERSONA_COLORS = {
    "Moderator": "#2c3e50",      # Dark blue-gray
    "Guide": "#2c3e50",          # Alias for Moderator
    "Note-Taker": "#34495e",     # Dark gray
    "Chronicle": "#34495e",      # Alias for Note-Taker
    "Philosopher": "#7f8c8d",    # Medium gray
    "Sage": "#7f8c8d",           # Alias for Philosopher
    "Scientist": "#2980b9",      # Muted blue
    "Eureka": "#2980b9",         # Alias for Scientist
    "Creative Writer": "#c0392b", # Muted red
    "Quill": "#c0392b",          # Alias for Creative Writer
    "Debate Enthusiast": "#d68910", # Muted orange
    "Socrates": "#d68910",       # Alias for Debate Enthusiast
    "Optimist": "#f39c12",       # Muted yellow
    "Bright": "#f39c12",         # Alias for Optimist
    "Skeptic": "#95a5a6",        # Light gray
    "Quest": "#95a5a6",          # Alias for Skeptic
    "Historian": "#8e44ad",      # Muted purple
    "Futurist": "#16a085",       # Muted teal
    "Minimalist": "#ecf0f1",     # Very light gray
    "Explorer": "#27ae60",       # Muted green
    "Mentor": "#e67e22",         # Muted dark orange
    "Comedian": "#f1c40f",       # Muted bright yellow
    "Analyst": "#3498db",        # Muted bright blue
    "Dreamer": "#9b59b6",        # Muted violet
    "Pragmatist": "#7f8c8d",     # Medium gray
}

# Default persona color (for unknown/new personas)
DEFAULT_PERSONA_COLOR = "#1f77b4"

# ==============================================================================
# SPACING TOKENS
# ==============================================================================

SPACING = {
    # Padding (system.css standard - uses small, precise values)
    "xs": "1px",
    "sm": "2px",
    "md": "4px",
    "lg": "8px",
    "xl": "16px",

    # Margins (system.css standard)
    "margin_xs": "2px",
    "margin_sm": "4px",
    "margin_md": "8px",
    "margin_lg": "16px",
    "margin_xl": "32px",

    # Border radius (system.css uses minimal rounding - 0-3px max)
    "radius_none": "0px",
    "radius_sm": "2px",
    "radius_md": "3px",  # Maximum allowed by system.css standards

    # Border width
    "border_thin": "1px",
    "border_thick": "2px",
}

# ==============================================================================
# TYPOGRAPHY
# ==============================================================================

FONTS = {
    "primary": '"Chicago", "SF Pro", "Courier New", monospace',
    "secondary": '"Geneva", "Helvetica Neue", sans-serif',
}

FONT_SIZES = {
    "heading": "12pt",  # Chicago 12pt standard
    "body": "9pt",      # Geneva 9pt standard
    "small": "8pt",
}

FONT_WEIGHTS = {
    "normal": "400",
    "bold": "700",
}

# ==============================================================================
# STYLE GENERATOR FUNCTIONS
# ==============================================================================

def system_button_style(
    text_color: str = None,
    bg_color: str = None,
    border_color: str = None,
    disabled: bool = False
) -> str:
    """
    Generate system.css compliant button styling for Streamlit.

    Args:
        text_color: Text color (default: black)
        bg_color: Background color (default: system button gray)
        border_color: Border color (default: black)
        disabled: Whether button is disabled (grays out text)

    Returns:
        CSS style string for inline use

    Example:
        st.markdown(
            f'<button style="{system_button_style()}">Click Me</button>',
            unsafe_allow_html=True
        )
    """
    text_color = text_color or SYSTEM_COLORS["text_primary"]
    bg_color = bg_color or SYSTEM_COLORS["button_bg"]
    border_color = border_color or SYSTEM_COLORS["button_border"]

    if disabled:
        text_color = SYSTEM_COLORS["text_disabled"]

    return f"""
        background-color: {bg_color};
        color: {text_color};
        border: {SPACING['border_thin']} solid {border_color};
        border-radius: {SPACING['radius_sm']};
        padding: {SPACING['md']} {SPACING['lg']};
        font-weight: {FONT_WEIGHTS['bold']};
        font-family: {FONTS['primary']};
        text-align: center;
        cursor: {'not-allowed' if disabled else 'pointer'};
    """.strip()


def system_container_style(
    bg_color: str = None,
    border_color: str = None,
    border_width: str = None
) -> str:
    """
    Apply system.css window aesthetic to Streamlit containers.

    Args:
        bg_color: Background color (default: white)
        border_color: Border color (default: black)
        border_width: Border width (default: 2px for window effect)

    Returns:
        CSS style string for inline use

    Example:
        st.markdown(
            f'<div style="{system_container_style()}">Content</div>',
            unsafe_allow_html=True
        )
    """
    bg_color = bg_color or SYSTEM_COLORS["window_bg"]
    border_color = border_color or SYSTEM_COLORS["window_border"]
    border_width = border_width or SPACING["border_thick"]

    return f"""
        border: {border_width} solid {border_color};
        background-color: {bg_color};
        padding: {SPACING['lg']};
        border-radius: {SPACING['radius_none']};
    """.strip()


def system_title_bar_style(active: bool = True) -> str:
    """
    Generate system.css title bar styling.

    Args:
        active: Whether the window/section is active (True) or inactive (False)

    Returns:
        CSS style string for inline use

    Example:
        st.markdown(
            f'<div style="{system_title_bar_style(active=True)}">Window Title</div>',
            unsafe_allow_html=True
        )
    """
    if active:
        return f"""
            background-color: {SYSTEM_COLORS['title_bar_active']};
            color: {SYSTEM_COLORS['text_inverse']};
            padding: {SPACING['md']} {SPACING['lg']};
            font-weight: {FONT_WEIGHTS['bold']};
            border-radius: {SPACING['radius_none']};
            min-height: 19px;
            font-family: {FONTS['primary']};
        """.strip()
    else:
        return f"""
            background-color: {SYSTEM_COLORS['title_bar_inactive']};
            color: {SYSTEM_COLORS['text_primary']};
            border: {SPACING['border_thin']} solid {SYSTEM_COLORS['window_border']};
            padding: {SPACING['md']} {SPACING['lg']};
            font-weight: {FONT_WEIGHTS['bold']};
            border-radius: {SPACING['radius_none']};
            min-height: 19px;
            font-family: {FONTS['primary']};
        """.strip()


def system_input_style() -> str:
    """
    System.css compliant input field styling.

    Returns:
        CSS style string for inline use

    Example:
        st.markdown(
            f'<input type="text" style="{system_input_style()}" aria-label="Search" />',
            unsafe_allow_html=True
        )
    """
    return f"""
        background-color: {SYSTEM_COLORS['input_bg']};
        color: {SYSTEM_COLORS['text_primary']};
        border: {SPACING['border_thin']} solid {SYSTEM_COLORS['input_border']};
        border-radius: {SPACING['radius_none']};
        padding: {SPACING['md']};
        font-family: {FONTS['primary']};
    """.strip()


def persona_badge_style(persona_name: str, persona_color: str) -> str:
    """
    Generate persona name badge with system.css aesthetic.

    This creates the colored badge that appears next to persona names in chat.
    Follows system.css standards with black borders and minimal border radius.

    Args:
        persona_name: Display name of the persona
        persona_color: Hex color code for the persona

    Returns:
        CSS style string for inline use

    Example:
        badge_html = f'<span style="{persona_badge_style("Philosopher", "#9b59b6")}">Philosopher</span>'
    """
    return f"""
        background-color: {persona_color};
        color: {SYSTEM_COLORS['text_inverse']};
        padding: {SPACING['sm']} {SPACING['lg']};
        border: {SPACING['border_thin']} solid {SYSTEM_COLORS['window_border']};
        border-radius: {SPACING['radius_sm']};
        font-weight: {FONT_WEIGHTS['bold']};
        font-family: {FONTS['primary']};
        font-size: {FONT_SIZES['body']};
    """.strip()


def mention_highlight_style(persona_color: str, text_color: str = None) -> str:
    """
    Generate @mention highlighting style.

    Creates subtle highlighting for @mentions in chat messages.
    Uses persona color as background with readable text color.

    Args:
        persona_color: Hex color code for the mentioned persona
        text_color: Text color (default: black for better contrast)

    Returns:
        CSS style string for inline use

    Example:
        mention_html = f'<span style="{mention_highlight_style("#9b59b6")}">@Philosopher</span>'
    """
    text_color = text_color or SYSTEM_COLORS["text_primary"]

    return f"""
        background-color: {persona_color};
        color: {text_color};
        padding: {SPACING['xs']} {SPACING['md']};
        border-radius: {SPACING['radius_md']};
        font-weight: {FONT_WEIGHTS['bold']};
        font-family: {FONTS['secondary']};
        font-size: {FONT_SIZES['small']};
    """.strip()


def current_speaker_style(persona_color: str) -> str:
    """
    Generate styling for current speaker indicator.

    Shows which persona is currently speaking with system.css aesthetic.

    Args:
        persona_color: Hex color code for the active persona

    Returns:
        CSS style string for inline use

    Example:
        speaker_html = f'<div style="{current_speaker_style("#9b59b6")}">Currently Speaking: Philosopher</div>'
    """
    return f"""
        background-color: {persona_color};
        color: {SYSTEM_COLORS['text_inverse']};
        padding: {SPACING['md']} {SPACING['lg']};
        border: {SPACING['border_thin']} solid {SYSTEM_COLORS['window_border']};
        border-radius: {SPACING['radius_sm']};
        font-weight: {FONT_WEIGHTS['bold']};
        font-family: {FONTS['primary']};
        text-align: center;
    """.strip()


def get_persona_color(persona_name: str) -> str:
    """
    Get the system.css compliant color for a persona.

    Looks up the persona name in PERSONA_COLORS dictionary,
    falling back to default if not found.

    Args:
        persona_name: Name of the persona

    Returns:
        Hex color code string

    Example:
        color = get_persona_color("Philosopher")  # Returns "#7f8c8d"
    """
    # Check both full name and aliases
    return PERSONA_COLORS.get(persona_name, DEFAULT_PERSONA_COLOR)


# ==============================================================================
# VALIDATION HELPERS
# ==============================================================================

def validate_color(color: str) -> bool:
    """
    Validate that a color is from approved palettes.

    Args:
        color: Hex color code to validate

    Returns:
        True if color is in SYSTEM_COLORS or PERSONA_COLORS, False otherwise
    """
    approved_colors = set(SYSTEM_COLORS.values()) | set(PERSONA_COLORS.values()) | {DEFAULT_PERSONA_COLOR}
    return color in approved_colors


def validate_spacing(value: str) -> bool:
    """
    Validate that a spacing value is from approved tokens.

    Args:
        value: Spacing value to validate (e.g., "4px")

    Returns:
        True if value is in SPACING tokens, False otherwise
    """
    approved_spacing = set(SPACING.values())
    return value in approved_spacing


# ==============================================================================
# ACCESSIBILITY HELPERS
# ==============================================================================

def make_accessible_button(label: str, style: str, onclick: str = None) -> str:
    """
    Create an accessible button with proper ARIA attributes.

    Args:
        label: Button text label
        style: CSS style string
        onclick: JavaScript onclick handler (optional)

    Returns:
        Complete HTML button element with accessibility features
    """
    onclick_attr = f'onclick="{onclick}"' if onclick else ""
    return f"""
        <button
            style="{style}"
            aria-label="{label}"
            role="button"
            tabindex="0"
            {onclick_attr}
        >
            {label}
        </button>
    """.strip()


def make_accessible_input(
    input_type: str,
    label: str,
    style: str,
    name: str = None,
    value: str = None
) -> str:
    """
    Create an accessible input field with proper ARIA attributes.

    Args:
        input_type: Input type (text, email, password, etc.)
        label: Accessible label for the input
        style: CSS style string
        name: Input name attribute
        value: Default value (optional)

    Returns:
        Complete HTML input element with accessibility features
    """
    name_attr = f'name="{name}"' if name else ""
    value_attr = f'value="{value}"' if value else ""

    return f"""
        <input
            type="{input_type}"
            style="{style}"
            aria-label="{label}"
            {name_attr}
            {value_attr}
        />
    """.strip()


# ==============================================================================
# STREAMLIT THEMING CONFIGURATION
# ==============================================================================

STREAMLIT_THEME_CONFIG = """
# .streamlit/config.toml
# System.css inspired theme configuration

[theme]
primaryColor = "#000000"        # System black
backgroundColor = "#FFFFFF"     # System white
secondaryBackgroundColor = "#C0C0C0"  # System gray
textColor = "#000000"           # Primary text
font = "monospace"              # Chicago/Geneva fallback

[ui]
hideTopBar = false
hideSidebarNav = false
"""


if __name__ == "__main__":
    # Demo/testing
    print("System.css Design Tokens Loaded")
    print("\n=== Color Palette ===")
    for key, value in SYSTEM_COLORS.items():
        print(f"{key}: {value}")

    print("\n=== Persona Colors ===")
    for key, value in PERSONA_COLORS.items():
        print(f"{key}: {value}")

    print("\n=== Example Styles ===")
    print("Button:", system_button_style())
    print("\nBadge:", persona_badge_style("Philosopher", "#9b59b6"))
    print("\nContainer:", system_container_style())
