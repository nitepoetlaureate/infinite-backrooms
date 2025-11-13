"""Constants and configuration for the Infinite Backrooms application.

This module centralizes all constants, configuration values, and loads
environment variables using python-dotenv.
"""

import os
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# ======================
# Ollama Configuration
# ======================

DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))
DEFAULT_RESPONSE_TIMEOUT = float(os.getenv("OLLAMA_RESPONSE_TIMEOUT", "300"))
OLLAMA_VERIFY_SSL = os.getenv("OLLAMA_VERIFY_SSL", "true").lower() == "true"


# ======================
# Logging Configuration
# ======================

LOG_DIRECTORY = Path(os.getenv("LOG_DIRECTORY", "conversations"))
LOG_FILE_PREFIX = os.getenv("LOG_FILE_PREFIX", "streamlit_backroom")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# ======================
# UI Configuration
# ======================

MIN_CONTEXT_MESSAGES = 1
MAX_CONTEXT_MESSAGES = 50
DEFAULT_CONTEXT_MESSAGES = int(os.getenv("DEFAULT_CONTEXT_MESSAGES", "10"))

MIN_HISTORY_MESSAGES = 10
MAX_HISTORY_MESSAGES = 200
DEFAULT_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "50"))

MIN_TEMPERATURE = 0.0
MAX_TEMPERATURE = 2.0
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))

ENABLE_THINKING = os.getenv("ENABLE_THINKING", "true").lower() == "true"


# ======================
# Auto-run Configuration
# ======================

AUTO_RUN_DELAY_MIN = int(os.getenv("AUTO_RUN_DELAY_MIN", "2"))
AUTO_RUN_DELAY_MAX = int(os.getenv("AUTO_RUN_DELAY_MAX", "8"))
AUTO_ADVANCE_DEFAULT = os.getenv("AUTO_ADVANCE_DEFAULT", "true").lower() == "true"


# ======================
# Development Settings
# ======================

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
ENABLE_PROFILING = os.getenv("ENABLE_PROFILING", "false").lower() == "false"


# ======================
# Security Settings
# ======================

MAX_PERSONA_NAME_LENGTH = int(os.getenv("MAX_PERSONA_NAME_LENGTH", "50"))
MAX_SYSTEM_PROMPT_LENGTH = int(os.getenv("MAX_SYSTEM_PROMPT_LENGTH", "10000"))
ENABLE_INPUT_VALIDATION = os.getenv("ENABLE_INPUT_VALIDATION", "true").lower() == "true"
REGEX_TIMEOUT = int(os.getenv("REGEX_TIMEOUT", "5"))


# ======================
# Persona Role Configuration
# ======================

# Persona role to emoji mapping
ROLE_EMOJI_MAP: Dict[str, str] = {
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

DEFAULT_ROLE = "Explorer"
DEFAULT_EMOJI = "🧭"


# ======================
# Role Templates
# ======================

ROLE_TEMPLATES: Dict[str, str] = {
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


# ======================
# Error Messages
# ======================

ERROR_MESSAGES = {
    "ollama_connection_failed": """
**Cannot connect to Ollama**

Please ensure:
1. Ollama is installed and running
   - Start it with: `ollama serve`
2. Ollama is accessible at: {url}
   - Check if the URL is correct
   - Verify the service is running on the correct port
3. At least one model is installed
   - Check with: `ollama list`
   - Install a model: `ollama pull llama2`

For more help, visit: https://ollama.ai/
""",
    "model_not_found": """
**Model not found: {model}**

Available options:
1. Check installed models: `ollama list`
2. Install the model: `ollama pull {model}`
3. Use a different installed model

Visit https://ollama.ai/library for available models.
""",
    "timeout_error": """
**Request timed out**

The AI response took too long to generate. Try:
1. Increasing the timeout in Settings
2. Using a smaller or faster model
3. Reducing the context message count
4. Checking your system resources

Current timeout: {timeout} seconds
""",
    "generation_error": """
**Error generating response**

Something went wrong during response generation:
- Check Ollama service status
- Verify the model is working: `ollama run {model}`
- Check system resources (RAM, CPU)
- Review Ollama logs for details

Technical details: {error}
"""
}
