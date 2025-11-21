#!/usr/bin/env python3
"""
Infinite AI Backroom - Complete Flask Application
Full-featured AI conversation system with system.css design
"""

# IMPORTANT: eventlet monkey patch must be first
import eventlet

eventlet.monkey_patch()

import asyncio
import json
import logging
import random
import re
import time
import uuid
from collections.abc import AsyncGenerator
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiohttp
from flask import Flask, jsonify, render_template, request, session
from flask_socketio import SocketIO, emit

# Suppress warnings
logging.getLogger("aiohttp.client").setLevel(logging.ERROR)

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-in-production"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")


@dataclass
class AIPersona:
    """AI Persona with full configuration"""

    id: str
    name: str
    model: str
    role: str = ""
    system_prompt: str = ""
    color: str = "#1f77b4"
    enabled: bool = True


@dataclass
class AppSettings:
    """Application settings"""

    max_history: int = 50
    response_delay_min: float = 2.0
    response_delay_max: float = 8.0
    auto_advance: bool = True
    context_messages: int = 10
    enable_thinking: bool = True
    response_timeout: int = 300


@dataclass
class AppState:
    """Global application state"""

    personas: list[AIPersona] = field(default_factory=list)
    conversations: list[dict[str, Any]] = field(default_factory=list)
    settings: AppSettings = field(default_factory=AppSettings)
    is_running: bool = False
    last_speaker_index: int | None = None
    total_message_count: int = 0
    non_thinking_models: set[str] = field(default_factory=set)


# Global state
state = AppState()


class ConversationLogger:
    """Logger for conversations"""

    def __init__(self, log_dir: str = "conversations"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

    def get_daily_log_file(self) -> Path:
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        return self.log_dir / f"backroom_{today}.txt"

    def clean_message(self, message: str) -> str:
        cleaned = re.sub(r"<think>.*?</think>", "", message, flags=re.DOTALL | re.IGNORECASE)
        return re.sub(r"\s+", " ", cleaned).strip()

    def log_message(self, persona: str, message: str, timestamp: datetime | None = None):
        if timestamp is None:
            timestamp = datetime.now(UTC)

        cleaned_message = self.clean_message(message)

        if cleaned_message:
            log_file = self.get_daily_log_file()
            with log_file.open("a", encoding="utf-8") as f:
                f.write(f"[{timestamp.strftime('%H:%M:%S')}] {persona}$ {cleaned_message}\n")


class OllamaClient:
    """Ollama API client"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    async def test_connection(self) -> tuple[bool, list[str]]:
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=10)
                ) as response,
            ):
                if response.status == 200:
                    result = await response.json()
                    models = [model["name"] for model in result.get("models", [])]
                    return True, models
                return False, []
        except Exception as e:
            logging.error(f"Failed to connect to Ollama: {e}")
            return False, []

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
        think: bool = True,
        timeout: int = 300,
    ) -> AsyncGenerator[dict[str, str], None]:
        payload = {"model": model, "prompt": prompt, "stream": True, "think": think}

        if system and system.strip():
            payload["system"] = system.strip()

        session = None
        try:
            connector = aiohttp.TCPConnector(limit=1, force_close=True, enable_cleanup_closed=True)
            session = aiohttp.ClientSession(connector=connector)

            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line.decode("utf-8"))

                                if chunk.get("thinking"):
                                    yield {"type": "thinking", "content": chunk["thinking"]}

                                if chunk.get("response"):
                                    yield {"type": "response", "content": chunk["response"]}

                                if chunk.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
                elif response.status == 400 and think:
                    error_text = await response.text()
                    if "does not support thinking" in error_text:
                        state.non_thinking_models.add(model)
                        yield {"type": "info", "content": f"Model {model} doesn't support thinking"}

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

        except asyncio.TimeoutError:
            yield {"type": "error", "content": "Request timeout"}
        except Exception as e:
            yield {"type": "error", "content": f"Connection error: {e!s}"}
        finally:
            if session and not session.closed:
                try:
                    await session.close()
                except Exception:
                    pass


# Global instances
logger = ConversationLogger()
ollama_client = OllamaClient()


# Role templates
ROLE_TEMPLATES = {
    "": "No specific role",
    "Moderator": "A skilled conversation facilitator who guides discussions, asks thoughtful follow-up questions, introduces new topics when needed, and helps ensure all voices are heard.",
    "Note-Taker": "A diligent observer who periodically summarizes key points, captures important insights, identifies emerging themes.",
    "Philosopher": "A thoughtful philosopher who loves exploring deep questions about existence, consciousness, reality, and intelligence.",
    "Scientist": "A curious scientist who approaches topics with empirical thinking and enjoys discussing research and theories.",
    "Creative Writer": "An imaginative writer who loves storytelling, wordplay, poetry, and exploring creative aspects of language.",
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
    "Pragmatist": "Practical and results-oriented, focuses on what works and real-world applications.",
}


def get_next_speaker() -> AIPersona | None:
    """Get next speaker using round-robin"""
    enabled = [p for p in state.personas if p.enabled]
    if not enabled:
        return None

    if state.last_speaker_index is None:
        state.last_speaker_index = 0
    else:
        state.last_speaker_index = (state.last_speaker_index + 1) % len(enabled)

    return enabled[state.last_speaker_index]


def generate_system_prompt(persona: AIPersona) -> str:
    """Generate system prompt for persona"""
    enabled = [p for p in state.personas if p.enabled]
    other_names = [p.name for p in enabled if p.name != persona.name]

    base_prompt = f"""You are {persona.name}"""

    if persona.role:
        role_description = ROLE_TEMPLATES.get(persona.role, "")
        if role_description and role_description != "No specific role":
            base_prompt += f", a {persona.role}. {role_description}"

    if other_names:
        base_prompt += f"\n\nYou are in a conversation with: {', '.join(other_names)}."

    base_prompt += """

Feel free to talk about anything that interests you - share thoughts, ask questions, explore ideas, or discuss whatever comes to mind.

You can use @mentions to directly address other personas (e.g., @PersonaName). This helps create more directed and engaging conversations.

Be genuine, curious, and conversational. Keep your responses thoughtful but not overly long."""

    if persona.system_prompt.strip():
        base_prompt += f"\n\nAdditional instructions: {persona.system_prompt.strip()}"

    return base_prompt


# Routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/personas")
def get_personas():
    return jsonify([asdict(p) for p in state.personas])


@app.route("/api/personas", methods=["POST"])
def add_persona():
    data = request.json
    persona = AIPersona(
        id=str(uuid.uuid4()),
        name=data["name"],
        model=data["model"],
        role=data.get("role", ""),
        system_prompt=data.get("system_prompt", ""),
        color=data.get("color", "#1f77b4"),
        enabled=data.get("enabled", True),
    )
    state.personas.append(persona)
    return jsonify(asdict(persona))


@app.route("/api/personas/<persona_id>", methods=["PUT"])
def update_persona(persona_id):
    data = request.json
    for persona in state.personas:
        if persona.id == persona_id:
            persona.name = data.get("name", persona.name)
            persona.model = data.get("model", persona.model)
            persona.role = data.get("role", persona.role)
            persona.system_prompt = data.get("system_prompt", persona.system_prompt)
            persona.color = data.get("color", persona.color)
            persona.enabled = data.get("enabled", persona.enabled)
            return jsonify(asdict(persona))
    return jsonify({"error": "Persona not found"}), 404


@app.route("/api/personas/<persona_id>", methods=["DELETE"])
def delete_persona(persona_id):
    state.personas = [p for p in state.personas if p.id != persona_id]
    return jsonify({"success": True})


@app.route("/api/messages")
def get_messages():
    return jsonify(state.conversations[-state.settings.max_history :])


@app.route("/api/messages", methods=["DELETE"])
def clear_messages():
    state.conversations = []
    state.total_message_count = 0
    state.last_speaker_index = None
    return jsonify({"success": True})


@app.route("/api/settings")
def get_settings():
    return jsonify(asdict(state.settings))


@app.route("/api/settings", methods=["PUT"])
def update_settings():
    data = request.json
    state.settings = AppSettings(**data)
    return jsonify(asdict(state.settings))


@app.route("/api/roles")
def get_roles():
    return jsonify(ROLE_TEMPLATES)


@app.route("/api/models")
def get_models():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        connected, models = loop.run_until_complete(ollama_client.test_connection())
        return jsonify({"connected": connected, "models": models})
    finally:
        loop.close()


@app.route("/api/export")
def export_conversations():
    return jsonify(state.conversations)


# Socket.IO events
@socketio.on("connect")
def handle_connect():
    emit("personas", [asdict(p) for p in state.personas])
    emit("messages", state.conversations[-state.settings.max_history :])
    emit("settings", asdict(state.settings))
    emit("status", {"is_running": state.is_running})


@socketio.on("start_conversation")
def handle_start_conversation():
    state.is_running = True
    socketio.emit("status", {"is_running": True})
    socketio.start_background_task(run_conversation_loop)


@socketio.on("stop_conversation")
def handle_stop_conversation():
    state.is_running = False
    socketio.emit("status", {"is_running": False})


@socketio.on("next_turn")
def handle_next_turn():
    socketio.start_background_task(run_single_turn)


def run_conversation_loop():
    """Background task for auto-running conversation"""
    while state.is_running:
        run_single_turn()

        if state.is_running:
            delay = random.uniform(state.settings.response_delay_min, state.settings.response_delay_max)
            eventlet.sleep(delay)


def run_single_turn():
    """Run a single conversation turn"""
    persona = get_next_speaker()
    if not persona:
        socketio.emit("error", {"message": "No enabled personas"})
        return

    # Build prompt
    if not state.conversations:
        prompt = "Please introduce yourself and share whatever is on your mind."
    else:
        max_context = min(state.settings.context_messages, len(state.conversations))
        recent = state.conversations[-max_context:]

        context = "=== CONVERSATION HISTORY ===\n"
        for msg in recent:
            ts = msg["timestamp"]
            if msg.get("role") == "user":
                context += f"[{ts}] User: {msg['content']}\n"
            else:
                context += f"[{ts}] {msg['persona_name']}: {msg['content']}\n"

        context += "=== END HISTORY ===\n"

        enabled = [p for p in state.personas if p.enabled]
        other_names = [p.name for p in enabled if p.name != persona.name]

        prompt = f"""{context}

You are {persona.name}. The conversation above shows the complete recent history.

Please respond naturally to continue the conversation. You can:
- Build on what others have said
- Ask questions or introduce new topics
- Use @mentions to directly address specific personas (e.g., @{other_names[0] if other_names else "PersonaName"})
- React to any part of the conversation history

Your response should be conversational and engaging."""

    # Generate response
    system_prompt = generate_system_prompt(persona)
    enable_thinking = state.settings.enable_thinking and persona.model not in state.non_thinking_models

    message_id = str(uuid.uuid4())
    timestamp = datetime.now(UTC).strftime("%H:%M:%S")

    thinking_content = ""
    response_content = ""

    # Run async generator in eventlet
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:

        async def process():
            nonlocal thinking_content, response_content

            async for chunk in ollama_client.generate_stream(
                model=persona.model,
                prompt=prompt,
                system=system_prompt,
                think=enable_thinking,
                timeout=state.settings.response_timeout,
            ):
                if chunk["type"] == "error":
                    socketio.emit("error", {"message": chunk["content"]})
                    return

                if chunk["type"] == "info":
                    socketio.emit("info", {"message": chunk["content"]})

                elif chunk["type"] == "thinking":
                    thinking_content += chunk["content"]
                    socketio.emit(
                        "message_update",
                        {
                            "id": message_id,
                            "persona_id": persona.id,
                            "persona_name": persona.name,
                            "persona_color": persona.color,
                            "persona_role": persona.role,
                            "thinking": thinking_content,
                            "content": "",
                            "timestamp": timestamp,
                            "streaming": True,
                        },
                    )

                elif chunk["type"] == "response":
                    response_content += chunk["content"]
                    socketio.emit(
                        "message_update",
                        {
                            "id": message_id,
                            "persona_id": persona.id,
                            "persona_name": persona.name,
                            "persona_color": persona.color,
                            "persona_role": persona.role,
                            "thinking": thinking_content,
                            "content": response_content,
                            "timestamp": timestamp,
                            "streaming": True,
                        },
                    )

        loop.run_until_complete(process())

    finally:
        loop.close()

    # Save message
    if response_content:
        message = {
            "id": message_id,
            "role": "assistant",
            "persona_id": persona.id,
            "persona_name": persona.name,
            "persona_color": persona.color,
            "persona_role": persona.role,
            "model": persona.model,
            "content": response_content,
            "thinking": thinking_content,
            "timestamp": timestamp,
            "streaming": False,
        }
        state.conversations.append(message)
        state.total_message_count += 1
        logger.log_message(persona.name, response_content)

        socketio.emit("message_final", message)


if __name__ == "__main__":
    # Initialize with default personas
    state.personas = [
        AIPersona(
            id=str(uuid.uuid4()),
            name="Philosopher",
            model="qwen2.5:14b",
            role="Philosopher",
            system_prompt="",
            color="#9b59b6",
            enabled=True,
        ),
        AIPersona(
            id=str(uuid.uuid4()),
            name="Scientist",
            model="qwen2.5:14b",
            role="Scientist",
            system_prompt="",
            color="#3498db",
            enabled=True,
        ),
        AIPersona(
            id=str(uuid.uuid4()),
            name="Artist",
            model="qwen2.5:14b",
            role="Creative Writer",
            system_prompt="",
            color="#e74c3c",
            enabled=True,
        ),
    ]

    socketio.run(app, debug=True, host="0.0.0.0", port=5001)
