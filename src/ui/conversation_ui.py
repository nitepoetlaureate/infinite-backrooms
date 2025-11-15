"""Conversation UI components for Streamlit interface.

Handles all UI rendering for conversation management with proper
separation from business logic and state management.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import Any, Dict

import streamlit as st

from src.models.persona import AIPersona
from src.services.conversation_orchestrator import ConversationOrchestrator
from src.state.session_manager import SecureSessionManager
from src.ui.components import (
    get_persona_avatar,
    highlight_mentions,
    render_persona_header,
    render_persona_list_item,
)


class ConversationUI:
    """UI manager for conversation interface.

    Handles all Streamlit UI rendering for conversation management
    while keeping business logic separate.

    Attributes:
        session_manager: Session state manager
        conversation_orchestrator: Business logic orchestrator
    """

    def __init__(
        self,
        session_manager: SecureSessionManager,
        conversation_orchestrator: ConversationOrchestrator,
    ) -> None:
        """Initialize the conversation UI manager.

        Args:
            session_manager: Session state manager
            conversation_orchestrator: Conversation business logic
        """
        self.session_manager = session_manager
        self.conversation_orchestrator = conversation_orchestrator

    def render_conversation_controls(self) -> None:
        """Render conversation control buttons."""
        enabled_personas = self.session_manager.get_enabled_personas()
        is_running = self.session_manager.is_conversation_running()

        col1, col2, col3, col4 = st.columns(4, vertical_alignment="bottom")

        with col1:
            if st.button(
                "▶️ Start Conversation",
                disabled=is_running,
                help="Start auto-running the conversation",
            ):
                self.session_manager.start_conversation()
                st.rerun()

        with col2:
            if st.button(
                "⏸️ Pause",
                disabled=not is_running,
                help="Pause the auto-running conversation",
            ):
                self.session_manager.stop_conversation()
                st.rerun()

        with col3:
            if st.button(
                "🔄 Next Turn",
                disabled=is_running,
                help="Manually advance to the next conversation turn",
            ):
                self.session_manager.set_pending_manual_turn(True)
                st.rerun()

        with col4:
            if st.button(
                "🗑️ Clear History",
                help="Clear all conversation history and reset speaker rotation",
            ):
                self.session_manager.clear_messages()
                st.rerun()

    def render_conversation_status(self) -> None:
        """Render conversation status information."""
        enabled_personas = self.session_manager.get_enabled_personas()

        if not enabled_personas:
            st.warning("⚠️ No enabled personas found. Please add and enable at least one persona.")
            return

        # Show conversation status
        if self.session_manager.is_conversation_running():
            st.success(f"🔄 Conversation Active • {len(enabled_personas)} personas")
        else:
            st.info("⏸️ Conversation Paused")

    def render_chat_input(self) -> None:
        """Render chat input for manual user messages."""
        if prompt := st.chat_input("Add a message to the conversation (optional)"):
            timestamp = datetime.now()

            message = {
                "role": "user",
                "content": prompt,
                "timestamp": timestamp,
                "persona_name": "User",
                "model": "Human",
            }

            self.session_manager.add_message(message)
            st.rerun()

    def render_conversation_messages(self) -> None:
        """Render the conversation history."""
        enabled_personas = self.session_manager.get_enabled_personas()
        messages = self.session_manager.get_messages()
        display_limit = self.session_manager.get_setting("max_history", 100)

        # Show info about message limit if applicable
        total_messages = len(messages)
        if total_messages > display_limit:
            st.info(
                f"📜 Showing last {display_limit} of {total_messages} total messages "
                f"(limited for performance). Full conversation history is available in **Export & Logs** tab."
            )

        # Display messages using Streamlit chat elements
        for message in messages:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
                    st.caption(f"🕒 {message['timestamp'].strftime('%H:%M:%S')}")
            else:
                # Find persona for avatar and styling
                persona = self.session_manager.find_persona_by_name(message["persona_name"])
                avatar = get_persona_avatar(persona)

                with st.chat_message("assistant", avatar=avatar):
                    # Show persona header
                    render_persona_header(persona) if persona else st.write(message["persona_name"])

                    # Show thinking process if available
                    if "thinking" in message and message["thinking"] and message["thinking"].strip():
                        with st.expander("🧠 AI's Thinking Process", expanded=False):
                            st.code(message["thinking"], language="text", wrap_lines=True)

                    # Show message content with @mention highlighting
                    content = message["content"]
                    if "@" in content:
                        content_with_highlights = highlight_mentions(content, enabled_personas)
                        st.markdown(content_with_highlights, unsafe_allow_html=True)
                    else:
                        st.write(content)

                    # Show timestamp and model info
                    st.caption(
                        f"🕒 {message['timestamp'].strftime('%H:%M:%S')} • 🤖 {message['model']}"
                    )

    def render_auto_run_interface(self) -> None:
        """Render the auto-running conversation interface."""
        if not self.session_manager.is_conversation_running():
            return

        if not self.session_manager.get_setting("auto_advance", False):
            return

        auto_run_count = self.session_manager.get_auto_run_count()
        enabled_personas = self.session_manager.get_enabled_personas()

        with st.status(
            f"🔄 Auto-running conversation... (Turn {auto_run_count})",
            expanded=True,
        ) as status:
            st.write("⏸️ Click **Pause** to stop auto-running")
            st.write(f"🎭 {len(enabled_personas)} personas active")

            # Calculate and show delay
            delay = self.conversation_orchestrator.get_conversation_delay()
            st.write(f"⏳ Waiting {delay:.1f} seconds...")
            time.sleep(delay)

            # Execute the next turn
            success, persona = await self._execute_turn_with_status(status)

            if success:
                status.update(label="Turn completed", state="complete", expanded=False)
            else:
                status.update(
                    label="Turn failed",
                    state="error",
                    expanded=False
                )

        # Continue the auto-run cycle
        if self.conversation_orchestrator.should_continue_conversation():
            st.rerun()

    async def _execute_turn_with_status(self, status_container: Any) -> tuple[bool, AIPersona | None]:
        """Execute a conversation turn with status updates.

        Args:
            status_container: Streamlit status container for updates

        Returns:
            Tuple of (success, persona)
        """
        def status_callback(message: str) -> None:
            """Update status container with message."""
            with status_container:
                st.info(message)

        return await self.conversation_orchestrator.execute_conversation_turn(status_callback)

    def render_manual_turn_if_pending(self) -> None:
        """Execute manual turn if one is pending."""
        if self.session_manager.is_pending_manual_turn():
            self.session_manager.set_pending_manual_turn(False)

            # Execute the turn
            success, persona = asyncio.run(
                self.conversation_orchestrator.execute_conversation_turn()
            )

            if not success:
                persona_name = persona.name if persona else "Unknown"
                st.error(f"Failed to execute turn for {persona_name}")

            st.rerun()

    def render_conversation_statistics(self) -> None:
        """Render conversation statistics panel."""
        stats = self.conversation_orchestrator.get_conversation_stats()

        st.subheader("📊 Conversation Statistics")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Messages", stats["total_messages"])
            st.metric("Auto-Run Turns", stats["auto_run_count"])
        with col2:
            st.metric("Enabled Personas", stats["enabled_personas"])
            st.metric("Session Age", f"{stats['session_age_seconds']:.0f}s")

        # Show message counts by persona
        if stats["persona_message_counts"]:
            st.subheader("💬 Message Activity")
            for persona_name, count in stats["persona_message_counts"].items():
                st.write(f"• {persona_name}: {count} messages")

        # Show conversation status
        if stats["conversation_active"]:
            st.success("🔄 Conversation is actively running")
        else:
            st.info("⏸️ Conversation is paused")

    def render(self) -> None:
        """Render the complete conversation interface."""
        # Check for enabled personas first
        enabled_personas = self.session_manager.get_enabled_personas()
        if not enabled_personas:
            st.warning("⚠️ No enabled personas found. Please add and enable at least one persona.")
            return

        # Render conversation controls
        self.render_conversation_controls()

        st.divider()

        # Render conversation status
        self.render_conversation_status()

        # Handle pending manual turn
        self.render_manual_turn_if_pending()

        st.divider()

        # Main chat interface
        st.subheader("Chat")

        # Render chat input
        self.render_chat_input()

        # Render conversation messages
        self.render_conversation_messages()

        # Render auto-run interface if active
        if self.session_manager.is_conversation_running():
            self.render_auto_run_interface()

    def render_sidebar_status(self) -> None:
        """Render conversation status in the sidebar."""
        enabled_personas = self.session_manager.get_enabled_personas()

        # Conversation status
        if self.session_manager.is_conversation_running():
            st.success("🔄 Conversation Running")
        else:
            st.warning("⚠️ Conversation Not Running")

        # Show active personas
        if enabled_personas:
            st.subheader("🤖 Active Personas")
            for persona in enabled_personas:
                render_persona_list_item(persona)
        else:
            st.info("No active personas yet. Create some in the Personas tab!")

        # Quick tips
        st.divider()
        st.subheader("💡 Quick Tips")
        st.markdown("• Use **Start Conversation** for auto-running")
        st.markdown("• Click **Next Turn** for manual control")
        st.markdown("• Add messages via chat input")
        st.markdown("• Personas rotate automatically")
        st.markdown("• AIs can use **@mentions** to address each other")

        context_messages = self.session_manager.get_setting("context_messages", 20)
        st.markdown(f"• Each AI sees the last **{context_messages}** messages")

        if self.session_manager.get_setting("enable_thinking", True):
            st.markdown("• 🧠 **Thinking enabled** - View AI reasoning in expanders")
            st.markdown("• Works best with **deepseek-r1** and compatible models")