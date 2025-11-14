# 🤖 Infinite AI Backroom - Interactive Multi-Persona Conversation Platform

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

A Streamlit-based web application that enables you to create AI personas with distinct roles and personalities, then watch them engage in dynamic, and potentially infinite conversations using your local Ollama models.

**✨ New Features (v0.1.4):**
- 📚 **Interactive tutorial** - First-run onboarding for new users
- ⌨️ **Keyboard shortcuts** - Quick navigation (`?` for help, `Ctrl+K` for chat)
- 🚀 **Performance optimizations** - 30-50% faster with session caching
- 📄 **Message pagination** - Handle 1,000+ messages smoothly
- 🧪 **Comprehensive test suite** - 191 tests, 56% coverage
- 📖 **Complete documentation** - Architecture, API, Security Audit
- 🔒 **Security audit** - Grade A-, OWASP Top 10 compliant
- 🎯 **CI/CD workflows** - Automated testing and quality checks

## 🔒 Security Notice

**This application is designed for local, single-user environments.**

✅ Safe for: Local development, personal AI experimentation, trusted networks
⚠️ Not safe for: Public deployment without authentication and access controls

The application includes comprehensive input validation and injection protection, but lacks authentication by design. See [SECURITY_AUDIT.md](SECURITY_AUDIT.md) for details.

![AI Backroom Screenshot](screenshot.png)

## Features

- **Multi-Persona Conversations**: Create and manage multiple AI personas with unique personalities and roles
- **Interactive Tutorial**: 4-step guided onboarding for new users with restart option
- **Keyboard Shortcuts**: Navigate faster with `?` (help), `Ctrl/Cmd+K` (focus chat), `Esc` (blur)
- **Real-time Chat Interface**: Beautiful tabbed interface with color-coded messages and persona identification
- **Role-Based Behavior**: 17 predefined roles that shape conversation dynamics and personality traits
- **@Mention System**: Personas can reference each other using @mentions with visual highlighting
- **Configurable Context**: Adjustable conversation history (1-50 messages) for AI context awareness
- **Message Pagination**: Smooth handling of 1,000+ messages with 50 messages per page
- **Performance Optimized**: Session-based caching for 30-50% faster conversation generation
- **Quick-Load Presets**: Instantly load diverse or structured conversation sets
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
   uv sync
   ```

3. **Start the application:**
   ```bash
   uv run streamlit run streamlit_backroom.py
   ```

4. **Verify Ollama connection:**
   - Navigate to the "Personas" tab
   - Click "Check Ollama Connection" to load available models
   - Ensure your models appear in the dropdown

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
- Adjust conversation context (1-50 messages)
- Configure response delays and auto-advance settings
- Manage conversation history limits (10-200 messages)
- Enable/disable thinking mode for compatible models
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
- Configurable context window (1-50 messages) determines how much conversation history each AI sees
- Larger context enables more coherent long-form discussions
- Smaller context keeps conversations focused and reduces processing time
- Optimal range: 10-20 messages for most conversations

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

### Running Tests

```bash
# Recommended: Use the test script for best experience
./scripts/test.sh              # Run unit tests with coverage (default)
./scripts/test.sh unit          # Run unit tests only
./scripts/test.sh all           # Run ALL tests (requires Ollama)
./scripts/test.sh fast          # Quick unit tests (no coverage)
./scripts/test.sh coverage      # Detailed coverage report

# Or run pytest directly
uv run pytest tests/ -v -k "not real and not Real"  # Unit tests only
uv run pytest tests/ --cov --cov-report=html         # All tests with coverage

# Run specific test file
uv run pytest tests/test_ollama_client.py -v

# View coverage report
open htmlcov/index.html
```

**Note:** Integration tests require a running Ollama server on `localhost:11434`. Use `-k "not real and not Real"` to skip integration tests if Ollama is not available.

### Code Quality

```bash
# Format code
uv run black .

# Lint code
uv run ruff check .

# Type check
uv run mypy .

# Security scan
uv run bandit -r .

# All quality checks
uv run ruff check . && uv run black --check . && uv run mypy . && uv run pytest --cov
```

### Project Structure

```
infinite-backrooms/
├── src/                    # Modular source code
│   ├── models/             # Data models (AIPersona)
│   ├── services/           # Services (OllamaClient, Logger)
│   ├── ui/                 # UI components
│   └── utils/              # Utilities and constants
├── tests/                  # Comprehensive test suite
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md     # System architecture
│   ├── API.md              # API reference
│   └── DEVELOPMENT.md      # Development guide
├── scripts/                # Utility scripts
└── .github/workflows/      # CI/CD pipelines
```

## Documentation

- **[AI Assistant Guide (CLAUDE.md)](CLAUDE.md)** - Comprehensive guide for AI assistants and developers
- **[Security Audit (SECURITY_AUDIT.md)](SECURITY_AUDIT.md)** - Comprehensive security review (Grade A-)
- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design and architecture
- **[API Reference](docs/API.md)** - Complete API documentation
- **[Development Guide](docs/DEVELOPMENT.md)** - Setup and development workflow
- **[Contributing Guidelines](CONTRIBUTING.md)** - How to contribute
- **[Changelog](CHANGELOG.md)** - Project history and changes

## Contributing

We welcome contributions! This project uses UV for dependency management.

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Install dependencies: `uv sync --dev`
4. Make your changes
5. Run tests: `./scripts/test.sh` or `uv run pytest tests/ -v -k "not real and not Real"`
6. Format code: `uv run black .`
7. Lint code: `uv run ruff check .`
8. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines including:
- Code of Conduct
- Development workflow
- Code standards
- Commit message format
- Review process

## Testing

This project has a comprehensive test suite with **191 passing unit tests** and **56.27% code coverage**:

- ✅ **191 unit tests** for all core components (100% passing)
- ✅ **29 integration tests** (require Ollama server)
- ✅ **Performance benchmarks** (persona creation, logging, caching)
- ✅ **Security tests** (input validation, injection protection)
- ✅ Async tests for OllamaClient
- ✅ Mock fixtures for testing
- ✅ HTML coverage reports
- ✅ CI/CD integration

Run `./scripts/test.sh` or `uv run pytest tests/ -v -k "not real and not Real"` to see all unit tests.

**Coverage by Module:**
- UI Components: 100%
- Input Validation: 100%
- UI Wrappers: 100%
- Persona Models: 100%
- Overall: 56.27%

## Security

Security is important to us. If you discover a security vulnerability:

1. **Do not** open a public issue
2. Email the maintainers directly
3. Provide detailed information about the vulnerability
4. Allow time for a fix before public disclosure

We run automated security scans:
- **Bandit** for code security issues
- **Safety** for dependency vulnerabilities
- **CodeQL** for additional analysis

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Created by [guinacio](https://github.com/guinacio)

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [Ollama](https://ollama.ai/)
- Managed with [UV](https://github.com/astral-sh/uv)

---

**Note**: This application requires a local Ollama installation with downloaded models. The AI personas will only be as capable as the underlying models you provide.

**Status**: Active development 🚧 | [Report Issues](https://github.com/guinacio/infinite-backrooms/issues) | [Discussions](https://github.com/guinacio/infinite-backrooms/discussions) 