"""Settings Management UI components for Streamlit interface.

Handles all application settings and configuration UI components
with proper validation and user feedback.
"""

from __future__ import annotations

import streamlit as st
from typing import Dict, Any, Optional

from src.state.session_manager import SecureSessionManager
from src.utils.constants import (
    AUTO_ADVANCE_DEFAULT,
    AUTO_RUN_DELAY_MAX,
    AUTO_RUN_DELAY_MIN,
    DEFAULT_CONTEXT_MESSAGES,
    DEFAULT_HISTORY_MESSAGES,
    DEFAULT_OLLAMA_URL,
    DEFAULT_RESPONSE_TIMEOUT,
    ENABLE_THINKING,
    MAX_CONTEXT_MESSAGES,
    MIN_CONTEXT_MESSAGES,
)


class SettingsManager:
    """UI manager for application settings interface.

    Handles all Streamlit UI rendering for settings management
    with proper validation and immediate feedback.

    Attributes:
        session_manager: Session state manager for settings data
    """

    def __init__(self, session_manager: SecureSessionManager) -> None:
        """Initialize the settings manager UI.

        Args:
            session_manager: Session state manager for settings data
        """
        self.session_manager = session_manager

    def render_settings_interface(self) -> None:
        """Render the complete settings management interface."""
        st.header("⚙️ Application Settings")

        # Create tabs for different setting categories
        tab1, tab2, tab3, tab4 = st.tabs([
            "🤖 Ollama Configuration",
            "💬 Conversation Settings",
            "🎨 Interface Settings",
            "🔧 Advanced Options"
        ])

        with tab1:
            self._render_ollama_settings()

        with tab2:
            self._render_conversation_settings()

        with tab3:
            self._render_interface_settings()

        with tab4:
            self._render_advanced_settings()

        # Action buttons at bottom
        st.divider()
        self._render_settings_actions()

    def _render_ollama_settings(self) -> None:
        """Render Ollama-related settings."""
        st.subheader("🤖 Ollama Configuration")

        # Ollama URL
        current_url = self.session_manager.get_setting("ollama_url", DEFAULT_OLLAMA_URL)
        new_url = st.text_input(
            "🔗 Ollama Server URL",
            value=current_url,
            placeholder="http://localhost:11434",
            help="URL of your Ollama server instance"
        )

        if new_url != current_url:
            if st.button("🔄 Update URL", key="update_ollama_url"):
                self._update_setting("ollama_url", new_url)
                st.success("✅ Ollama URL updated")
                st.rerun()

        # Connection status
        st.subheader("📊 Connection Status")
        self._render_connection_status()

        # Model management
        st.subheader("🧠 Model Management")
        self._render_model_management()

    def _render_connection_status(self) -> None:
        """Render Ollama connection status and controls."""
        # Check current connection
        if st.button("🔍 Check Connection", key="check_ollama_conn"):
            with st.spinner("Connecting to Ollama..."):
                # This would need to be connected to the conversation orchestrator
                # For now, we'll simulate the connection check
                st.session_state.ollama_connection_check = True
                st.rerun()

        # Show connection result
        if st.session_state.get("ollama_connection_check"):
            # Simulate connection result (in real implementation, this would check actual connection)
            available_models = self.session_manager.get_available_models()
            if available_models:
                st.success("✅ Connected to Ollama")
                st.caption(f"Found {len(available_models)} models:")
                for model in available_models:
                    st.code(f"• {model}")
            else:
                st.error("❌ Failed to connect to Ollama")
                st.caption("Please ensure Ollama is running and accessible")

    def _render_model_management(self) -> None:
        """Render model list and management controls."""
        available_models = self.session_manager.get_available_models()

        if not available_models:
            st.info("📝 No models available. Check your Ollama connection.")
            return

        st.write("**Available Models:**")
        for i, model in enumerate(available_models):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.code(model)
            with col2:
                if st.button("🧪 Test", key=f"test_model_{i}"):
                    st.info(f"Testing model: {model}")
                    # In real implementation, this would test the model
            with col3:
                # Show model capabilities (thinking support, etc.)
                if "deepseek" in model.lower() or "r1" in model.lower():
                    st.caption("🧠")

    def _render_conversation_settings(self) -> None:
        """Render conversation-related settings."""
        st.subheader("💬 Conversation Settings")

        # Auto-advance settings
        st.write("**Auto-Conversation Control**")
        auto_advance = self.session_manager.get_setting("auto_advance", AUTO_ADVANCE_DEFAULT)

        col1, col2 = st.columns(2)
        with col1:
            new_auto_advance = st.checkbox(
                "🔄 Enable Auto-Advance",
                value=auto_advance,
                help="Automatically continue conversation with next persona"
            )

        with col2:
            if new_auto_advance:
                st.caption("💡 Conversation will continue automatically")
            else:
                st.caption("💡 Manual control required for each turn")

        if new_auto_advance != auto_advance:
            self._update_setting("auto_advance", new_auto_advance)

        # Delay settings
        if new_auto_advance:
            st.write("**Response Timing**")
            delay_min = self.session_manager.get_setting("response_delay_min", 2)
            delay_max = self.session_manager.get_setting("response_delay_max", 5)

            col1, col2 = st.columns(2)
            with col1:
                new_delay_min = st.number_input(
                    "⏱️ Min Delay (seconds)",
                    min_value=AUTO_RUN_DELAY_MIN,
                    max_value=AUTO_RUN_DELAY_MAX,
                    value=delay_min,
                    help="Minimum delay between AI responses"
                )

            with col2:
                new_delay_max = st.number_input(
                    "⏱️ Max Delay (seconds)",
                    min_value=AUTO_RUN_DELAY_MIN,
                    max_value=AUTO_RUN_DELAY_MAX,
                    value=delay_max,
                    help="Maximum delay between AI responses"
                )

            # Validate delay settings
            if new_delay_min >= new_delay_max:
                st.error("❌ Min delay must be less than max delay")
            else:
                if new_delay_min != delay_min:
                    self._update_setting("response_delay_min", new_delay_min)
                if new_delay_max != delay_max:
                    self._update_setting("response_delay_max", new_delay_max)

        # Context settings
        st.write("**Memory and Context**")
        context_messages = self.session_manager.get_setting("context_messages", DEFAULT_CONTEXT_MESSAGES)
        history_messages = self.session_manager.get_setting("history_messages", DEFAULT_HISTORY_MESSAGES)

        col1, col2 = st.columns(2)
        with col1:
            new_context = st.slider(
                "🧠 Context Messages",
                min_value=MIN_CONTEXT_MESSAGES,
                max_value=MAX_CONTEXT_MESSAGES,
                value=context_messages,
                help="Number of previous messages AI can see"
            )

        with col2:
            new_history = st.number_input(
                "📚 History Limit",
                min_value=10,
                max_value=1000,
                value=history_messages,
                step=10,
                help="Maximum messages to keep in memory"
            )

        if new_context != context_messages:
            self._update_setting("context_messages", new_context)
        if new_history != history_messages:
            self._update_setting("history_messages", new_history)

        # Response timeout
        st.write("**Response Handling**")
        timeout = self.session_manager.get_setting("response_timeout", DEFAULT_RESPONSE_TIMEOUT)
        new_timeout = st.number_input(
            "⏰ Response Timeout (seconds)",
            min_value=30,
            max_value=600,
            value=timeout,
            step=10,
            help="Maximum time to wait for AI response"
        )

        if new_timeout != timeout:
            self._update_setting("response_timeout", new_timeout)

        # Thinking mode
        st.write("**AI Thinking Mode**")
        thinking_enabled = self.session_manager.get_setting("enable_thinking", ENABLE_THINKING)
        new_thinking = st.checkbox(
            "🧠 Enable Thinking Mode",
            value=thinking_enabled,
            help="Show AI reasoning process (works with compatible models)"
        )

        if new_thinking != thinking_enabled:
            self._update_setting("enable_thinking", new_thinking)

        if new_thinking:
            st.caption("💡 Works best with deepseek-r1 and compatible models")
            st.caption("💡 Allows you to see the AI's internal reasoning process")

    def _render_interface_settings(self) -> None:
        """Render UI/UX settings."""
        st.subheader("🎨 Interface Settings")

        # Theme settings
        st.write("**Appearance**")
        theme = self.session_manager.get_setting("theme", "System 7")
        new_theme = st.selectbox(
            "🎨 Theme",
            options=["System 7", "Default", "Dark", "Light"],
            index=["System 7", "Default", "Dark", "Light"].index(theme) if theme in ["System 7", "Default", "Dark", "Light"] else 0,
            help="Choose the visual theme for the interface"
        )

        if new_theme != theme:
            self._update_setting("theme", new_theme)
            st.info("🔄 Theme will be applied on page reload")
            st.rerun()

        # Sidebar settings
        st.write("**Sidebar Configuration**")
        sidebar_state = self.session_manager.get_setting("sidebar_state", "expanded")
        new_sidebar_state = st.selectbox(
            "📱 Default Sidebar State",
            options=["expanded", "collapsed"],
            index=["expanded", "collapsed"].index(sidebar_state) if sidebar_state in ["expanded", "collapsed"] else 0,
            help="Default sidebar state when app loads"
        )

        if new_sidebar_state != sidebar_state:
            self._update_setting("sidebar_state", new_sidebar_state)

        # Display settings
        st.write("**Message Display**")
        show_timestamps = self.session_manager.get_setting("show_timestamps", True)
        new_show_timestamps = st.checkbox(
            "🕐 Show Timestamps",
            value=show_timestamps,
            help="Display timestamps on messages"
        )

        if new_show_timestamps != show_timestamps:
            self._update_setting("show_timestamps", new_show_timestamps)

        show_avatars = self.session_manager.get_setting("show_avatars", True)
        new_show_avatars = st.checkbox(
            "👤 Show Avatars",
            value=show_avatars,
            help="Display persona avatars in conversation"
        )

        if new_show_avatars != show_avatars:
            self._update_setting("show_avatars", new_show_avatars)

        # Font size
        font_size = self.session_manager.get_setting("font_size", "medium")
        new_font_size = st.selectbox(
            "📝 Font Size",
            options=["small", "medium", "large"],
            index=["small", "medium", "large"].index(font_size) if font_size in ["small", "medium", "large"] else 1,
            help="Text size for the interface"
        )

        if new_font_size != font_size:
            self._update_setting("font_size", new_font_size)

    def _render_advanced_settings(self) -> None:
        """Render advanced configuration settings."""
        st.subheader("🔧 Advanced Options")

        # Performance settings
        st.write("**Performance**")
        max_concurrent_requests = self.session_manager.get_setting("max_concurrent_requests", 5)
        new_max_concurrent = st.number_input(
            "🔄 Max Concurrent Requests",
            min_value=1,
            max_value=20,
            value=max_concurrent_requests,
            help="Maximum number of simultaneous AI requests"
        )

        if new_max_concurrent != max_concurrent_requests:
            self._update_setting("max_concurrent_requests", new_max_concurrent)

        # Debug settings
        st.write("**Debug & Logging**")
        debug_mode = self.session_manager.get_setting("debug_mode", False)
        new_debug_mode = st.checkbox(
            "🐛 Debug Mode",
            value=debug_mode,
            help="Enable debug information and verbose logging"
        )

        if new_debug_mode != debug_mode:
            self._update_setting("debug_mode", new_debug_mode)

        log_level = self.session_manager.get_setting("log_level", "INFO")
        new_log_level = st.selectbox(
            "📊 Log Level",
            options=["DEBUG", "INFO", "WARNING", "ERROR"],
            index=["DEBUG", "INFO", "WARNING", "ERROR"].index(log_level) if log_level in ["DEBUG", "INFO", "WARNING", "ERROR"] else 1,
            help="Logging verbosity level"
        )

        if new_log_level != log_level:
            self._update_setting("log_level", new_log_level)

        # Experimental features
        st.write("**Experimental Features**")
        experimental_features = self.session_manager.get_setting("experimental_features", {})

        # Persona memory
        enable_persona_memory = experimental_features.get("persona_memory", False)
        new_persona_memory = st.checkbox(
            "🧠 Persona Memory",
            value=enable_persona_memory,
            help="Allow personas to remember information across conversations (experimental)"
        )

        # Streaming optimization
        streaming_optimization = experimental_features.get("streaming_optimization", True)
        new_streaming_opt = st.checkbox(
            "⚡ Streaming Optimization",
            value=streaming_optimization,
            help="Optimize response streaming for better performance"
        )

        # Update experimental features
        if (new_persona_memory != enable_persona_memory or
            new_streaming_opt != streaming_optimization):
            new_experimental = experimental_features.copy()
            new_experimental["persona_memory"] = new_persona_memory
            new_experimental["streaming_optimization"] = new_streaming_opt
            self._update_setting("experimental_features", new_experimental)

        # Reset settings
        st.write("**Reset Options**")
        if st.button("🔄 Reset to Defaults", type="secondary"):
            st.session_state.show_reset_confirm = True

        if st.session_state.get("show_reset_confirm", False):
            st.error("⚠️ **WARNING**: This will reset all settings to default values!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Yes, Reset All", type="primary"):
                    self._reset_all_settings()
            with col2:
                if st.button("❌ Cancel"):
                    st.session_state.show_reset_confirm = False
                    st.rerun()

    def _render_settings_actions(self) -> None:
        """Render action buttons for settings management."""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("💾 Save Settings", use_container_width=True, type="primary"):
                self._save_settings()
                st.success("✅ Settings saved successfully!")

        with col2:
            if st.button("📥 Export Settings", use_container_width=True):
                self._export_settings()

        with col3:
            if st.button("📤 Import Settings", use_container_width=True):
                self._show_import_interface()

        with col4:
            if st.button("🔄 Reload Settings", use_container_width=True):
                self._reload_settings()
                st.success("✅ Settings reloaded!")

        # Import interface (hidden by default)
        if st.session_state.get("show_import_settings", False):
            st.markdown("---")
            st.subheader("📤 Import Settings")
            uploaded_file = st.file_uploader(
                "Choose a settings file",
                type=["json"],
                help="Upload a JSON settings file to import"
            )

            if uploaded_file:
                if st.button("📥 Import", type="primary"):
                    self._import_settings(uploaded_file)

            if st.button("❌ Cancel"):
                st.session_state.show_import_settings = False
                st.rerun()

    def _update_setting(self, key: str, value: Any) -> None:
        """Update a single setting.

        Args:
            key: Setting key
            value: New setting value
        """
        self.session_manager.set_setting(key, value)

    def _save_settings(self) -> None:
        """Save current settings to session state."""
        # Settings are automatically saved to session state when updated
        # This method provides a save button for user feedback
        pass

    def _export_settings(self) -> None:
        """Export current settings as downloadable JSON file."""
        settings = self.session_manager.get_all_settings()

        import json
        settings_json = json.dumps(settings, indent=2, default=str)

        st.download_button(
            label="📥 Download Settings (JSON)",
            data=settings_json,
            file_name=f"ai_backroom_settings_{st.session_state.session_id}.json",
            mime="application/json"
        )
        st.info("📄 Settings exported successfully!")

    def _show_import_interface(self) -> None:
        """Show the settings import interface."""
        st.session_state.show_import_settings = True
        st.rerun()

    def _import_settings(self, uploaded_file) -> None:
        """Import settings from uploaded JSON file.

        Args:
            uploaded_file: Uploaded file containing settings
        """
        try:
            import json
            settings = json.loads(uploaded_file.read().decode("utf-8"))

            # Validate settings structure
            if not isinstance(settings, dict):
                raise ValueError("Invalid settings format")

            # Apply settings
            for key, value in settings.items():
                self.session_manager.set_setting(key, value)

            st.success("✅ Settings imported successfully!")
            st.session_state.show_import_settings = False
            st.rerun()

        except Exception as e:
            st.error(f"❌ Failed to import settings: {str(e)}")

    def _reload_settings(self) -> None:
        """Reload settings from session state."""
        # Settings are automatically loaded from session state
        # This method provides a reload button for user feedback
        pass

    def _reset_all_settings(self) -> None:
        """Reset all settings to default values."""
        from src.utils.constants import DEFAULT_SETTINGS

        # Apply default settings
        for key, value in DEFAULT_SETTINGS.items():
            self.session_manager.set_setting(key, value)

        st.success("✅ All settings reset to defaults!")
        st.session_state.show_reset_confirm = False
        st.rerun()

    def render_quick_settings(self) -> None:
        """Render a simplified quick settings interface."""
        with st.expander("⚙️ Quick Settings", expanded=False):
            # Most commonly changed settings
            auto_advance = self.session_manager.get_setting("auto_advance", AUTO_ADVANCE_DEFAULT)
            new_auto_advance = st.checkbox(
                "🔄 Auto-Advance Conversation",
                value=auto_advance,
                key="quick_auto_advance"
            )

            if new_auto_advance != auto_advance:
                self._update_setting("auto_advance", new_auto_advance)

            thinking_enabled = self.session_manager.get_setting("enable_thinking", ENABLE_THINKING)
            new_thinking = st.checkbox(
                "🧠 Show AI Thinking",
                value=thinking_enabled,
                key="quick_thinking"
            )

            if new_thinking != thinking_enabled:
                self._update_setting("enable_thinking", new_thinking)

            # Quick action buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Check Ollama", key="quick_check_ollama", use_container_width=True):
                    st.session_state.ollama_connection_check = True
                    st.rerun()

            with col2:
                if st.button("⚙️ Full Settings", key="quick_full_settings", use_container_width=True):
                    st.session_state.active_tab = "Settings"
                    st.rerun()

    def get_setting_summary(self) -> Dict[str, Any]:
        """Get a summary of key settings for display.

        Returns:
            Dictionary with key setting values
        """
        return {
            "auto_advance": self.session_manager.get_setting("auto_advance", AUTO_ADVANCE_DEFAULT),
            "thinking_enabled": self.session_manager.get_setting("enable_thinking", ENABLE_THINKING),
            "context_messages": self.session_manager.get_setting("context_messages", DEFAULT_CONTEXT_MESSAGES),
            "available_models": len(self.session_manager.get_available_models()),
            "debug_mode": self.session_manager.get_setting("debug_mode", False)
        }