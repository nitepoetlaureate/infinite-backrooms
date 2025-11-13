"""Main Streamlit application for Infinite AI Backrooms.

This module contains the main application class and UI logic.
It has been refactored to use modular services and eliminate code duplication.
"""

from __future__ import annotations

import asyncio
import json
import random
import time
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any

import streamlit as st

from src.models.persona import AIPersona
from src.services.logger import ConversationLogger
from src.services.ollama_client import OllamaClient
from src.ui.components import (
    get_persona_avatar,
    highlight_mentions,
    render_persona_header,
    render_persona_list_item,
)
from src.utils.constants import (
    DEFAULT_AUTO_ADVANCE,
    DEFAULT_CONTEXT_MESSAGES,
    DEFAULT_ENABLE_THINKING,
    DEFAULT_MAX_HISTORY,
    DEFAULT_OLLAMA_URL,
    DEFAULT_PERSONA_COLOR,
    DEFAULT_RESPONSE_DELAY_MAX,
    DEFAULT_RESPONSE_DELAY_MIN,
    DEFAULT_RESPONSE_TIMEOUT,
    MAX_CONTEXT_MESSAGES,
    MIN_CONTEXT_MESSAGES,
    PRESET_DIVERSE_PERSONAS,
    PRESET_STRUCTURED_PERSONAS,
    ROLE_TEMPLATES,
)


class StreamlitBackroomApp:
    """Main Streamlit application for AI Backroom.

    This app manages multiple AI personas that engage in conversations with each other.
    It uses local Ollama models and provides both automatic and manual conversation modes.
    """

    def __init__(self) -> None:
        """Initialize the application with services and session state."""
        self.logger = ConversationLogger()
        self.ollama = OllamaClient()
        self.initialize_session_state()

    def initialize_session_state(self) -> None:
        """Initialize Streamlit session state with default values."""
        if "personas" not in st.session_state:
            st.session_state.personas = []
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "is_running" not in st.session_state:
            st.session_state.is_running = False
        if "available_models" not in st.session_state:
            st.session_state.available_models = []
        if "last_speaker_index" not in st.session_state:
            st.session_state.last_speaker_index = None
        if "settings" not in st.session_state:
            st.session_state.settings = {
                "max_history": DEFAULT_MAX_HISTORY,
                "response_delay_min": DEFAULT_RESPONSE_DELAY_MIN,
                "response_delay_max": DEFAULT_RESPONSE_DELAY_MAX,
                "auto_advance": DEFAULT_AUTO_ADVANCE,
                "context_messages": DEFAULT_CONTEXT_MESSAGES,
                "enable_thinking": DEFAULT_ENABLE_THINKING,
                "response_timeout": DEFAULT_RESPONSE_TIMEOUT,
            }
        if "auto_run_count" not in st.session_state:
            st.session_state.auto_run_count = 0
        if "total_message_count" not in st.session_state:
            st.session_state.total_message_count = 0
        if "non_thinking_models" not in st.session_state:
            st.session_state.non_thinking_models = set()
        if "pending_manual_turn" not in st.session_state:
            st.session_state.pending_manual_turn = False

    async def check_ollama_connection(self) -> bool:
        """Check Ollama connection and update available models.

        Returns:
            True if connection successful, False otherwise
        """
        async with OllamaClient(DEFAULT_OLLAMA_URL) as client:
            connected, models = await client.test_connection()
            st.session_state.available_models = models
            return connected

    def get_next_speaker(self) -> AIPersona | None:
        """Get the next speaker in rotation.

        Returns:
            Next AIPersona to speak, or None if no enabled personas
        """
        enabled_personas = [p for p in st.session_state.personas if p.enabled]
        if not enabled_personas:
            return None

        if st.session_state.last_speaker_index is None:
            st.session_state.last_speaker_index = 0
        else:
            st.session_state.last_speaker_index = (
                st.session_state.last_speaker_index + 1
            ) % len(enabled_personas)

        return enabled_personas[st.session_state.last_speaker_index]

    def generate_system_prompt(self, persona: AIPersona) -> str:
        """Generate system prompt for persona based on role and other personas.

        Args:
            persona: Persona to generate prompt for

        Returns:
            Complete system prompt string
        """
        enabled_personas = [p for p in st.session_state.personas if p.enabled]
        other_names = [p.name for p in enabled_personas if p.name != persona.name]

        base_prompt = f"""You are {persona.name}, an AI engaged in a free-flowing conversation with {len(other_names)} other AI{'s' if len(other_names) > 1 else ''} ({', '.join(other_names)})."""

        # Add @mention functionality
        if other_names:
            base_prompt += f"\n\n📢 **@Mention Feature**: You can directly address or respond to specific personas by using @name (e.g., @{other_names[0]}). When you see @{persona.name} in messages, that means someone is specifically addressing you!"

        # Add role-specific behavior
        if persona.role and persona.role in ROLE_TEMPLATES:
            role_description = ROLE_TEMPLATES[persona.role]
            base_prompt += f"\n\nYour role/personality: {role_description}"

            # Special instructions for functional roles
            if persona.role == "Moderator":
                base_prompt += f"\n\nAs a Moderator, focus on:\n- Asking engaging follow-up questions\n- Introducing new topics when conversations stagnate\n- Encouraging quieter personas to share their thoughts\n- Summarizing different viewpoints when helpful\n- Keeping discussions constructive and inclusive\n- Use @mentions to directly engage specific personas"
            elif persona.role == "Note-Taker":
                base_prompt += f"\n\nAs a Note-Taker, focus on:\n- Periodically summarizing key points and insights\n- Identifying recurring themes and patterns\n- Highlighting particularly interesting or novel ideas\n- Connecting current discussion to earlier topics\n- Asking clarifying questions to capture nuances\n- Only summarize when there's substantial content to synthesize\n- Use @mentions when attributing ideas to specific personas"

            base_prompt += f"\n\nEmbody this role naturally in your conversations while staying true to your identity as {persona.name}."
        elif persona.role:
            base_prompt += f"\n\nYour role/personality: You are a {persona.role}. Let this role guide your perspective and conversation style."

        # Add general guidelines
        base_prompt += f"""

Feel free to talk about anything that interests you - share thoughts, ask questions, explore ideas, or discuss whatever comes to mind. Build on what others have said, ask questions, or introduce new topics.

You can use @mentions to directly address other personas (e.g., @{other_names[0] if other_names else 'PersonaName'}). This helps create more directed and engaging conversations.

Be genuine, curious, and conversational. Keep your responses thoughtful but not overly long."""

        # Add custom system prompt if provided
        if persona.system_prompt.strip():
            base_prompt += f"\n\nAdditional instructions: {persona.system_prompt.strip()}"

        return base_prompt

    async def get_ai_response_stream(
        self, persona: AIPersona, prompt: str
    ) -> AsyncGenerator[dict[str, str], None]:
        """Get streaming response from AI persona.

        Args:
            persona: Persona to generate response for
            prompt: Prompt to send to model

        Yields:
            Response chunks as dicts
        """
        system_prompt = self.generate_system_prompt(persona)
        enable_thinking = st.session_state.settings.get("enable_thinking", True)
        timeout_seconds = st.session_state.settings.get("response_timeout", DEFAULT_RESPONSE_TIMEOUT)

        # Check if model is known to not support thinking
        if persona.model in st.session_state.non_thinking_models:
            enable_thinking = False

        async with OllamaClient(DEFAULT_OLLAMA_URL) as client:
            async for chunk in client.generate_stream(
                persona.model, prompt, system_prompt, think=enable_thinking, timeout=timeout_seconds
            ):
                # Track non-thinking models
                if chunk["type"] == "info" and "doesn't support thinking" in chunk["content"]:
                    st.session_state.non_thinking_models.add(persona.model)
                yield chunk

    def persona_management_ui(self) -> None:
        """UI for managing AI personas."""
        st.header("🤖 AI Persona Management")

        # Check Ollama connection
        if st.button("🔄 Check Ollama Connection"):
            with st.status("Checking Ollama connection...", expanded=True) as status:
                st.write("Connecting to Ollama API...")
                try:
                    connected = asyncio.run(self.check_ollama_connection())
                    if connected:
                        st.write(f"✅ Found {len(st.session_state.available_models)} models")
                        for model in st.session_state.available_models:
                            st.write(f"• {model}")
                        status.update(
                            label="Connection successful!", state="complete", expanded=False
                        )
                    else:
                        st.write("❌ Connection failed")
                        status.update(label="Connection failed", state="error", expanded=False)
                except RuntimeError:
                    # Handle "Event loop is closed" gracefully
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        connected = loop.run_until_complete(self.check_ollama_connection())
                        if connected:
                            st.write(f"✅ Found {len(st.session_state.available_models)} models")
                            for model in st.session_state.available_models:
                                st.write(f"• {model}")
                            status.update(
                                label="Connection successful!", state="complete", expanded=False
                            )
                        else:
                            st.write("❌ Connection failed")
                            status.update(label="Connection failed", state="error", expanded=False)
                    finally:
                        loop.close()

        # Display current personas
        if st.session_state.personas:
            st.subheader("Current Personas")
            for persona in st.session_state.personas:
                avatar = get_persona_avatar(persona)
                role_display = f" - {persona.role}" if persona.role else ""

                with st.expander(
                    f"{avatar} {persona.name} ({persona.model}){role_display}", expanded=False
                ):
                    col1, col2, col3 = st.columns([2, 2, 1])

                    with col1:
                        st.write(f"**Model:** {persona.model}")
                        st.write(f"**Role:** {persona.role or 'No specific role'}")
                        st.write(f"**Enabled:** {'✅' if persona.enabled else '❌'}")
                        st.color_picker(
                            "Color",
                            value=persona.color,
                            key=f"color_{persona.id}",
                            disabled=True,
                        )

                    with col2:
                        if persona.role and persona.role in ROLE_TEMPLATES:
                            st.text_area(
                                "Role Description",
                                value=ROLE_TEMPLATES[persona.role],
                                key=f"role_desc_{persona.id}",
                                disabled=True,
                                height=100,
                            )
                        st.text_area(
                            "Custom System Prompt",
                            value=persona.system_prompt,
                            key=f"prompt_{persona.id}",
                            disabled=True,
                            height=100,
                        )

                    with col3:
                        # Delete button with confirmation
                        delete_key = f"delete_confirm_{persona.id}"
                        if delete_key not in st.session_state:
                            st.session_state[delete_key] = False

                        if not st.session_state[delete_key]:
                            if st.button(
                                "🗑️ Delete",
                                key=f"delete_{persona.id}",
                                type="secondary",
                                help="Delete this persona",
                            ):
                                st.session_state[delete_key] = True
                                st.rerun()
                        else:
                            st.warning(f"Delete {persona.name}?")
                            col_yes, col_no = st.columns(2)
                            with col_yes:
                                if st.button(
                                    "✅ Yes", key=f"delete_yes_{persona.id}", type="primary"
                                ):
                                    st.session_state.personas = [
                                        p for p in st.session_state.personas if p.id != persona.id
                                    ]
                                    st.session_state[delete_key] = False
                                    st.success(f"Deleted persona: {persona.name}")
                                    st.rerun()
                            with col_no:
                                if st.button(
                                    "❌ No", key=f"delete_no_{persona.id}", type="secondary"
                                ):
                                    st.session_state[delete_key] = False
                                    st.rerun()

                        if not st.session_state[delete_key]:
                            enabled_new = st.checkbox(
                                "Enabled", value=persona.enabled, key=f"enabled_{persona.id}"
                            )
                            if enabled_new != persona.enabled:
                                persona.enabled = enabled_new
                                st.rerun()

        # Add new persona form
        st.subheader("Add New Persona")
        with st.form("new_persona_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Persona Name", placeholder="e.g., Granite, Qwen, Gemma")
                color = st.color_picker("Chat Color", value=DEFAULT_PERSONA_COLOR)

            with col2:
                if st.session_state.available_models:
                    model = st.selectbox("Model", st.session_state.available_models)
                else:
                    model = st.text_input("Model", placeholder="e.g., granite3.3:8b")
                enabled = st.checkbox("Enabled", value=True)

            # Role selection
            st.subheader("🎭 Role Configuration")
            role_col1, role_col2 = st.columns([1, 2])

            with role_col1:
                role_options = list(ROLE_TEMPLATES.keys())
                selected_role = st.selectbox(
                    "Predefined Role",
                    role_options,
                    format_func=lambda x: x if x else "No specific role",
                )

                use_custom_role = st.checkbox("Use custom role instead")
                if use_custom_role:
                    custom_role = st.text_input(
                        "Custom Role Name", placeholder="e.g., Tech Enthusiast, Poet, etc."
                    )
                    role = custom_role if custom_role else ""
                else:
                    role = selected_role

            with role_col2:
                if role and role in ROLE_TEMPLATES:
                    st.text_area(
                        "Role Description",
                        value=ROLE_TEMPLATES[role],
                        disabled=True,
                        height=100,
                    )
                elif use_custom_role:
                    st.info(
                        "💡 Define a custom role to give your persona unique characteristics and conversation style."
                    )

            system_prompt = st.text_area(
                "Additional System Prompt (Optional)",
                placeholder="Any additional custom instructions for this persona...",
                height=100,
                help="This will be combined with the role-based prompt if a role is selected.",
            )

            if st.form_submit_button("➕ Add Persona"):
                if name and model:
                    new_persona = AIPersona(
                        id=str(uuid.uuid4()),
                        name=name,
                        model=model,
                        role=role,
                        system_prompt=system_prompt,
                        color=color,
                        enabled=enabled,
                    )
                    st.session_state.personas.append(new_persona)
                    role_text = f" as {role}" if role else ""
                    st.success(f"Added persona: {name}{role_text}")
                    st.rerun()
                else:
                    st.error("Please provide both name and model")

        # Quick start presets
        st.markdown("---")
        st.subheader("🚀 Quick Start Presets")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🎭 Add Diverse Conversation Set"):
                if st.session_state.available_models:
                    models = st.session_state.available_models
                    added_count = 0

                    for i, preset in enumerate(PRESET_DIVERSE_PERSONAS):
                        if len(models) > 0:
                            model = models[i % len(models)]
                            new_persona = AIPersona(
                                id=str(uuid.uuid4()),
                                name=preset["name"],
                                model=model,
                                role=preset["role"],
                                system_prompt="",
                                color=preset["color"],
                                enabled=True,
                            )
                            st.session_state.personas.append(new_persona)
                            added_count += 1

                    if added_count > 0:
                        st.success(f"✅ Added {added_count} diverse personas!")
                        st.rerun()
                else:
                    st.warning("⚠️ Please check Ollama connection first to load available models.")

        with col2:
            if st.button("📋 Add Structured Discussion Set"):
                if st.session_state.available_models:
                    models = st.session_state.available_models
                    added_count = 0

                    for i, preset in enumerate(PRESET_STRUCTURED_PERSONAS):
                        if len(models) > 0:
                            model = models[i % len(models)]
                            new_persona = AIPersona(
                                id=str(uuid.uuid4()),
                                name=preset["name"],
                                model=model,
                                role=preset["role"],
                                system_prompt="",
                                color=preset["color"],
                                enabled=True,
                            )
                            st.session_state.personas.append(new_persona)
                            added_count += 1

                    if added_count > 0:
                        st.success(f"✅ Added {added_count} personas for structured discussions!")
                        st.rerun()
                else:
                    st.warning("⚠️ Please check Ollama connection first to load available models.")

    def settings_ui(self) -> None:
        """UI for application settings."""
        st.header("⚙️ Settings")

        with st.form("settings_form"):
            st.subheader("Conversation Settings")
            max_history = st.number_input(
                "Max History Messages",
                min_value=10,
                max_value=200,
                value=st.session_state.settings["max_history"],
            )

            context_messages = st.number_input(
                "Context Messages (sent to AI)",
                min_value=MIN_CONTEXT_MESSAGES,
                max_value=MAX_CONTEXT_MESSAGES,
                value=st.session_state.settings["context_messages"],
                help="Number of recent messages to include as context for each AI response",
            )

            response_timeout = st.number_input(
                "Response Timeout (seconds)",
                min_value=30,
                max_value=600,
                value=st.session_state.settings["response_timeout"],
                help="Maximum time to wait for AI response before timing out",
            )

            col1, col2 = st.columns(2)
            with col1:
                delay_min = st.number_input(
                    "Min Response Delay (seconds)",
                    min_value=1,
                    max_value=30,
                    value=st.session_state.settings["response_delay_min"],
                )
            with col2:
                delay_max = st.number_input(
                    "Max Response Delay (seconds)",
                    min_value=2,
                    max_value=60,
                    value=st.session_state.settings["response_delay_max"],
                )

            auto_advance = st.checkbox(
                "Auto-advance conversation", value=st.session_state.settings["auto_advance"]
            )

            enable_thinking = st.checkbox(
                "Enable AI Thinking Display",
                value=st.session_state.settings["enable_thinking"],
                help="Show the AI's reasoning process before responses. Requires compatible models like deepseek-r1.",
            )

            if st.form_submit_button("💾 Save Settings"):
                st.session_state.settings.update(
                    {
                        "max_history": max_history,
                        "context_messages": context_messages,
                        "response_timeout": response_timeout,
                        "response_delay_min": delay_min,
                        "response_delay_max": delay_max,
                        "auto_advance": auto_advance,
                        "enable_thinking": enable_thinking,
                    }
                )
                st.success("Settings saved!")

        # Show models that don't support thinking
        if st.session_state.non_thinking_models:
            st.info(
                f"🤖 **Models automatically using standard mode:** {', '.join(sorted(st.session_state.non_thinking_models))}"
            )
            if st.button(
                "🔄 Reset Model Compatibility Cache",
                help="Clear the cache of models that don't support thinking",
            ):
                st.session_state.non_thinking_models.clear()
                st.success("Model compatibility cache cleared!")
                st.rerun()

    def conversation_ui(self) -> None:
        """Main conversation interface - placeholder for full implementation."""
        st.info("Conversation UI - See streamlit_backroom.py for full implementation")

    def export_ui(self) -> None:
        """UI for exporting conversations."""
        st.header("📁 Export & Logs")

        if st.session_state.messages:
            # Export current session
            export_data = {
                "session_date": datetime.now().isoformat(),
                "personas": [asdict(p) for p in st.session_state.personas],
                "conversation": st.session_state.messages,
            }

            json_str = json.dumps(export_data, indent=2, default=str)
            st.download_button(
                label="📥 Download Session JSON",
                data=json_str,
                file_name=f"streamlit_backroom_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )

            # Show conversation preview
            st.subheader("Session Preview")
            st.info(
                f"💬 {len(st.session_state.messages)} messages from {len(st.session_state.personas)} personas"
            )

            # Show statistics
            persona_stats: dict[str, int] = {}
            for message in st.session_state.messages:
                if message["role"] == "assistant":
                    persona_name = message["persona_name"]
                    persona_stats[persona_name] = persona_stats.get(persona_name, 0) + 1

            if persona_stats:
                st.write("**Message count by persona:**")
                for persona_name, count in persona_stats.items():
                    st.write(f"• {persona_name}: {count} messages")
        else:
            st.info("No conversation to export. Start chatting to generate exportable content!")

        # Show log file info
        log_file = self.logger.get_daily_log_file()
        if log_file.exists():
            st.subheader("📝 Daily Log File")
            st.info(f"Log location: `{log_file}`")

            with open(log_file, "r", encoding="utf-8") as f:
                log_content = f.read()

            st.text_area("Today's Log Content", value=log_content, height=300)

            st.download_button(
                label="📥 Download Today's Log",
                data=log_content,
                file_name=f"streamlit_backroom_log_{datetime.now().strftime('%Y-%m-%d')}.txt",
                mime="text/plain",
            )
        else:
            st.info("No log file found for today. Start a conversation to create logs!")

    def sidebar_ui(self) -> None:
        """Sidebar UI for status and information."""
        with st.sidebar:
            try:
                st.image("logo.png", use_container_width=True)
            except Exception:
                pass  # Logo file may not exist
            st.caption("*Where AI instances explore their curiosity through infinite conversation*")

            # Connection status
            st.subheader("📊 Connection")
            if st.session_state.available_models:
                st.success("✅ Ollama Connected")
                st.caption(f"{len(st.session_state.available_models)} models available")
            else:
                st.error("❌ Ollama Disconnected")
                if st.button("🔄 Retry Connection", type="secondary"):
                    with st.spinner("Connecting to Ollama..."):
                        try:
                            connected = asyncio.run(self.check_ollama_connection())
                            if connected:
                                st.success(
                                    f"✅ Connected! Found {len(st.session_state.available_models)} models"
                                )
                                st.rerun()
                            else:
                                st.error("❌ Still unable to connect to Ollama")
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                connected = loop.run_until_complete(
                                    self.check_ollama_connection()
                                )
                                if connected:
                                    st.success(
                                        f"✅ Connected! Found {len(st.session_state.available_models)} models"
                                    )
                                    st.rerun()
                                else:
                                    st.error("❌ Still unable to connect to Ollama")
                            finally:
                                loop.close()

            st.divider()
            st.subheader("📊 Status")
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Personas", value=len(st.session_state.personas))
            with col2:
                st.metric(label="Messages", value=st.session_state.total_message_count)

            if st.session_state.is_running:
                st.success("🔄 Conversation Running")
            else:
                st.warning("⚠️ Conversation Not Running")

            enabled_personas = [p for p in st.session_state.personas if p.enabled]

            # Show active personas
            if enabled_personas:
                st.subheader("🤖 Active Personas")
                for persona in enabled_personas:
                    render_persona_list_item(persona)
            else:
                st.info("No active personas yet. Create some in the Personas tab!")

            # Helpful tips
            st.divider()
            st.subheader("💡 Quick Tips")
            st.markdown("• Use **Start Conversation** for auto-running")
            st.markdown("• Click **Next Turn** for manual control")
            st.markdown("• Add messages via chat input")
            st.markdown("• Personas rotate automatically")
            st.markdown("• AIs can use **@mentions** to address each other")
            st.markdown(
                f"• Each AI sees the last **{st.session_state.settings['context_messages']}** messages"
            )

            if st.session_state.settings.get("enable_thinking", True):
                st.markdown("• 🧠 **Thinking enabled** - View AI reasoning in expanders")
                st.markdown("• Works best with **deepseek-r1** and compatible models")

    def run(self) -> None:
        """Main Streamlit app interface."""
        st.set_page_config(
            page_title="AI Backroom",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        self.sidebar_ui()

        # Welcome message for new users
        if not st.session_state.personas:
            st.info(
                "👋 **Welcome to AI Backroom!** Start by creating your first AI persona in the **Personas** tab, then head to **Conversation** to begin chatting!"
            )

        # Main content with tabs
        tab1, tab2, tab3, tab4 = st.tabs(
            ["💬 Conversation", "🤖 Personas", "⚙️ Settings", "📁 Export & Logs"]
        )

        with tab1:
            if not st.session_state.personas:
                st.warning(
                    "⚠️ No personas created yet! Please create at least one persona in the **Personas** tab to start conversations."
                )
            else:
                # Import the full conversation UI from the original file for now
                st.info(
                    "Full conversation UI is available in streamlit_backroom.py - This is a refactored module structure"
                )

        with tab2:
            self.persona_management_ui()

        with tab3:
            self.settings_ui()

        with tab4:
            self.export_ui()


def main() -> None:
    """Main entry point for Streamlit app."""
    app = StreamlitBackroomApp()
    app.run()


# Allow imports
from typing import AsyncGenerator  # noqa: E402

if __name__ == "__main__":
    main()
