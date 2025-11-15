# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive development infrastructure
  - Pre-commit hooks with Ruff, MyPy, and Bandit
  - GitHub Actions CI/CD pipeline
  - Docker and docker-compose support
  - Pytest test suite with coverage reporting
- Complete project metadata in pyproject.toml
- MIT License
- Contributing guidelines (CONTRIBUTING.md)
- Security policy (SECURITY.md)
- Environment variable support with .env.example
- Proper logging configuration
- Development and production requirements files

### Changed
- Updated Ruff to v0.8.4 (from v0.1.15)
- Fixed pyproject.toml dependencies (removed built-in modules)
- Improved warning handling with proper logging
- Enhanced .gitignore with comprehensive exclusions

### Fixed
- Broken pre-commit configuration (removed non-existent validate_ui_standards.py)
- Dependency management issues
- Missing project metadata

### Security
- Added Bandit security scanning
- Replaced excessive warning suppression with targeted logging
- Added security best practices documentation

## [0.1.0] - 2024

### Added
- Initial release
- Multi-persona AI conversation platform
- Streamlit web interface
- Ollama integration
- 17+ predefined persona roles
- @mention system for persona interaction
- Conversation logging
- Export functionality
- Standalone log viewer application
- Real-time streaming responses
- AI thinking mode support

[Unreleased]: https://github.com/guinacio/infinite-backrooms/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/guinacio/infinite-backrooms/releases/tag/v0.1.0
