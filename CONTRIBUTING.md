# Contributing to Infinite Backrooms

Thank you for your interest in contributing to Infinite Backrooms! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/guinacio/infinite-backrooms.git
   cd infinite-backrooms
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

## Development Workflow

### Code Quality

We use several tools to maintain code quality:

- **Ruff**: Linting and code formatting
- **MyPy**: Type checking
- **Bandit**: Security scanning
- **Pytest**: Testing

Run these checks locally before committing:

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Or run individually
ruff check .
ruff format .
mypy streamlit_backroom.py log_viewer.py
bandit -r . -c pyproject.toml
pytest
```

### Testing

Write tests for new features and bug fixes:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_logger.py
```

### Code Style

- Follow PEP 8 guidelines (enforced by Ruff)
- Use type hints where appropriate
- Write descriptive docstrings for classes and functions
- Keep functions focused and single-purpose
- Maximum line length: 120 characters

### Commit Messages

Follow conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Example:
```
feat(personas): add custom role validation

Add validation to ensure custom roles meet minimum requirements
and provide helpful error messages to users.
```

## Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and commit them with clear messages

3. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a Pull Request** with:
   - Clear description of changes
   - Reference to related issues
   - Screenshots for UI changes
   - Test coverage for new code

5. **Respond to review feedback** and make necessary changes

## Reporting Issues

When reporting bugs, please include:

- Description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs or error messages

## Feature Requests

We welcome feature requests! Please:

- Check existing issues first
- Provide clear use case description
- Explain why this benefits users
- Be open to discussion and alternatives

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other contributors

## Questions?

If you have questions, feel free to:
- Open a discussion on GitHub
- Comment on related issues
- Reach out to maintainers

Thank you for contributing! 🎉
