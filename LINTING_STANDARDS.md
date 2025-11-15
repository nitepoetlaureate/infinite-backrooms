# Linting & Code Quality Standards for Infinite Backrooms

## Executive Summary: My Professional Opinion

**TL;DR:** For a Streamlit Python project enforcing system.css UX/UI standards, traditional CSS linting (Prettier, Stylelint) **won't work** because there are no separate CSS files. Instead, I recommend a **Python-centric approach** with:

1. **Ruff** (fast Python linter/formatter replacing Black + Flake8 + isort)
2. **Custom UI validation script** (to check design token usage)
3. **Pre-commit hooks** (to enforce standards automatically)
4. **Type checking with mypy** (optional but highly recommended)

This will ensure both **code quality** AND **UX/UI standards adherence** in a way that actually fits your architecture.

---

## The Problem: Why Traditional CSS Linting Won't Work

### Traditional CSS Tooling (❌ Not Applicable)

- **Prettier**: Formats CSS, HTML, JS - but your styles are Python strings
- **Stylelint**: Lints CSS files - but you have no CSS files
- **ESLint**: Lints JavaScript - but you're using Python/Streamlit

### What You Actually Have

```python
# This is Python code with inline HTML/CSS strings
persona_name_styled = f'<span style="background-color: {persona_color}; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold;">{message["persona_name"]}</span>'
```

**The Challenge:** Your UI code is:
- Python strings (not separate CSS files)
- Generated dynamically (not static HTML)
- Embedded in Streamlit components (not traditional frontend)

**The Solution:** Python linting + custom validation for design tokens

---

## Recommended Linting Stack

### 1. Ruff (Primary Linter & Formatter)

**Why Ruff?**
- 10-100x faster than Black, Flake8, isort combined
- Single tool replaces multiple tools
- Excellent Streamlit support
- Active development (written in Rust)

**Installation:**
```bash
pip install ruff
```

**Configuration:** Create `ruff.toml` in project root:

```toml
# ruff.toml - Ruff configuration for Infinite Backrooms

# Target Python 3.12+
target-version = "py312"

# Line length (recommended: 88 for Black compatibility, 100 for readability)
line-length = 100

# Enable automatic fixing where possible
fix = true

[lint]
# Select linting rules
# See: https://docs.astral.sh/ruff/rules/
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort (import sorting)
    "N",      # pep8-naming
    "UP",     # pyupgrade (modernize Python code)
    "B",      # flake8-bugbear (common bugs)
    "C4",     # flake8-comprehensions
    "DTZ",    # flake8-datetimez (timezone awareness)
    "T10",    # flake8-debugger (no debugger statements)
    "EM",     # flake8-errmsg (error message format)
    "ISC",    # flake8-implicit-str-concat
    "ICN",    # flake8-import-conventions
    "PIE",    # flake8-pie (misc best practices)
    "PYI",    # flake8-pyi (type stub files)
    "PT",     # flake8-pytest-style
    "Q",      # flake8-quotes
    "RSE",    # flake8-raise
    "RET",    # flake8-return
    "SIM",    # flake8-simplify
    "TCH",    # flake8-type-checking
    "ARG",    # flake8-unused-arguments
    "PTH",    # flake8-use-pathlib
    "ERA",    # eradicate (commented-out code)
    "PL",     # Pylint
    "TRY",    # tryceratops (exception handling)
    "RUF",    # Ruff-specific rules
]

# Ignore specific rules
ignore = [
    "E501",   # Line too long (handled by formatter)
    "PLR0913", # Too many arguments to function
    "TRY003", # Avoid specifying long messages outside exception class
    "EM101",  # Exception must not use string literal (too strict for this project)
]

# Exclude directories from linting
exclude = [
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "build",
    "dist",
]

[lint.per-file-ignores]
# Allow certain violations in specific files
"__init__.py" = ["F401"]  # Unused imports (common in __init__.py)
"streamlit_backroom.py" = ["PLR0915"]  # Too many statements (main file is complex)

[lint.isort]
# Import sorting configuration
known-first-party = ["ui_design_tokens"]
force-single-line = false
lines-after-imports = 2

[lint.pylint]
# Pylint-specific settings
max-args = 8  # Allow up to 8 function arguments
max-branches = 15  # Allow complex branching in Streamlit apps

[format]
# Formatting settings
quote-style = "double"  # Use double quotes
indent-style = "space"  # Use spaces (4 spaces per indent)
line-ending = "lf"  # Unix line endings

# Skip magic trailing comma (more compact formatting)
skip-magic-trailing-comma = false

# Prefer single-line docstrings for short descriptions
docstring-code-format = true
```

**Usage:**
```bash
# Check code
ruff check .

# Check and auto-fix
ruff check . --fix

# Format code
ruff format .

# Check and format in one command
ruff check . --fix && ruff format .
```

---

### 2. Custom UI Validation Script

Since traditional CSS linters won't work, create a **custom Python script** to validate design token usage.

**Create:** `scripts/validate_ui_standards.py`

```python
#!/usr/bin/env python3
"""
UI Standards Validation Script
===============================

Validates that all UI code adheres to system.css design standards
by checking for hardcoded values instead of design tokens.

Usage:
    python scripts/validate_ui_standards.py

Exit Codes:
    0 - All checks passed
    1 - Violations found
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


# Patterns to detect violations
VIOLATIONS = {
    "hardcoded_colors": r'(?:color|background-color|border-color):\s*#[0-9a-fA-F]{3,6}',
    "hardcoded_padding": r'padding:\s*\d+px(?:\s+\d+px)*',
    "hardcoded_margin": r'margin:\s*\d+px(?:\s+\d+px)*',
    "hardcoded_border_radius": r'border-radius:\s*\d+px',
    "random_spacing": r'(?:padding|margin):\s*(?:[3579]|1[1-9]|[2-9]\d+)px',  # Non-standard values
}

# Files to check
TARGET_FILES = [
    "streamlit_backroom.py",
    "log_viewer.py",
]

# Allowed exceptions (specific lines that are grandfathered in)
EXCEPTIONS = {
    # Format: ("filename", line_number, "pattern")
}


def find_violations(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Find UI standard violations in a Python file.

    Args:
        file_path: Path to the Python file to check

    Returns:
        List of tuples: (line_number, violation_type, matched_text)
    """
    violations = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, start=1):
        # Skip comments
        if line.strip().startswith('#'):
            continue

        # Check for violations
        for violation_type, pattern in VIOLATIONS.items():
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                # Check if this is an allowed exception
                if (file_path.name, line_num, violation_type) not in EXCEPTIONS:
                    violations.append((line_num, violation_type, match.group(0)))

    return violations


def check_imports(file_path: Path) -> bool:
    """
    Check if file imports design tokens module.

    Args:
        file_path: Path to the Python file to check

    Returns:
        True if imports ui_design_tokens, False otherwise
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    return 'from ui_design_tokens import' in content or 'import ui_design_tokens' in content


def main() -> int:
    """Run validation checks."""
    print("🎨 Validating UI/UX Standards (system.css compliance)\n")

    total_violations = 0
    files_checked = 0

    for filename in TARGET_FILES:
        file_path = Path(filename)

        if not file_path.exists():
            print(f"⚠️  Warning: {filename} not found")
            continue

        files_checked += 1
        print(f"Checking {filename}...")

        # Check for design tokens import
        has_import = check_imports(file_path)
        if not has_import:
            print(f"  ⚠️  Warning: No design tokens import found")

        # Find violations
        violations = find_violations(file_path)

        if violations:
            print(f"  ❌ Found {len(violations)} violation(s):\n")
            for line_num, violation_type, matched_text in violations:
                print(f"    Line {line_num}: {violation_type}")
                print(f"      → {matched_text}")
                print()
            total_violations += len(violations)
        else:
            print(f"  ✅ No violations found\n")

    # Summary
    print("=" * 60)
    if total_violations == 0:
        print(f"✅ All {files_checked} files passed validation!")
        return 0
    else:
        print(f"❌ Found {total_violations} violation(s) across {files_checked} file(s)")
        print("\n💡 Fix these by:")
        print("   1. Import design tokens: from ui_design_tokens import SYSTEM_COLORS, SPACING")
        print("   2. Replace hardcoded values with tokens")
        print("   3. Use style generator functions (persona_badge_style, etc.)")
        print("\nSee ui_design_tokens.py and .claude/skills/ux-ui-standards.md for guidance")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

**Usage:**
```bash
# Make executable
chmod +x scripts/validate_ui_standards.py

# Run validation
python scripts/validate_ui_standards.py
```

---

### 3. Pre-commit Hooks

**Why Pre-commit?**
- Automatically run checks before each commit
- Catch violations early
- Enforce consistency across contributors

**Installation:**
```bash
pip install pre-commit
```

**Configuration:** Create `.pre-commit-config.yaml`:

```yaml
# .pre-commit-config.yaml - Pre-commit hooks for Infinite Backrooms

repos:
  # Ruff linting and formatting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.15  # Use latest version
    hooks:
      # Run Ruff linter
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
        name: Ruff Linter

      # Run Ruff formatter
      - id: ruff-format
        name: Ruff Formatter

  # Built-in pre-commit hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
        name: Trim trailing whitespace
      - id: end-of-file-fixer
        name: Fix end of files
      - id: check-yaml
        name: Check YAML syntax
      - id: check-toml
        name: Check TOML syntax
      - id: check-json
        name: Check JSON syntax
      - id: check-added-large-files
        args: [--maxkb=1000]
        name: Check for large files
      - id: check-merge-conflict
        name: Check for merge conflicts
      - id: detect-private-key
        name: Detect private keys
      - id: mixed-line-ending
        args: [--fix=lf]
        name: Fix mixed line endings

  # Custom UI standards validation
  - repo: local
    hooks:
      - id: validate-ui-standards
        name: Validate UI/UX Standards
        entry: python scripts/validate_ui_standards.py
        language: python
        pass_filenames: false
        always_run: true
        stages: [commit]
```

**Setup:**
```bash
# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Update hook versions
pre-commit autoupdate
```

---

### 4. Type Checking with mypy (Optional but Recommended)

**Why mypy?**
- Catch type errors before runtime
- Improve code quality and maintainability
- Better IDE support (autocomplete, etc.)

**Installation:**
```bash
pip install mypy
```

**Configuration:** Create `mypy.ini`:

```ini
# mypy.ini - Type checking configuration

[mypy]
python_version = 3.12
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = False  # Start lenient, tighten later
check_untyped_defs = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_optional = True

# Per-module options
[mypy-streamlit.*]
ignore_missing_imports = True

[mypy-aiohttp.*]
ignore_missing_imports = True

[mypy-pandas.*]
ignore_missing_imports = True
```

**Usage:**
```bash
mypy streamlit_backroom.py
mypy log_viewer.py
```

---

## Recommended Development Workflow

### Daily Development

```bash
# Before committing
ruff check . --fix      # Lint and auto-fix
ruff format .           # Format code
python scripts/validate_ui_standards.py  # Check UI standards
```

### CI/CD Pipeline

Add to `.github/workflows/lint.yml`:

```yaml
name: Lint & Validate

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install ruff
          pip install -r requirements.txt

      - name: Run Ruff linter
        run: ruff check .

      - name: Run Ruff formatter check
        run: ruff format --check .

      - name: Validate UI/UX standards
        run: python scripts/validate_ui_standards.py
```

---

## Migration Plan

### Phase 1: Setup (Week 1)

1. ✅ Install Ruff: `pip install ruff`
2. ✅ Create `ruff.toml` configuration
3. ✅ Run initial format: `ruff format .`
4. ✅ Fix critical linting issues: `ruff check . --fix`
5. ✅ Commit configuration files

### Phase 2: Custom Validation (Week 2)

1. ✅ Create `scripts/` directory
2. ✅ Implement `validate_ui_standards.py`
3. ✅ Run validation and document existing violations
4. ✅ Create baseline (grandfather in existing issues)
5. ✅ Commit validation script

### Phase 3: Pre-commit Hooks (Week 3)

1. ✅ Install pre-commit: `pip install pre-commit`
2. ✅ Create `.pre-commit-config.yaml`
3. ✅ Run `pre-commit install`
4. ✅ Test on sample commits
5. ✅ Document in README

### Phase 4: Refactoring (Ongoing)

1. ✅ Systematically refactor files to use `ui_design_tokens`
2. ✅ Reduce violations count
3. ✅ Update validation script to enforce stricter rules
4. ✅ Achieve zero violations

---

## FAQ

### Q: Why not Prettier for Python?

**A:** Prettier's Python plugin (prettier-python) is unmaintained. Ruff is the modern standard and significantly faster.

### Q: Why not Black?

**A:** Ruff's formatter is compatible with Black but 10-100x faster and includes linting. Using one tool is simpler.

### Q: Can I still use ESLint/Stylelint for future frontend code?

**A:** Yes! If you add React/Vue/traditional HTML+CSS in the future, absolutely add those tools. But for Streamlit, they're not applicable.

### Q: What about checking inline CSS strings?

**A:** That's exactly what `validate_ui_standards.py` does - it uses regex to find CSS patterns in Python strings.

### Q: How strict should we be?

**A:** Start lenient (warn about violations) → Gradually tighten → Eventually enforce (fail builds on violations).

### Q: Will this slow down commits?

**A:** Ruff is extremely fast (~100ms for this codebase). Pre-commit hooks add ~1-2 seconds total.

---

## My Professional Recommendation

### Short Term (Implement Immediately)

1. **Install Ruff** - Replaces Black, Flake8, isort
2. **Create `ui_design_tokens.py`** - Already done! ✅
3. **Run initial format** - Get codebase to consistent baseline

### Medium Term (Next 2-4 Weeks)

1. **Implement custom UI validation** - Catch design token violations
2. **Setup pre-commit hooks** - Automate enforcement
3. **Refactor existing UI code** - Systematically apply design tokens

### Long Term (Ongoing)

1. **Add type hints** - Gradually improve type coverage
2. **Enforce stricter linting** - Raise the bar over time
3. **CI/CD integration** - Automate in pull requests

---

## Conclusion

For a Streamlit project enforcing system.css standards, **traditional CSS linting won't work**. Instead:

✅ **DO:**
- Use Ruff for Python linting and formatting
- Create custom validation for design token usage
- Setup pre-commit hooks for automation
- Gradually refactor to improve compliance

❌ **DON'T:**
- Try to use Prettier/Stylelint on inline CSS strings
- Add complex ESLint configs for non-existent JavaScript
- Manually check every commit (automate it!)

This approach gives you:
- **Fast** linting (Ruff is 10-100x faster than alternatives)
- **Comprehensive** checking (Python code + UI standards)
- **Automated** enforcement (pre-commit hooks)
- **Gradual** improvement (warn → enforce over time)

**The result:** Consistent, high-quality code that adheres to system.css design standards while maintaining Python best practices.

---

## Additional Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Pre-commit Framework](https://pre-commit.com/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [PEP 8 - Python Style Guide](https://peps.python.org/pep-0008/)
- [system.css Design System](https://github.com/sakofchit/system.css)

---

**Questions or suggestions?** Update this document as the project evolves!
