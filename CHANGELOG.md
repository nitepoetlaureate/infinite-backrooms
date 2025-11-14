# Changelog

All notable changes to the Infinite AI Backrooms project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2025-11-14

### Added - Phase 1: Critical Blockers Completed
- Test runner script (`scripts/test.sh`) with multiple modes
  - Unit tests only mode
  - Fast mode (no coverage)
  - Full test suite mode
  - Coverage reporting mode
- UI module structure created
  - `src/ui/persona_ui.py` - Persona management wrapper
  - `src/ui/conversation_ui.py` - Conversation display wrapper
  - `src/ui/settings_ui.py` - Settings and export wrapper
  - Architecture ready for future detailed refactoring

### Changed - Phase 1: Test Environment & CI/CD
- Updated GitHub Actions CI workflow (`.github/workflows/ci.yml`)
  - All commands now use `uv run` for proper environment isolation
  - Tests explicitly skip integration tests that require Ollama
  - Added `-k "not real and not Real"` filter to all test commands
- Updated README.md test instructions
  - Added detailed testing guide with script usage
  - Clarified distinction between unit and integration tests
  - Added note about Ollama requirement for integration tests
- Updated contribution guide with correct test commands

### Fixed - Phase 1: Critical Issues
- **Log viewer file pattern mismatch** (`log_viewer.py:27-31`)
  - Added `streamlit_backroom_*.txt` pattern to match current logger output
  - Maintained backward compatibility with legacy patterns
  - Fixed issue where new logs wouldn't display in viewer
- **Test environment configuration**
  - CI/CD now properly uses virtual environment via `uv run`
  - Local development has convenient test script
  - All 132 unit tests passing ✅

### Documentation - Phase 1: Accuracy Improvements
- **README.md**
  - Fixed context window claim: "5-25 messages" → "1-50 messages" (accurate)
  - Fixed role count claim: "17+ predefined roles" → "17 predefined roles" (precise)
  - Updated test commands throughout
- **ARCHITECTURE.md**
  - Fixed context window documentation to match implementation
  - Fixed role count documentation
  - Added quick start preset options to feature list
- **Verified JSON export feature exists** (lines 1376-1388 in streamlit_backroom.py)
  - Exports session data, personas, and conversation history
  - Feature was already implemented, documentation was accurate

### Testing
- All 132 unit tests passing ✅
- 29 integration tests skipped (require Ollama server)
- Test coverage: ~48% (focus on business logic)
- Zero test failures in unit test suite

## [0.1.0] - Previous Release

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
