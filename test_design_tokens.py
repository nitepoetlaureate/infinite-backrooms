#!/usr/bin/env python3
"""
Test script to verify system.css design tokens are working correctly
"""

from ui_design_tokens import (
    SPACING,
    SYSTEM_COLORS,
    mention_highlight_style,
    persona_badge_style,
)

print("=" * 80)
print("SYSTEM.CSS DESIGN TOKENS VERIFICATION")
print("=" * 80)
print()

# Test spacing tokens
print("✅ SPACING TOKENS:")
print(f"  xs: {SPACING['xs']} (expected: 1px)")
print(f"  sm: {SPACING['sm']} (expected: 2px)")
print(f"  md: {SPACING['md']} (expected: 4px)")
print(f"  lg: {SPACING['lg']} (expected: 8px)")
print(f"  radius_sm: {SPACING['radius_sm']} (expected: 2px)")
print(f"  radius_md: {SPACING['radius_md']} (expected: 3px)")
print(f"  border_thin: {SPACING['border_thin']} (expected: 1px)")
print()

# Test system colors
print("✅ SYSTEM COLORS:")
print(f"  window_border: {SYSTEM_COLORS['window_border']} (expected: #000000)")
print(f"  text_inverse: {SYSTEM_COLORS['text_inverse']} (expected: #FFFFFF)")
print()

# Test persona badge style
print("✅ PERSONA BADGE STYLE:")
badge_style = persona_badge_style("Philosopher", "#9b59b6")
print(badge_style)
print()

# Verify critical attributes
print("🔍 CRITICAL CHECKS:")
checks = {
    "Has black border": "border: 1px solid #000000" in badge_style,
    "Has 2px border-radius": "border-radius: 2px" in badge_style,
    "Has 2px 8px padding": "padding: 2px 8px" in badge_style,
    "Has white text": "color: #FFFFFF" in badge_style,
}

all_passed = True
for check, passed in checks.items():
    status = "✅" if passed else "❌"
    print(f"  {status} {check}")
    if not passed:
        all_passed = False

print()
print("✅ MENTION HIGHLIGHT STYLE:")
mention_style = mention_highlight_style("#9b59b6")
print(mention_style)
print()

# Verify mention style
mention_checks = {
    "Has 3px border-radius": "border-radius: 3px" in mention_style,
    "Has 1px 4px padding": "padding: 1px 4px" in mention_style,
}

for check, passed in mention_checks.items():
    status = "✅" if passed else "❌"
    print(f"  {status} {check}")
    if not passed:
        all_passed = False

print()
print("=" * 80)
if all_passed:
    print("✅ ALL CHECKS PASSED - system.css styling is correct!")
else:
    print("❌ SOME CHECKS FAILED - system.css styling has issues!")
print("=" * 80)
