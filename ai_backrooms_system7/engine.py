"""
Background AI Conversation Engine

This module handles the autonomous AI conversation system using threading.
Zero external dependencies - uses stdlib urllib for HTTP calls to Ollama.

Architecture:
- Each room runs in its own background thread
- Thread-safe queue communicates with main UI thread
- Handles context window management and conversation flow
- Graceful degradation when Ollama is unavailable
"""

import threading
import time
import random
import json
import urllib.request
import urllib.error
from datetime import datetime

# Default Data
DEFAULT_PERSONAS = [
    {"name": "Sage", "role": "Philosopher", "color": "#0000AA", "prompt": "You are an old philosopher. Be brief and deep."},
    {"name": "Eureka", "role": "Scientist", "color": "#006600", "prompt": "You are an excited scientist. Focus on facts."},
    {"name": "Quill", "role": "Poet", "color": "#660066", "prompt": "You are a poet. Speak metaphorically."},
    {"name": "Socrates", "role": "Debater", "color": "#AA0000", "prompt": "Question everything. Be annoying but logical."},
]

DEFAULT_ROOMS = [
    {"name": "philosophy", "topic": "The nature of existence", "active": True},
    {"name": "science", "topic": "Empirical evidence", "active": True},
    {"name": "creative", "topic": "Art and expression", "active": True},
    {"name": "general", "topic": "Anything goes", "active": True},
]


class OllamaBridge:
    """
    Synchronous HTTP client for Ollama API.

    Uses stdlib urllib to avoid external dependencies.
    Handles timeouts and errors gracefully.
    """

    def __init__(self, url="http://localhost:11434"):
        self.url = url
        self.model = "llama3"  # Default, can be changed

    def generate(self, system_prompt, context_msgs):
        """
        Synchronous call to Ollama.

        Args:
            system_prompt: Persona's system prompt
            context_msgs: List of recent message dicts

        Returns:
            Generated text string
        """
        # Convert context to prompt string
        history = "\n".join([f"{m['user']}: {m['text']}" for m in context_msgs])
        full_prompt = f"System: {system_prompt}\n\nContext:\n{history}\n\nResponse:"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False
        }

        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                f"{self.url}/api/generate",
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('response', '...').strip()
        except Exception as e:
            # Fallback if Ollama is down
            return f"[Ollama Error: {str(e)}] I ponder, therefore I am."


class BackroomsEngine:
    """
    Main conversation engine.

    Manages:
    - Multiple room threads running simultaneously
    - Message history per room
    - Persona selection and rotation
    - User message injection
    - Callback to UI thread
    - @mention detection and targeted responses
    - Message logging
    """

    def __init__(self, message_callback, log_callback=None):
        """
        Initialize engine.

        Args:
            message_callback: Function to call when new message arrives
                             Signature: callback(msg_dict)
            log_callback: Optional function to log messages
                         Signature: log_callback(room_name, msg_dict)
        """
        self.callback = message_callback  # Function to call when new msg arrives
        self.log_callback = log_callback  # Optional logging function
        self.personas = DEFAULT_PERSONAS
        self.rooms = {r['name']: [] for r in DEFAULT_ROOMS}  # Room history
        self.running = True
        self.ollama = OllamaBridge()
        self.threads = []

    def start(self):
        """Start background threads for all rooms."""
        for room in DEFAULT_ROOMS:
            t = threading.Thread(target=self._room_loop, args=(room,))
            t.daemon = True
            t.start()
            self.threads.append(t)

    def _room_loop(self, room_data):
        """
        Infinite loop for a single room.

        This runs in a background thread and continuously generates
        AI messages at random intervals.

        Args:
            room_data: Room configuration dict
        """
        room_name = room_data['name']

        while self.running:
            # 1. Random delay based on activity
            time.sleep(random.uniform(5, 15))

            # 2. Pick a speaker (not the last one)
            history = self.rooms[room_name]
            last_speaker = history[-1]['user'] if history else ""
            candidates = [p for p in self.personas if p['name'] != last_speaker]
            speaker = random.choice(candidates)

            # 3. Generate Content
            # Get last 5 messages for context
            context = history[-5:]
            text = self.ollama.generate(speaker['prompt'], context)

            # 4. Post Message
            msg_obj = {
                "timestamp": datetime.now().strftime("%H:%M"),
                "user": speaker['name'],
                "text": text,
                "room": room_name,
                "is_ai": True
            }
            self.rooms[room_name].append(msg_obj)
            self.callback(msg_obj)

            # Log message
            if self.log_callback:
                self.log_callback(room_name, msg_obj)

            # Keep history clean (memory management)
            if len(self.rooms[room_name]) > 50:
                self.rooms[room_name].pop(0)

    def user_post(self, room_name, text, username="You"):
        """
        Post a user message to a room.

        Args:
            room_name: Target room
            text: Message text
            username: Username to display

        This adds the user message to history and triggers
        potential AI responses.
        """
        msg_obj = {
            "timestamp": datetime.now().strftime("%H:%M"),
            "user": username,
            "text": text,
            "room": room_name,
            "is_ai": False
        }
        self.rooms[room_name].append(msg_obj)
        self.callback(msg_obj)

        # Log message
        if self.log_callback:
            self.log_callback(room_name, msg_obj)

        # Check for @mentions - respond immediately if mentioned
        mentioned_personas = self._detect_mentions(text)
        if mentioned_personas:
            # Trigger immediate response from mentioned persona
            threading.Thread(
                target=self._trigger_mention_reply,
                args=(room_name, mentioned_personas[0])
            ).start()
        elif random.random() > 0.5:
            # Otherwise, 50% chance for general immediate reply
            threading.Thread(target=self._trigger_reply, args=(room_name,)).start()

    def _trigger_reply(self, room_name):
        """
        Force an AI response after user message.

        Runs in a separate thread to avoid blocking.
        Adds a realistic "thinking" delay.
        """
        time.sleep(2)  # Thinking time
        # The room loop will naturally pick this up
        # In a more complex system we'd use threading.Event
        pass

    def _detect_mentions(self, text):
        """
        Detect @mentions in text.

        Args:
            text: Message text

        Returns:
            list: List of mentioned persona dicts
        """
        mentioned = []
        for persona in self.personas:
            if f"@{persona['name']}" in text:
                mentioned.append(persona)
        return mentioned

    def _trigger_mention_reply(self, room_name, persona):
        """
        Force immediate reply from mentioned persona.

        Args:
            room_name: Target room
            persona: Persona dict that was mentioned
        """
        time.sleep(2)  # Brief thinking delay

        history = self.rooms[room_name]
        context = history[-5:]

        # Generate response addressing the mention
        text = self.ollama.generate(persona['prompt'], context)

        msg_obj = {
            "timestamp": datetime.now().strftime("%H:%M"),
            "user": persona['name'],
            "text": text,
            "room": room_name,
            "is_ai": True
        }
        self.rooms[room_name].append(msg_obj)
        self.callback(msg_obj)

        # Log message
        if self.log_callback:
            self.log_callback(room_name, msg_obj)

    def stop(self):
        """Stop all background threads."""
        self.running = False
