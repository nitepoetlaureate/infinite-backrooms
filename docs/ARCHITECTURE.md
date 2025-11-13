# Architecture Documentation

## Overview

Infinite AI Backrooms is an interactive multi-persona AI conversation platform that enables users to create and manage multiple AI personas with distinct roles and personalities, then watch them engage in dynamic, autonomous conversations using local Ollama models.

### Technology Stack

- **Frontend**: Streamlit web framework (Python-based)
- **Backend**: Async Python with aiohttp for HTTP communication
- **LLM Provider**: Local Ollama models (supports any Ollama-compatible model)
- **Storage**: File system for conversation logs, session state for runtime data
- **Data Format**: JSON for exports, TXT for human-readable logs

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Web UI                         │
│  ┌─────────────┬──────────────┬─────────────┬─────────────┐ │
│  │Conversation │   Personas   │  Settings   │Export & Logs│ │
│  │    Tab      │     Tab      │    Tab      │     Tab     │ │
│  └─────────────┴──────────────┴─────────────┴─────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Application State (Session)                     │
│  • Personas List    • Conversation History                   │
│  • Turn Count       • Settings & Configuration               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  Service Layer                               │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │  OllamaClient        │  │ ConversationLogger   │        │
│  │  • test_connection() │  │ • log_message()      │        │
│  │  • generate_stream() │  │ • clean_message()    │        │
│  └──────────────────────┘  └──────────────────────┘        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              External Services & Storage                     │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │  Ollama API Server   │  │ File System          │        │
│  │  localhost:11434     │  │ conversations/       │        │
│  └──────────────────────┘  └──────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. UI Layer

The UI is built with Streamlit and organized into tabbed sections:

#### Conversation Tab
- Displays real-time conversation flow
- Color-coded messages by persona
- @mention highlighting
- Manual control with "Next Turn" button
- Auto-run mode for continuous conversation

#### Personas Tab
- Persona management interface
- Create, edit, delete personas
- Role selection (17+ predefined roles)
- System prompt customization
- Model assignment per persona
- Visual color coding

#### Settings Tab
- Ollama connection configuration
- Context window size (5-25 messages)
- Temperature and other model parameters
- Response timeout configuration

#### Export & Logs Tab
- Export conversation as JSON
- View conversation statistics
- Access daily log files
- Session management

### 2. Model Layer

#### AIPersona Dataclass

```python
@dataclass
class AIPersona:
    id: str              # Unique identifier
    name: str            # Display name
    model: str           # Ollama model name
    role: str            # Persona role (e.g., "analyst", "creative")
    system_prompt: str   # Customized system instructions
    color: str           # Hex color for UI display
    enabled: bool        # Whether persona participates
```

**Responsibilities:**
- Encapsulates persona configuration
- Provides immutable persona identity
- Enables serialization for export/import

### 3. Service Layer

#### OllamaClient

Manages all communication with the Ollama API server.

**Key Methods:**
- `test_connection() -> tuple[bool, List[str]]`: Verifies API availability and retrieves model list
- `generate_stream(model, prompt, context, system_prompt) -> AsyncGenerator`: Streams LLM responses

**Features:**
- Async/await pattern for non-blocking I/O
- Streaming response handling
- Connection pooling
- Timeout management
- Error recovery

#### ConversationLogger

Handles persistent logging of conversations to daily text files.

**Key Methods:**
- `get_daily_log_file() -> Path`: Returns path to today's log file
- `log_message(persona, message, timestamp)`: Appends message to log
- `clean_message(message) -> str`: Removes thinking tags and cleans formatting

**Features:**
- Daily log rotation (one file per day)
- Automatic directory creation
- Thinking tag removal (`<think>...</think>`)
- UTF-8 encoding for unicode support
- Timestamped entries

### 4. Conversation Management

#### Turn-Based Flow

1. **Speaker Selection**: Determines next speaker based on:
   - @mentions in previous message (direct addressing)
   - Round-robin rotation (fair distribution)
   - Random selection (fallback)

2. **Context Building**: Assembles conversation history:
   - Filters last N messages (configurable, default 10)
   - Formats as role-based chat history
   - Includes system prompts

3. **Response Generation**:
   - Async streaming from Ollama
   - Real-time UI updates
   - Thinking tag handling
   - Token-by-token display

4. **Logging & Storage**:
   - Append to session history
   - Write to daily log file
   - Update UI display

#### Auto-Run Mode

Autonomous conversation mode that:
- Continuously generates turns without user intervention
- Can be paused/resumed
- Respects configurable delays between turns
- Includes safety limits (max turns)

## Data Flow

### Message Flow Diagram

```
User Input / Auto-Run Trigger
          ↓
    Speaker Selection
    (get_next_speaker)
          ↓
    Build Context
    (last N messages)
          ↓
    OllamaClient.generate_stream()
          ↓
    Ollama API Server
    (local inference)
          ↓
    Stream Response Tokens
          ↓
    ┌─────────────┬─────────────┐
    ↓             ↓             ↓
Update UI    Log to File   Store in Session
(Streamlit)  (ConversationLogger)  (History)
```

### State Management

Streamlit session state manages runtime data:

```python
st.session_state = {
    "personas": List[AIPersona],
    "conversation_history": List[Dict],
    "turn_count": int,
    "auto_mode": bool,
    "ollama_url": str,
    "available_models": List[str],
    "context_messages": int,
    "temperature": float,
    # ... additional settings
}
```

**State Lifecycle:**
1. Initialize on first load
2. Persist across page reruns
3. Modified by user interactions
4. Cleared on session reset

## Session Management

### Session Lifecycle

1. **Initialization**
   - Check if session is initialized
   - Set default values
   - Load saved settings (if available)

2. **Runtime**
   - Handle user interactions
   - Manage personas
   - Process conversations
   - Update state

3. **Export/Import**
   - Export: Serialize personas and history to JSON
   - Import: Load personas from JSON file

4. **Reset**
   - Clear conversation history
   - Reset turn count
   - Preserve personas and settings

## Error Handling Strategy

### Connection Errors

**Ollama API Unreachable:**
- Catch: `aiohttp.ClientError`, `asyncio.TimeoutError`
- Response: User-friendly error message with troubleshooting steps
- Recovery: Allow retry, show connection status

**Model Not Found:**
- Catch: HTTP 404 from Ollama API
- Response: Display available models, suggest alternatives
- Recovery: Allow model reselection

### Generation Errors

**Timeout:**
- Configurable timeout (default: 120s, response: 300s)
- Graceful degradation
- Allow cancellation

**Malformed Response:**
- JSON parsing errors
- Partial response handling
- Fallback to error message

### Resource Management

**Async Session Cleanup:**
- Proper `async with` context managers
- Session closure on completion
- Connector cleanup
- Event loop management

**File System Errors:**
- Directory creation failures
- Write permission issues
- Disk space checks

### User Input Validation

**Persona Creation:**
- Name validation (non-empty, length limits)
- Model name validation
- System prompt sanitization

**Settings:**
- Range validation (context size, temperature)
- URL format validation
- Numeric input validation

## Performance Considerations

### Optimization Strategies

1. **Streamlit Caching**
   - Cache role emoji mappings
   - Cache role templates
   - Cache persona lookups

2. **Message Rendering**
   - Pagination for long conversations
   - Virtual scrolling for history
   - Efficient persona lookups (dict vs list iteration)

3. **Async Operations**
   - Non-blocking I/O for API calls
   - Concurrent connection testing
   - Background logging

4. **Resource Limits**
   - Maximum conversation history
   - Context window limits
   - Auto-run turn limits

### Scalability

**Current Limitations:**
- Single-user web app (no multi-tenancy)
- In-memory session storage (no database)
- Local Ollama instance (no distributed inference)

**Potential Improvements:**
- Database for persistent storage
- Distributed Ollama cluster support
- WebSocket for real-time updates
- Multi-user support with authentication

## Security Considerations

### Input Validation
- Sanitize all user inputs
- Prevent path traversal in log filenames
- Validate model names and URLs
- Limit string lengths

### API Security
- Support HTTPS for remote Ollama instances
- SSL certificate validation
- Timeout protection
- Rate limiting (future enhancement)

### Data Privacy
- All data stays local (no external APIs)
- Conversation logs stored locally
- No telemetry or analytics
- User controls data export/deletion

## Extension Points

### Adding New Features

1. **New Persona Roles**
   - Add to role emoji map
   - Add role template
   - No code changes required

2. **Custom Model Parameters**
   - Extend AIPersona dataclass
   - Update UI for parameter input
   - Pass to OllamaClient

3. **Alternative LLM Providers**
   - Implement provider-specific client
   - Implement same interface as OllamaClient
   - Swap in settings

4. **Enhanced Logging**
   - Extend ConversationLogger
   - Add structured logging
   - Database persistence

## Testing Strategy

### Unit Tests
- OllamaClient methods (mocked API)
- ConversationLogger file operations
- AIPersona dataclass
- Helper functions
- Validation functions

### Integration Tests
- Full conversation flow
- Logging pipeline
- UI interactions (via Streamlit testing)

### Performance Tests
- Large conversation handling
- Long-running auto-run mode
- Resource cleanup verification

## Deployment

### Local Development
```bash
uv sync
uv run streamlit run streamlit_backroom.py
```

### Production Considerations
- Run behind reverse proxy (nginx, caddy)
- Use process manager (systemd, supervisor)
- Set resource limits
- Configure firewall
- Monitor Ollama server health

## Future Architecture Enhancements

1. **Microservices Architecture**
   - Separate UI and backend services
   - API-first design
   - Containerization (Docker)

2. **Database Layer**
   - PostgreSQL for structured data
   - Vector database for embeddings
   - Full-text search

3. **Real-time Communication**
   - WebSocket for live updates
   - Server-sent events
   - Pub/sub messaging

4. **Scalability**
   - Horizontal scaling
   - Load balancing
   - Distributed caching
   - Queue-based processing

---

**Last Updated:** 2024-11-13
**Version:** 0.1.0
