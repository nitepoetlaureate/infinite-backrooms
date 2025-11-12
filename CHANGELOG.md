# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive type hints for all functions and methods
- Configuration module (`config.py`) with environment variable support
- Environment variable configuration for Ollama API settings
- Environment variable configuration for conversation settings
- Environment variable configuration for logging settings
- CI/CD pipeline with GitHub Actions
- Comprehensive test suite (50+ tests)
- Security tests for XSS prevention
- Tests for ConversationLogger functionality
- Tests for LogParser functionality
- LICENSE file (MIT)
- SECURITY.md with vulnerability reporting guidelines
- CONTRIBUTING.md with development guidelines
- Project metadata in pyproject.toml

### Fixed
- **[CRITICAL SECURITY]** XSS vulnerability in HTML rendering (4 locations)
- Bare except clause in log_viewer.py
- File I/O operations now have proper error handling
- Removed unused imports (os, threading, ThreadPoolExecutor, glob)

### Changed
- Extracted `ROLE_EMOJI_MAP` to module-level constant (eliminated 4 duplicates)
- Updated dependencies: removed stdlib modules (asyncio, pathlib, dataclasses)
- All hardcoded configuration values now use centralized config system
- Ollama client now uses configurable timeouts
- ConversationLogger now uses configurable log directory and file prefix

### Removed
- Incorrect dependencies from requirements.txt and pyproject.toml

## [0.1.0] - 2025-01-XX

### Added
- Initial release
- Multi-persona AI conversation platform
- Streamlit web interface
- Ollama API integration
- 17+ predefined personality roles
- @mention system for persona interactions
- Automatic conversation logging
- Log viewer application
- Session export functionality
- Real-time streaming responses
- Thinking display for compatible models

### Features
- Create and manage multiple AI personas
- Configurable conversation context
- Auto-advance conversation mode
- Manual conversation control
- Color-coded persona messages
- Daily log files with timestamps
- Advanced log analysis and search
- Export conversations as JSON

---

## Migration Guide

### Upgrading to Unreleased Version

#### Environment Variables

You can now configure the application using environment variables:

**Ollama Configuration:**
```bash
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_CONNECTION_TIMEOUT=10
export OLLAMA_RESPONSE_TIMEOUT=300
```

**Conversation Configuration:**
```bash
export MAX_HISTORY=50
export CONTEXT_MESSAGES=10
export RESPONSE_DELAY_MIN=2
export RESPONSE_DELAY_MAX=8
export AUTO_ADVANCE=true
export ENABLE_THINKING=true
```

**Logging Configuration:**
```bash
export LOG_DIR="conversations"
export LOG_FILE_PREFIX="streamlit_backroom"
```

#### Breaking Changes

None. The configuration system uses the same default values as before.

---

## Security Updates

### Version 0.1.0+
- **[CRITICAL]** Fixed XSS vulnerability in persona name and role rendering
- All user-provided content is now properly sanitized before HTML rendering
- File operations include comprehensive error handling
- Dependencies cleaned up to remove security risks

See [SECURITY.md](SECURITY.md) for our security policy and how to report vulnerabilities.
