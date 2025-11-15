#!/usr/bin/env python3
"""Infinite AI Backroom - Streamlit Web App.

Interactive web interface for managing AI personas and running infinite conversations.
This version has been refactored to use modular services and eliminate code duplication.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
import uuid
from collections.abc import Coroutine
from dataclasses import asdict
from datetime import datetime
from typing import Any, TypeVar

import aiohttp
import streamlit as st

from src.models.persona import AIPersona
from src.services.logger import ConversationLogger
from src.ui.components import (
    get_persona_avatar,
    highlight_mentions,
    render_persona_header,
    render_persona_list_item,
)
from src.ui.tutorial import reset_tutorial, show_tutorial
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
    LOGO_IMAGE_PATH,
    MAX_CONTEXT_MESSAGES,
    MAX_HISTORY_MESSAGES,
    MAX_RESPONSE_DELAY,
    MAX_RESPONSE_DELAY_MAX,
    MAX_RESPONSE_TIMEOUT,
    MIN_CONTEXT_MESSAGES,
    MIN_HISTORY_MESSAGES,
    MIN_RESPONSE_DELAY,
    MIN_RESPONSE_DELAY_MAX,
    MIN_RESPONSE_TIMEOUT,
    PRESET_DIVERSE_PERSONAS,
    PRESET_STRUCTURED_PERSONAS,
    ROLE_TEMPLATES,
    SYSTEM_CSS_PATH,
)
from src.utils.session import get_ollama_client
from src.utils.validation import validate_model_name, validate_persona_name

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variable for async functions
T = TypeVar("T")


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """Run async function in Streamlit context.

    Handles Streamlit's event loop quirks by trying asyncio.run() first,
    and falling back to manual event loop creation if needed.

    Args:
        coro: Coroutine to run

    Returns:
        Result of the coroutine
    """
    try:
        return asyncio.run(coro)
    except RuntimeError as e:
        # Handle "Event loop is closed" or "no running event loop" errors
        logger.debug(f"asyncio.run() failed, creating new event loop: {e}")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            try:
                loop.close()
            except Exception as close_error:
                logger.debug(f"Error closing event loop: {close_error}")


def inject_system_css() -> None:
    """Inject System.css styling into the Streamlit app for retro Mac OS aesthetic."""
    try:
        with open(SYSTEM_CSS_PATH) as f:
            system_css = f.read()
    except FileNotFoundError:
        logger.warning(
            f"System CSS file not found at {SYSTEM_CSS_PATH} - using fallback minimal styling"
        )
        # Provide minimal fallback styling if CSS file is missing
        system_css = """
        /* Minimal fallback styling */
        .stApp {
            font-family: monospace !important;
        }
        """
    except PermissionError:
        logger.error(
            f"Permission denied reading {SYSTEM_CSS_PATH} - using fallback minimal styling"
        )
        system_css = ""
    except Exception as e:
        logger.error(f"Error reading {SYSTEM_CSS_PATH}: {e} - using fallback minimal styling")
        system_css = ""

    st.markdown(
        f"""
        <style>
        {system_css}

        /* ===== Streamlit-specific System 7 Overrides ===== */

        /* Main app background - System 7 grid pattern */
        .stApp {{
            font-family: 'Courier New', 'Monaco', 'Menlo', monospace !important;
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
            font-family: 'Courier New', 'Monaco', 'Menlo', monospace !important;
        }}

        /* Headers - Chicago font */
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Courier New', 'Monaco', 'Menlo', monospace !important;
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
    """Main Streamlit application for AI Backroom."""

    def __init__(self) -> None:
        """Initialize the application."""
        self.logger = ConversationLogger()
        self.max_event_loop_retries = 3  # Maximum retries for event loop failures
        self.initialize_session_state()

    def initialize_session_state(self) -> None:
        """Initialize Streamlit session state."""
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
                "max_history": DEFAULT_HISTORY_MESSAGES,
                "response_delay_min": AUTO_RUN_DELAY_MIN,
                "response_delay_max": AUTO_RUN_DELAY_MAX,
                "auto_advance": AUTO_ADVANCE_DEFAULT,
                "context_messages": DEFAULT_CONTEXT_MESSAGES,
                "enable_thinking": ENABLE_THINKING,
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
        if "message_page" not in st.session_state:
            st.session_state.message_page = 0
        if "messages_per_page" not in st.session_state:
            st.session_state.messages_per_page = 50  # Default pagination size

    async def check_ollama_connection(self) -> bool:
        """Check Ollama connection and update available models.

        Uses cached OllamaClient for improved performance.

        Returns:
            True if connection successful
        """
        client = await get_ollama_client(st.session_state, DEFAULT_OLLAMA_URL)
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
            st.session_state.last_speaker_index = (st.session_state.last_speaker_index + 1) % len(
                enabled_personas
            )

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

        # Add role-specific behavior
        if persona.role and persona.role in ROLE_TEMPLATES:
            role_description = ROLE_TEMPLATES[persona.role]
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

        Uses cached OllamaClient for improved performance across multiple requests.

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

        # Use cached client for improved performance
        client = await get_ollama_client(st.session_state, DEFAULT_OLLAMA_URL)
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
                    connected = run_async(self.check_ollama_connection())
                    if connected:
                        st.write(f"✅ Found {len(st.session_state.available_models)} models")
                        for model in st.session_state.available_models:
                            st.write(f"• {model}")
                        status.update(
                            label="Connection successful!", state="complete", expanded=False
                        )
                    else:
                        st.write("❌ Connection failed - Please ensure Ollama is running")
                        st.write("💡 Try: `ollama serve` in your terminal")
                        status.update(label="Connection failed", state="error", expanded=False)
                except Exception as e:
                    logger.error(f"Error checking Ollama connection: {str(e)}")
                    st.error("**❌ Cannot connect to Ollama**")
                    with st.expander("🔧 Troubleshooting Guide", expanded=True):
                        st.markdown("""
                        ### Common Solutions:

                        1. **Ensure Ollama is installed and running**
                           ```bash
                           # Start Ollama server
                           ollama serve
                           ```

                        2. **Verify Ollama is accessible**
                           - Default URL: http://localhost:11434
                           - Check if the service is running: `ps aux | grep ollama`

                        3. **Check if models are installed**
                           ```bash
                           # List installed models
                           ollama list

                           # Install a model if needed
                           ollama pull llama2
                           ```

                        4. **Firewall or network issues**
                           - Ensure port 11434 is not blocked
                           - Try accessing http://localhost:11434 in your browser

                        5. **Check Ollama logs for errors**
                           ```bash
                           # View Ollama logs
                           journalctl -u ollama -f
                           ```

                        **Technical details:** `{str(e)}`
                        """)
                    status.update(label="Connection check failed", state="error", expanded=True)

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
                if not name or not model:
                    st.error("**❌ Missing Required Fields**")
                    with st.expander("📝 What's needed", expanded=True):
                        st.markdown("""
                        ### Required Information

                        To create a persona, you must provide:

                        1. **Persona Name** (required)
                           - Give your AI persona a unique name
                           - Examples: "Socrates", "Einstein", "DataBot"

                        2. **Model** (required)
                           - Select or enter an Ollama model name
                           - Click "🔄 Check Ollama Connection" to see available models
                           - Common models: `llama2`, `mistral`, `deepseek-r1`

                        **Optional fields:**
                        - **Role**: Predefined personality type
                        - **Custom System Prompt**: Additional behavior instructions
                        - **Color**: Visual distinction in chat
                        """)
                else:
                    # Validate persona name
                    name_valid, name_error = validate_persona_name(name)
                    if not name_valid:
                        st.error(f"Invalid persona name: {name_error}")
                    else:
                        # Validate model name
                        model_valid, model_error = validate_model_name(model)
                        if not model_valid:
                            st.error(f"Invalid model name: {model_error}")
                        else:
                            # All validations passed, create persona
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
                min_value=MIN_HISTORY_MESSAGES,
                max_value=MAX_HISTORY_MESSAGES,
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
                min_value=MIN_RESPONSE_TIMEOUT,
                max_value=MAX_RESPONSE_TIMEOUT,
                value=st.session_state.settings["response_timeout"],
                help="Maximum time to wait for AI response before timing out",
            )

            col1, col2 = st.columns(2)
            with col1:
                delay_min = st.number_input(
                    "Min Response Delay (seconds)",
                    min_value=MIN_RESPONSE_DELAY,
                    max_value=MAX_RESPONSE_DELAY,
                    value=st.session_state.settings["response_delay_min"],
                )
            with col2:
                delay_max = st.number_input(
                    "Max Response Delay (seconds)",
                    min_value=MIN_RESPONSE_DELAY_MAX,
                    max_value=MAX_RESPONSE_DELAY_MAX,
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
        """Main conversation interface using native Streamlit chat elements."""
        # Check if we have enabled personas
        enabled_personas = [p for p in st.session_state.personas if p.enabled]
        if not enabled_personas:
            st.warning("⚠️ No enabled personas found. Please add and enable at least one persona.")
            return

        # Create persona lookup dictionary for O(1) access (performance optimization)
        persona_lookup = {p.name: p for p in st.session_state.personas}

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
            # Clear History with confirmation dialog
            clear_confirm_key = "clear_history_confirm"
            if clear_confirm_key not in st.session_state:
                st.session_state[clear_confirm_key] = False

            if not st.session_state[clear_confirm_key]:
                if st.button("🗑️ Clear History", disabled=not st.session_state.messages):
                    if st.session_state.messages:  # Only confirm if there are messages
                        st.session_state[clear_confirm_key] = True
                        st.rerun()
            else:
                # Show confirmation using columns
                st.markdown("⚠️ **Clear all?**")
                confirm_col1, confirm_col2 = st.columns(2)
                with confirm_col1:
                    if st.button("✅ Yes", key="clear_yes", type="primary"):
                        logger.info(
                            f"Clearing conversation history ({len(st.session_state.messages)} messages)"
                        )
                        st.session_state.messages = []
                        st.session_state.total_message_count = 0
                        st.session_state.last_speaker_index = None
                        st.session_state[clear_confirm_key] = False
                        st.success("✅ History cleared!")
                        st.rerun()
                with confirm_col2:
                    if st.button("❌ No", key="clear_no", type="secondary"):
                        st.session_state[clear_confirm_key] = False
                        st.rerun()

        # Handle manual turn if pending
        if st.session_state.pending_manual_turn:
            st.session_state.pending_manual_turn = False
            self.run_single_turn(auto_mode=False)
            st.rerun()

        st.divider()

        # Display conversation using native chat elements
        st.subheader("Chat")

        # Chat input for manual messages
        if prompt := st.chat_input("Add a message to the conversation (optional)"):
            timestamp = datetime.now()
            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": prompt,
                    "timestamp": timestamp,
                    "persona_name": "User",
                    "model": "Human",
                }
            )
            st.session_state.total_message_count += 1
            self.logger.log_message("User", prompt, timestamp)
            st.rerun()

        # Pagination for large conversations
        total_messages = len(st.session_state.messages)
        messages_per_page = st.session_state.messages_per_page
        total_pages = max(1, (total_messages + messages_per_page - 1) // messages_per_page)

        # Reset to last page if current page is out of bounds
        if st.session_state.message_page >= total_pages:
            st.session_state.message_page = max(0, total_pages - 1)

        # Calculate message range for current page
        start_idx = st.session_state.message_page * messages_per_page
        end_idx = min(start_idx + messages_per_page, total_messages)
        messages_to_display = st.session_state.messages[start_idx:end_idx]

        # Pagination controls (shown if more than one page)
        if total_pages > 1:
            st.markdown(f"**Messages {start_idx + 1}-{end_idx} of {total_messages}**")
            pcol1, pcol2, pcol3, pcol4 = st.columns([1, 1, 2, 1])

            with pcol1:
                if st.button("⏮️ First", disabled=st.session_state.message_page == 0):
                    st.session_state.message_page = 0
                    st.rerun()

            with pcol2:
                if st.button("◀️ Prev", disabled=st.session_state.message_page == 0):
                    st.session_state.message_page -= 1
                    st.rerun()

            with pcol3:
                st.markdown(
                    f"<div style='text-align: center; padding: 8px;'>Page {st.session_state.message_page + 1} of {total_pages}</div>",
                    unsafe_allow_html=True
                )

            with pcol4:
                if st.button("Next ▶️", disabled=st.session_state.message_page >= total_pages - 1):
                    st.session_state.message_page += 1
                    st.rerun()

            st.divider()
        elif total_messages > 0:
            st.markdown(f"**{total_messages} message{'s' if total_messages != 1 else ''} total**")

        # Display messages using st.chat_message
        for message in messages_to_display:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
                    st.caption(f"🕒 {message['timestamp'].strftime('%H:%M:%S')}")
            else:
                # Find persona for avatar and role info (O(1) lookup)
                persona = persona_lookup.get(message["persona_name"])
                avatar = get_persona_avatar(persona)

                with st.chat_message("assistant", avatar=avatar):
                    # Show persona name and role with colored background
                    render_persona_header(persona) if persona else st.write(message["persona_name"])

                    # Show thinking if available
                    if (
                        "thinking" in message
                        and message["thinking"]
                        and message["thinking"].strip()
                    ):
                        with st.expander("🧠 AI's Thinking Process", expanded=False):
                            st.code(message["thinking"], language="text", wrap_lines=True)

                    # Show message content with @mention highlighting
                    content = message["content"]
                    content_with_highlights = highlight_mentions(content, enabled_personas)

                    if "@" in content and content != content_with_highlights:
                        st.markdown(content_with_highlights, unsafe_allow_html=True)
                    else:
                        st.write(message["content"])

                    # Show timestamp and model
                    st.caption(
                        f"🕒 {message['timestamp'].strftime('%H:%M:%S')} • 🤖 {message['model']}"
                    )

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

    def run_single_turn(self, auto_mode: bool = False, status_container: Any | None = None) -> None:
        """Run a single conversation turn with streaming response.

        Args:
            auto_mode: Whether in automatic mode
            status_container: Optional status container for auto mode
        """
        current_persona = self.get_next_speaker()
        if not current_persona:
            st.error("**❌ No Active Personas**")
            with st.expander("🔧 Troubleshooting Guide", expanded=True):
                st.markdown("""
                ### No Personas Available for Conversation

                You need at least one enabled persona to start a conversation.

                **How to fix:**
                1. **Create a new persona**
                   - Go to the **Personas** tab
                   - Click "➕ Add Persona"
                   - Fill in name, model, and role
                   - Ensure "Enabled" is checked

                2. **Enable existing personas**
                   - Go to the **Personas** tab
                   - Find your personas in the list
                   - Check the "Enabled" checkbox for at least one persona

                3. **Quick start with presets**
                   - Go to the **Personas** tab
                   - Click "🎭 Add Diverse Conversation Set" or
                   - Click "📋 Add Structured Discussion Set"
                   - This will add multiple pre-configured personas

                4. **Check Ollama connection first**
                   - Click "🔄 Check Ollama Connection" in the Personas tab
                   - Ensure models are available before creating personas
                """)
            return

        # Generate prompt based on conversation history
        if not st.session_state.messages:
            prompt = "Please introduce yourself and share whatever is on your mind."
        else:
            # Get conversation history based on settings
            max_context_messages = min(
                st.session_state.settings["context_messages"], len(st.session_state.messages)
            )
            recent_messages = st.session_state.messages[-max_context_messages:]

            context = "=== CONVERSATION HISTORY ===\n"
            for msg in recent_messages:
                timestamp_str = msg["timestamp"].strftime("%H:%M:%S")
                if msg["role"] == "user":
                    context += f"[{timestamp_str}] User: {msg['content']}\n"
                else:
                    context += f"[{timestamp_str}] {msg['persona_name']}: {msg['content']}\n"

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

            # Get streaming response using standardized async pattern
            thinking_content, response_content = run_async(
                self._process_stream_response(
                    current_persona,
                    prompt,
                    auto_mode,
                    status_container,
                )
            )

            # Show timestamp and model
            timestamp = datetime.now()
            st.caption(f"🕒 {timestamp.strftime('%H:%M:%S')} • 🤖 {current_persona.model}")

        # Add response to conversation history
        final_response = response_content.strip()
        if final_response and not final_response.startswith("Error"):
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": final_response,
                    "timestamp": timestamp,
                    "persona_name": current_persona.name,
                    "model": current_persona.model,
                    "thinking": thinking_content,
                }
            )

            st.session_state.total_message_count += 1
            self.logger.log_message(current_persona.name, final_response, timestamp)

            # Keep history manageable
            max_history = st.session_state.settings["max_history"]
            if len(st.session_state.messages) > max_history:
                st.session_state.messages = st.session_state.messages[-max_history:]

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
            logger.info("AI response generation was cancelled")
            if auto_mode and status_container:
                with status_container:
                    st.info("🛑 Response cancelled")
            else:
                st.info("🛑 Response cancelled")
            return thinking_content, response_content
        except aiohttp.ClientError as e:
            logger.error(f"Network error during stream processing: {str(e)}")
            st.error("**❌ Network Connection Lost**")
            with st.expander("🔧 Troubleshooting Guide", expanded=True):
                st.markdown(f"""
                ### Network Error During AI Response

                The connection to Ollama was lost while generating a response.

                **Quick Fixes:**
                1. **Check if Ollama is still running**
                   ```bash
                   ps aux | grep ollama
                   ```
                   If not running, restart it: `ollama serve`

                2. **Network connectivity**
                   - Ensure your computer hasn't gone to sleep
                   - Check if localhost connectivity is working
                   - Test: Open http://localhost:11434 in your browser

                3. **Resource constraints**
                   - Ollama may have crashed due to insufficient memory
                   - Check system resources: `top` or Activity Monitor
                   - Consider using a smaller model

                4. **Try again**
                   - Click "Next Turn" to retry with the same persona
                   - The error may be temporary

                **Technical details:** `{str(e)}`
                """)
            return thinking_content, response_content
        except TimeoutError as e:
            logger.error(f"Timeout during stream processing: {str(e)}")
            st.error("**❌ Response Timeout**")
            with st.expander("🔧 Troubleshooting Guide", expanded=True):
                st.markdown(f"""
                ### AI Response Took Too Long

                The AI model didn't complete its response within the timeout limit.

                **Solutions:**
                1. **Increase timeout in Settings**
                   - Go to the **Settings** tab
                   - Increase "Response Timeout" (current: {st.session_state.settings.get('response_timeout', DEFAULT_RESPONSE_TIMEOUT)}s)
                   - Recommended: 300-600 seconds for larger models

                2. **Use a smaller/faster model**
                   - Larger models (70B, 34B) take longer to respond
                   - Consider using smaller models (7B, 13B) for faster responses
                   - Examples: `llama2:7b`, `mistral:7b`

                3. **Reduce context messages**
                   - Go to **Settings** tab
                   - Reduce "Context Messages" to send less history
                   - This speeds up processing

                4. **Check system resources**
                   - Model may be running slowly due to insufficient RAM/CPU
                   - Close other applications to free up resources
                   - Check: `top` or Activity Monitor

                5. **Verify Ollama is responsive**
                   - Test with: `ollama run llama2 "hello"`
                   - If slow, restart Ollama: `killall ollama && ollama serve`

                **Current timeout:** {st.session_state.settings.get('response_timeout', DEFAULT_RESPONSE_TIMEOUT)} seconds
                """)
            return thinking_content, response_content
        except Exception as e:
            logger.error(f"Unexpected error during stream processing: {str(e)}")
            st.error("**❌ Unexpected Error**")
            with st.expander("🔧 Troubleshooting Guide", expanded=True):
                st.markdown(f"""
                ### Something Went Wrong

                An unexpected error occurred while processing the AI response.

                **What to try:**
                1. **Try again**
                   - Click "Next Turn" to retry
                   - The error may be temporary

                2. **Check Ollama status**
                   ```bash
                   # Verify Ollama is running
                   ps aux | grep ollama

                   # Test Ollama directly
                   ollama run llama2 "test"
                   ```

                3. **Restart the conversation**
                   - Clear conversation and start fresh
                   - This may resolve state-related issues

                4. **Check logs for details**
                   - Look in the **Export & Logs** tab
                   - Review error details in the application logs

                5. **Report persistent issues**
                   - If this keeps happening, it may be a bug
                   - Note the error details below for reporting

                **Error type:** `{type(e).__name__}`
                **Error details:** `{str(e)}`
                """)
            return thinking_content, response_content

        return thinking_content, response_content

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

            with open(log_file, encoding="utf-8") as f:
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
                st.image(str(LOGO_IMAGE_PATH), use_container_width=True)
            except Exception as e:
                logger.debug(f"Logo image not found or failed to load: {e}")
                st.write("**AI Backroom**")
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
                            connected = run_async(self.check_ollama_connection())
                            if connected:
                                st.success(
                                    f"✅ Connected! Found {len(st.session_state.available_models)} models"
                                )
                                logger.info(
                                    f"Successfully reconnected to Ollama ({len(st.session_state.available_models)} models)"
                                )
                                st.rerun()
                            else:
                                st.error("❌ Still unable to connect to Ollama")
                                st.info("💡 Please ensure Ollama is running: `ollama serve`")
                        except Exception as e:
                            logger.error(f"Error retrying connection: {str(e)}")
                            st.error(f"❌ Connection error: {str(e)}")

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

            if st.session_state.settings.get("enable_thinking", ENABLE_THINKING):
                st.markdown("• 🧠 **Thinking enabled** - View AI reasoning in expanders")
                st.markdown("• Works best with **deepseek-r1** and compatible models")

            # Tutorial control
            st.divider()
            if st.button("📚 Restart Tutorial", key="restart_tutorial_sidebar"):
                reset_tutorial(st.session_state)
                st.success("Tutorial reset! Page will reload.")
                st.rerun()

    def run(self) -> None:
        """Main Streamlit app interface."""
        self.sidebar_ui()

        # Add keyboard shortcuts
        st.markdown("""
        <script>
        document.addEventListener('keydown', function(e) {
            // Press '?' to show keyboard shortcuts help
            if (e.key === '?' && !e.ctrlKey && !e.altKey && !e.metaKey) {
                // Check if we're not in an input field
                if (!e.target.matches('input, textarea')) {
                    alert('⌨️ Keyboard Shortcuts:\\n\\n' +
                          '? - Show this help\\n' +
                          'Ctrl/Cmd + K - Focus chat input\\n' +
                          'Esc - Blur/unfocus current element\\n\\n' +
                          'Note: Use buttons for conversation controls');
                    e.preventDefault();
                }
            }

            // Ctrl/Cmd + K to focus chat input
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                const chatInput = document.querySelector('[data-testid="stChatInput"] input, [data-testid="stChatInput"] textarea');
                if (chatInput) {
                    chatInput.focus();
                    e.preventDefault();
                }
            }

            // Escape to blur current element
            if (e.key === 'Escape') {
                document.activeElement.blur();
            }
        });
        </script>
        """, unsafe_allow_html=True)

        # Show first-run tutorial for new users
        if not st.session_state.get("tutorial_completed", False) and not st.session_state.personas:
            show_tutorial(st.session_state)
            # Don't show main tabs during tutorial
            return

        # Welcome message for users who skipped tutorial
        if not st.session_state.personas and st.session_state.get("tutorial_completed", False):
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
                self.conversation_ui()

        with tab2:
            self.persona_management_ui()

        with tab3:
            self.settings_ui()

        with tab4:
            self.export_ui()


def main() -> None:
    """Main entry point for Streamlit app."""
    # Set page config FIRST before any other Streamlit commands
    st.set_page_config(
        page_title="AI Backroom",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inject System.css for retro Mac OS aesthetic
    inject_system_css()

    app = StreamlitBackroomApp()
    app.run()


# Type imports for async generator
from collections.abc import AsyncGenerator  # noqa: E402, F401

if __name__ == "__main__":
    main()
