# Contributing to Infinite Backrooms

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions. We're here to build great software together.

## Getting Started

### Prerequisites

- Python 3.12 or higher
- [UV package manager](https://github.com/astral-sh/uv)
- [Ollama](https://ollama.ai/) running locally
- Git

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR-USERNAME/infinite-backrooms.git
   cd infinite-backrooms
   ```

2. **Install Dependencies**
   ```bash
   # Install main dependencies
   uv sync

   # Install development dependencies
   uv sync --extra dev
   ```

3. **Run the Application**
   ```bash
   uv run streamlit run streamlit_backroom.py
   ```

4. **Run Tests**
   ```bash
   uv run pytest
   ```

## Development Workflow

### Branch Strategy

- `main`: Production-ready code
- Feature branches: `feature/your-feature-name`
- Bug fixes: `fix/bug-description`
- Security fixes: `security/vulnerability-name`

### Making Changes

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Write clean, readable code
   - Follow Python best practices (PEP 8)
   - Add docstrings to functions and classes
   - Keep functions focused and reasonably sized

3. **Test Your Changes**
   ```bash
   # Run tests
   uv run pytest

   # Run linter
   uv run ruff check .

   # Format code
   uv run ruff format .

   # Type check
   uv run mypy .
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "type: brief description

   More detailed description if needed.
   Addresses #issue-number"
   ```

   Commit types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `security`

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

   Then create a Pull Request on GitHub.

## Code Style Guidelines

### Python Style

- Follow PEP 8 with 120 character line length
- Use type hints for function signatures
- Write descriptive variable and function names
- Add docstrings for all public functions/classes

Example:
```python
def calculate_response_time(persona: AIPersona, context_size: int) -> float:
    """
    Calculate estimated response time for a persona.

    Args:
        persona: The AI persona generating the response
        context_size: Number of messages in context

    Returns:
        Estimated response time in seconds
    """
    # Implementation
    pass
```

### Streamlit Code

- Keep UI functions separate from business logic
- Use session state appropriately
- Add helpful comments for complex UI flows
- Test UI changes manually before committing

### Security

- **Never** commit secrets, API keys, or credentials
- Sanitize all user input before HTML rendering
- Use parameterized queries for any database operations
- Validate file paths before file operations

## Testing

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use descriptive test function names
- Test both success and failure cases
- Mock external dependencies (Ollama API, file I/O)

Example:
```python
def test_sanitize_html_prevents_xss():
    """Ensure HTML sanitization prevents XSS attacks"""
    malicious_input = '<script>alert("XSS")</script>'
    result = sanitize_html(malicious_input)
    assert '<script>' not in result
    assert '&lt;script&gt;' in result
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=.

# Run specific test file
uv run pytest tests/test_streamlit_backroom.py

# Run specific test
uv run pytest tests/test_streamlit_backroom.py::test_sanitize_html
```

## Pull Request Guidelines

### Before Submitting

- [ ] All tests pass
- [ ] Code is formatted with ruff
- [ ] No linting errors
- [ ] Type checking passes
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (if applicable)
- [ ] Security implications considered

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Security fix

## Testing
How was this tested?

## Checklist
- [ ] Tests pass
- [ ] Code formatted
- [ ] Documentation updated
- [ ] No security issues introduced

## Related Issues
Closes #123
```

## Documentation

### Code Documentation

- Add docstrings to all public functions/classes
- Use Google-style docstrings
- Include type hints
- Document exceptions raised

### User Documentation

- Update README.md for user-facing changes
- Add examples for new features
- Update troubleshooting section if needed

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release branch
4. Run full test suite
5. Create GitHub release with notes
6. Tag release: `git tag v0.1.0`

## Questions or Need Help?

- Open an issue with the `question` label
- Check existing issues and discussions
- Review documentation

## Recognition

Contributors will be:
- Listed in CHANGELOG.md
- Acknowledged in release notes
- Added to GitHub contributors page

---

Thank you for contributing to Infinite Backrooms! 🤖✨
