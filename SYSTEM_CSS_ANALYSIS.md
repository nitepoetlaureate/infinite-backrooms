# System.css Elements Being Ignored by Streamlit

## CRITICAL MISSING ELEMENTS:

### 1. CSS Custom Properties (Variables) NOT BEING USED
System.css defines these in :root but we're hardcoding everything:
```css
:root {
  --box-shadow: 2px 2px;
  --element-spacing: 8px;
  --grouped-element-spacing: 6px;
  --radio-width: 12px;
  --checkbox-width: 13px;
  --primary: #FFFFFF;
  --secondary: #000000;
  --tertiary: #A5A5A5;
  --disabled: #B6B7B8;
}
```
**Impact**: We're hardcoding values instead of using the theme variables.

### 2. BORDER-IMAGE SVG FOR BUTTONS (MAJOR VISUAL IMPACT)
The .btn class uses elaborate SVG border-images for authentic System 7 raised buttons:
```css
.btn {
  border-style: solid;
  border-width: 5.5px;
  border-image: url("data:image/svg+xml,...") 30 stretch;
}
```
**Impact**: Our buttons look flat, not like real System 7 buttons with that characteristic beveled edge.

### 3. INNER-BORDER / OUTER-BORDER PATTERNS
```css
.inner-border {
  border-top: 3.5px solid;
  border-bottom: 3.5px solid;
  border-left: 5px solid;
  border-right: 5px solid;
}
.outer-border {
  border: 2px solid;
  padding: 3px;
}
```
**Impact**: Missing the 3D inset/outset effect for panels and windows.

### 4. TITLE-BAR STRIPED PATTERN
```css
.title-bar {
  background: linear-gradient(var(--secondary) 50%, transparent 50%);
  background-size: 6.67% 13.33%;
  background-clip: content-box;
}
```
**Impact**: Headers don't have the iconic System 7 striped title bar look.

### 5. INSET BOX-SHADOW FOR INPUTS
```css
--border-field: inset -1px -1px #ffffff,
                inset 1px 1px #0c0c0c,
                inset -2px -2px #dfdfdf,
                inset 2px 2px #808080;
```
**Impact**: Input fields look flat instead of having the recessed 3D look.

### 6. PROPER CHECKBOX/RADIO PSEUDO-ELEMENTS
System.css uses ::before and ::after for checkboxes with proper spacing:
```css
input[type="checkbox"] + label::before {
  /* Box */
}
input[type="checkbox"]:checked + label::after {
  /* Checkmark image */
}
```
**Impact**: Our checkboxes don't look like System 7 checkboxes.

### 7. WINDOW CHROME (.window, .window-pane)
```css
.window {
  /* Window styling */
}
.window-pane {
  /* Scrollable content area */
}
```
**Impact**: Main content area doesn't look like a proper System 7 window.

## CLASSES WE'RE NOT USING AT ALL:
- `.standard-button` (min-width: 59px, min-height: 20px)
- `.standard-dialog` (dialogs with shadows)
- `.field-row` (form field spacing)
- `.separator` (horizontal divider)
- `.details-bar` (status bar)
- `.menu-items` (menu styling)
- `.heading` (section headers)

## VISUAL ELEMENTS BROKEN:
1. **Buttons**: No beveled edges (missing border-image SVG)
2. **Inputs**: No 3D inset effect (missing complex box-shadow)
3. **Panels**: No double-border effect (missing inner/outer borders)
4. **Headers**: No striped pattern (missing title-bar background)
5. **Checkboxes**: Not authentic System 7 style
6. **Windows**: No proper window chrome

## RECOMMENDED FIXES:
1. Extract and apply border-image SVG to ALL buttons
2. Use CSS custom properties throughout
3. Apply inner-border styling to panels/cards
4. Apply title-bar striped pattern to headers and active tabs
5. Use proper inset box-shadow for inputs
6. Create Streamlit-specific classes that map to system.css patterns
