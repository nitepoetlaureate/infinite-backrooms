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


# Patterns to detect violations
VIOLATIONS = {
    "hardcoded_colors": r"(?:color|background-color|border-color):\s*#[0-9a-fA-F]{3,6}",
    "hardcoded_padding": r"padding:\s*\d+px(?:\s+\d+px)*",
    "hardcoded_margin": r"margin:\s*\d+px(?:\s+\d+px)*",
    "hardcoded_border_radius": r"border-radius:\s*\d+px",
    "random_spacing": r"(?:padding|margin):\s*(?:[3579]|1[1-9]|[2-9]\d+)px",  # Non-standard values
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


def find_violations(file_path: Path) -> list[tuple[int, str, str]]:
    """
    Find UI standard violations in a Python file.

    Args:
        file_path: Path to the Python file to check

    Returns:
        List of tuples: (line_number, violation_type, matched_text)
    """
    violations = []

    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, start=1):
        # Skip comments
        if line.strip().startswith("#"):
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
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    return "from ui_design_tokens import" in content or "import ui_design_tokens" in content


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
            print("  ⚠️  Warning: No design tokens import found")

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
            print("  ✅ No violations found\n")

    # Summary
    print("=" * 60)
    if total_violations == 0:
        print(f"✅ All {files_checked} files passed validation!")
        return 0
    print(f"❌ Found {total_violations} violation(s) across {files_checked} file(s)")
    print("\n💡 Fix these by:")
    print("   1. Import design tokens: from ui_design_tokens import SYSTEM_COLORS, SPACING")
    print("   2. Replace hardcoded values with tokens")
    print("   3. Use style generator functions (persona_badge_style, etc.)")
    print("\nSee ui_design_tokens.py and .claude/skills/ux-ui-standards.md for guidance")
    return 1


if __name__ == "__main__":
    sys.exit(main())
