"""Streamlit utility functions and helpers.

Provides common Streamlit operations, safe async handling,
and UI utilities for the Infinite Backrooms application.
"""

from __future__ import annotations

import asyncio
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Optional, Dict, List, Union

import streamlit as st


def safe_async_call(
    async_func: Callable,
    *args,
    timeout: Optional[float] = None,
    fallback: Any = None,
    show_error: bool = True,
    **kwargs
) -> Any:
    """Safely execute async function in Streamlit context.

    Streamlit doesn't support async functions directly, so this helper
    provides safe async execution with proper error handling.

    Args:
        async_func: Async function to execute
        *args: Arguments to pass to async function
        timeout: Optional timeout in seconds
        fallback: Value to return on error
        show_error: Whether to display error in UI
        **kwargs: Keyword arguments to pass to async function

    Returns:
        Result of async function or fallback on error
    """
    try:
        # Try to run in existing event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Event loop is running, use thread-based execution
                return _run_async_in_thread(async_func, *args, timeout=timeout, **kwargs)
            else:
                # Event loop exists but not running, use it
                if timeout:
                    return loop.run_until_complete(
                        asyncio.wait_for(async_func(*args, **kwargs), timeout=timeout)
                    )
                else:
                    return loop.run_until_complete(async_func(*args, **kwargs))
        except RuntimeError:
            # No event loop, create new one
            if timeout:
                return asyncio.run(asyncio.wait_for(async_func(*args, **kwargs), timeout=timeout))
            else:
                return asyncio.run(async_func(*args, **kwargs))

    except asyncio.TimeoutError:
        error_msg = f"Operation timed out after {timeout or 'default'} seconds"
        if show_error:
            st.error(f"⏰ {error_msg}")
        return fallback
    except Exception as e:
        error_msg = f"Async operation failed: {str(e)}"
        if show_error:
            st.error(f"❌ {error_msg}")
            if st.session_state.get("debug_mode", False):
                st.code(traceback.format_exc())
        return fallback


def _run_async_in_thread(
    async_func: Callable,
    *args,
    timeout: Optional[float] = None,
    **kwargs
) -> Any:
    """Run async function in separate thread.

    Args:
        async_func: Async function to execute
        *args: Arguments to pass to async function
        timeout: Optional timeout in seconds
        **kwargs: Keyword arguments to pass to async function

    Returns:
        Result of async function
    """
    def run_in_thread():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if timeout:
                    return loop.run_until_complete(
                        asyncio.wait_for(async_func(*args, **kwargs), timeout=timeout)
                    )
                else:
                    return loop.run_until_complete(async_func(*args, **kwargs))
            finally:
                loop.close()
        except Exception as e:
            return e

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_in_thread)
        return future.result(timeout=timeout)


def get_session_state(key: str, default: Any = None) -> Any:
    """Get value from Streamlit session state with default.

    Args:
        key: Session state key
        default: Default value if key doesn't exist

    Returns:
        Value from session state or default
    """
    return st.session_state.get(key, default)


def set_session_state(key: str, value: Any) -> None:
    """Set value in Streamlit session state.

    Args:
        key: Session state key
        value: Value to set
    """
    st.session_state[key] = value


def toggle_session_state(key: str) -> bool:
    """Toggle boolean value in session state.

    Args:
        key: Session state key to toggle

    Returns:
        New value after toggle
    """
    current_value = get_session_state(key, False)
    new_value = not current_value
    set_session_state(key, new_value)
    return new_value


def inject_css(css_code: str) -> None:
    """Inject custom CSS into Streamlit app.

    Args:
        css_code: CSS code to inject
    """
    st.markdown(f"<style>{css_code}</style>", unsafe_allow_html=True)


def inject_system_css() -> None:
    """Inject System 7 themed CSS for retro Mac OS aesthetic."""
    css_code = """
    /* Import Chicago font */
    @font-face {
        font-family: 'Chicago_12';
        src: url('https://fontmeme.com/fonts/chicago-font/') format('woff');
        font-weight: normal;
        font-style: normal;
    }

    /* Fallback fonts */
    @font-face {
        font-family: 'Chicago';
        src: local('Chicago'), local('System');
        font-weight: normal;
        font-style: normal;
    }

    /* Main app background - System 7 grid pattern */
    .stApp {
        font-family: Chicago_12, Chicago, Monaco, monospace !important;
        background: linear-gradient(90deg, #FFFFFF 21px, transparent 1%) center,
                    linear-gradient(#FFFFFF 21px, transparent 1%) center, #000000 !important;
        background-size: 22px 22px !important;
        background-attachment: fixed !important;
        color: #000000 !important;
    }

    /* Main content area */
    .main .block-container {
        background-color: #FFFFFF !important;
        border: 2px solid #000000 !important;
        box-shadow: 2px 2px #000000 !important;
        padding: 2rem !important;
        font-family: Chicago_12, Chicago, Monaco, monospace !important;
    }

    /* Headers - Chicago font */
    h1, h2, h3, h4, h5, h6 {
        font-family: Chicago, Chicago_12, monospace !important;
        color: #000000 !important;
    }

    /* Buttons - System 7 style */
    .stButton > button {
        font-family: Chicago_12, Chicago, monospace !important;
        font-size: 18px !important;
        min-height: 20px !important;
        min-width: 59px !important;
        padding: 4px 20px !important;
        background: #FFFFFF !important;
        color: #000000 !important;
        border: 3px solid #000000 !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        text-align: center !important;
        cursor: pointer !important;
    }

    .stButton > button:hover {
        background: #F0F0F0 !important;
        border: 3px solid #000000 !important;
    }

    .stButton > button:active {
        background: #000000 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
    }

    /* Text inputs - Monaco font with simple border */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        font-family: Monaco, monospace !important;
        font-size: 14px !important;
        border: 2px solid #000000 !important;
        border-radius: 0 !important;
        background: #FFFFFF !important;
        color: #000000 !important;
        padding: 4px 8px !important;
        box-shadow: inset 1px 1px 0px #000000 !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        outline: 2px solid #000000 !important;
        outline-offset: 2px !important;
        border-color: #000000 !important;
        box-shadow: inset 1px 1px 0px #000000 !important;
    }

    /* Select boxes */
    .stSelectbox > div > div {
        font-family: Chicago_12, Monaco, monospace !important;
        font-size: 14px !important;
        border: 2px solid #000000 !important;
        border-radius: 0 !important;
        background: #FFFFFF !important;
    }

    /* Tabs - System 7 style */
    .stTabs [data-baseweb="tab-list"] {
        background: #FFFFFF !important;
        border-bottom: 2px solid #000000 !important;
        gap: 2px !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: Chicago_12, Chicago, monospace !important;
        font-size: 14px !important;
        background: #FFFFFF !important;
        border: 2px solid #000000 !important;
        border-bottom: none !important;
        border-radius: 8px 8px 0 0 !important;
        color: #000000 !important;
        padding: 8px 16px !important;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: #F0F0F0 !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #FFFFFF !important;
        border: 2px solid #000000 !important;
        border-radius: 8px !important;
        font-family: Chicago_12, Chicago, monospace !important;
    }

    /* Metrics */
    .stMetric {
        background-color: #FFFFFF !important;
        border: 2px solid #000000 !important;
        box-shadow: 1px 1px #000000 !important;
        font-family: Chicago_12, Chicago, monospace !important;
    }

    /* Sidebar */
    .css-1d391kg {
        background-color: #F0F0F0 !important;
        border-right: 2px solid #000000 !important;
    }

    /* Progress bar */
    .stProgress .progress-bar {
        background-color: #000000 !important;
    }

    /* Success/Info/Warning/Error boxes */
    .stAlert {
        border: 2px solid #000000 !important;
        border-radius: 0 !important;
        font-family: Chicago_12, Chicago, monospace !important;
    }

    .element-container .stAlert {
        background-color: #FFFFFF !important;
    }

    /* Code blocks */
    .stCode {
        background-color: #F0F0F0 !important;
        border: 1px solid #000000 !important;
        font-family: Monaco, monospace !important;
    }

    /* Dataframes */
    .stDataFrame {
        border: 1px solid #000000 !important;
        font-family: Monaco, monospace !important;
    }

    .stDataFrame table {
        border-collapse: collapse !important;
    }

    .stDataFrame th, .stDataFrame td {
        border: 1px solid #000000 !important;
        padding: 4px 8px !important;
    }
    """
    inject_css(css_code)


def show_loading_with_message(message: str, timeout: Optional[float] = None) -> None:
    """Show loading spinner with custom message.

    Args:
        message: Message to display
        timeout: Optional timeout to stop loading
    """
    with st.spinner(message):
        if timeout:
            time.sleep(timeout)
        else:
            # Keep spinning until caller context ends
            pass


def create_status_indicator(
    status: str,
    message: str = "",
    show_icon: bool = True
) -> None:
    """Create status indicator with icon and message.

    Args:
        status: Status type ("success", "error", "warning", "info")
        message: Optional message to display
        show_icon: Whether to show status icon
    """
    icons = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️"
    }

    icon = icons.get(status, "")
    if show_icon and icon:
        display_message = f"{icon} {message}"
    else:
        display_message = message

    if status == "success":
        st.success(display_message)
    elif status == "error":
        st.error(display_message)
    elif status == "warning":
        st.warning(display_message)
    elif status == "info":
        st.info(display_message)
    else:
        st.write(display_message)


def create_expandable_section(
    title: str,
    content: str,
    expanded: bool = False,
    icon: str = ""
) -> None:
    """Create expandable section with markdown content.

    Args:
        title: Section title
        content: Content to display (markdown supported)
        expanded: Whether section is expanded by default
        icon: Optional icon to prepend to title
    """
    display_title = f"{icon} {title}" if icon else title
    with st.expander(display_title, expanded=expanded):
        st.markdown(content)


def create_metric_row(
    metrics: Dict[str, Union[str, int, float]],
    columns: Optional[int] = None
) -> None:
    """Create a row of metrics.

    Args:
        metrics: Dictionary of metric_name -> metric_value
        columns: Number of columns to use (auto-calculated if None)
    """
    if columns is None:
        columns = min(len(metrics), 4)

    metric_items = list(metrics.items())
    cols = st.columns(columns)

    for i, (key, value) in enumerate(metric_items):
        col_index = i % columns
        with cols[col_index]:
            st.metric(key.replace("_", " ").title(), value)


def create_progress_tracker(
    steps: List[str],
    current_step: int,
    show_percentage: bool = True
) -> None:
    """Create progress tracker for multi-step processes.

    Args:
        steps: List of step names
        current_step: Current step index (0-based)
        show_percentage: Whether to show percentage completion
    """
    if not steps:
        return

    progress = (current_step + 1) / len(steps)

    if show_percentage:
        st.progress(progress, text=f"Step {current_step + 1} of {len(steps)} ({progress:.1%})")
    else:
        st.progress(progress)

    # Show step list
    step_cols = st.columns(len(steps))
    for i, step in enumerate(steps):
        with step_cols[i]:
            if i < current_step:
                st.success(f"✅ {step}")
            elif i == current_step:
                st.info(f"🔄 {step}")
            else:
                st.write(f"⏳ {step}")


def create_download_link(
    data: str,
    filename: str,
    link_text: str = "Download",
    mime_type: str = "text/plain"
) -> None:
    """Create download link for data.

    Args:
        data: Data to download
        filename: Filename for download
        link_text: Text to display for link
        mime_type: MIME type of data
    """
    st.download_button(
        label=link_text,
        data=data,
        file_name=filename,
        mime=mime_type
    )


def create_confirmation_dialog(
    message: str,
    confirm_text: str = "Confirm",
    cancel_text: str = "Cancel",
    key: str = "confirm_dialog"
) -> bool:
    """Create confirmation dialog for destructive actions.

    Args:
        message: Confirmation message
        confirm_text: Text for confirm button
        cancel_text: Text for cancel button
        key: Unique key for dialog

    Returns:
        True if confirmed, False otherwise
    """
    st.error(message)
    col1, col2 = st.columns(2)
    with col1:
        if st.button(confirm_text, key=f"{key}_confirm", type="primary"):
            return True
    with col2:
        if st.button(cancel_text, key=f"{key}_cancel"):
            return False
    return False


def format_timestamp(
    timestamp,
    format_style: str = "medium"
) -> str:
    """Format timestamp for display.

    Args:
        timestamp: Datetime object or string
        format_style: Format style ("short", "medium", "long", "time")

    Returns:
        Formatted timestamp string
    """
    if isinstance(timestamp, str):
        try:
            from datetime import datetime
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            return timestamp

    if format_style == "short":
        return timestamp.strftime("%Y-%m-%d")
    elif format_style == "medium":
        return timestamp.strftime("%Y-%m-%d %H:%M")
    elif format_style == "long":
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    elif format_style == "time":
        return timestamp.strftime("%H:%M:%S")
    else:
        return str(timestamp)


def sanitize_session_data(data: Any) -> Any:
    """Sanitize data for storage in session state.

    Args:
        data: Data to sanitize

    Returns:
        Sanitized data safe for session state
    """
    if isinstance(data, dict):
        return {k: sanitize_session_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_session_data(item) for item in data]
    elif hasattr(data, '__dict__'):
        # Convert objects to dict if possible
        try:
            return data.__dict__
        except:
            return str(data)
    else:
        # For basic types, return as-is
        return data


def cache_with_session_state(
    key: str,
    func: Callable,
    *args,
    ttl: Optional[float] = None,
    **kwargs
) -> Any:
    """Cache function result in session state.

    Args:
        key: Cache key
        func: Function to cache result for
        *args: Arguments to pass to function
        ttl: Time-to-live in seconds (optional)
        **kwargs: Keyword arguments to pass to function

    Returns:
        Cached result or new result
    """
    cache_key = f"cache_{key}"
    cache_data = get_session_state(cache_key, {})

    # Check if cache is valid
    if cache_data:
        cached_time = cache_data.get("time", 0)
        if ttl is None or (time.time() - cached_time) < ttl:
            return cache_data["result"]

    # Compute and cache result
    result = func(*args, **kwargs)
    cache_data = {
        "time": time.time(),
        "result": result
    }
    set_session_state(cache_key, cache_data)

    return result


def create_sidebar_section(title: str, content_func: Callable) -> None:
    """Create standardized sidebar section.

    Args:
        title: Section title
        content_func: Function that renders section content
    """
    with st.sidebar:
        st.subheader(title)
        content_func()


def handle_rerun_delay(delay: float = 0.5) -> None:
    """Handle delayed rerun to avoid rapid successive updates.

    Args:
        delay: Delay in seconds before rerun
    """
    if delay > 0:
        time.sleep(delay)
    st.rerun()


def get_device_info() -> Dict[str, str]:
    """Get device information from user agent.

    Returns:
        Dictionary with device information
    """
    # This is a simplified implementation
    # In production, you'd parse st.experimental_get_query_params() or use JavaScript
    return {
        "device_type": "desktop",  # Placeholder
        "browser": "unknown",      # Placeholder
        "screen_size": "unknown"    # Placeholder
    }


def create_responsive_layout(
    desktop_content: Callable,
    mobile_content: Optional[Callable] = None
) -> None:
    """Create responsive layout based on device.

    Args:
        desktop_content: Function for desktop layout
        mobile_content: Optional function for mobile layout
    """
    device_info = get_device_info()

    if device_info.get("device_type") == "mobile" and mobile_content:
        mobile_content()
    else:
        desktop_content()


def validate_streamlit_inputs(
    validations: Dict[str, Dict[str, Any]]
) -> Dict[str, List[str]]:
    """Validate Streamlit form inputs.

    Args:
        validations: Dictionary of field_name -> validation_rules
            validation_rules can include:
            - required: bool
            - min_length: int
            - max_length: int
            - pattern: str (regex)
            - custom: Callable(str) -> bool

    Returns:
        Dictionary of field_name -> list of error messages
    """
    errors = {}

    for field_name, rules in validations.items():
        field_errors = []
        value = get_session_state(field_name, "")

        # Required validation
        if rules.get("required", False) and not str(value).strip():
            field_errors.append(f"{field_name} is required")

        # Length validation
        str_value = str(value)
        if str_value:
            min_len = rules.get("min_length")
            if min_len and len(str_value) < min_len:
                field_errors.append(f"{field_name} must be at least {min_len} characters")

            max_len = rules.get("max_length")
            if max_len and len(str_value) > max_len:
                field_errors.append(f"{field_name} must be no more than {max_len} characters")

        # Pattern validation
        pattern = rules.get("pattern")
        if pattern and str_value:
            import re
            if not re.match(pattern, str_value):
                field_errors.append(f"{field_name} format is invalid")

        # Custom validation
        custom_validator = rules.get("custom")
        if custom_validator and str_value:
            try:
                if not custom_validator(str_value):
                    field_errors.append(f"{field_name} validation failed")
            except Exception as e:
                field_errors.append(f"{field_name} validation error: {str(e)}")

        if field_errors:
            errors[field_name] = field_errors

    return errors


def show_validation_errors(errors: Dict[str, List[str]]) -> None:
    """Display validation errors to user.

    Args:
        errors: Dictionary of field_name -> list of error messages
    """
    if errors:
        st.error("⚠️ Please fix the following errors:")
        for field_name, field_errors in errors.items():
            for error in field_errors:
                st.write(f"• {error}")


# Performance monitoring utilities
class PerformanceTimer:
    """Context manager for timing operations."""

    def __init__(self, operation_name: str, show_in_ui: bool = False):
        self.operation_name = operation_name
        self.show_in_ui = show_in_ui
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        if self.show_in_ui:
            with st.spinner(f"Starting {self.operation_name}..."):
                pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time

        if self.show_in_ui:
            st.success(f"✅ {self.operation_name} completed in {duration:.2f}s")

        # Log performance if debug mode is enabled
        if get_session_state("debug_mode", False):
            print(f"[PERF] {self.operation_name}: {duration:.3f}s")

    def get_duration(self) -> float:
        """Get operation duration.

        Returns:
            Duration in seconds
        """
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0