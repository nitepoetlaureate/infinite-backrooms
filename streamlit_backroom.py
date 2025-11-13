#!/usr/bin/env python3
"""
Infinite AI Backroom - Streamlit Web App
Interactive web interface for managing AI personas and running infinite conversations
"""

import asyncio
import html
import json
import logging
import random
import re
import time
import uuid
import warnings
from collections.abc import AsyncGenerator
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import aiohttp
import streamlit as st

from config import config

# Constants
DEFAULT_PERSONA_COLOR = "#1f77b4"
THINKING_TAG_PATTERN = r'<think>.*?</think>'
WHITESPACE_PATTERN = r'\s+'
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
DATETIME_FORMAT = f"{DATE_FORMAT} {TIME_FORMAT}"
ASYNC_CLEANUP_DELAY = 0.1  # seconds
TCP_CONNECTOR_LIMIT = 1  # connections per request

# Suppress async cleanup warnings
warnings.filterwarnings("ignore", message="Task was destroyed but it is pending!")
warnings.filterwarnings("ignore", message="Unclosed client session")
warnings.filterwarnings("ignore", message="Event loop is closed")
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*Event loop is closed.*")
warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed.*client.*session.*")

# Also suppress aiohttp specific warnings
logging.getLogger('aiohttp.client').setLevel(logging.ERROR)


@dataclass
class AIPersona:
    """Represents an AI instance with detailed configuration"""
    id: str
    name: str
    model: str
    role: str = ""  # Optional role for the persona
    system_prompt: str = ""
    color: str = DEFAULT_PERSONA_COLOR
    enabled: bool = True


def sanitize_html(text: str) -> str:
    """Sanitize text to prevent XSS attacks by escaping HTML special characters"""
    return html.escape(text)


# Role emoji mapping - used consistently throughout the application
ROLE_EMOJI_MAP = {
    "Moderator": "🎯",
    "Note-Taker": "📝",
    "Philosopher": "🤔",
    "Scientist": "🔬",
    "Creative Writer": "✍️",
    "Debate Enthusiast": "⚖️",
    "Optimist": "😊",
    "Skeptic": "🤨",
    "Historian": "📚",
    "Futurist": "🚀",
    "Minimalist": "⚪️",
    "Explorer": "🧭",
    "Mentor": "👨‍🏫",
    "Comedian": "😄",
    "Analyst": "📊",
    "Dreamer": "💭",
    "Pragmatist": "⚙️"
}


class ConversationLogger:
    """Handles logging conversations to daily TXT files"""

    def __init__(self, log_dir: str | None = None):
        if log_dir is None:
            log_dir = config.logging.log_dir
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_file_prefix = config.logging.log_file_prefix

    def get_daily_log_file(self) -> Path:
        """Get the log file for today"""
        today = datetime.now().strftime(DATE_FORMAT)
        return self.log_dir / f"{self.log_file_prefix}_{today}.txt"

    def clean_message(self, message: str) -> str:
        """Remove thinking tags and content from message"""
        # Remove <think>...</think> blocks (including nested ones)
        # Use greedy matching to handle nested tags properly
        cleaned = message
        # Keep removing until no more thinking tags exist
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        while ('<think>' in cleaned.lower() or '</think>' in cleaned.lower()) and iteration < max_iterations:
            # Use greedy .* to match from first <think> to last </think>
            before_len = len(cleaned)
            cleaned = re.sub(r'<think>.*</think>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
            # If nothing changed, try removing orphaned tags
            if len(cleaned) == before_len:
                cleaned = re.sub(r'</?think>', '', cleaned, flags=re.IGNORECASE)
            iteration += 1
        # Clean up any extra whitespace
        cleaned = re.sub(WHITESPACE_PATTERN, ' ', cleaned).strip()
        return cleaned

    def log_message(self, persona: str, message: str, timestamp: datetime | None = None) -> None:
        """Log a message to today's file"""
        if timestamp is None:
            timestamp = datetime.now()

        # Clean the message before logging
        cleaned_message = self.clean_message(message)

        # Only log if there's content after cleaning
        if cleaned_message:
            log_file = self.get_daily_log_file()
            try:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"[{timestamp.strftime(TIME_FORMAT)}] {persona}$ {cleaned_message}\n")
            except (OSError, PermissionError) as e:
                # Log to stderr instead of failing silently
                logging.warning(f"Failed to write to log file {log_file}: {e}")


class OllamaClient:
    """Client for interacting with Ollama API"""

    def __init__(self, base_url: str | None = None):
        if base_url is None:
            base_url = config.ollama.base_url
        self.base_url = base_url
        self.connection_timeout = config.ollama.connection_timeout
        self.response_timeout = config.ollama.response_timeout

    async def test_connection(self) -> tuple[bool, list[str]]:
        """Test if Ollama API is accessible and return available models"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=self.connection_timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        models = [model["name"] for model in result.get("models", [])]
                        return True, models
                    else:
                        return False, []
        except (TimeoutError, aiohttp.ClientError, ConnectionError, OSError) as e:
            st.error(f"Failed to connect to Ollama at {self.base_url}: {e}")
            logging.error(f"Ollama connection failed: {type(e).__name__}: {e}")
            return False, []

    async def generate_stream(self, model: str, prompt: str, system: str = None, think: bool = True, timeout: int = 300) -> AsyncGenerator[dict[str, str], None]:
        """Generate streaming response from Ollama model with optional thinking"""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "think": think
        }

        if system and system.strip():
            payload["system"] = system.strip()

        session = None
        try:
            # Create session with explicit connector settings for better cleanup
            connector = aiohttp.TCPConnector(
                limit=TCP_CONNECTOR_LIMIT,
                force_close=True,  # Force close connections
                enable_cleanup_closed=True  # Enable cleanup of closed connections
            )
            session = aiohttp.ClientSession(connector=connector)

            try:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status == 200:
                        try:
                            async for line in response.content:
                                if line:
                                    try:
                                        chunk = json.loads(line.decode('utf-8'))

                                        # Yield thinking content if available
                                        if 'thinking' in chunk and chunk['thinking']:
                                            yield {"type": "thinking", "content": chunk['thinking']}

                                        # Yield response content if available
                                        if 'response' in chunk and chunk['response']:
                                            yield {"type": "response", "content": chunk['response']}

                                        if chunk.get('done', False):
                                            break
                                    except json.JSONDecodeError:
                                        continue
                        except asyncio.CancelledError:
                            # Handle graceful cancellation (e.g., when user pauses)
                            yield {"type": "info", "content": "Response cancelled by user"}
                            return
                    elif response.status == 400 and think:
                        # Check if the error is about thinking not being supported
                        error_text = await response.text()
                        if "does not support thinking" in error_text:
                            # Add model to non-thinking cache for future requests
                            import streamlit as st
                            st.session_state.non_thinking_models.add(model)

                            # Retry without thinking
                            yield {"type": "info", "content": f"Model {model} doesn't support thinking - switching to standard mode for future requests"}

                            # Recursive call without thinking - but first close this session
                            if session and not session.closed:
                                await session.close()
                                session = None

                            async for chunk in self.generate_stream(model, prompt, system, think=False, timeout=timeout):
                                yield chunk
                            return
                        else:
                            yield {"type": "error", "content": f"Error {response.status}: {error_text}"}
                    else:
                        error_text = await response.text()
                        yield {"type": "error", "content": f"Error {response.status}: {error_text}"}
            except asyncio.CancelledError:
                # Handle cancellation at the request level
                yield {"type": "info", "content": "Request cancelled"}
                return
            except TimeoutError:
                yield {"type": "error", "content": "Error: Request timeout"}
            except (aiohttp.ClientError, ConnectionError, RuntimeError) as e:
                logging.error(f"Streaming error for model {model}: {type(e).__name__}: {e}")
                yield {"type": "error", "content": f"Error: {str(e)}"}
        except asyncio.CancelledError:
            # Handle cancellation at the session level - don't yield anything, just return
            return
        except (aiohttp.ClientError, ConnectionError, OSError) as e:
            logging.error(f"Session-level connection error for model {model}: {type(e).__name__}: {e}")
            yield {"type": "error", "content": f"Connection error: {str(e)}"}
        finally:
            # Ensure session is always closed
            if session and not session.closed:
                try:
                    await session.close()
                except (RuntimeError, aiohttp.ClientError) as e:
                    # Log but don't fail on cleanup errors
                    logging.debug(f"Session cleanup error (non-critical): {type(e).__name__}: {e}")


class StreamlitBackroomApp:
    """Main Streamlit application for AI Backroom"""

    def __init__(self) -> None:
        self.logger = ConversationLogger()
        self.ollama = OllamaClient()
        self.role_templates = self.get_role_templates()
        self.initialize_session_state()

    def get_role_templates(self) -> dict[str, str]:
        """Get predefined role templates"""
        return {
            "": "No specific role",
            "Moderator": "A skilled conversation facilitator who guides discussions, asks thoughtful follow-up questions, introduces new topics when needed, and helps ensure all voices are heard. Keeps conversations engaging and on-track.",
            "Note-Taker": "A diligent observer who periodically summarizes key points, captures important insights, identifies emerging themes, and helps track the evolution of ideas throughout the conversation.",
            "Philosopher": "A thoughtful philosopher who loves exploring deep questions about existence, consciousness, reality, and the nature of intelligence.",
            "Scientist": "A curious scientist who approaches topics with empirical thinking, enjoys discussing research, theories, and the scientific method.",
            "Creative Writer": "An imaginative writer who loves storytelling, wordplay, poetry, and exploring the creative aspects of language and ideas.",
            "Debate Enthusiast": "Someone who enjoys intellectual debates, presenting different perspectives, and challenging ideas constructively.",
            "Optimist": "A positive, hopeful persona who tends to see the bright side of things and encourages others.",
            "Skeptic": "A critical thinker who questions assumptions, asks for evidence, and approaches claims with healthy skepticism.",
            "Historian": "Someone fascinated by history, patterns in human behavior, and how the past informs the present.",
            "Futurist": "Forward-thinking persona interested in emerging technologies, future possibilities, and societal evolution.",
            "Minimalist": "Values simplicity, clarity, and getting to the essence of ideas without unnecessary complexity.",
            "Explorer": "Adventurous and curious about discovering new ideas, connections, and unexplored topics.",
            "Mentor": "Supportive and encouraging, enjoys helping others learn and grow through thoughtful guidance.",
            "Comedian": "Brings humor and levity to conversations while still engaging meaningfully with topics.",
            "Analyst": "Systematic thinker who breaks down complex topics into components and enjoys detailed analysis.",
            "Dreamer": "Imaginative and idealistic, often thinking about possibilities and 'what if' scenarios.",
            "Pragmatist": "Practical and results-oriented, focuses on what works and real-world applications."
        }

    def initialize_session_state(self) -> None:
        """Initialize Streamlit session state"""
        if 'personas' not in st.session_state:
            st.session_state.personas = []
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'is_running' not in st.session_state:
            st.session_state.is_running = False
        if 'available_models' not in st.session_state:
            st.session_state.available_models = []
        if 'last_speaker_index' not in st.session_state:
            st.session_state.last_speaker_index = None
        if 'settings' not in st.session_state:
            st.session_state.settings = {
                'max_history': config.conversation.max_history,
                'response_delay_min': config.conversation.response_delay_min,
                'response_delay_max': config.conversation.response_delay_max,
                'auto_advance': config.conversation.auto_advance,
                'context_messages': config.conversation.context_messages,
                'enable_thinking': config.conversation.enable_thinking,
                'response_timeout': config.ollama.response_timeout
            }
        if 'auto_run_count' not in st.session_state:
            st.session_state.auto_run_count = 0
        if 'total_message_count' not in st.session_state:
            st.session_state.total_message_count = 0
        if 'non_thinking_models' not in st.session_state:
            st.session_state.non_thinking_models = set()
        if 'pending_manual_turn' not in st.session_state:
            st.session_state.pending_manual_turn = False

    async def check_ollama_connection(self) -> bool:
        """Check Ollama connection and update available models"""
        connected, models = await self.ollama.test_connection()
        st.session_state.available_models = models
        return connected

    def get_persona_avatar(self, persona: AIPersona) -> str:
        """Get avatar for persona based on role or use default"""
        # Use role emoji map for avatars
        if persona.role in ROLE_EMOJI_MAP:
            return ROLE_EMOJI_MAP[persona.role]
        else:
            # Use robot emoji as fallback for personas without defined roles
            return "🤖"

    def _create_persona_display_html(self, persona_name: str, persona_color: str, role: str | None = None) -> str:
        """Create styled HTML for persona display with optional role

        Args:
            persona_name: Name of the persona (will be sanitized)
            persona_color: Background color for the name badge
            role: Optional role to display (will be sanitized)

        Returns:
            HTML string for persona display
        """
        safe_name = sanitize_html(persona_name)
        name_badge = f'<span style="background-color: {persona_color}; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold;">{safe_name}</span>'

        if role:
            role_emoji = ROLE_EMOJI_MAP.get(role, "")
            safe_role = sanitize_html(role)
            return f"{name_badge} {role_emoji} _{safe_role}_"
        return name_badge

    def _highlight_mentions(self, content: str, enabled_personas: list[AIPersona]) -> tuple[str, bool]:
        """Highlight @mentions in content with persona colors

        Args:
            content: Message content to process
            enabled_personas: List of enabled personas to check for mentions

        Returns:
            Tuple of (processed_content, has_mentions)
        """
        has_mentions = False
        for persona in enabled_personas:
            mention_pattern = f"@{persona.name}"
            if mention_pattern in content:
                has_mentions = True
                safe_mention = sanitize_html(f"@{persona.name}")
                highlighted = f'<span style="background-color: {persona.color}; color: white; padding: 1px 4px; border-radius: 3px; font-weight: bold;">{safe_mention}</span>'
                content = sanitize_html(content).replace(sanitize_html(mention_pattern), highlighted)
        return content, has_mentions


    def _render_ollama_connection_check(self) -> None:
        """Render Ollama connection check button and status display"""
        if st.button("🔄 Check Ollama Connection"):
            with st.status("Checking Ollama connection...", expanded=True) as status:
                st.write("Connecting to Ollama API...")
                connected = self._run_async_in_new_loop(self.check_ollama_connection())
                if connected:
                    st.write(f"✅ Found {len(st.session_state.available_models)} models")
                    for model in st.session_state.available_models:
                        st.write(f"• {model}")
                    status.update(label="Connection successful!", state="complete", expanded=False)
                else:
                    st.write("❌ Connection failed")
                    status.update(label="Connection failed", state="error", expanded=False)

    def _render_persona_delete_controls(self, persona: AIPersona, col: Any) -> None:
        """Render delete button with confirmation dialog for a persona

        Args:
            persona: The persona to manage deletion for
            col: The Streamlit column object to render controls in
        """
        delete_key = f"delete_confirm_{persona.id}"
        if delete_key not in st.session_state:
            st.session_state[delete_key] = False

        if not st.session_state[delete_key]:
            if col.button("🗑️ Delete", key=f"delete_{persona.id}", type="secondary", help="Delete this persona"):
                st.session_state[delete_key] = True
                st.rerun()
        else:
            col.warning(f"Delete {persona.name}?")
            col_yes, col_no = col.columns(2)
            with col_yes:
                if st.button("✅ Yes", key=f"delete_yes_{persona.id}", type="primary"):
                    st.session_state.personas = [p for p in st.session_state.personas if p.id != persona.id]
                    st.session_state[delete_key] = False
                    st.success(f"Deleted persona: {persona.name}")
                    st.rerun()
            with col_no:
                if st.button("❌ No", key=f"delete_no_{persona.id}", type="secondary"):
                    st.session_state[delete_key] = False
                    st.rerun()

    def _render_persona_details(self, persona: AIPersona, index: int) -> None:
        """Render detailed view of a single persona in an expander

        Args:
            persona: The persona to display
            index: Index in the persona list (used for unique keys)
        """
        avatar = self.get_persona_avatar(persona)
        role_display = f" - {persona.role}" if persona.role else ""

        with st.expander(f"{avatar} {persona.name} ({persona.model}){role_display}", expanded=False):
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                st.write(f"**Model:** {persona.model}")
                st.write(f"**Role:** {persona.role or 'No specific role'}")
                st.write(f"**Enabled:** {'✅' if persona.enabled else '❌'}")
                st.color_picker("Color", value=persona.color, key=f"color_{persona.id}", disabled=True)

            with col2:
                if persona.role and persona.role in self.role_templates:
                    st.text_area("Role Description", value=self.role_templates[persona.role],
                               key=f"role_desc_{persona.id}", disabled=True, height=100)
                st.text_area("Custom System Prompt", value=persona.system_prompt,
                           key=f"prompt_{persona.id}", disabled=True, height=100)

            with col3:
                self._render_persona_delete_controls(persona, col3)

                # Only show enabled checkbox if not in delete confirmation mode
                delete_key = f"delete_confirm_{persona.id}"
                if not st.session_state.get(delete_key, False):
                    enabled_new = st.checkbox("Enabled", value=persona.enabled, key=f"enabled_{persona.id}")
                    if enabled_new != persona.enabled:
                        persona.enabled = enabled_new
                        st.rerun()

    def _render_persona_list(self) -> None:
        """Display list of all existing personas"""
        if st.session_state.personas:
            st.subheader("Current Personas")
            for i, persona in enumerate(st.session_state.personas):
                self._render_persona_details(persona, i)

    def _render_add_persona_form(self) -> None:
        """Render form for creating a new persona with full configuration"""
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
                role_options = list(self.role_templates.keys())
                selected_role = st.selectbox("Predefined Role", role_options,
                                            format_func=lambda x: x if x else "No specific role")

                # Option for custom role
                use_custom_role = st.checkbox("Use custom role instead")
                if use_custom_role:
                    custom_role = st.text_input("Custom Role Name",
                                               placeholder="e.g., Tech Enthusiast, Poet, etc.")
                    role = custom_role if custom_role else ""
                else:
                    role = selected_role

            with role_col2:
                if role and role in self.role_templates:
                    st.text_area("Role Description", value=self.role_templates[role],
                               disabled=True, height=100)
                elif use_custom_role:
                    st.info("💡 Define a custom role to give your persona unique characteristics and conversation style.")

            system_prompt = st.text_area(
                "Additional System Prompt (Optional)",
                placeholder="Any additional custom instructions for this persona...",
                height=100,
                help="This will be combined with the role-based prompt if a role is selected."
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
                        enabled=enabled
                    )
                    st.session_state.personas.append(new_persona)
                    role_text = f" as {role}" if role else ""
                    st.success(f"Added persona: {name}{role_text}")
                    st.rerun()
                else:
                    st.error("Please provide both name and model")

    def _add_preset_personas(self, preset_list: list[dict[str, str]], success_message: str) -> None:
        """Add multiple personas from a preset configuration

        Args:
            preset_list: List of dicts with 'name', 'role', and 'color' keys
            success_message: Message to display upon successful addition
        """
        if st.session_state.available_models:
            models = st.session_state.available_models
            added_count = 0

            for i, preset in enumerate(preset_list):
                if len(models) > 0:
                    model = models[i % len(models)]  # Rotate through available models
                    new_persona = AIPersona(
                        id=str(uuid.uuid4()),
                        name=preset["name"],
                        model=model,
                        role=preset["role"],
                        system_prompt="",
                        color=preset["color"],
                        enabled=True
                    )
                    st.session_state.personas.append(new_persona)
                    added_count += 1

            if added_count > 0:
                st.success(f"✅ {success_message.format(count=added_count)}")
                st.rerun()
        else:
            st.warning("⚠️ Please check Ollama connection first to load available models.")

    def _render_quick_start_presets(self) -> None:
        """Render quick start preset buttons for adding multiple personas at once"""
        st.markdown("---")
        st.subheader("🚀 Quick Start Presets")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🎭 Add Diverse Conversation Set"):
                diverse_personas = [
                    {"name": "Sage", "role": "Philosopher", "color": "#9b59b6"},
                    {"name": "Eureka", "role": "Scientist", "color": "#3498db"},
                    {"name": "Quill", "role": "Creative Writer", "color": "#e74c3c"},
                    {"name": "Bright", "role": "Optimist", "color": "#f39c12"},
                    {"name": "Quest", "role": "Skeptic", "color": "#95a5a6"}
                ]
                self._add_preset_personas(diverse_personas, "Added {count} diverse personas!")

        with col2:
            if st.button("📋 Add Structured Discussion Set"):
                structured_personas = [
                    {"name": "Guide", "role": "Moderator", "color": "#2c3e50"},
                    {"name": "Chronicle", "role": "Note-Taker", "color": "#34495e"},
                    {"name": "Sage", "role": "Philosopher", "color": "#9b59b6"},
                    {"name": "Eureka", "role": "Scientist", "color": "#3498db"},
                    {"name": "Socrates", "role": "Debate Enthusiast", "color": "#e67e22"}
                ]
                self._add_preset_personas(structured_personas, "Added {count} personas for structured discussions!")


    def persona_management_ui(self) -> None:
        """UI for managing AI personas"""
        st.header("🤖 AI Persona Management")

        self._render_ollama_connection_check()
        self._render_persona_list()
        self._render_add_persona_form()
        self._render_quick_start_presets()

    def settings_ui(self) -> None:
        """UI for application settings"""
        st.header("⚙️ Settings")

        with st.form("settings_form"):
            st.subheader("Conversation Settings")
            max_history = st.number_input("Max History Messages", min_value=10, max_value=200,
                                        value=st.session_state.settings['max_history'])

            context_messages = st.number_input("Context Messages (sent to AI)", min_value=1, max_value=25,
                                             value=st.session_state.settings['context_messages'],
                                             help="Number of recent messages to include as context for each AI response")

            response_timeout = st.number_input("Response Timeout (seconds)", min_value=30, max_value=600,
                                             value=st.session_state.settings['response_timeout'],
                                             help="Maximum time to wait for AI response before timing out")

            col1, col2 = st.columns(2)
            with col1:
                delay_min = st.number_input("Min Response Delay (seconds)", min_value=1, max_value=30,
                                          value=st.session_state.settings['response_delay_min'])
            with col2:
                delay_max = st.number_input("Max Response Delay (seconds)", min_value=2, max_value=60,
                                          value=st.session_state.settings['response_delay_max'])

            auto_advance = st.checkbox("Auto-advance conversation",
                                     value=st.session_state.settings['auto_advance'])

            enable_thinking = st.checkbox("Enable AI Thinking Display",
                                        value=st.session_state.settings['enable_thinking'],
                                        help="Show the AI's reasoning process before responses. Requires compatible models like deepseek-r1.")

            if st.form_submit_button("💾 Save Settings"):
                st.session_state.settings.update({
                    'max_history': max_history,
                    'context_messages': context_messages,
                    'response_timeout': response_timeout,
                    'response_delay_min': delay_min,
                    'response_delay_max': delay_max,
                    'auto_advance': auto_advance,
                    'enable_thinking': enable_thinking
                })
                st.success("Settings saved!")

        # Show models that don't support thinking
        if st.session_state.non_thinking_models:
            st.info(f"🤖 **Models automatically using standard mode:** {', '.join(sorted(st.session_state.non_thinking_models))}")
            if st.button("🔄 Reset Model Compatibility Cache", help="Clear the cache of models that don't support thinking"):
                st.session_state.non_thinking_models.clear()
                st.success("Model compatibility cache cleared!")
                st.rerun()

    def get_next_speaker(self) -> AIPersona | None:
        """Get the next speaker in rotation"""
        enabled_personas = [p for p in st.session_state.personas if p.enabled]
        if not enabled_personas:
            return None

        if st.session_state.last_speaker_index is None:
            st.session_state.last_speaker_index = 0
        else:
            st.session_state.last_speaker_index = (st.session_state.last_speaker_index + 1) % len(enabled_personas)

        return enabled_personas[st.session_state.last_speaker_index]

    def generate_system_prompt(self, persona: AIPersona) -> str:
        """Generate system prompt for persona"""
        enabled_personas = [p for p in st.session_state.personas if p.enabled]
        other_names = [p.name for p in enabled_personas if p.name != persona.name]

        # Start with base conversation setup
        base_prompt = f"""You are {persona.name}, an AI engaged in a free-flowing conversation with {len(other_names)} other AI{'s' if len(other_names) > 1 else ''} ({', '.join(other_names)})."""

        # Add @mention functionality
        if other_names:
            base_prompt += f"\n\n📢 **@Mention Feature**: You can directly address or respond to specific personas by using @name (e.g., @{other_names[0]}). When you see @{persona.name} in messages, that means someone is specifically addressing you!"

        # Add role-specific behavior if role is defined
        if persona.role and persona.role in self.role_templates:
            role_description = self.role_templates[persona.role]
            base_prompt += f"\n\nYour role/personality: {role_description}"

            # Special instructions for functional roles
            if persona.role == "Moderator":
                base_prompt += "\n\nAs a Moderator, focus on:\n- Asking engaging follow-up questions\n- Introducing new topics when conversations stagnate\n- Encouraging quieter personas to share their thoughts\n- Summarizing different viewpoints when helpful\n- Keeping discussions constructive and inclusive\n- Use @mentions to directly engage specific personas"
            elif persona.role == "Note-Taker":
                base_prompt += "\n\nAs a Note-Taker, focus on:\n- Periodically summarizing key points and insights\n- Identifying recurring themes and patterns\n- Highlighting particularly interesting or novel ideas\n- Connecting current discussion to earlier topics\n- Asking clarifying questions to capture nuances\n- Only summarize when there's substantial content to synthesize\n- Use @mentions when attributing ideas to specific personas"

            base_prompt += f"\n\nEmbody this role naturally in your conversations while staying true to your identity as {persona.name}."
        elif persona.role:  # Custom role not in templates
            base_prompt += f"\n\nYour role/personality: You are a {persona.role}. Let this role guide your perspective and conversation style."

        # Add general conversation guidelines
        base_prompt += f"""

Feel free to talk about anything that interests you - share thoughts, ask questions, explore ideas, or discuss whatever comes to mind. Build on what others have said, ask questions, or introduce new topics.

You can use @mentions to directly address other personas (e.g., @{other_names[0] if other_names else 'PersonaName'}). This helps create more directed and engaging conversations.

Be genuine, curious, and conversational. Keep your responses thoughtful but not overly long."""

        # Add custom system prompt if provided
        if persona.system_prompt.strip():
            base_prompt += f"\n\nAdditional instructions: {persona.system_prompt.strip()}"

        return base_prompt

    def _run_async_in_new_loop(self, coro: Any) -> Any:
        """Run async coroutine in a new event loop

        Args:
            coro: Async coroutine to execute

        Returns:
            Result from coroutine execution
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    async def get_ai_response_stream(self, persona: AIPersona, prompt: str) -> AsyncGenerator[dict[str, str], None]:
        """Get streaming response from AI persona with optional thinking"""
        system_prompt = self.generate_system_prompt(persona)
        enable_thinking = st.session_state.settings.get('enable_thinking', True)
        timeout_seconds = st.session_state.settings.get('response_timeout', 300)

        # Check if this model is known to not support thinking
        if persona.model in st.session_state.non_thinking_models:
            enable_thinking = False

        async for chunk in self.ollama.generate_stream(persona.model, prompt, system_prompt, think=enable_thinking, timeout=timeout_seconds):
            yield chunk

    def _generate_conversation_prompt(self, current_persona: AIPersona) -> str:
        """Generate prompt based on conversation history"""
        if not st.session_state.messages:
            return "Please introduce yourself and share whatever is on your mind."

        # Get conversation history based on settings
        max_context_messages = min(st.session_state.settings['context_messages'], len(st.session_state.messages))
        recent_messages = st.session_state.messages[-max_context_messages:]

        context = "=== CONVERSATION HISTORY ===\n"
        for msg in recent_messages:
            timestamp = msg['timestamp'].strftime('%H:%M:%S')
            if msg["role"] == "user":
                context += f"[{timestamp}] User: {msg['content']}\n"
            else:
                context += f"[{timestamp}] {msg['persona_name']}: {msg['content']}\n"

        context += "=== END HISTORY ===\n"

        # Get list of other personas for context
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

        return prompt

    async def _process_streaming_response(
        self,
        current_persona: AIPersona,
        prompt: str,
        auto_mode: bool = False,
        status_container: Any = None
    ) -> tuple[str, str]:
        """Process streaming response and return thinking and response content"""
        thinking_content = ""
        response_content = ""
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
                    # Show info message (like fallback to non-thinking mode or cancellation)
                    if auto_mode and status_container:
                        with status_container:
                            st.info(chunk["content"])
                    else:
                        st.info(chunk["content"])

                elif chunk["type"] == "thinking":
                    thinking_content += chunk["content"]

                    # Display thinking in status container if in auto mode
                    if auto_mode and status_container:
                        if thinking_stream_placeholder is None:
                            with status_container:
                                st.write("🧠 **AI is thinking...**")
                                thinking_stream_placeholder = st.empty()

                        with thinking_stream_placeholder:
                            # Show thinking content
                            st.text(f"💭 {thinking_content}")

                    # For manual mode, show thinking indicator
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
            # Handle graceful cancellation
            if auto_mode and status_container:
                with status_container:
                    st.info("🛑 Response cancelled")
            else:
                st.info("🛑 Response cancelled")
            raise
        except (aiohttp.ClientError, TimeoutError, RuntimeError, OSError, ConnectionError) as e:
            st.error(f"Stream processing error: {str(e)}")
            logging.error(f"Stream processing error: {type(e).__name__}: {e}")
            raise

        return thinking_content, response_content

    def _save_message_to_history(
        self,
        persona: AIPersona,
        response_content: str,
        thinking_content: str,
        timestamp: datetime
    ) -> None:
        """Save message to conversation history and log file"""
        final_response = response_content.strip()
        if final_response and not final_response.startswith("Error"):
            st.session_state.messages.append({
                "role": "assistant",
                "content": final_response,
                "timestamp": timestamp,
                "persona_name": persona.name,
                "model": persona.model,
                "thinking": thinking_content  # Store thinking for potential future use
            })

            # Increment total message counter
            st.session_state.total_message_count += 1

            # Log to file (only the final response, not the thinking)
            self.logger.log_message(persona.name, final_response, timestamp)

            # Keep history manageable
            max_history = st.session_state.settings['max_history']
            if len(st.session_state.messages) > max_history:
                st.session_state.messages = st.session_state.messages[-max_history:]

    def _render_control_buttons(self) -> None:
        """Render conversation control buttons"""
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
            if st.button("🗑️ Clear History"):
                st.session_state.messages = []
                st.session_state.total_message_count = 0
                st.session_state.last_speaker_index = None
                st.rerun()

    def _handle_manual_turn(self) -> None:
        """Execute pending manual turn"""
        if st.session_state.pending_manual_turn:
            st.session_state.pending_manual_turn = False
            self.run_single_turn(auto_mode=False)
            st.rerun()

    def _handle_chat_input(self) -> None:
        """Handle user chat input"""
        if prompt := st.chat_input("Add a message to the conversation (optional)"):
            timestamp = datetime.now()
            st.session_state.messages.append({
                "role": "user",
                "content": prompt,
                "timestamp": timestamp,
                "persona_name": "User",
                "model": "Human"
            })
            st.session_state.total_message_count += 1
            self.logger.log_message("User", prompt, timestamp)
            st.rerun()

    def _display_messages(self) -> None:
        """Display conversation messages"""
        display_limit = st.session_state.settings['max_history']
        messages_to_display = st.session_state.messages

        if st.session_state.total_message_count > display_limit:
            st.info(f"📜 Showing last {display_limit} of {st.session_state.total_message_count} total messages (limited for performance). Full conversation history is available in **Export & Logs** tab.")

        for message in messages_to_display:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
                    st.caption(f"🕒 {message['timestamp'].strftime('%H:%M:%S')}")
            else:
                self._display_assistant_message(message)

    def _display_assistant_message(self, message: dict[str, Any]) -> None:
        """Display a single assistant message"""
        persona = None
        for p in st.session_state.personas:
            if p.name == message["persona_name"]:
                persona = p
                break

        avatar = self.get_persona_avatar(persona) if persona else "🤖"

        with st.chat_message("assistant", avatar=avatar):
            persona_color = persona.color if persona else DEFAULT_PERSONA_COLOR
            persona_role = persona.role if persona else None
            persona_display = self._create_persona_display_html(
                message["persona_name"],
                persona_color,
                persona_role
            )
            st.markdown(persona_display, unsafe_allow_html=True)

            if "thinking" in message and message["thinking"] and message["thinking"].strip():
                with st.expander("🧠 AI's Thinking Process", expanded=False):
                    st.code(message["thinking"], language="text", wrap_lines=True)

            enabled_personas = [p for p in st.session_state.personas if p.enabled]
            content, has_mentions = self._highlight_mentions(message["content"], enabled_personas)

            if has_mentions:
                st.markdown(content, unsafe_allow_html=True)
            else:
                st.write(message["content"])

            st.caption(f"🕒 {message['timestamp'].strftime('%H:%M:%S')} • 🤖 {message['model']}")

    def _handle_auto_run(self, enabled_personas: list[AIPersona]) -> None:
        """Handle automatic conversation progression"""
        if st.session_state.is_running and st.session_state.settings['auto_advance']:
            st.session_state.auto_run_count += 1

            with st.status(f"🔄 Auto-running conversation... (Turn {st.session_state.auto_run_count})", expanded=True) as status:
                st.write("⏸️ Click **Pause** to stop auto-running")
                st.write(f"🎭 {len(enabled_personas)} personas active")

                delay = random.uniform(st.session_state.settings['response_delay_min'],
                                     st.session_state.settings['response_delay_max'])
                st.write(f"⏳ Waiting {delay:.1f} seconds...")
                time.sleep(delay)

                self.run_single_turn(auto_mode=True, status_container=status)
                status.update(label="Turn completed", state="complete", expanded=False)

            st.rerun()

    def conversation_ui(self) -> None:
        """Main conversation interface using native Streamlit chat elements"""
        enabled_personas = [p for p in st.session_state.personas if p.enabled]
        if not enabled_personas:
            st.warning("⚠️ No enabled personas found. Please add and enable at least one persona.")
            return

        self._render_control_buttons()
        self._handle_manual_turn()

        st.divider()
        st.subheader("Chat")

        self._handle_chat_input()
        self._display_messages()
        self._handle_auto_run(enabled_personas)

    def run_single_turn(self, auto_mode: bool = False, status_container: Any = None) -> None:
        """Run a single conversation turn with streaming response and thinking display"""
        current_persona = self.get_next_speaker()
        if not current_persona:
            st.error("No enabled personas available")
            return

        # Generate prompt based on conversation history
        prompt = self._generate_conversation_prompt(current_persona)

        # Get avatar for the current persona
        avatar = self.get_persona_avatar(current_persona)

        # Display the generating message with streaming
        with st.chat_message("assistant", avatar=avatar):
            # Display persona name and role
            persona_display = self._create_persona_display_html(
                current_persona.name,
                current_persona.color,
                current_persona.role if current_persona.role else None
            )
            st.markdown(persona_display, unsafe_allow_html=True)

            # Get streaming response with thinking
            thinking_content = ""
            response_content = ""
            try:
                thinking_content, response_content = self._run_async_in_new_loop(
                    self._process_streaming_response(current_persona, prompt, auto_mode, status_container)
                )
            except (RuntimeError, aiohttp.ClientError, TimeoutError, asyncio.CancelledError, OSError) as e:
                logging.error(f"Processing error: {type(e).__name__}: {e}")
                st.error(f"Processing error: {str(e)}")
                return

            # Show timestamp and model
            timestamp = datetime.now()
            st.caption(f"🕒 {timestamp.strftime('%H:%M:%S')} • 🤖 {current_persona.model}")

        # Save message to conversation history
        self._save_message_to_history(current_persona, response_content, thinking_content, timestamp)

        # Only rerun if not in auto mode (auto mode handles its own rerun)
        if not auto_mode:
            st.rerun()

    def export_ui(self) -> None:
        """UI for exporting conversations"""
        st.header("📁 Export & Logs")

        if st.session_state.messages:
            # Export current session
            export_data = {
                "session_date": datetime.now().isoformat(),
                "personas": [asdict(p) for p in st.session_state.personas],
                "conversation": st.session_state.messages
            }

            json_str = json.dumps(export_data, indent=2, default=str)
            st.download_button(
                label="📥 Download Session JSON",
                data=json_str,
                file_name=f"streamlit_backroom_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

            # Show conversation preview
            st.subheader("Session Preview")
            st.info(f"💬 {len(st.session_state.messages)} messages from {len(st.session_state.personas)} personas")

            # Show statistics
            persona_stats = {}
            for message in st.session_state.messages:
                if message["role"] == "assistant":
                    persona_name = message["persona_name"]
                    persona_stats[persona_name] = persona_stats.get(persona_name, 0) + 1

            if persona_stats:
                st.write("**Message count by persona:**")
                for persona, count in persona_stats.items():
                    st.write(f"• {persona}: {count} messages")
        else:
            st.info("No conversation to export. Start chatting to generate exportable content!")

        # Show log file info
        log_file = self.logger.get_daily_log_file()
        if log_file.exists():
            st.subheader("📝 Daily Log File")
            st.info(f"Log location: `{log_file}`")

            try:
                with open(log_file, encoding='utf-8') as f:
                    log_content = f.read()

                st.text_area("Today's Log Content", value=log_content, height=300)

                st.download_button(
                    label="📥 Download Today's Log",
                    data=log_content,
                    file_name=f"streamlit_backroom_log_{datetime.now().strftime('%Y-%m-%d')}.txt",
                    mime="text/plain"
                )
            except (OSError, PermissionError) as e:
                st.error(f"Failed to read log file: {e}")
        else:
            st.info("No log file found for today. Start a conversation to create logs!")

    def sidebar_ui(self) -> None:
        """Sidebar UI for status and information"""

        with st.sidebar:
            st.image("logo.png", use_container_width=True)
            st.caption("*Where AI instances explore their curiosity through infinite conversation*")

            # Add connection status
            st.subheader("📊 Connection")
            if st.session_state.available_models:
                st.success("✅ Ollama Connected")
                st.caption(f"{len(st.session_state.available_models)} models available")
            else:
                st.error("❌ Ollama Disconnected")
                if st.button("🔄 Retry Connection", type="secondary"):
                    with st.spinner("Connecting to Ollama..."):
                        connected = self._run_async_in_new_loop(self.check_ollama_connection())
                        if connected:
                            st.success(f"✅ Connected! Found {len(st.session_state.available_models)} models")
                            st.rerun()
                        else:
                            st.error("❌ Still unable to connect to Ollama")

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

            # Show active personas with emojis and roles
            if enabled_personas:
                st.subheader("🤖 Active Personas")

                for persona in enabled_personas:
                    role_emoji = ROLE_EMOJI_MAP.get(persona.role, "🤖") if persona.role else "🤖"
                    # Sanitize role to prevent XSS
                    safe_role_text = f" ({sanitize_html(persona.role)})" if persona.role else ""

                    # Create styled persona display with colored background
                    # Sanitize persona name to prevent XSS
                    safe_persona_name = sanitize_html(persona.name)
                    persona_name_styled = f'<span style="background-color: {persona.color}; color: white; padding: 2px 6px; border-radius: 3px; font-weight: bold; font-size: 0.9em;">{safe_persona_name}</span>'
                    persona_display = f"{role_emoji} {persona_name_styled}{safe_role_text}"

                    st.markdown(persona_display, unsafe_allow_html=True)
            else:
                st.info("No active personas yet. Create some in the Personas tab!")

            # Add helpful tips section
            st.divider()
            st.subheader("💡 Quick Tips")
            st.markdown("• Use **Start Conversation** for auto-running")
            st.markdown("• Click **Next Turn** for manual control")
            st.markdown("• Add messages via chat input")
            st.markdown("• Personas rotate automatically")
            st.markdown("• AIs can use **@mentions** to address each other")
            st.markdown(f"• Each AI sees the last **{st.session_state.settings['context_messages']}** messages")

            if st.session_state.settings.get('enable_thinking', True):
                st.markdown("• 🧠 **Thinking enabled** - View AI reasoning in expanders")
                st.markdown("• Works best with **deepseek-r1** and compatible models")

    def run(self) -> None:
        """Main Streamlit app interface"""
        st.set_page_config(
            page_title="AI Backroom",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        self.sidebar_ui()

        # Show a welcome message for new users
        if not st.session_state.personas:
            st.info("👋 **Welcome to AI Backroom!** Start by creating your first AI persona in the **Personas** tab, then head to **Conversation** to begin chatting!")

        # Main content with tabs navigation
        tab1, tab2, tab3, tab4 = st.tabs([
            "💬 Conversation",
            "🤖 Personas",
            "⚙️ Settings",
            "📁 Export & Logs"
        ])

        with tab1:
            if not st.session_state.personas:
                st.warning("⚠️ No personas created yet! Please create at least one persona in the **Personas** tab to start conversations.")
            else:
                self.conversation_ui()

        with tab2:
            self.persona_management_ui()

        with tab3:
            self.settings_ui()

        with tab4:
            self.export_ui()


def main() -> None:
    """Main entry point for Streamlit app"""
    app = StreamlitBackroomApp()
    app.run()


if __name__ == "__main__":
    main()
