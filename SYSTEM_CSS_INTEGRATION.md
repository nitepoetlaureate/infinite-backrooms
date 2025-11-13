# System.css Integration Guide

## Overview

This application uses [System.css](https://github.com/sakofchit/system.css) to provide a retro Apple Mac OS System 7 aesthetic (1984-1991 era). System.css is a pure CSS library that recreates the classic monochrome Macintosh interface.

## Directory Structure

```
infinite-backrooms/
├── system-css-main/          # Original System.css library (source)
│   ├── style.css             # Main System.css stylesheet
│   ├── fonts/                # Classic Mac fonts (Chicago, Monaco, Geneva)
│   ├── icon/                 # UI elements (scrollbars, buttons, checkboxes)
│   ├── docs/                 # System.css documentation
│   └── draggabilly-master/   # Draggable window library (optional)
│
└── static/                   # Production-ready static assets
    ├── css/
    │   └── system.css        # Processed CSS with updated font paths
    ├── fonts/                # Web fonts for classic Mac typography
    │   ├── ChicagoFLF.woff(2)      # Chicago font
    │   ├── ChiKareGo2.woff(2)      # Chicago 12pt recreation
    │   ├── FindersKeepers.woff(2)  # Geneva 9pt recreation
    │   └── monaco.woff(2)          # Monaco monospace font
    └── icons/                # UI icons (SVG format)
        ├── button*.svg
        ├── checkmark.svg
        ├── radio*.svg
        └── scrollbar*.svg
```

## How It Works

### 1. CSS Injection

The `inject_system_css()` function in `streamlit_backroom.py` loads and injects the System.css stylesheet into the Streamlit application:

```python
def inject_system_css() -> None:
    """Inject System.css styling into the Streamlit app for retro Mac OS aesthetic."""
    with open("static/css/system.css", "r") as f:
        system_css = f.read()

    st.markdown(f"<style>{system_css}...</style>", unsafe_allow_html=True)
```

This function is called at the start of `main()` before the app initializes.

### 2. Local Asset Serving

- **No CDN dependency**: All CSS, fonts, and icons are served locally from the `static/` directory
- **Font paths updated**: The CSS font paths have been adjusted from `fonts/` to `../fonts/` to work with the directory structure
- **Streamlit compatibility**: Additional CSS rules are applied for Streamlit-specific components

### 3. Typography

The application uses these classic Macintosh fonts:

- **Chicago** / **Chicago_12**: Main UI font (recreated from original bitmap fonts)
- **Geneva_9**: Alternative UI font (FindersKeepers recreation)
- **Monaco**: Monospace font for code and input fields

## Design System

System.css provides these CSS custom properties:

```css
:root {
  --primary: #FFFFFF;         /* White */
  --secondary: #000000;       /* Black */
  --tertiary: #A5A5A5;        /* Grey */
  --disabled: #B6B7B8;        /* Dark Grey */
}
```

### Available Components

- Windows with title bars (`.window`, `.title-bar`)
- Buttons (`.btn`)
- Text inputs (`.text-input`)
- Checkboxes and radio buttons
- Scrollbars (custom styled)
- Modeless dialogs
- Field rows and groupings

## Linting & Formatting

The `system-css-main/` directory is properly configured in linting tools:

### Ruff (pyproject.toml)
```toml
[tool.ruff]
exclude = [
    "system-css-main/node_modules",
    "system-css-main/draggabilly-master",
]
```

### Black (pyproject.toml)
```toml
[tool.black]
extend-exclude = '''
/(
  system-css-main/node_modules
  | system-css-main/draggabilly-master
)/
'''
```

### .gitignore
```gitignore
# System CSS - Keep source but ignore node_modules
system-css-main/node_modules/
system-css-main/.DS_Store
```

## Maintenance

### Updating System.css

If you need to update to a newer version of System.css:

1. Update files in `system-css-main/`
2. Copy updated assets to `static/`:
   ```bash
   cp system-css-main/style.css static/css/system.css
   cp -r system-css-main/fonts/* static/fonts/
   cp -r system-css-main/icon/* static/icons/
   ```
3. Fix font paths in `static/css/system.css`:
   ```bash
   sed -i 's|url("fonts/|url("../fonts/|g' static/css/system.css
   ```

### Customization

To customize the System.css theme:

1. Edit `static/css/system.css` directly (for production changes)
2. Or modify `system-css-main/style.css` and re-copy (for source changes)

Add Streamlit-specific overrides in the `inject_system_css()` function.

## Resources

- **System.css GitHub**: https://github.com/sakofchit/system.css
- **System.css Documentation**: https://sakofchit.github.io/system.css/
- **Inspiration**: [98.css](https://github.com/jdan/98.css) (Windows 98 equivalent)
- **Fonts by**: [@blogmywiki](https://twitter.com/blogmywiki) (Chicago & Geneva recreations)

## Benefits

1. **Nostalgic UX**: Retro Mac OS aesthetic provides unique, memorable experience
2. **No JavaScript**: Pure CSS solution, lightweight and fast
3. **Offline-first**: No CDN dependencies, all assets served locally
4. **Customizable**: Easy to modify and extend with custom styles
5. **Framework agnostic**: Works with any frontend framework (including Streamlit)

## Design Agent Integration

When working with aesthetic/design agents:

- **Keep visual consistency**: All UI elements should follow System.css classes
- **Use available components**: Leverage existing `.window`, `.btn`, `.field-row` etc.
- **Test compatibility**: Ensure Streamlit widgets work with System.css styling
- **Respect monochrome**: Maintain the black & white aesthetic
- **Use appropriate fonts**: Chicago for headers, Monaco for code/inputs
