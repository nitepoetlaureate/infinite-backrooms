#!/usr/bin/env python3
"""Infinite AI Backroom - Streamlit Web App (Refactored Modular Version).

Interactive web interface for managing AI personas and running infinite conversations.
This version uses modular architecture with clear separation of concerns.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import streamlit as st

from src.models.persona import AIPersona
from src.services.conversation_orchestrator import ConversationOrchestrator
from src.services.logger import ConversationLogger
from src.state.session_manager import SecureSessionManager
from src.ui.conversation_ui import ConversationUI
from src.ui.persona_manager import PersonaManager
from src.ui.settings_manager import SettingsManager
from src.ui.export_manager import ExportManager
from src.utils.streamlit_helpers import (
    safe_async_call,
    inject_system_css,
    get_session_state,
    set_session_state,
    PerformanceTimer
)
from src.utils.thread_utils import cleanup_thread_resources

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StreamlitBackroomApp:
    """Main application class with modular architecture.

    Orchestrates all application components and provides clean separation
    between UI, business logic, and state management.
    """

    def __init__(self) -> None:
        """Initialize the application with all required components."""
        # Core components
        self.session_manager = SecureSessionManager()
        self.conversation_logger = ConversationLogger()
        self.conversation_orchestrator = ConversationOrchestrator(
            session_manager=self.session_manager,
            conversation_logger=self.conversation_logger
        )

        # UI managers
        self.conversation_ui = ConversationUI(
            session_manager=self.session_manager,
            conversation_orchestrator=self.conversation_orchestrator
        )
        self.persona_manager = PersonaManager(self.session_manager)
        self.settings_manager = SettingsManager(self.session_manager)
        self.export_manager = ExportManager(
            session_manager=self.session_manager,
            conversation_logger=self.conversation_logger
        )

    def initialize_session(self) -> None:
        """Initialize session state and default values."""
        self.session_manager.initialize_session()
        logger.info(f"Session initialized: {self.session_manager.session_id}")

    def check_ollama_connection(self) -> bool:
        """Check connection to Ollama service.

        Returns:
            True if connected successfully, False otherwise
        """
        with PerformanceTimer("Ollama connection check"):
            try:
                connected = safe_async_call(
                    self.conversation_orchestrator.check_ollama_connection,
                    timeout=10.0,
                    fallback=False
                )
                return connected
            except Exception as e:
                logger.error(f"Ollama connection check failed: {e}")
                return False

    def render_welcome_interface(self) -> None:
        """Render welcome interface for new users."""
        st.info(
            "👋 **Welcome to AI Backroom!** "
            "Start by creating your first AI persona in the **Personas** tab, "
            "then head to **Conversation** to begin chatting!"
        )

    def render_conversation_tab(self) -> None:
        """Render conversation interface tab."""
        personas = self.session_manager.get_enabled_personas()

        if not personas:
            st.warning(
                "⚠️ No enabled personas available! "
                "Please create and enable some personas in the **Personas** tab."
            )
        else:
            self.conversation_ui.render_conversation_interface()

    def render_personas_tab(self) -> None:
        """Render persona management tab."""
        self.persona_manager.render_persona_management_interface()

    def render_settings_tab(self) -> None:
        """Render settings management tab."""
        self.settings_manager.render_settings_interface()

    def render_export_tab(self) -> None:
        """Render export and logs tab."""
        self.export_manager.render_export_interface()

    def render_sidebar(self) -> None:
        """Render application sidebar with status and controls."""
        with st.sidebar:
            # Logo and description
            try:
                st.image("logo.png", use_container_width=True)
            except Exception:
                pass
            st.caption("*Where AI instances explore their curiosity through infinite conversation*")

            # Connection status
            self._render_connection_status()

            # Statistics
            self._render_session_statistics()

            # Active personas
            self._render_active_personas()

            # Quick tips
            self._render_quick_tips()

    def _render_connection_status(self) -> None:
        """Render Ollama connection status."""
        st.subheader("📊 Connection")

        available_models = self.session_manager.get_available_models()
        if available_models:
            st.success("✅ Ollama Connected")
            st.caption(f"{len(available_models)} models available")
        else:
            st.error("❌ Ollama Disconnected")
            if st.button("🔄 Retry Connection", type="secondary"):
                with st.spinner("Connecting to Ollama..."):
                    connected = self.check_ollama_connection()
                    if connected:
                        models = self.session_manager.get_available_models()
                        st.success(f"✅ Connected! Found {len(models)} models")
                        st.rerun()
                    else:
                        st.error("❌ Still unable to connect to Ollama")

    def _render_session_statistics(self) -> None:
        """Render session statistics in sidebar."""
        st.subheader("📊 Status")
        stats = self.session_manager.get_stats()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Personas", stats.get("total_personas", 0))
        with col2:
            st.metric("Messages", stats.get("total_message_count", 0))

        if self.session_manager.is_conversation_running():
            st.success("🔄 Conversation Running")
        else:
            st.warning("⚠️ Conversation Not Running")

    def _render_active_personas(self) -> None:
        """Render list of active personas."""
        enabled_personas = self.session_manager.get_enabled_personas()

        if enabled_personas:
            st.subheader("🤖 Active Personas")
            from src.ui.components import render_persona_list_item
            for persona in enabled_personas:
                render_persona_list_item(persona)
        else:
            st.info("No active personas yet. Create some in the Personas tab!")

    def _render_quick_tips(self) -> None:
        """Render quick tips for users."""
        st.divider()
        st.subheader("💡 Quick Tips")
        st.markdown("• Use **Start Conversation** for auto-running")
        st.markdown("• Click **Next Turn** for manual control")
        st.markdown("• Add messages via chat input")
        st.markdown("• Personas rotate automatically")
        st.markdown("• AIs can use **@mentions** to address each other")

        context_messages = self.session_manager.get_setting("context_messages", 10)
        st.markdown(f"• Each AI sees the last **{context_messages}** messages")

        if self.session_manager.get_setting("enable_thinking", False):
            st.markdown("• 🧠 **Thinking enabled** - View AI reasoning in expanders")
            st.markdown("• Works best with **deepseek-r1** and compatible models")

    def handle_error(self, error: Exception, context: str = "") -> None:
        """Handle application errors gracefully.

        Args:
            error: Exception that occurred
            context: Context where error occurred
        """
        error_msg = f"Error in {context}: {str(error)}"
        logger.error(error_msg, exc_info=True)

        if get_session_state("debug_mode", False):
            st.error(f"❌ {error_msg}")
            st.code(str(error))
        else:
            st.error("❌ An unexpected error occurred. Please try again.")

    def run(self) -> None:
        """Main application entry point."""
        try:
            # Initialize session
            self.initialize_session()

            # Render sidebar
            self.render_sidebar()

            # Main content tabs
            tab1, tab2, tab3, tab4 = st.tabs([
                "💬 Conversation",
                "🤖 Personas",
                "⚙️ Settings",
                "📁 Export & Logs"
            ])

            with tab1:
                self.render_conversation_tab()

            with tab2:
                self.render_personas_tab()

            with tab3:
                self.render_settings_tab()

            with tab4:
                self.render_export_tab()

            # Show welcome message for new users
            if not self.session_manager.get_personas():
                self.render_welcome_interface()

        except Exception as e:
            self.handle_error(e, "main application loop")


def configure_page() -> None:
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="AI Backroom",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def initialize_application_state() -> None:
    """Initialize global application state."""
    # Set up session state variables
    if "app_initialized" not in st.session_state:
        st.session_state.app_initialized = True
        st.session_state.debug_mode = False
        st.session_state.active_tab = "Conversation"

    # Cleanup any previous thread resources
    cleanup_thread_resources()


def main() -> None:
    """Main entry point for Streamlit application."""
    # Configure page first (required by Streamlit)
    configure_page()

    # Inject CSS styling
    inject_system_css()

    # Initialize application state
    initialize_application_state()

    # Create and run application
    app = StreamlitBackroomApp()
    app.run()


if __name__ == "__main__":
    main()