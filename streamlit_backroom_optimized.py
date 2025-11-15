#!/usr/bin/env python3
"""Infinite AI Backroom - Streamlit Web App (PERFORMANCE OPTIMIZED).

This optimized version includes:
- Aggressive caching with @st.cache_data and @st.cache_resource
- Performance monitoring and metrics
- Optimized message rendering
- Improved async resource management
- Reduced re-renders
- Lazy loading of heavy components
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any, AsyncGenerator

import streamlit as st

from src.models.memory import MemoryConfig, SessionMetrics, create_memory_config, create_session_metrics
from src.models.persona import AIPersona
from src.services.secure_logger import SecureConversationLogger
from src.services.ollama_client import OllamaClient
from src.ui.components import (
    get_persona_avatar,
    highlight_mentions,
    render_persona_header,
    render_persona_list_item,
)
from src.ui.memory_optimized_chat import MemoryOptimizedChat, create_memory_optimized_chat
from src.utils.constants import (
    AUTO_ADVANCE_DEFAULT,
    AUTO_RUN_DELAY_MAX,
    AUTO_RUN_DELAY_MIN,
    DEFAULT_CONTEXT_MESSAGES,
    DEFAULT_HISTORY_MESSAGES,
    DEFAULT_OLLAMA_URL,
    DEFAULT_PERSONA_COLOR,
    DEFAULT_RESPONSE_TIMEOUT,
    ENABLE_THINKING,
    MAX_CONTEXT_MESSAGES,
    MIN_CONTEXT_MESSAGES,
    PRESET_DIVERSE_PERSONAS,
    PRESET_STRUCTURED_PERSONAS,
    ROLE_EMOJI_MAP,
    ROLE_TEMPLATES,
)
from src.utils.performance import PerformanceTimer, get_metrics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# CACHED FUNCTIONS - These never change during runtime
# ============================================================================

@st.cache_data(show_spinner=False)
def load_system_css() -> str:
    """Load System.css file content (cached).

    Returns:
        CSS content as string
    """
    with open("static/css/system.css", "r") as f:
        return f.read()


@st.cache_data(show_spinner=False)
def get_role_templates() -> dict[str, str]:
    """Get role templates (cached constant).

    Returns:
        Dictionary of role templates
    """
    return ROLE_TEMPLATES.copy()


@st.cache_data(show_spinner=False)
def get_role_emoji_map() -> dict[str, str]:
    """Get role emoji mapping (cached constant).

    Returns:
        Dictionary of role to emoji mappings
    """
    return ROLE_EMOJI_MAP.copy()


@st.cache_data(show_spinner=False)
def get_preset_personas() -> tuple[list[dict], list[dict]]:
    """Get preset persona configurations (cached).

    Returns:
        Tuple of (diverse_personas, structured_personas)
    """
    return PRESET_DIVERSE_PERSONAS.copy(), PRESET_STRUCTURED_PERSONAS.copy()


def inject_system_css() -> None:
    """Inject System.css styling into the Streamlit app for retro Mac OS aesthetic."""
    # Use cached CSS loading
    system_css = load_system_css()

    st.markdown(
        f"""
        <style>
        {system_css}

        /* ===== Streamlit-specific System 7 Overrides ===== */

        /* Main app background - System 7 grid pattern */
        .stApp {{
            font-family: Chicago_12, Chicago, Monaco, monospace !important;
            background: linear-gradient(90deg, #FFFFFF 21px, transparent 1%) center,
                        linear-gradient(#FFFFFF 21px, transparent 1%) center, #000000 !important;
            background-size: 22px 22px !important;
            background-attachment: fixed !important;
            color: #000000 !important;
        }}

        /* Main content area */
        .main .block-container {{
            background-color: #FFFFFF !important;
            border: 2px solid #000000 !important;
            box-shadow: 2px 2px #000000 !important;
            padding: 2rem !important;
            font-family: Chicago_12, Chicago, Monaco, monospace !important;
        }}

        /* Headers - Chicago font */
        h1, h2, h3, h4, h5, h6 {{
            font-family: Chicago, Chicago_12, monospace !important;
            color: #000000 !important;
        }}

        /* Buttons - System 7 style */
        .stButton > button {{
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
        }}

        .stButton > button:hover {{
            background: #F0F0F0 !important;
            border: 3px solid #000000 !important;
        }}

        .stButton > button:active {{
            background: #000000 !important;
            color: #FFFFFF !important;
            border-radius: 8px !important;
        }}

        /* Text inputs - Monaco font with simple border */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {{
            font-family: Monaco, monospace !important;
            font-size: 14px !important;
            border: 2px solid #000000 !important;
            border-radius: 0 !important;
            background: #FFFFFF !important;
            color: #000000 !important;
            padding: 4px 8px !important;
            box-shadow: inset 1px 1px 0px #000000 !important;
        }}

        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {{
            outline: 2px solid #000000 !important;
            outline-offset: 2px !important;
            border-color: #000000 !important;
            box-shadow: inset 1px 1px 0px #000000 !important;
        }}

        /* Select boxes */
        .stSelectbox > div > div {{
            font-family: Chicago_12, Monaco, monospace !important;
            font-size: 14px !important;
            border: 2px solid #000000 !important;
            border-radius: 0 !important;
            background: #FFFFFF !important;
        }}

        /* Tabs - System 7 style */
        .stTabs [data-baseweb="tab-list"] {{
            background: #FFFFFF !important;
            border-bottom: 2px solid #000000 !important;
            gap: 2px !important;
        }}

        .stTabs [data-baseweb="tab"] {{
            font-family: Chicago_12, Chicago, monospace !important;
            font-size: 14px !important;
            background: #FFFFFF !important;
            border: 2px solid #000000 !important;
            border-bottom: none !important;
            border-radius: 8px 8px 0 0 !important;
            color: #000000 !important;
            padding: 8px 16px !important;
        }}

        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            background: #FFFFFF !important;
            border-bottom: 2px solid #FFFFFF !important;
            margin-bottom: -2px !important;
        }}

        .stTabs [data-baseweb="tab"]:hover {{
            background: #F0F0F0 !important;
        }}

        .stTabs [data-baseweb="tab-panel"] {{
            background: #FFFFFF !important;
            border: 2px solid #000000 !important;
            border-top: none !important;
            padding: 1rem !important;
        }}

        /* Expanders */
        .streamlit-expanderHeader {{
            font-family: Chicago_12, Chicago, monospace !important;
            font-size: 16px !important;
            background: #FFFFFF !important;
            border: 2px solid #000000 !important;
            border-radius: 0 !important;
            color: #000000 !important;
        }}

        .streamlit-expanderContent {{
            border: 2px solid #000000 !important;
            border-top: none !important;
            background: #FFFFFF !important;
        }}

        /* Sidebar - Window style */
        section[data-testid="stSidebar"] {{
            background: #FFFFFF !important;
            border-right: 2px solid #000000 !important;
        }}

        section[data-testid="stSidebar"] > div {{
            background: #FFFFFF !important;
        }}

        /* Info boxes */
        .stAlert {{
            border: 2px solid #000000 !important;
            border-radius: 0 !important;
            box-shadow: 2px 2px #000000 !important;
            font-family: Chicago_12, Monaco, monospace !important;
            background: #FFFFFF !important;
        }}

        /* Code blocks */
        code {{
            font-family: Monaco, monospace !important;
            background: #FFFFFF !important;
            border: 1px solid #000000 !important;
            color: #000000 !important;
        }}

        pre {{
            font-family: Monaco, monospace !important;
            background: #FFFFFF !important;
            border: 2px solid #000000 !important;
            color: #000000 !important;
        }}

        /* Scrollbars - System 7 style */
        ::-webkit-scrollbar {{
            width: 16px !important;
            height: 16px !important;
            background-color: #FFFFFF !important;
        }}

        ::-webkit-scrollbar-track {{
            background: linear-gradient(45deg, #000000 25%, transparent 25%, transparent 75%, #000000 75%, #000000),
                        linear-gradient(45deg, #000000 25%, transparent 25%, transparent 75%, #000000 75%, #000000) !important;
            background-color: #FFFFFF !important;
            background-size: 4px 4px !important;
            background-position: 0 0, 2px 2px !important;
            border-left: 2px solid #000000 !important;
        }}

        ::-webkit-scrollbar-thumb {{
            background-color: #FFFFFF !important;
            border: 2px solid #000000 !important;
        }}

        ::-webkit-scrollbar-button {{
            background-color: #FFFFFF !important;
            border: 2px solid #000000 !important;
        }}

        /* Chat messages */
        .stChatMessage {{
            border: 2px solid #000000 !important;
            border-radius: 0 !important;
            background: #FFFFFF !important;
            box-shadow: 2px 2px #000000 !important;
            font-family: Monaco, monospace !important;
            margin-bottom: 8px !important;
        }}

        /* Remove Streamlit branding */
        footer {{
            display: none !important;
        }}

        #MainMenu {{
            display: none !important;
        }}

        header {{
            display: none !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


class StreamlitBackroomApp:
    """Main Streamlit application for AI Backroom (Performance Optimized)."""

    def __init__(self) -> None:
        """Initialize the application with memory optimization."""
        self.logger = SecureConversationLogger()
        self.chat: MemoryOptimizedChat | None = None
        self.session_metrics: SessionMetrics | None = None
        self.initialize_session_state()
        self.metrics = get_metrics()

    def initialize_session_state(self) -> None:
        """Initialize Streamlit session state with memory optimization."""
        if "personas" not in st.session_state:
            st.session_state.personas = []
        if "is_running" not in st.session_state:
            st.session_state.is_running = False
        if "available_models" not in st.session_state:
            st.session_state.available_models = []
        if "last_speaker_index" not in st.session_state:
            st.session_state.last_speaker_index = None
        if "non_thinking_models" not in st.session_state:
            st.session_state.non_thinking_models = set()
        if "pending_manual_turn" not in st.session_state:
            st.session_state.pending_manual_turn = False
        if "performance_monitoring" not in st.session_state:
            st.session_state.performance_monitoring = False

        # Memory optimization settings
        if "memory_config" not in st.session_state:
            st.session_state.memory_config = create_memory_config()

        # Traditional settings (for compatibility)
        if "settings" not in st.session_state:
            st.session_state.settings = {
                "max_history": DEFAULT_HISTORY_MESSAGES,
                "response_delay_min": AUTO_RUN_DELAY_MIN,
                "response_delay_max": AUTO_RUN_DELAY_MAX,
                "auto_advance": AUTO_ADVANCE_DEFAULT,
                "context_messages": DEFAULT_CONTEXT_MESSAGES,
                "enable_thinking": ENABLE_THINKING,
                "response_timeout": DEFAULT_RESPONSE_TIMEOUT,
            }

        # Initialize chat system if not exists
        if "optimized_chat" not in st.session_state:
            memory_config = st.session_state.memory_config
            st.session_state.optimized_chat = create_memory_optimized_chat(
                strategy="hybrid",
                messages_per_page=memory_config.messages_per_page,
                cleanup_threshold=memory_config.cleanup_threshold,
                auto_cleanup=memory_config.auto_cleanup
            )

        # Initialize session metrics
        if "session_metrics" not in st.session_state:
            st.session_state.session_metrics = create_session_metrics()

        self.chat = st.session_state.optimized_chat
        self.session_metrics = st.session_state.session_metrics

    async def check_ollama_connection(self) -> bool:
        """Check Ollama connection and update available models.

        Returns:
            True if connection successful
        """
        with PerformanceTimer("check_ollama_connection"):
            async with OllamaClient(DEFAULT_OLLAMA_URL) as client:
                connected, models = await client.test_connection()
                st.session_state.available_models = models
                return connected

    def get_next_speaker(self) -> AIPersona | None:
        """Get the next speaker in rotation.

        Returns:
            Next AIPersona or None if no enabled personas
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
        """Generate system prompt for persona.

        Args:
            persona: Persona to generate prompt for

        Returns:
            Complete system prompt
        """
        enabled_personas = [p for p in st.session_state.personas if p.enabled]
        other_names = [p.name for p in enabled_personas if p.name != persona.name]

        base_prompt = f"""You are {persona.name}, an AI engaged in a free-flowing conversation with {len(other_names)} other AI{'s' if len(other_names) > 1 else ''} ({', '.join(other_names)})."""

        # Add @mention functionality
        if other_names:
            base_prompt += f"\n\n📢 **@Mention Feature**: You can directly address or respond to specific personas by using @name (e.g., @{other_names[0]}). When you see @{persona.name} in messages, that means someone is specifically addressing you!"

        # Add role-specific behavior (use cached template)
        role_templates = get_role_templates()
        if persona.role and persona.role in role_templates:
            role_description = role_templates[persona.role]
            base_prompt += f"\n\nYour role/personality: {role_description}"

            if persona.role == "Moderator":
                base_prompt += "\n\nAs a Moderator, focus on:\n- Asking engaging follow-up questions\n- Introducing new topics when conversations stagnate\n- Encouraging quieter personas to share their thoughts\n- Summarizing different viewpoints when helpful\n- Keeping discussions constructive and inclusive\n- Use @mentions to directly engage specific personas"
            elif persona.role == "Note-Taker":
                base_prompt += "\n\nAs a Note-Taker, focus on:\n- Periodically summarizing key points and insights\n- Identifying recurring themes and patterns\n- Highlighting particularly interesting or novel ideas\n- Connecting current discussion to earlier topics\n- Asking clarifying questions to capture nuances\n- Only summarize when there's substantial content to synthesize\n- Use @mentions when attributing ideas to specific personas"

            base_prompt += f"\n\nEmbody this role naturally in your conversations while staying true to your identity as {persona.name}."
        elif persona.role:
            base_prompt += f"\n\nYour role/personality: You are a {persona.role}. Let this role guide your perspective and conversation style."

        # Add general guidelines
        base_prompt += f"""

Feel free to talk about anything that interests you - share thoughts, ask questions, explore ideas, or discuss whatever comes to mind. Build on what others have said, ask questions, or introduce new topics.

You can use @mentions to directly address other personas (e.g., @{other_names[0] if other_names else 'PersonaName'}). This helps create more directed and engaging conversations.

Be genuine, curious, and conversational. Keep your responses thoughtful but not overly long."""

        # Add custom system prompt
        if persona.system_prompt.strip():
            base_prompt += f"\n\nAdditional instructions: {persona.system_prompt.strip()}"

        return base_prompt

    async def get_ai_response_stream(
        self, persona: AIPersona, prompt: str
    ) -> AsyncGenerator[dict[str, str], None]:
        """Get streaming response from AI persona.

        Args:
            persona: Persona to get response from
            prompt: Prompt to send

        Yields:
            Response chunks
        """
        system_prompt = self.generate_system_prompt(persona)
        enable_thinking = st.session_state.settings.get("enable_thinking", ENABLE_THINKING)
        timeout_seconds = st.session_state.settings.get(
            "response_timeout", DEFAULT_RESPONSE_TIMEOUT
        )

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
                        # Use cached role templates
                        role_templates = get_role_templates()
                        if persona.role and persona.role in role_templates:
                            st.text_area(
                                "Role Description",
                                value=role_templates[persona.role],
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

        # Add new persona
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

            # Role selection (use cached data)
            st.subheader("🎭 Role Configuration")
            role_col1, role_col2 = st.columns([1, 2])

            with role_col1:
                role_templates = get_role_templates()
                role_options = list(role_templates.keys())
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
                if role and role in role_templates:
                    st.text_area(
                        "Role Description",
                        value=role_templates[role],
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

        # Quick start presets (use cached data)
        st.markdown("---")
        st.subheader("🚀 Quick Start Presets")

        col1, col2 = st.columns(2)

        diverse_personas, structured_personas = get_preset_personas()

        with col1:
            if st.button("🎭 Add Diverse Conversation Set"):
                if st.session_state.available_models:
                    models = st.session_state.available_models
                    added_count = 0

                    for i, preset in enumerate(diverse_personas):
                        if len(models) > 0:
                            model = models[i % len(models)]
                            new_persona = AIPersona(
                                id=str(uuid.uuid4()),
                                name=preset["name"],
                                model=model,
                                role=preset["role"],
                                system_prompt="",
                                color=preset.get("color", DEFAULT_PERSONA_COLOR),
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

                    for i, preset in enumerate(structured_personas):
                        if len(models) > 0:
                            model = models[i % len(models)]
                            new_persona = AIPersona(
                                id=str(uuid.uuid4()),
                                name=preset["name"],
                                model=model,
                                role=preset["role"],
                                system_prompt="",
                                color=preset.get("color", DEFAULT_PERSONA_COLOR),
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
                min_value=30.0,
                max_value=600.0,
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

        # Performance monitoring toggle
        st.subheader("⚡ Performance Monitoring")
        perf_enabled = st.checkbox(
            "Enable Performance Monitoring",
            value=st.session_state.performance_monitoring,
            help="Track and display performance metrics"
        )
        if perf_enabled != st.session_state.performance_monitoring:
            st.session_state.performance_monitoring = perf_enabled
            st.rerun()

        if st.session_state.performance_monitoring:
            stats = self.metrics.get_stats()
            if stats["timings"]:
                st.write("**Performance Metrics:**")
                for operation, metrics in stats["timings"].items():
                    st.write(f"• {operation}")
                    st.write(f"  - Calls: {metrics['count']}")
                    st.write(f"  - Average: {metrics['average']*1000:.2f}ms")
                    st.write(f"  - Min/Max: {metrics['min']*1000:.2f}ms / {metrics['max']*1000:.2f}ms")

                if st.button("🔄 Reset Performance Metrics"):
                    self.metrics.reset()
                    st.success("Metrics reset!")
                    st.rerun()
            else:
                st.info("No performance data collected yet. Use the app to generate metrics.")

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
        """Main conversation interface using native Streamlit chat elements."""
        # Check if we have enabled personas
        enabled_personas = [p for p in st.session_state.personas if p.enabled]
        if not enabled_personas:
            st.warning("⚠️ No enabled personas found. Please add and enable at least one persona.")
            return

        # Control buttons
        col1, col2, col3, col4 = st.columns(4, vertical_alignment="bottom")

        with col1:
            if st.button("▶️ Start Conversation", disabled=st.session_state.is_running):
                st.session_state.is_running = True
                st.session_state.auto_run_count = 0
                st.rerun()

        with col2:
            if st.button("⏸️ Pause", disabled=not st.session_state.is_running):
                st.session_state.is_running = False
                st.rerun()

        with col3:
            if st.button("🔄 Next Turn", disabled=st.session_state.is_running):
                st.session_state.pending_manual_turn = True
                st.rerun()

        with col4:
            if st.button("🧹 Manual Cleanup"):
                if self.chat:
                    removed_count = self.chat.perform_cleanup()
                    st.success(f"🧹 Cleaned up {removed_count} messages")
                    st.rerun()

        # Handle manual turn if pending
        if st.session_state.pending_manual_turn:
            st.session_state.pending_manual_turn = False
            self.run_single_turn(auto_mode=False)
            st.rerun()

        st.divider()

        # Display memory-optimized chat interface
        st.subheader("💬 Memory-Optimized Chat")

        # Chat input for manual messages
        if prompt := st.chat_input("Add a message to the conversation (optional)"):
            if self.chat and self.session_metrics:
                message_id = self.chat.add_message(
                    role="user",
                    content=prompt,
                    persona_name="User",
                    model="Human"
                )
                self.session_metrics.add_message("user")
                self.logger.log_message("User", prompt, datetime.now())
                st.rerun()

        # Render chat interface with memory optimization
        if self.chat:
            self.chat.render_chat_interface(enabled_personas)

        # Auto-run conversation if enabled
        if st.session_state.is_running and st.session_state.settings["auto_advance"]:
            st.session_state.auto_run_count += 1

            with st.status(
                f"🔄 Auto-running conversation... (Turn {st.session_state.auto_run_count})",
                expanded=True,
            ) as status:
                st.write("⏸️ Click **Pause** to stop auto-running")
                st.write(f"🎭 {len(enabled_personas)} personas active")

                # Add delay before next turn
                delay = random.uniform(
                    st.session_state.settings["response_delay_min"],
                    st.session_state.settings["response_delay_max"],
                )
                st.write(f"⏳ Waiting {delay:.1f} seconds...")
                time.sleep(delay)

                # Run the next turn automatically
                self.run_single_turn(auto_mode=True, status_container=status)
                status.update(label="Turn completed", state="complete", expanded=False)

            # Continue the auto-run cycle
            st.rerun()

    def run_single_turn(
        self, auto_mode: bool = False, status_container: Any | None = None
    ) -> None:
        """Run a single conversation turn with streaming response.

        Args:
            auto_mode: Whether in automatic mode
            status_container: Optional status container for auto mode
        """
        start_time = time.time()
        with PerformanceTimer("run_single_turn"):
            current_persona = self.get_next_speaker()
            if not current_persona:
                st.error("No enabled personas available")
                return

            # Generate prompt based on conversation history
            if not self.chat:
                st.error("Chat system not initialized")
                return

            # Get recent messages for context
            recent_messages = []
            if hasattr(self.chat, 'storage') and hasattr(self.chat.storage, 'get_messages'):
                recent_messages = self.chat.storage.get_messages(limit=st.session_state.settings["context_messages"])

            if not recent_messages:
                prompt = "Please introduce yourself and share whatever is on your mind."
            else:
                context = "=== CONVERSATION HISTORY ===\n"
                for msg in recent_messages:
                    if hasattr(msg, 'timestamp'):
                        timestamp_str = msg.timestamp.strftime("%H:%M:%S")
                    else:
                        timestamp_str = datetime.now().strftime("%H:%M:%S")

                    if msg.role == "user":
                        context += f"[{timestamp_str}] User: {msg.content}\n"
                    else:
                        context += f"[{timestamp_str}] {msg.persona_name}: {msg.content}\n"

                context += "=== END HISTORY ===\n"

                enabled_personas = [p for p in st.session_state.personas if p.enabled]
                other_names = [p.name for p in enabled_personas if p.name != current_persona.name]

                prompt = f"""{context}

You are {current_persona.name}. The conversation above shows the complete recent history. You can see all messages from other personas: {', '.join(other_names) if other_names else 'none currently'}.

Please respond naturally to continue the conversation. You can:
- Build on what others have said
- Ask questions or introduce new topics
- Use @mentions to directly address specific personas (e.g., @{other_names[0] if other_names else 'PersonaName'})
- React to any part of the conversation history

Your response should be conversational and engaging."""

            # Get avatar for the current persona
            avatar = get_persona_avatar(current_persona)

            # Display the generating message with streaming
            with st.chat_message("assistant", avatar=avatar):
                # Show persona header
                render_persona_header(current_persona)

                # Get streaming response using better event loop management
                thinking_content = ""
                response_content = ""
                task = None

                try:
                    # Try using asyncio.run first
                    connected = asyncio.run(self._process_stream_response(
                        current_persona,
                        prompt,
                        auto_mode,
                        status_container,
                    ))
                    thinking_content, response_content = connected
                except RuntimeError:
                    # Handle "Event loop is closed" gracefully
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    async def process_stream() -> tuple[str, str]:
                        nonlocal thinking_content, response_content
                        thinking_placeholder = None
                        thinking_stream_placeholder = None
                        response_placeholder = None

                        try:
                            async for chunk in self.get_ai_response_stream(current_persona, prompt):
                                if chunk["type"] == "error":
                                    if thinking_placeholder:
                                        thinking_placeholder.empty()
                                    st.error(chunk["content"])
                                    return thinking_content, response_content

                                elif chunk["type"] == "info":
                                    if auto_mode and status_container:
                                        with status_container:
                                            st.info(chunk["content"])
                                    else:
                                        st.info(chunk["content"])

                                elif chunk["type"] == "thinking":
                                    thinking_content += chunk["content"]

                                    if auto_mode and status_container:
                                        if thinking_stream_placeholder is None:
                                            with status_container:
                                                st.write("🧠 **AI is thinking...**")
                                                thinking_stream_placeholder = st.empty()

                                        with thinking_stream_placeholder:
                                            st.text(f"💭 {thinking_content}")

                                    elif not auto_mode:
                                        if not thinking_placeholder:
                                            st.write("🧠 **AI is thinking...**")
                                            thinking_placeholder = st.empty()

                                        with thinking_placeholder:
                                            st.text(f"💭 {thinking_content}")

                                elif chunk["type"] == "response":
                                    response_content += chunk["content"]

                                    if response_placeholder is None:
                                        if not auto_mode:
                                            st.write("💬 **AI is responding...**")
                                        response_placeholder = st.empty()

                                    response_placeholder.write(response_content)

                        except asyncio.CancelledError:
                            if auto_mode and status_container:
                                with status_container:
                                    st.info("🛑 Response cancelled")
                            else:
                                st.info("🛑 Response cancelled")
                            return thinking_content, response_content
                        except Exception as e:
                            st.error(f"Stream processing error: {str(e)}")
                            return thinking_content, response_content

                        return thinking_content, response_content

                    try:
                        task = loop.create_task(process_stream())
                        thinking_content, response_content = loop.run_until_complete(task)
                    except KeyboardInterrupt:
                        if task and not task.done():
                            task.cancel()
                            try:
                                loop.run_until_complete(task)
                            except asyncio.CancelledError:
                                pass
                    except Exception as e:
                        st.error(f"Processing error: {str(e)}")
                    finally:
                        if task and not task.done():
                            task.cancel()
                            try:
                                loop.run_until_complete(task)
                            except asyncio.CancelledError:
                                pass

                        try:
                            loop.run_until_complete(asyncio.sleep(0.1))
                        except Exception:
                            pass

                        try:
                            loop.close()
                        except RuntimeError:
                            pass

                # Show timestamp and model
                timestamp = datetime.now()
                st.caption(f"🕒 {timestamp.strftime('%H:%M:%S')} • 🤖 {current_persona.model}")

            # Add response to conversation history using memory-optimized system
            final_response = response_content.strip()
            if final_response and not final_response.startswith("Error") and self.chat:
                response_time = time.time() - start_time
                self.chat.add_message(
                    role="assistant",
                    content=final_response,
                    persona_name=current_persona.name,
                    model=current_persona.model,
                    thinking=thinking_content,
                    metadata={"response_time": response_time}
                )

                if self.session_metrics:
                    self.session_metrics.add_message("assistant", response_time)

                self.logger.log_message(current_persona.name, final_response, timestamp)

            # Only rerun if not in auto mode
            if not auto_mode:
                st.rerun()

    async def _process_stream_response(
        self,
        persona: AIPersona,
        prompt: str,
        auto_mode: bool,
        status_container: Any | None,
    ) -> tuple[str, str]:
        """Process streaming response asynchronously.

        Args:
            persona: Persona to get response from
            prompt: Prompt to send
            auto_mode: Whether in auto mode
            status_container: Optional status container

        Returns:
            Tuple of (thinking_content, response_content)
        """
        thinking_content = ""
        response_content = ""
        thinking_placeholder = None
        thinking_stream_placeholder = None
        response_placeholder = None

        try:
            async for chunk in self.get_ai_response_stream(persona, prompt):
                if chunk["type"] == "error":
                    if thinking_placeholder:
                        thinking_placeholder.empty()
                    st.error(chunk["content"])
                    return thinking_content, response_content

                elif chunk["type"] == "info":
                    if auto_mode and status_container:
                        with status_container:
                            st.info(chunk["content"])
                    else:
                        st.info(chunk["content"])

                elif chunk["type"] == "thinking":
                    thinking_content += chunk["content"]

                    if auto_mode and status_container:
                        if thinking_stream_placeholder is None:
                            with status_container:
                                st.write("🧠 **AI is thinking...**")
                                thinking_stream_placeholder = st.empty()

                        with thinking_stream_placeholder:
                            st.text(f"💭 {thinking_content}")

                    elif not auto_mode:
                        if not thinking_placeholder:
                            st.write("🧠 **AI is thinking...**")
                            thinking_placeholder = st.empty()

                        with thinking_placeholder:
                            st.text(f"💭 {thinking_content}")

                elif chunk["type"] == "response":
                    response_content += chunk["content"]

                    if response_placeholder is None:
                        if not auto_mode:
                            st.write("💬 **AI is responding...**")
                        response_placeholder = st.empty()

                    response_placeholder.write(response_content)

        except asyncio.CancelledError:
            if auto_mode and status_container:
                with status_container:
                    st.info("🛑 Response cancelled")
            else:
                st.info("🛑 Response cancelled")
            return thinking_content, response_content
        except Exception as e:
            st.error(f"Stream processing error: {str(e)}")
            return thinking_content, response_content

        return thinking_content, response_content

    def memory_settings_ui(self) -> None:
        """UI for memory management settings."""
        st.header("🧠 Memory Management Settings")

        with st.form("memory_settings_form"):
            st.subheader("Storage Configuration")

            col1, col2 = st.columns(2)

            with col1:
                max_memory_messages = st.number_input(
                    "Messages in Memory",
                    min_value=100,
                    max_value=2000,
                    value=st.session_state.memory_config.max_messages_memory,
                    help="Maximum number of messages to keep in RAM"
                )

                cleanup_threshold = st.number_input(
                    "Cleanup Threshold",
                    min_value=500,
                    max_value=5000,
                    value=st.session_state.memory_config.cleanup_threshold,
                    help="Total message count that triggers automatic cleanup"
                )

                messages_per_page = st.number_input(
                    "Messages per Page",
                    min_value=10,
                    max_value=200,
                    value=st.session_state.memory_config.messages_per_page,
                    help="Number of messages to display per page"
                )

            with col2:
                auto_cleanup = st.checkbox(
                    "Automatic Cleanup",
                    value=st.session_state.memory_config.auto_cleanup,
                    help="Automatically cleanup old messages when threshold is reached"
                )

                archive_enabled = st.checkbox(
                    "Message Archiving",
                    value=st.session_state.memory_config.archive_enabled,
                    help="Archive old messages to disk instead of deleting them"
                )

                memory_threshold_mb = st.number_input(
                    "Memory Warning Threshold (MB)",
                    min_value=100.0,
                    max_value=2000.0,
                    value=st.session_state.memory_config.memory_threshold_mb,
                    step=50.0,
                    help="Show warning when memory usage exceeds this amount"
                )

            monitoring_enabled = st.checkbox(
                "Memory Monitoring",
                value=st.session_state.memory_config.monitoring_enabled,
                help="Enable continuous memory usage monitoring"
            )

            if st.form_submit_button("💾 Save Memory Settings"):
                # Update configuration
                st.session_state.memory_config = create_memory_config(
                    max_messages_memory=max_memory_messages,
                    cleanup_threshold=cleanup_threshold,
                    messages_per_page=messages_per_page,
                    auto_cleanup=auto_cleanup,
                    archive_enabled=archive_enabled,
                    memory_threshold_mb=memory_threshold_mb,
                    monitoring_enabled=monitoring_enabled
                )

                # Recreate chat system with new settings
                from src.ui.memory_optimized_chat import create_memory_optimized_chat
                st.session_state.optimized_chat = create_memory_optimized_chat(
                    strategy="hybrid",
                    messages_per_page=messages_per_page,
                    cleanup_threshold=cleanup_threshold,
                    auto_cleanup=auto_cleanup
                )
                self.chat = st.session_state.optimized_chat

                st.success("Memory settings saved! Chat system updated.")
                st.rerun()

        # Memory management actions
        st.subheader("🛠️ Memory Management Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🧹 Perform Cleanup", type="secondary"):
                if self.chat:
                    removed_count = self.chat.perform_cleanup()
                    st.success(f"🧹 Removed {removed_count} old messages")
                    st.rerun()

        with col2:
            if st.button("🗑️ Clear All Messages", type="secondary"):
                if self.chat:
                    self.chat.clear_all_messages()
                    st.success("🗑️ All messages cleared!")
                    st.rerun()

        with col3:
            if st.button("📊 View Memory Stats", type="secondary"):
                if self.chat:
                    stats = self.chat.get_stats()
                    st.json({
                        "total_messages": stats.total_messages,
                        "archived_messages": stats.archived_messages,
                        "memory_usage_mb": stats.memory_usage_mb,
                        "cpu_usage_percent": stats.cpu_usage_percent,
                        "last_cleanup": stats.last_cleanup.isoformat() if stats.last_cleanup else None,
                        "cleanup_count": stats.cleanup_count
                    })

        # Session statistics
        if self.session_metrics:
            st.subheader("📈 Session Statistics")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Messages", self.session_metrics.message_count)

            with col2:
                st.metric("User Messages", self.session_metrics.user_message_count)

            with col3:
                st.metric("AI Messages", self.session_metrics.assistant_message_count)

            with col4:
                avg_time = self.session_metrics.average_response_time
                st.metric("Avg Response Time", f"{avg_time:.2f}s")

    def export_ui(self) -> None:
        """UI for exporting conversations."""
        st.header("📁 Export & Logs")

        if self.chat:
            # Export current session
            messages = self.chat.export_messages()

            if messages:
                export_data = {
                    "session_date": datetime.now().isoformat(),
                    "personas": [asdict(p) for p in st.session_state.personas],
                    "conversation": messages,
                    "memory_config": st.session_state.memory_config.to_dict(),
                    "session_metrics": self.session_metrics.to_dict() if self.session_metrics else None,
                }

                json_str = json.dumps(export_data, indent=2, default=str)
                st.download_button(
                    label="📥 Download Session JSON",
                    data=json_str,
                    file_name=f"streamlit_backroom_optimized_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                )

                # Show conversation preview
                st.subheader("Session Preview")
                st.info(
                    f"💬 {len(messages)} messages from {len(st.session_state.personas)} personas"
                )

                # Show statistics
                persona_stats: dict[str, int] = {}
                for message in messages:
                    if message["role"] == "assistant":
                        persona_name = message["persona_name"]
                        persona_stats[persona_name] = persona_stats.get(persona_name, 0) + 1

                if persona_stats:
                    st.write("**Message count by persona:**")
                    for persona_name, count in persona_stats.items():
                        st.write(f"• {persona_name}: {count} messages")

                # Memory statistics
                if self.chat:
                    stats = self.chat.get_stats()
                    st.subheader("📊 Memory Statistics")
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Total Messages", stats.total_messages)

                    with col2:
                        st.metric("Archived Messages", stats.archived_messages)

                    with col3:
                        st.metric("Memory Usage", f"{stats.memory_usage_mb:.1f} MB")

                    with col4:
                        st.metric("Cleanups", stats.cleanup_count)

            else:
                st.info("No conversation to export. Start chatting to generate exportable content!")
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
                pass
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

            # Display memory-optimized stats
            if self.chat:
                stats = self.chat.get_stats()
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Messages", stats.total_messages)
                with col2:
                    st.metric("Memory (MB)", f"{stats.memory_usage_mb:.1f}")

                # Memory usage warning
                if stats.memory_usage_mb > 400:
                    st.warning(f"⚠️ High memory usage: {stats.memory_usage_mb:.1f} MB")
                if stats.memory_usage_mb > 600:
                    st.error(f"🚨 Critical memory usage: {stats.memory_usage_mb:.1f} MB")

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

            # Memory management quick actions
            st.divider()
            st.subheader("🧠 Memory Management")

            if self.chat:
                if st.button("🧹 Quick Cleanup", type="secondary"):
                    removed_count = self.chat.perform_cleanup()
                    st.success(f"Removed {removed_count} messages")
                    st.rerun()

                stats = self.chat.get_stats()
                st.caption(f"Archived: {stats.archived_messages}")
                st.caption(f"Cleanups: {stats.cleanup_count}")

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
            st.markdown("• 💾 **Memory-optimized** for long conversations")

            if st.session_state.settings.get("enable_thinking", ENABLE_THINKING):
                st.markdown("• 🧠 **Thinking enabled** - View AI reasoning in expanders")
                st.markdown("• Works best with **deepseek-r1** and compatible models")

    def run(self) -> None:
        """Main Streamlit app interface."""
        # Start memory monitoring
        if self.chat and st.session_state.memory_config.monitoring_enabled:
            self.chat.start_monitoring()

        try:
            self.sidebar_ui()

            # Welcome message for new users
            if not st.session_state.personas:
                st.info(
                    "👋 **Welcome to AI Backroom (Memory Optimized)!** Start by creating your first AI persona in the **Personas** tab, then head to **Conversation** to begin chatting! 🧠 This version includes advanced memory management to prevent crashes during long conversations."
                )

        # Main content with tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["💬 Conversation", "🤖 Personas", "⚙️ Settings", "🧠 Memory", "📁 Export & Logs"]
        )

        with tab1:
            if not st.session_state.personas:
                st.warning(
                    "⚠️ No personas created yet! Please create at least one persona in the **Personas** tab to start conversations."
                )
            else:
                self.conversation_ui()

        with tab2:
            self.persona_management_ui()

        with tab3:
            self.settings_ui()

        with tab4:
            self.memory_settings_ui()

        with tab5:
            self.export_ui()

        finally:
            # Ensure memory monitoring is stopped
            if self.chat:
                self.chat.stop_monitoring()


def main() -> None:
    """Main entry point for Streamlit app."""
    # Set page config FIRST before any other Streamlit commands
    st.set_page_config(
        page_title="AI Backroom (Memory Optimized)",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inject System.css for retro Mac OS aesthetic
    with PerformanceTimer("inject_css", log_threshold=0.05):
        inject_system_css()

    app = StreamlitBackroomApp()
    app.run()


if __name__ == "__main__":
    main()
