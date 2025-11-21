#!/usr/bin/env python3
"""
Infinite AI Backroom - Flask Web App with System.css
Real-time chat interface using system.css design system
"""

import asyncio
import json
import logging
import random
import re
import uuid
from collections.abc import AsyncGenerator
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import aiohttp
from flask import Flask, jsonify, render_template, request, session
from flask_socketio import SocketIO, emit

# Suppress async warnings
logging.getLogger("aiohttp.client").setLevel(logging.ERROR)

app = Flask(__name__)
app.config["SECRET_KEY"] = "infinite-backrooms-secret-key-change-in-production"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")


@dataclass
class AIPersona:
    """Represents an AI instance with detailed configuration"""

    id: str
    name: str
    model: str
    role: str = ""
    system_prompt: str = ""
    color: str = "#1f77b4"
    enabled: bool = True


class ConversationLogger:
    """Handles logging conversations to daily TXT files"""

    def __init__(self, log_dir: str = "conversations"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

    def get_daily_log_file(self) -> Path:
        """Get the log file for today"""
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        return self.log_dir / f"backroom_{today}.txt"

    def clean_message(self, message: str) -> str:
        """Remove thinking tags and content from message"""
        cleaned = re.sub(r"<think>.*?</think>", "", message, flags=re.DOTALL | re.IGNORECASE)
        return re.sub(r"\s+", " ", cleaned).strip()

    def log_message(self, persona: str, message: str, timestamp: datetime | None = None):
        """Log a message to today's file"""
        if timestamp is None:
            timestamp = datetime.now(UTC)

        cleaned_message = self.clean_message(message)

        if cleaned_message:
            log_file = self.get_daily_log_file()
            with log_file.open("a", encoding="utf-8") as f:
                f.write(f"[{timestamp.strftime('%H:%M:%S')}] {persona}$ {cleaned_message}\n")


class OllamaClient:
    """Client for interacting with Ollama API"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    async def test_connection(self) -> tuple[bool, list[str]]:
        """Test if Ollama API is accessible and return available models"""
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
        """Generate streaming response from Ollama model"""
        payload = {"model": model, "prompt": prompt, "stream": True, "think": think}

        if system and system.strip():
            payload["system"] = system.strip()

        session = None
        try:
            connector = aiohttp.TCPConnector(
                limit=1, force_close=True, enable_cleanup_closed=True
            )
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
                else:
                    error_text = await response.text()
                    yield {"type": "error", "content": f"Error {response.status}: {error_text}"}

        finally:
            if session and not session.closed:
                await session.close()


# Global state
conversations = []
personas = []
logger = ConversationLogger()
ollama_client = OllamaClient()


# Default personas with system.css compatible colors
DEFAULT_PERSONAS = [
    {
        "name": "Philosopher",
        "model": "qwen2.5:14b",
        "role": "🤔",
        "system_prompt": "You are a deep thinker who explores philosophical concepts.",
        "color": "#9b59b6",
    },
    {
        "name": "Scientist",
        "model": "qwen2.5:14b",
        "role": "🔬",
        "system_prompt": "You are a scientist who thinks empirically.",
        "color": "#3498db",
    },
    {
        "name": "Artist",
        "model": "qwen2.5:14b",
        "role": "🎨",
        "system_prompt": "You are a creative artist with unique perspectives.",
        "color": "#e74c3c",
    },
]


def initialize_personas():
    """Initialize default personas"""
    global personas
    personas = [
        AIPersona(
            id=str(uuid.uuid4()),
            name=p["name"],
            model=p["model"],
            role=p["role"],
            system_prompt=p["system_prompt"],
            color=p["color"],
            enabled=True,
        )
        for p in DEFAULT_PERSONAS
    ]


@app.route("/")
def index():
    """Main chat interface"""
    return render_template("chat.html")


@app.route("/api/personas")
def get_personas():
    """Get all personas"""
    return jsonify([asdict(p) for p in personas])


@app.route("/api/messages")
def get_messages():
    """Get all messages"""
    return jsonify(conversations)


@socketio.on("connect")
def handle_connect():
    """Handle new client connection"""
    emit("personas", [asdict(p) for p in personas])
    emit("messages", conversations)


@socketio.on("start_conversation")
def handle_start_conversation(data):
    """Start a new conversation round"""
    asyncio.run(run_conversation_round())


async def run_conversation_round():
    """Run one round of conversation with all enabled personas"""
    enabled_personas = [p for p in personas if p.enabled]

    if not enabled_personas:
        socketio.emit("error", {"message": "No enabled personas"})
        return

    # Build context from recent messages
    context_messages = conversations[-10:] if conversations else []
    context = "\n".join(
        [f"{msg['persona_name']}: {msg['content']}" for msg in context_messages]
    )

    for persona in enabled_personas:
        # Build prompt
        if context:
            prompt = f"Previous conversation:\n{context}\n\nYour response:"
        else:
            prompt = "Start an interesting conversation:"

        # Generate response
        full_response = ""
        thinking_content = ""

        message_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).isoformat()

        async for chunk in ollama_client.generate_stream(
            model=persona.model,
            prompt=prompt,
            system=persona.system_prompt,
            think=True,
        ):
            if chunk["type"] == "thinking":
                thinking_content += chunk["content"]
            elif chunk["type"] == "response":
                full_response += chunk["content"]
                # Emit streaming update
                socketio.emit(
                    "message_update",
                    {
                        "id": message_id,
                        "persona_id": persona.id,
                        "persona_name": persona.name,
                        "persona_color": persona.color,
                        "persona_role": persona.role,
                        "content": full_response,
                        "thinking": thinking_content,
                        "timestamp": timestamp,
                        "streaming": True,
                    },
                )

        # Final message
        if full_response:
            message = {
                "id": message_id,
                "persona_id": persona.id,
                "persona_name": persona.name,
                "persona_color": persona.color,
                "persona_role": persona.role,
                "content": full_response,
                "thinking": thinking_content,
                "timestamp": timestamp,
                "streaming": False,
            }
            conversations.append(message)
            logger.log_message(persona.name, full_response)

            socketio.emit("message_final", message)


if __name__ == "__main__":
    initialize_personas()
    socketio.run(app, debug=True, host="0.0.0.0", port=5001, allow_unsafe_werkzeug=True)
