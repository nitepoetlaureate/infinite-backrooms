"""
Build Executable Script

Creates standalone executables using PyInstaller.
Supports macOS (.app), Windows (.exe), and Linux.

Usage:
    pip install pyinstaller
    python build_executable.py
"""

import os
import sys
import platform
import subprocess


def build_executable():
    """Build platform-specific executable."""

    print("🔨 AI Backrooms - Executable Builder")
    print("=" * 40)
    print()

    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("❌ PyInstaller not found!")
        print("Install with: pip install pyinstaller")
        sys.exit(1)

    system = platform.system()
    print(f"✅ Building for: {system}")
    print()

    # Common PyInstaller options
    options = [
        "main.py",
        "--name=AIBackrooms",
        "--onefile",
        "--windowed",
        "--clean",
    ]

    # Platform-specific options
    if system == "Darwin":  # macOS
        print("📦 Building macOS .app bundle...")
        options.extend([
            "--icon=assets/icon.icns" if os.path.exists("assets/icon.icns") else "",
        ])
    elif system == "Windows":
        print("📦 Building Windows .exe...")
        options.extend([
            "--icon=assets/icon.ico" if os.path.exists("assets/icon.ico") else "",
        ])
    else:  # Linux
        print("📦 Building Linux executable...")

    # Remove empty options
    options = [opt for opt in options if opt]

    # Run PyInstaller
    print()
    print("Running PyInstaller...")
    print(f"Command: pyinstaller {' '.join(options)}")
    print()

    try:
        subprocess.run(["pyinstaller"] + options, check=True)
        print()
        print("✅ Build successful!")
        print()
        print("Output location:")
        print(f"  - dist/AIBackrooms")
        print()

        # Show size
        if system == "Darwin":
            output_path = "dist/AIBackrooms.app"
        elif system == "Windows":
            output_path = "dist/AIBackrooms.exe"
        else:
            output_path = "dist/AIBackrooms"

        if os.path.exists(output_path):
            if os.path.isdir(output_path):
                import shutil
                size = sum(os.path.getsize(os.path.join(dirpath, filename))
                          for dirpath, _, filenames in os.walk(output_path)
                          for filename in filenames)
            else:
                size = os.path.getsize(output_path)

            size_mb = size / (1024 * 1024)
            print(f"📊 Size: {size_mb:.1f} MB")

    except subprocess.CalledProcessError as e:
        print()
        print(f"❌ Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_executable()
