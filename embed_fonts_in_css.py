#!/usr/bin/env python3
"""Embed base64 fonts directly into system.css for Streamlit inline injection."""

import base64
import re
from pathlib import Path

# Read the CSS file
css_path = Path("static/css/system.css")
with open(css_path) as f:
    css_content = f.read()

# Font files to embed
fonts = {
    "../fonts/ChicagoFLF.woff2": ("static/fonts/ChicagoFLF.woff2", "woff2"),
    "../fonts/monaco.woff2": ("static/fonts/monaco.woff2", "woff2"),
    "../fonts/ChiKareGo2.woff2": ("static/fonts/ChiKareGo2.woff2", "woff2"),
    "../fonts/FindersKeepers.woff2": ("static/fonts/FindersKeepers.woff2", "woff2"),
}

# Replace each font URL with base64 data URI
for url_path, (file_path, font_format) in fonts.items():
    font_file = Path(file_path)

    if not font_file.exists():
        print(f"Warning: {font_file} not found, skipping")
        continue

    # Read and encode font
    with open(font_file, "rb") as f:
        font_data = base64.b64encode(f.read()).decode("utf-8")

    # Create data URI
    data_uri = f"data:font/{font_format};base64,{font_data}"

    # Replace in CSS (escape special regex chars in path)
    pattern = re.escape(f'url("{url_path}")')
    replacement = f'url("{data_uri}")'
    css_content = css_content.replace(f'url("{url_path}")', f'url("{data_uri}")')

    print(f"Embedded: {url_path} ({len(font_data)} chars)")

# Write embedded CSS
output_path = Path("static/css/system_embedded.css")
with open(output_path, "w") as f:
    f.write(css_content)

print(f"\nWrote embedded CSS to: {output_path}")
print(f"File size: {output_path.stat().st_size} bytes")
