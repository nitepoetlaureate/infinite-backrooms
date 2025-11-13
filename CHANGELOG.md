# Changelog

All notable changes to the Infinite AI Backrooms project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive test suite with pytest
  - Unit tests for AIPersona dataclass
  - Unit tests for ConversationLogger
  - Unit tests for OllamaClient (async tests)
  - Mock fixtures for testing
  - Test coverage configuration (80%+ goal)
- Full documentation suite
  - ARCHITECTURE.md - System design and architecture
  - API.md - Complete API reference
  - DEVELOPMENT.md - Development setup and workflow
  - CONTRIBUTING.md - Contribution guidelines
  - This CHANGELOG.md
- pytest configuration in pyproject.toml
  - Coverage reporting (HTML, XML, terminal)
  - Async test support
  - Test markers (unit, integration, slow)
- Enhanced pyproject.toml configuration
  - Project URLs (homepage, repository, issues)
  - Build system configuration
  - Ruff linting rules
  - Black formatting rules
  - Mypy type checking rules
  - Bandit security scanning configuration
- Development dependencies
  - bandit for security scanning
  - safety for dependency vulnerability checking
- Environment variable support via python-dotenv
  - .env.example template
  - Configuration via environment variables

### Changed
- Updated pyproject.toml metadata
  - Changed project name from "code-test" to "infinite-backrooms"
  - Added proper project description
  - Added author information
  - Added license declaration (MIT)
  - Updated Streamlit version requirement (1.28.0 → 1.39.0)
- Enhanced test coverage configuration
  - Changed coverage source from ["src"] to ["."] to match current structure
  - Added branch coverage
  - Expanded omit patterns
  - Enhanced exclude_lines for better coverage reporting
- Improved pyproject.toml organization
  - Added project.urls section
  - Added build-system section
  - Enhanced tool configurations

### Fixed
- pyproject.toml dependency issues (addressed by Team 1)
  - Removed built-in modules: asyncio, pathlib, dataclasses
  - Removed unused requests dependency
  - Aligned all dependencies properly

### Removed
- Invalid dependencies from pyproject.toml
  - asyncio (built-in module)
  - pathlib (built-in module)
  - dataclasses (built-in module)
  - requests (unused)

## [0.1.0] - 2024-11-12

### Added
- Initial release of Infinite AI Backrooms
- Multi-persona conversation platform
- Streamlit-based web interface
- Local Ollama integration
- 17+ predefined persona roles
- @mention system for directed conversation
- Automatic conversation logging
- Daily log file rotation
- Conversation export to JSON
- Standalone log viewer application
- Real-time streaming responses
- Configurable context window (5-25 messages)
- Temperature and model parameter configuration
- Auto-run mode for autonomous conversations
- Color-coded persona messages
- Session state management
- Thinking tag filtering in logs

### Core Features
- **AIPersona dataclass**: Persona configuration and management
- **OllamaClient**: Async HTTP client for Ollama API
  - Connection testing
  - Streaming response generation
  - Timeout management
- **ConversationLogger**: Daily log file management
  - Automatic directory creation
  - Message cleaning (removes thinking tags)
  - UTF-8 encoding support

### UI Components
- **Conversation Tab**: Real-time chat display
- **Personas Tab**: Persona management interface
- **Settings Tab**: Configuration options
- **Export & Logs Tab**: Export and log access

### Documentation
- Comprehensive README.md
- Installation instructions
- Usage examples
- Role system documentation

### Development
- UV package manager support
- uv.lock for dependency locking
- Basic project structure

---

## Release Categories

### Added
- New features, capabilities, or enhancements

### Changed
- Changes to existing functionality or behavior

### Deprecated
- Features that will be removed in future releases

### Removed
- Features or functionality that have been removed

### Fixed
- Bug fixes and error corrections

### Security
- Security improvements and vulnerability fixes

---

## Version History

- **[Unreleased]**: Current development version
- **[0.1.0]**: Initial release (2024-11-12)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute to this project.

---

**Changelog Format:** [Keep a Changelog](https://keepachangelog.com/)
**Versioning:** [Semantic Versioning](https://semver.org/)
