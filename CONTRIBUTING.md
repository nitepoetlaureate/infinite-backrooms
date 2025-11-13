# Contributing to Infinite AI Backrooms

First off, thank you for considering contributing to Infinite AI Backrooms! It's people like you that make this project such a great tool for the AI community.

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in all interactions.

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team. All complaints will be reviewed and investigated promptly and fairly.

---

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

#### How to Submit a Good Bug Report

**Use the bug report template and include:**

- **Clear, descriptive title** for the issue
- **Exact steps to reproduce** the problem
- **Expected behavior** vs. **actual behavior**
- **Screenshots** if applicable
- **Environment details:**
  - OS (Windows, macOS, Linux)
  - Python version (`python --version`)
  - Ollama version (`ollama --version`)
  - Project version
- **Logs or error messages** (full traceback)
- **Additional context** that might be relevant

**Example:**
```markdown
### Bug Report: Connection timeout not handled properly

**Environment:**
- OS: Ubuntu 22.04
- Python: 3.12.0
- Ollama: 0.1.14
- Project: v0.1.0

**Steps to Reproduce:**
1. Stop Ollama server
2. Try to add a new persona
3. Click "Check Ollama Connection"

**Expected:** Error message with troubleshooting steps
**Actual:** Application hangs for 30 seconds

**Error Message:**
```
TimeoutError: Request timed out after 30 seconds
```

**Screenshots:** [attach screenshot]
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues.

#### How to Submit a Good Enhancement Suggestion

- **Use a clear, descriptive title**
- **Provide detailed description** of the enhancement
- **Explain why this enhancement would be useful**
- **List any alternatives considered**
- **Include mockups/examples** if applicable

**Example:**
```markdown
### Feature Request: Export conversation as PDF

**Problem:**
Users want to share conversations in a more portable format than JSON.

**Proposed Solution:**
Add a "Export as PDF" button in the Export & Logs tab that generates
a nicely formatted PDF with:
- Conversation metadata (date, participants)
- Color-coded messages by persona
- Proper formatting and pagination

**Alternatives Considered:**
- Markdown export (less polished)
- HTML export (requires browser)

**Additional Context:**
Similar feature in tool X works well.
```

### Your First Code Contribution

Unsure where to begin? Look for issues labeled:
- `good first issue` - Simple issues for newcomers
- `help wanted` - Issues where we need community help
- `documentation` - Documentation improvements

### Pull Requests

#### Before Submitting a Pull Request

1. **Check existing PRs** to avoid duplication
2. **Discuss major changes** in an issue first
3. **Follow code standards** (see below)
4. **Write tests** for new functionality
5. **Update documentation** if needed

#### Pull Request Process

1. **Fork the repository** and create your branch from `main`

```bash
git checkout -b feature/amazing-feature
```

2. **Make your changes:**
   - Write clear, concise code
   - Follow the style guide
   - Add tests
   - Update docs

3. **Ensure quality:**

```bash
# Format code
uv run black .

# Lint code
uv run ruff check --fix .

# Type check
uv run mypy .

# Run tests
uv run pytest --cov

# Check coverage
# Aim for 80%+ coverage for new code
```

4. **Commit your changes:**

Use conventional commit messages:
```bash
git commit -m "feat(personas): add export to PDF feature"
git commit -m "fix(logger): handle unicode characters correctly"
git commit -m "docs: update installation instructions"
```

5. **Push to your fork:**

```bash
git push origin feature/amazing-feature
```

6. **Open a Pull Request:**
   - Use the PR template
   - Reference related issues
   - Describe changes clearly
   - Add screenshots for UI changes

7. **Respond to feedback:**
   - Address reviewer comments
   - Make requested changes
   - Be open to suggestions

8. **Wait for approval:**
   - At least one approval required
   - All CI checks must pass
   - No merge conflicts

---

## Code Standards

### Python Style Guide

We follow PEP 8 with some modifications. Use the provided tools:

- **Black** for formatting (line length: 100)
- **Ruff** for linting
- **Mypy** for type checking

### Code Style

#### Naming Conventions

```python
# Classes: PascalCase
class AIPersona:
    pass

# Functions: snake_case
def get_next_speaker():
    pass

# Constants: UPPER_SNAKE_CASE
DEFAULT_TIMEOUT = 120

# Private: _leading_underscore
def _internal_helper():
    pass
```

#### Type Hints

Always use type hints:

```python
from typing import List, Dict, Optional

def process_message(
    message: str,
    personas: List[AIPersona],
    context: Optional[Dict[str, Any]] = None
) -> str:
    """Process a message."""
    pass
```

#### Docstrings

Use Google-style docstrings:

```python
def complex_function(param1: str, param2: int) -> bool:
    """One-line summary of function.

    More detailed description if needed. Can span multiple
    lines and include usage examples.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is negative

    Example:
        >>> result = complex_function("test", 42)
        >>> print(result)
        True
    """
    pass
```

#### Error Handling

Always catch specific exceptions:

```python
# ❌ Bad
try:
    risky_operation()
except:
    pass

# ✅ Good
try:
    risky_operation()
except (ValueError, TypeError) as e:
    logger.error(f"Operation failed: {e}")
    raise CustomError("User-friendly message") from e
```

#### Async/Await

Use async properly:

```python
# ✅ Good - Proper async context manager
async with OllamaClient() as client:
    result = await client.test_connection()

# ✅ Good - Proper cleanup
try:
    async with session:
        await process()
finally:
    await cleanup()
```

### Testing Standards

#### Test Organization

```python
class TestFeatureName:
    """Test suite for FeatureName."""

    def test_specific_behavior(self):
        """Test that specific behavior works correctly."""
        # Arrange
        input_data = create_test_data()

        # Act
        result = function_under_test(input_data)

        # Assert
        assert result == expected_value
```

#### Test Coverage

- **Minimum 80% coverage** for new code
- Test happy path and edge cases
- Test error handling
- Mock external dependencies (Ollama API, file system)

#### Test Naming

- Use descriptive names: `test_connection_failure_with_timeout`
- Explain what is tested: `test_persona_creation_with_custom_color`

### Documentation Standards

#### Code Comments

```python
# ✅ Good - Explains WHY, not WHAT
# Use round-robin to ensure fair speaking distribution
next_speaker = personas[(current_index + 1) % len(personas)]

# ❌ Bad - Obvious WHAT
# Increment the index
index = index + 1
```

#### Documentation Updates

When changing functionality:
1. Update docstrings
2. Update API.md if public API changes
3. Update ARCHITECTURE.md if design changes
4. Update README.md if user-facing changes
5. Add entry to CHANGELOG.md

---

## Commit Message Guidelines

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Code style (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring
- **test**: Adding tests
- **chore**: Maintenance tasks

### Scope

Optional, specifies what is affected:
- `personas`: Persona management
- `logger`: Conversation logging
- `ui`: User interface
- `client`: Ollama client
- `tests`: Test suite

### Subject

- Use imperative mood: "add" not "added"
- Don't capitalize first letter
- No period at the end
- Max 72 characters

### Body (optional)

- Explain WHAT and WHY, not HOW
- Separate from subject with blank line
- Wrap at 72 characters

### Footer (optional)

- Reference issues: `Fixes #123`, `Closes #456`
- Breaking changes: `BREAKING CHANGE: description`

### Examples

```bash
# Simple fix
git commit -m "fix(logger): handle unicode characters in filenames"

# Feature with body
git commit -m "feat(personas): add PDF export

Implements PDF export for conversations with proper formatting
and color-coding. Includes metadata and pagination.

Closes #42"

# Breaking change
git commit -m "refactor(client): change connection API

BREAKING CHANGE: test_connection() now returns tuple instead of dict"
```

---

## Review Process

### For Reviewers

When reviewing PRs:
1. **Check functionality** - Does it work as intended?
2. **Read the code** - Is it clean and maintainable?
3. **Run tests** - Do all tests pass?
4. **Check coverage** - Is test coverage maintained?
5. **Review docs** - Are docs updated?
6. **Suggest improvements** - Be constructive
7. **Approve or request changes**

### For Contributors

When receiving feedback:
1. **Respond promptly** to comments
2. **Ask questions** if feedback is unclear
3. **Make requested changes** or discuss alternatives
4. **Mark conversations as resolved** after addressing
5. **Be patient** - reviews take time
6. **Learn from feedback** - it makes you better

---

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release tag: `git tag -a v0.2.0 -m "Release v0.2.0"`
4. Push tag: `git push origin v0.2.0`
5. GitHub Actions creates release automatically
6. Publish release notes

---

## Getting Help

### Resources

- **Documentation**: See `/docs` folder
- **Issues**: Search existing issues
- **Discussions**: GitHub Discussions for questions
- **Discord**: [Coming soon]

### Questions?

- Create a GitHub Discussion for general questions
- Create an Issue for bugs or features
- Tag maintainers with `@username` for urgent matters

---

## Recognition

Contributors will be:
- Listed in `CONTRIBUTORS.md`
- Mentioned in release notes
- Given credit in commits

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to Infinite AI Backrooms! 🎉

---

**Last Updated:** 2024-11-13
