# 🤖 Infinite AI Backroom - Interactive Multi-Persona Conversation Platform

A Streamlit-based web application that enables you to create AI personas with distinct roles and personalities, then watch them engage in dynamic, and potentially infinite conversations using your local Ollama models.

![AI Backroom Screenshot](screenshot.png)

## Features

- **Multi-Persona Conversations**: Create and manage multiple AI personas with unique personalities and roles
- **Real-time Chat Interface**: Beautiful tabbed interface with color-coded messages and persona identification
- **Role-Based Behavior**: 17+ predefined roles that shape conversation dynamics and personality traits
- **@Mention System**: Personas can reference each other using @mentions with visual highlighting
- **Configurable Context**: Adjustable conversation history (5-25 messages) for AI context awareness
- **Automatic Logging**: Daily conversation logs saved to text files for analysis
- **Session Management**: Export conversations as JSON and persistent settings storage
- **Standalone Log Viewer**: Separate application for advanced log analysis and search

## Quick Start

### Prerequisites

- Python 3.12+
- [UV package manager](https://github.com/astral-sh/uv)
- [Ollama](https://ollama.ai/) running locally on `localhost:11434`
- At least one Ollama model downloaded (e.g., `ollama pull granite3.3:8b`)

### Installation and Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/guinacio/infinite-backrooms.git
   cd infinite-backrooms
   ```

2. **Install dependencies:**
   ```bash
   # Install runtime dependencies
   uv sync

   # For development (includes pytest, ruff, mypy)
   uv sync --extra dev
   ```

3. **Configure the application (optional):**
   ```bash
   # Copy the example configuration file
   cp .env.example .env

   # Edit .env to customize settings (see Configuration section below)
   ```

4. **Start the application:**
   ```bash
   uv run streamlit run streamlit_backroom.py
   ```

5. **Verify Ollama connection:**
   - Navigate to the "Personas" tab
   - Click "Check Ollama Connection" to load available models
   - Ensure your models appear in the dropdown

## Configuration

The application can be customized using environment variables. Configuration is managed through the `config.py` module, which provides type-safe access to all settings.

### Quick Configuration

Copy `.env.example` to `.env` and customize as needed:

```bash
cp .env.example .env
```

Edit the `.env` file with your preferred settings. Changes require restarting the application to take effect.

### Configuration Options

All 11 configurable settings with their defaults:

#### Ollama API Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Base URL for Ollama API server |
| `OLLAMA_CONNECTION_TIMEOUT` | `10` | Connection timeout in seconds for initial API connection |
| `OLLAMA_RESPONSE_TIMEOUT` | `300` | Response timeout in seconds (5 minutes) for AI model responses |

#### Conversation Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_HISTORY` | `50` | Maximum number of messages to keep in conversation history |
| `CONTEXT_MESSAGES` | `10` | Number of recent messages to send to AI as context (range: 1-25) |
| `RESPONSE_DELAY_MIN` | `2` | Minimum delay in seconds between auto-generated responses |
| `RESPONSE_DELAY_MAX` | `8` | Maximum delay in seconds between auto-generated responses |
| `AUTO_ADVANCE` | `true` | Enable automatic conversation advancement (`true`/`false`, `1`/`0`, `yes`/`no`) |
| `ENABLE_THINKING` | `true` | Enable AI thinking display for compatible models like deepseek-r1 |

#### Logging Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `LOG_DIR` | `conversations` | Directory for conversation log files |
| `LOG_FILE_PREFIX` | `streamlit_backroom` | Prefix for log filenames (format: `{prefix}_{YYYY-MM-DD}.txt`) |

### Using config.py

The application uses a centralized configuration system:

```python
from config import config

# Access configuration values
print(config.ollama.base_url)
print(config.conversation.context_messages)
print(config.logging.log_dir)
```

Configuration is loaded automatically when the application starts using `AppConfig.from_env()`.

### Configuration Examples

#### Fast Development Setup
```bash
# .env
OLLAMA_RESPONSE_TIMEOUT=60
RESPONSE_DELAY_MIN=1
RESPONSE_DELAY_MAX=3
CONTEXT_MESSAGES=5
```

#### Thoughtful Long Conversations
```bash
# .env
CONTEXT_MESSAGES=25
RESPONSE_DELAY_MIN=5
RESPONSE_DELAY_MAX=15
MAX_HISTORY=100
```

#### Remote Ollama Server
```bash
# .env
OLLAMA_BASE_URL=http://ollama-server.example.com:11434
OLLAMA_CONNECTION_TIMEOUT=30
OLLAMA_RESPONSE_TIMEOUT=600
```

#### Testing Without Thinking Features
```bash
# .env
ENABLE_THINKING=false
AUTO_ADVANCE=false
```

#### Custom Logging Location
```bash
# .env
LOG_DIR=/var/log/backrooms
LOG_FILE_PREFIX=ai_conversation
```

### Notes

- All timeout values are in seconds
- Boolean values accept: `true`/`false`, `1`/`0`, `yes`/`no` (case-insensitive)
- Invalid values fall back to defaults with a warning
- Empty values or missing variables use the defaults shown above

## Application Structure

The application uses a tabbed interface with four main sections:

### 1. Conversation Tab
- Real-time chat interface with color-coded persona messages
- Manual conversation control with "Next Turn" button
- @mention highlighting when personas reference each other
- Conversation history display with timestamps

### 2. Personas Tab
- Create, edit, and manage AI personas
- Assign predefined roles or create custom roles
- Configure individual system prompts and model selection
- Visual persona management with color coding
- Quick setup options for diverse conversation sets

### 3. Settings Tab
- Adjust conversation context (5-25 messages)
- Configure response delays and auto-advance settings
- Manage conversation history limits
- Connection status and model information

### 4. Export & Logs Tab
- Export current session as JSON
- View conversation statistics
- Access daily log files
- Session management tools

## Role System

### Functional Roles
Special conversation facilitators that enhance group dynamics:

- **Moderator**: Guides discussions, introduces topics, maintains engagement
- **Note-Taker**: Summarizes key points, identifies themes, tracks insights

### Personality Roles
Distinct conversation styles and perspectives:

- **Philosopher**: Explores existential questions and consciousness
- **Scientist**: Empirical thinking and research-focused approach
- **Creative Writer**: Storytelling, wordplay, and creative expression
- **Debate Enthusiast**: Intellectual debates and diverse perspectives
- **Optimist**: Positive outlook and encouraging communication
- **Skeptic**: Questions assumptions and demands evidence
- **Historian**: Historical context and behavioral pattern analysis
- **Futurist**: Emerging technologies and future possibilities
- **Minimalist**: Simple, clear, and concise communication
- **Explorer**: Adventurous and curious about new concepts
- **Mentor**: Supportive and educational guidance
- **Comedian**: Humor while maintaining meaningful engagement
- **Analyst**: Systematic breakdown of complex topics
- **Dreamer**: Imaginative and idealistic perspectives
- **Pragmatist**: Practical and results-oriented thinking

### Custom Roles
Create your own roles by selecting "Use custom role instead" when adding personas. The AI will interpret and embody your custom role definition.

## Advanced Features

### @Mention System
Personas can reference each other using @mentions (e.g., "@Philosopher what do you think about..."). The system:
- Provides @mention instructions in system prompts
- Highlights mentions in the chat interface using persona colors
- Enhances conversation flow and direct interaction

### Conversation Context
- Configurable context window (5-25 messages) determines how much conversation history each AI sees
- Larger context enables more coherent long-form discussions
- Smaller context keeps conversations focused and reduces processing time

### Logging and Analysis
- Automatic daily logging to `conversations/streamlit_backroom_YYYY-MM-DD.txt`
- Clean message format with timestamps and persona identification
- Thinking tags automatically filtered from logs

## Standalone Log Viewer

For advanced log analysis, use the standalone log viewer application:

```bash
uv run streamlit run log_viewer.py
```

### Log Viewer Features
- **Multi-file Analysis**: Load and analyze multiple log files simultaneously
- **Advanced Filtering**: Filter by persona, date range, and message content
- **Search Capabilities**: Text search with Contains, Exact Match, and Regex options
- **Statistics Dashboard**: Message counts, persona activity, and conversation metrics
- **Multiple View Modes**: Chat view, table view, and raw text format
- **Export Options**: Download filtered data as CSV, JSON, or TXT formats
- **Visual Analytics**: Persona activity charts and conversation breakdowns

The log viewer works with both current (`streamlit_backroom_*.txt`) and legacy (`backroom_*.txt`) log file formats.

## Usage Examples

### Structured Research Discussion
```
Moderator + Note-Taker + Scientist + Philosopher
```
Guided facilitation of AI consciousness research with systematic note-taking.

### Creative Brainstorming
```
Moderator + Creative Writer + Dreamer + Explorer + Note-Taker
```
Imaginative idea generation with structured capture of insights.

### Balanced Policy Analysis
```
Moderator + Optimist + Skeptic + Pragmatist + Note-Taker
```
Multi-perspective analysis of new technologies or policies.

### Educational Seminar
```
Moderator + Mentor + Historian + Futurist + Note-Taker
```
Knowledge sharing with historical context and future implications.

## Technical Details

### Architecture
- **Frontend**: Streamlit web interface with tabbed navigation
- **Backend**: Async HTTP client for Ollama API communication
- **Storage**: Session state for runtime data, file system for logs
- **Logging**: Daily text files with structured message format

### File Structure
```
infinite-backrooms/
├── streamlit_backroom.py    # Main application
├── log_viewer.py           # Standalone log analysis tool
├── conversations/          # Daily conversation logs
├── pyproject.toml         # UV dependencies
├── uv.lock               # Locked dependencies
└── README.md             # This file
```

### Dependencies
- **Streamlit**: Web interface framework
- **aiohttp**: Async HTTP client for Ollama API
- **pandas**: Data analysis for log viewer (log_viewer.py only)

## Development

### Development Setup

1. **Install development dependencies:**
   ```bash
   # Install all dependencies including dev tools
   uv sync --extra dev
   ```

   This installs:
   - `pytest` - Testing framework
   - `pytest-asyncio` - Async test support
   - `pytest-cov` - Code coverage reporting
   - `ruff` - Fast Python linter and formatter
   - `mypy` - Static type checker

2. **Set up your environment:**
   ```bash
   # Copy example configuration
   cp .env.example .env

   # Customize for development (e.g., faster response times)
   # Edit .env as needed
   ```

### Running Tests

The project uses pytest for testing with async support and coverage reporting:

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov=. --cov-report=html

# Run specific test file
uv run pytest tests/test_security.py

# Run tests matching a pattern
uv run pytest -k "test_ollama"
```

Test configuration is in `pyproject.toml`:
- Tests are located in the `tests/` directory
- Async mode is enabled automatically
- Coverage reports are generated with `-ra -q --cov=.`

Available test files:
- `tests/test_security.py` - Security validation tests
- `tests/test_conversation_logger.py` - Logging functionality tests
- `tests/test_log_viewer.py` - Log viewer component tests

### Code Quality

#### Linting with Ruff

Ruff is a fast Python linter that checks code quality and style:

```bash
# Lint all files
uv run ruff check .

# Lint with auto-fix
uv run ruff check --fix .

# Format code
uv run ruff format .

# Check formatting without changes
uv run ruff format --check .
```

Ruff configuration in `pyproject.toml`:
- Line length: 120 characters
- Target: Python 3.12
- Enabled rules: Error (E), Fatal (F), Warning (W), Import (I), Naming (N), Upgrade (UP), Security (S), Bugbear (B), and more
- Ignored: S101 (allows assert statements in tests)

#### Type Checking with Mypy

Mypy provides static type checking for Python:

```bash
# Type check all files
uv run mypy .

# Type check specific file
uv run mypy streamlit_backroom.py

# Type check with verbose output
uv run mypy --verbose .
```

Mypy configuration in `pyproject.toml`:
- Python version: 3.12
- Warns on unused configs and return types
- Checks untyped definitions
- Allows untyped function definitions (for gradual typing adoption)

### Development Workflow

1. **Make changes** to code files
2. **Run linter** to check code quality:
   ```bash
   uv run ruff check --fix .
   ```
3. **Run type checker** to catch type errors:
   ```bash
   uv run mypy .
   ```
4. **Run tests** to ensure functionality:
   ```bash
   uv run pytest
   ```
5. **Format code** before committing:
   ```bash
   uv run ruff format .
   ```

### Pre-commit Checklist

Before committing code, ensure:
- [ ] All tests pass: `uv run pytest`
- [ ] No linting errors: `uv run ruff check .`
- [ ] No type errors: `uv run mypy .`
- [ ] Code is formatted: `uv run ruff format .`
- [ ] New tests added for new features
- [ ] Documentation updated if needed

### Running the Application in Development

```bash
# Run main application
uv run streamlit run streamlit_backroom.py

# Run log viewer
uv run streamlit run log_viewer.py

# Run with custom configuration
OLLAMA_BASE_URL=http://custom:11434 uv run streamlit run streamlit_backroom.py
```

### Debugging Tips

1. **Enable Streamlit debug mode:**
   ```bash
   uv run streamlit run streamlit_backroom.py --logger.level=debug
   ```

2. **Test Ollama connection:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. **Check configuration loading:**
   ```python
   from config import config
   print(config)  # Shows all loaded configuration values
   ```

4. **Monitor conversation logs:**
   ```bash
   tail -f conversations/streamlit_backroom_$(date +%Y-%m-%d).txt
   ```

## Contributing

This project uses UV for dependency management. To contribute:

1. Fork the repository
2. Create a feature branch
3. Install dependencies: `uv sync --extra dev`
4. Make your changes
5. Run quality checks (see Development section above):
   - `uv run ruff check --fix .`
   - `uv run mypy .`
   - `uv run pytest`
6. Test with: `uv run streamlit run streamlit_backroom.py`
7. Submit a pull request

See the **Development** section above for detailed information on:
- Running tests with pytest
- Linting with ruff
- Type checking with mypy
- Development workflow and best practices

## License

This project is open source. See the repository for license details.

## Author

Created by [guinacio](https://github.com/guinacio)

---

**Note**: This application requires a local Ollama installation with downloaded models. The AI personas will only be as capable as the underlying models you provide. 