# API Documentation

This document provides comprehensive documentation of all public APIs, classes, and functions in the Infinite AI Backrooms application.

## Table of Contents

- [OllamaClient](#ollamaclient)
- [ConversationLogger](#conversationlogger)
- [AIPersona](#aipersona)
- [Helper Functions](#helper-functions)
- [Constants](#constants)

---

## OllamaClient

Client for interacting with the Ollama API server.

### Class Definition

```python
class OllamaClient:
    """Client for interacting with Ollama API"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        """Initialize the Ollama client.

        Args:
            base_url: Base URL for Ollama API server (default: "http://localhost:11434")
        """
```

### Methods

#### test_connection

```python
async def test_connection(self) -> tuple[bool, List[str]]:
    """Test if Ollama API is accessible and return available models.

    Returns:
        Tuple containing:
            - bool: True if connection successful, False otherwise
            - List[str]: List of available model names

    Raises:
        None: All exceptions are caught and returned as (False, [])

    Example:
        >>> client = OllamaClient()
        >>> success, models = await client.test_connection()
        >>> if success:
        ...     print(f"Available models: {models}")
        ... else:
        ...     print("Connection failed")
    """
```

**Error Handling:**
- `aiohttp.ClientError`: Network errors, connection refused
- `asyncio.TimeoutError`: Request timeout (10 seconds)
- `json.JSONDecodeError`: Invalid API response
- HTTP errors: Non-200 status codes

**Response Format:**
```python
# Success
(True, ["llama2:latest", "mistral:7b", "granite3.3:8b"])

# Failure
(False, [])
```

#### generate_stream

```python
async def generate_stream(
    self,
    model: str,
    prompt: str,
    context: List[int] = None,
    system_prompt: str = "",
    temperature: float = 0.7,
    timeout: float = 300.0
) -> AsyncGenerator[Dict[str, Any], None]:
    """Generate streaming response from Ollama model.

    Args:
        model: Ollama model name (e.g., "llama2:latest")
        prompt: User prompt or message
        context: Optional context from previous responses
        system_prompt: Optional system prompt to guide model behavior
        temperature: Sampling temperature (0.0-2.0, default 0.7)
        timeout: Response timeout in seconds (default 300)

    Yields:
        Dict containing response chunks with keys:
            - response: str - Generated text chunk
            - done: bool - Whether generation is complete
            - context: List[int] - Context for next request (when done=True)

    Raises:
        aiohttp.ClientError: Network or connection errors
        asyncio.TimeoutError: Request timeout exceeded
        json.JSONDecodeError: Malformed API response

    Example:
        >>> client = OllamaClient()
        >>> full_response = ""
        >>> async for chunk in client.generate_stream(
        ...     model="llama2:latest",
        ...     prompt="Hello, how are you?",
        ...     system_prompt="You are a friendly assistant."
        ... ):
        ...     if not chunk.get("done"):
        ...         full_response += chunk.get("response", "")
        >>> print(full_response)
    """
```

**Request Format:**
```python
{
    "model": "llama2:latest",
    "prompt": "User message here",
    "system": "You are a helpful assistant",
    "context": [1, 2, 3, ...],  # Optional
    "stream": True,
    "options": {
        "temperature": 0.7
    }
}
```

**Response Stream Format:**
```python
# Streaming chunks
{"response": "Hello", "done": False}
{"response": " there", "done": False}
{"response": "!", "done": False}

# Final chunk
{
    "response": "",
    "done": True,
    "context": [1, 2, 3, ...],
    "total_duration": 1234567890,
    "load_duration": 123456789,
    "prompt_eval_count": 10,
    "eval_count": 50
}
```

---

## ConversationLogger

Handles logging conversations to daily text files.

### Class Definition

```python
class ConversationLogger:
    """Handles logging conversations to daily TXT files"""

    def __init__(self, log_dir: str = "conversations"):
        """Initialize the conversation logger.

        Args:
            log_dir: Directory for storing log files (default: "conversations")

        Side Effects:
            Creates log_dir if it doesn't exist
        """
```

### Methods

#### get_daily_log_file

```python
def get_daily_log_file(self) -> Path:
    """Get the log file path for today.

    Returns:
        Path: Path object for today's log file

    Format:
        streamlit_backroom_YYYY-MM-DD.txt

    Example:
        >>> logger = ConversationLogger()
        >>> log_file = logger.get_daily_log_file()
        >>> print(log_file)
        conversations/streamlit_backroom_2024-11-13.txt
    """
```

#### clean_message

```python
def clean_message(self, message: str) -> str:
    """Remove thinking tags and clean up message formatting.

    Removes:
        - <think>...</think> blocks (including nested)
        - Extra whitespace
        - Leading/trailing whitespace

    Args:
        message: Raw message text

    Returns:
        str: Cleaned message text

    Example:
        >>> logger = ConversationLogger()
        >>> raw = "Here is my thought: <think>internal reasoning</think> Final answer."
        >>> clean = logger.clean_message(raw)
        >>> print(clean)
        'Here is my thought: Final answer.'
    """
```

#### log_message

```python
def log_message(
    self,
    persona: str,
    message: str,
    timestamp: datetime = None
) -> None:
    """Log a message to today's log file.

    Args:
        persona: Name of the persona/speaker
        message: Message content (will be cleaned)
        timestamp: Optional timestamp (default: current time)

    Side Effects:
        - Creates log file if it doesn't exist
        - Appends cleaned message to log file
        - Skips logging if message is empty after cleaning

    Format:
        [HH:MM:SS] PersonaName$ Message content

    Example:
        >>> logger = ConversationLogger()
        >>> logger.log_message("Alice", "Hello everyone!")
        # Writes: [14:30:45] Alice$ Hello everyone!
    """
```

---

## AIPersona

Dataclass representing an AI persona with configuration.

### Class Definition

```python
@dataclass
class AIPersona:
    """Represents an AI instance with detailed configuration"""

    id: str              # Unique identifier (UUID)
    name: str            # Display name
    model: str           # Ollama model name
    role: str = ""       # Optional role (e.g., "analyst", "creative")
    system_prompt: str = ""  # Custom system instructions
    color: str = "#1f77b4"   # Hex color for UI display
    enabled: bool = True     # Whether persona participates
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | str | (required) | Unique identifier, typically UUID |
| `name` | str | (required) | Display name for the persona |
| `model` | str | (required) | Ollama model name (e.g., "llama2:latest") |
| `role` | str | `""` | Predefined role or custom role |
| `system_prompt` | str | `""` | System instructions for the AI |
| `color` | str | `"#1f77b4"` | Hex color code for UI |
| `enabled` | bool | `True` | Whether persona is active |

### Usage Examples

```python
from dataclasses import asdict
import uuid

# Create a new persona
persona = AIPersona(
    id=str(uuid.uuid4()),
    name="Socrates",
    model="llama2:latest",
    role="philosopher",
    system_prompt="You are Socrates, asking probing questions to explore ideas.",
    color="#9B59B6",
    enabled=True
)

# Access fields
print(persona.name)  # "Socrates"
print(persona.role)  # "philosopher"

# Convert to dictionary (for JSON export)
persona_dict = asdict(persona)

# Disable a persona
persona.enabled = False

# Check if two personas are the same
persona1 == persona2  # Compares all fields
```

---

## Helper Functions

### get_next_speaker

```python
def get_next_speaker(
    personas: List[AIPersona],
    history: List[Dict[str, str]],
    current_speaker: Optional[str]
) -> str:
    """Determine the next speaker in the conversation.

    Selection Logic:
        1. Check for @mentions in last message
        2. Use round-robin rotation if no mentions
        3. Random selection as fallback

    Args:
        personas: List of available personas
        history: Conversation history (list of messages)
        current_speaker: Name of the current speaker (optional)

    Returns:
        str: Name of the next persona to speak

    Raises:
        ValueError: If personas list is empty

    Example:
        >>> personas = [persona1, persona2, persona3]
        >>> history = [
        ...     {"speaker": "Alice", "message": "@Bob what do you think?"}
        ... ]
        >>> next_speaker = get_next_speaker(personas, history, "Alice")
        >>> print(next_speaker)
        'Bob'
    """
```

### extract_mentions

```python
def extract_mentions(message: str) -> List[str]:
    """Extract @mentions from a message.

    Args:
        message: Message text to parse

    Returns:
        List[str]: List of mentioned names (without @ symbol)

    Example:
        >>> mentions = extract_mentions("Hey @Alice and @Bob, what do you think?")
        >>> print(mentions)
        ['Alice', 'Bob']
    """
```

### highlight_mentions

```python
def highlight_mentions(
    message: str,
    personas: List[AIPersona]
) -> str:
    """Highlight @mentions with persona colors in HTML.

    Args:
        message: Message text
        personas: List of personas to match mentions against

    Returns:
        str: HTML string with highlighted mentions

    Example:
        >>> highlighted = highlight_mentions("@Alice is right!", personas)
        >>> print(highlighted)
        '<span style="color: #FF5733">@Alice</span> is right!'
    """
```

### format_conversation_context

```python
def format_conversation_context(
    history: List[Dict[str, str]],
    max_messages: int = 10
) -> List[Dict[str, str]]:
    """Format conversation history for LLM context.

    Args:
        history: Full conversation history
        max_messages: Maximum number of messages to include

    Returns:
        List[Dict[str, str]]: Formatted messages for LLM

    Format:
        [
            {"role": "assistant", "content": "..."},
            {"role": "assistant", "content": "..."}
        ]

    Example:
        >>> context = format_conversation_context(history, max_messages=5)
        >>> print(len(context))
        5
    """
```

---

## Constants

### Role Emoji Map

```python
ROLE_EMOJI_MAP: Dict[str, str] = {
    "explorer": "🧭",
    "analyst": "📊",
    "creative": "🎨",
    "critic": "🔍",
    "mediator": "⚖️",
    "optimist": "🌟",
    "pessimist": "⚠️",
    "scientist": "🔬",
    "philosopher": "🤔",
    "comedian": "😄",
    "historian": "📜",
    "futurist": "🔮",
    "devil's advocate": "😈",
    "pragmatist": "🔧",
    "visionary": "👁️",
    "skeptic": "🤨",
    "mentor": "👨‍🏫",
    "student": "📚"
}
```

### Role Templates

Predefined system prompts for each role:

```python
ROLE_TEMPLATES: Dict[str, str] = {
    "explorer": "You are an adventurous explorer, always curious and eager to discover new ideas.",
    "analyst": "You are a data-driven analyst who examines information critically and systematically.",
    "creative": "You are a creative thinker who generates innovative ideas and unique perspectives.",
    # ... etc
}
```

### Configuration Constants

```python
# Ollama
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_TIMEOUT = 120.0
DEFAULT_RESPONSE_TIMEOUT = 300.0

# Logging
LOG_DIRECTORY = "conversations"
LOG_FILE_PREFIX = "streamlit_backroom"

# UI
MIN_CONTEXT_MESSAGES = 1
MAX_CONTEXT_MESSAGES = 50
DEFAULT_CONTEXT_MESSAGES = 10

MIN_TEMPERATURE = 0.0
MAX_TEMPERATURE = 2.0
DEFAULT_TEMPERATURE = 0.7
```

---

## Error Codes and Messages

### Common Error Responses

| Error | Code | Message | Resolution |
|-------|------|---------|------------|
| Connection Failed | `CONN_FAIL` | "Cannot connect to Ollama" | Check Ollama server status |
| Model Not Found | `MODEL_404` | "Model not available" | Pull model with `ollama pull` |
| Timeout | `TIMEOUT` | "Request timeout exceeded" | Increase timeout or check server |
| Invalid Input | `INVALID` | "Invalid input parameters" | Check parameter formats |

---

## WebSocket Events (Future)

*Reserved for future real-time communication features*

---

## Rate Limiting (Future)

*Reserved for future rate limiting features*

---

## Deprecation Notices

None at this time.

---

**Last Updated:** 2024-11-13
**API Version:** 0.1.0
