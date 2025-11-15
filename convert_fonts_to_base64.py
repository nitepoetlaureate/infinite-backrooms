#!/usr/bin/env python3
"""Convert font files to base64 data URIs for embedding in CSS."""

import base64
from pathlib import Path

fonts = [
    ("ChicagoFLF.woff2", "woff2"),
    ("monaco.woff2", "woff2"),
    ("ChiKareGo2.woff2", "woff2"),
]

for font_file, font_format in fonts:
    font_path = Path("static/fonts") / font_file

    if not font_path.exists():
        print(f"Warning: {font_path} not found")
        continue

    with open(font_path, "rb") as f:
        font_data = base64.b64encode(f.read()).decode("utf-8")

    print(f"\n/* {font_file} */")
    print(f"src: url('data:font/{font_format};base64,{font_data}') format('{font_format}');")
