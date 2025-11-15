#!/usr/bin/env python3
"""Infinite AI Backroom - Streamlit Web App (Async Pattern Optimized).

Interactive web interface for managing AI personas and running infinite conversations.
This version uses optimized async execution patterns to avoid event loop conflicts.
"""

from __future__ import annotations

import json
import logging
import random
import time
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any, Generator

import streamlit as st

from src.models.persona import AIPersona
from src.services.logger import ConversationLogger
from src.services.ollama_client import OllamaClient  # Use unified client
from src.ui.components import (
    get_persona_avatar,
    highlight_mentions,
    render_persona_header,
    render_persona_list_item,
)
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
from src.utils.streamlit_async import (
    safe_async_call,
    streamlit_singleton_resource,
    safe_stream_wrapper,
    get_streamlit_cached_client,
    handle_streamlit_async_error,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_ollama_client():
    """Get or create a singleton Ollama client for Streamlit."""
    return OllamaClient(base_url=DEFAULT_OLLAMA_URL)


def inject_system_css() -> None:
    """Inject System.css styling into the Streamlit app for retro Mac OS aesthetic."""
    try:
        with open("static/css/system.css", "r") as f:
            system_css = f.read()
    except FileNotFoundError:
        system_css = ""  # Fallback if CSS file doesn't exist

    st.markdown(
        f"""
        <style>
        {system_css}

        /* ===== Streamlit-specific System 7 Overrides ===== */

        /* Main app background - System 7 grid pattern */
        .stApp {{
            font-family: Chicago_12, Chicago, Monaco, monospace !important;
            background: linear-gradient(90deg, #FFFFFF 21px, transparent 1%) center,
                        linear-gradient(#FFFFFF 21px, transparent 1%) center,
                        #dadada;
            background-size: 22px 22px;
        }}

        /* Headers with System 7 styling */
        .stMarkdown h1 {{
            font-family: Chicago_12, Chicago, Monaco, monospace !important;
            font-size: 24px !important;
            font-weight: bold !important;
            color: #000000 !important;
            text-shadow: 1px 1px 0 #ffffff, -1px -1px 0 #000000, 1px -1px 0 #000000, -1px 1px 0 #000000;
        }}

        /* Buttons with System 7 appearance */
        .stButton > button {{
            font-family: Chicago_12, Chicago, Monaco, monospace !important;
            background: #ffffff !important;
            border: 2px outset #c0c0c0 !important;
            border-radius: 0px !important;
            color: #000000 !important;
            font-weight: bold !important;
            padding: 8px 16px !important;
            box-shadow: 2px 2px 4px rgba(0,0,0,0.3) !important;
        }}

        .stButton > button:hover {{
            background: #e0e0e0 !important;
            border: 2px inset #c0c0c0 !important;
        }}

        .stButton > button:active {{
            background: #c0c0c0 !important;
            border: 2px inset #808080 !important;
        }}

        /* Input fields with System 7 styling */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {{
            font-family: Monaco, monospace !important;
            background: #ffffff !important;
            border: 2px inset #c0c0c0 !important;
            border-radius: 0px !important;
            color: #000000 !important;
        }}

        /* Selectboxes and multiselects */
        .stSelectbox > div > div > select,
        .stMultiSelect > div > div > select {{
            font-family: Monaco, monospace !important;
            background: #ffffff !important;
            border: 2px inset #c0c0c0 !important;
            border-radius: 0px !important;
            color: #000000 !important;
        }}

        /* Expander headers */
        .streamlit-expanderHeader {{
            background: #c0c0c0 !important;
            border: 2px outset #ffffff !important;
            border-radius: 0px !important;
            font-family: Chicago_12, Chicago, Monaco, monospace !important;
            font-weight: bold !important;
            color: #000000 !important;
        }}

        /* Sidebar styling */
        .css-1d391kg {{
            background: linear-gradient(90deg, #FFFFFF 21px, transparent 1%) center,
                        linear-gradient(#FFFFFF 21px, transparent 1%) center,
                        #c0c0c0;
            background-size: 22px 22px;
        }}

        /* Success/info/error messages with System 7 styling */
        .stSuccess {{
            background: #c0ffc0 !important;
            border: 2px outset #00ff00 !important;
            border-radius: 0px !important;
            color: #000000 !important;
        }}

        .stInfo {{
            background: #c0c0ff !important;
            border: 2px outset #0000ff !important;
            border-radius: 0px !important;
            color: #000000 !important;
        }}

        .stError {{
            background: #ffc0c0 !important;
            border: 2px outset #ff0000 !important;
            border-radius: 0px !important;
            color: #000000 !important;
        }}

        .stWarning {{
            background: #ffffc0 !important;
            border: 2px outset #ffff00 !important;
            border-radius: 0px !important;
            color: #000000 !important;
        }}

        /* Chat message styling */
        .chat-message {{
            background: #ffffff !important;
            border: 2px solid #c0c0c0 !important;
            border-radius: 0px !important;
            padding: 12px !important;
            margin: 8px 0 !important;
            box-shadow: 2px 2px 4px rgba(0,0,0,0.1) !important;
        }}

        /* Metrics with System 7 styling */
        .metric-container {{
            background: #ffffff !important;
            border: 2px inset #c0c0c0 !important;
            border-radius: 0px !important;
            padding: 8px !important;
        }}

        /* Progress bars */
        .stProgress > div > div > div > div {{
            background: #000080 !important;
        }}

        /* Custom scrollbar for webkit browsers */
        ::-webkit-scrollbar {{
            width: 16px;
        }}

        ::-webkit-scrollbar-track {{
            background: #c0c0c0;
            border: 2px inset #ffffff;
        }}

        ::-webkit-scrollbar-thumb {{
            background: #808080;
            border: 2px outset #c0c0c0;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: #a0a0a0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


class StreamlitBackroomSafeApp:
    """Safe Streamlit app with optimized async patterns."""

    def __init__(self) -> None:
        """Initialize the app with safe patterns."""
        self.logger = ConversationLogger()

    def check_ollama_connection(self) -> bool:
        """Check Ollama connection using safe async execution."""
        try:
            # Use singleton client for better resource management
            client = get_streamlit_cached_client(get_ollama_client, "connection_check")
            connected, models = safe_async_call(client.test_connection())

            if connected:
                st.session_state.available_models = models
                return True
            else:
                st.session_state.available_models = []
                return False

        except Exception as e:
            error_msg = handle_streamlit_async_error(e, "connection check")
            st.error(error_msg)
            st.session_state.available_models = []
            return False

    @safe_stream_wrapper
    async def get_ai_response_stream(self, persona: AIPersona, prompt: str):
        """Get streaming response from AI persona using optimized async patterns.

        Args:
            persona: Persona to get response from
            prompt: Prompt to send

        Yields:
            Response chunks with standardized format
        """
        system_prompt = self.generate_system_prompt(persona)
        enable_thinking = st.session_state.settings.get("enable_thinking", ENABLE_THINKING)
        timeout_seconds = st.session_state.settings.get("response_timeout", DEFAULT_RESPONSE_TIMEOUT)

        # Check if model is known to not support thinking
        if persona.model in st.session_state.non_thinking_models:
            enable_thinking = False

        # Use singleton client for connection pooling
        client = get_streamlit_cached_client(get_ollama_client, "ai_response")

        try:
            async with client as client_instance:
                async for chunk in client_instance.generate_stream(
                    model=persona.model,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    think=enable_thinking,
                    timeout=timeout_seconds
                ):
                    # Track non-thinking models
                    if chunk.get("type") == "info" and "doesn't support thinking" in chunk.get("content", ""):
                        st.session_state.non_thinking_models.add(persona.model)

                    yield chunk

        except Exception as e:
            logger.error(f"AI response stream error: {e}")
            yield {
                "type": "error",
                "content": handle_streamlit_async_error(e, "AI response generation")
            }

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


# The rest of the class would continue with the conversation_ui, persona_management_ui, etc.
# This is a partial file showing the key async pattern optimizations