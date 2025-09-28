"""
Build configuration for PyInstaller executable creation.
"""
import os
import sys
from pathlib import Path

# Project metadata
PROJECT_NAME = "ExifAnalyzer"
VERSION = "1.0.0-beta"
AUTHOR = "ExifAnalyzer Team"
DESCRIPTION = "Cross-platform Image Metadata Tool"

# Build paths
PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"

# Entry points
CLI_ENTRY = PROJECT_ROOT / "cli_launcher.py"
GUI_ENTRY = PROJECT_ROOT / "gui_launcher.py"

# PyInstaller configuration
PYINSTALLER_OPTIONS = {
    "name": PROJECT_NAME,
    "onefile": True,
    "windowed": False,  # Set to True for GUI version
    "icon": None,  # Add icon path when available
    "add_data": [
        # Add any data files needed
    ],
    "hidden_imports": [
        "PIL",
        "piexif",
        "PySimpleGUI",
        "click",
        "exif_analyzer",
        "exif_analyzer.core",
        "exif_analyzer.core.engine",
        "exif_analyzer.core.metadata",
        "exif_analyzer.adapters",
        "exif_analyzer.core.base_adapter",
        "exif_analyzer.adapters.jpeg_adapter",
        "exif_analyzer.adapters.png_adapter",
        "exif_analyzer.cli.progress",
    ],
    "exclude_modules": [
        "tkinter",  # Exclude if not needed
    ]
}

# Platform-specific configurations
WINDOWS_CONFIG = {
    "icon": "assets/icon.ico",
    "version_file": "version_info.txt",
    "uac_admin": False,
}

MACOS_CONFIG = {
    "icon": "assets/icon.icns",
    "bundle_identifier": "com.exifanalyzer.app",
}

LINUX_CONFIG = {
    "icon": "assets/icon.png",
}

def get_platform_config():
    """Get platform-specific configuration."""
    if sys.platform.startswith('win'):
        return WINDOWS_CONFIG
    elif sys.platform.startswith('darwin'):
        return MACOS_CONFIG
    else:
        return LINUX_CONFIG

def create_build_directories():
    """Create necessary build directories."""
    BUILD_DIR.mkdir(exist_ok=True)
    DIST_DIR.mkdir(exist_ok=True)

    # Create assets directory if it doesn't exist
    assets_dir = PROJECT_ROOT / "assets"
    assets_dir.mkdir(exist_ok=True)

    return assets_dir