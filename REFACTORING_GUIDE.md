# UX/UI Refactoring Guide - System.css Standards Implementation

This document shows the before/after examples of refactoring inline styles to use centralized design tokens following system.css standards.

## Summary of Changes

**Total violations fixed:** 8
**Files refactored:** 1 (streamlit_backroom.py)
**Design system:** system.css (retro Apple System OS 1984-1991)

---

## Refactoring Examples

### 1. Persona Badge Styles (Chat Messages)

**Location:** `streamlit_backroom.py:848`

**❌ BEFORE:**
```python
persona_name_styled = f'<span style="background-color: {persona_color}; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold;">{message["persona_name"]}</span>'
```

**✅ AFTER:**
```python
from ui_design_tokens import persona_badge_style

persona_name_styled = f'<span style="{persona_badge_style(message["persona_name"], persona_color)}">{message["persona_name"]}</span>'
```

**Benefits:**
- Centralized styling - change once, update everywhere
- Consistent spacing (uses `SPACING` tokens)
- System.css compliant border-radius (2px instead of 4px)
- Reusable across all persona displays

---

### 2. @Mention Highlighting

**Location:** `streamlit_backroom.py:876`

**❌ BEFORE:**
```python
highlighted_mention = f'<span style="background-color: {p.color}; color: white; padding: 1px 4px; border-radius: 3px; font-weight: bold;">@{p.name}</span>'
```

**✅ AFTER:**
```python
from ui_design_tokens import mention_highlight_style

highlighted_mention = f'<span style="{mention_highlight_style(p.color)}">@{p.name}</span>'
```

**Benefits:**
- Dedicated function for @mentions with proper contrast
- Uses standard spacing tokens (`SPACING['xs']`, `SPACING['md']`)
- System.css compliant border-radius (3px maximum)
- Accessible color contrast (text_primary on colored background)

---

### 3. Current Speaker Display

**Location:** `streamlit_backroom.py:990`

**❌ BEFORE:**
```python
persona_name_styled = f'<span style="background-color: {current_persona.color}; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold;">{current_persona.name}</span>'
```

**✅ AFTER:**
```python
from ui_design_tokens import persona_badge_style

persona_name_styled = f'<span style="{persona_badge_style(current_persona.name, current_persona.color)}">{current_persona.name}</span>'
```

**Benefits:**
- Same function as chat message badges (consistency!)
- System.css compliant (reduced border-radius from 4px → 2px)
- Maintainable - update design system, not individual instances

---

### 4. Sidebar Persona Display

**Location:** `streamlit_backroom.py:1274`

**❌ BEFORE:**
```python
persona_name_styled = f'<span style="background-color: {persona.color}; color: white; padding: 2px 6px; border-radius: 3px; font-weight: bold; font-size: 0.9em;">{persona.name}</span>'
```

**✅ AFTER:**
```python
from ui_design_tokens import persona_badge_style

persona_name_styled = f'<span style="{persona_badge_style(persona.name, persona.color)}">{persona.name}</span>'
```

**Benefits:**
- **Standardized padding** (was 2px 6px, now 2px 8px - consistent with other badges)
- **Standardized font-size** (was 0.9em, now 9pt from system.css standards)
- **Standardized border-radius** (was 3px, now 2px - system.css standard)
- Visual consistency across entire application

---

## Design Tokens Overview

### What We're Using

```python
from ui_design_tokens import (
    persona_badge_style,      # For persona name badges
    mention_highlight_style,   # For @mention highlighting
    SYSTEM_COLORS,            # Color palette (monochrome + muted accents)
    SPACING,                  # Spacing tokens (1px, 2px, 4px, 8px, 16px)
)
```

### Key Functions

#### `persona_badge_style(persona_name, persona_color)`
Generates consistent persona badge styling with:
- Background: `persona_color`
- Text color: White (`#FFFFFF`)
- Padding: `2px 8px` (system.css standard)
- Border: `1px solid black`
- Border-radius: `2px` (system.css standard - minimal rounding)
- Font-weight: Bold (`700`)
- Font-family: Chicago monospace

#### `mention_highlight_style(persona_color, text_color=None)`
Generates @mention highlighting with:
- Background: `persona_color`
- Text color: Black (`#000000`) for better contrast
- Padding: `1px 4px` (system.css micro-spacing)
- Border-radius: `3px` (system.css maximum)
- Font-weight: Bold
- Font-family: Geneva sans-serif

---

## System.css Standards Applied

### Spacing
**Before:** Random values (2px, 1px, 4px, 6px, 8px) with no consistency
**After:** System.css tokens:
- `xs`: 1px
- `sm`: 2px
- `md`: 4px
- `lg`: 8px
- `xl`: 16px

### Border Radius
**Before:** 3px and 4px (too rounded for system.css)
**After:** 2-3px maximum (system.css retro aesthetic)

### Colors
**Before:** Hardcoded in multiple places
**After:** Centralized in `PERSONA_COLORS` and `SYSTEM_COLORS` dictionaries

### Typography
**Before:** Inconsistent (bold in HTML, 0.9em font-size)
**After:** System.css standards (Chicago 12pt, Geneva 9pt, bold via design tokens)

---

## Validation Results

### Before Refactoring
```
❌ Found 8 violation(s) across 2 file(s)

streamlit_backroom.py:
  Line 750: hardcoded_padding → padding: 2px 8px
  Line 750: hardcoded_border_radius → border-radius: 4px
  Line 778: hardcoded_padding → padding: 1px 4px
  Line 778: hardcoded_border_radius → border-radius: 3px
  Line 881: hardcoded_padding → padding: 2px 8px
  Line 881: hardcoded_border_radius → border-radius: 4px
  Line 1165: hardcoded_padding → padding: 2px 6px
  Line 1165: hardcoded_border_radius → border-radius: 3px
```

### After Refactoring
```
✅ All 2 files passed validation!
```

**Achievement unlocked:** Zero UI violations! 🎉

---

## Migration Strategy Used

1. **Import design tokens** at top of file
2. **Replace inline styles** with function calls
3. **Validate** with `python scripts/validate_ui_standards.py`
4. **Test visually** to ensure no regressions
5. **Document** changes in this guide

---

## Future Improvements

### Additional Refactoring Opportunities
- [ ] Role emoji mapping could be moved to design tokens
- [ ] Container styles for expanders/tabs
- [ ] Button styles for Streamlit buttons (if custom styling needed)
- [ ] Input field styles

### Design System Enhancements
- [ ] Add dark mode support (toggle between monochrome themes)
- [ ] Create additional badge variants (success, warning, error)
- [ ] Add animation/transition tokens (if needed)
- [ ] Document component accessibility guidelines

---

## Developer Guidelines

### When Adding New UI Elements

1. **Check design tokens first** - Is there a function for this?
2. **Don't hardcode values** - Use `SPACING`, `SYSTEM_COLORS`, etc.
3. **Validate early** - Run `python scripts/validate_ui_standards.py` often
4. **Ask for review** - When unsure, consult `.claude/skills/ux-ui-standards.md`

### Common Patterns

```python
# ✅ Good - Uses design tokens
from ui_design_tokens import persona_badge_style
badge = f'<span style="{persona_badge_style(name, color)}">{name}</span>'

# ❌ Bad - Hardcoded values
badge = f'<span style="background: blue; padding: 5px;">{name}</span>'

# ✅ Good - Uses spacing tokens
from ui_design_tokens import SPACING
padding = f"padding: {SPACING['md']} {SPACING['lg']}"

# ❌ Bad - Magic numbers
padding = "padding: 4px 8px"
```

---

## Testing Checklist

After refactoring UI code:

- [ ] Run `python scripts/validate_ui_standards.py` (must show 0 violations)
- [ ] Run `ruff check .` (fix any critical issues)
- [ ] Run `ruff format .` (ensure consistent formatting)
- [ ] Visual inspection in browser (no layout breaks)
- [ ] Test with different persona colors (contrast/readability)
- [ ] Test in different screen sizes (responsive behavior)
- [ ] Check accessibility (keyboard navigation, screen readers)

---

## Conclusion

This refactoring demonstrates the power of centralized design tokens:
- **8 violations → 0 violations**
- **Inline styles → Reusable functions**
- **Inconsistent spacing → System.css standards**
- **Hard to maintain → Easy to update**

By following system.css standards and using design tokens, we've created a consistent, maintainable, and aesthetically cohesive UI that matches the retro Apple System OS aesthetic.

**Next steps:** Continue this pattern for any new UI components, and gradually refactor remaining inline styles as the application evolves.

---

**Last updated:** 2025-11-15
**Standards version:** system.css (System 6 monochrome)
**Validation tool:** `scripts/validate_ui_standards.py`
