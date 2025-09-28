#!/usr/bin/env python3
"""
CLI Launcher for ExifAnalyzer
Properly sets up module paths and launches the CLI interface.
"""
import sys
import os
from pathlib import Path

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
if src_dir.exists():
    sys.path.insert(0, str(src_dir))

# Import and run the CLI
if __name__ == '__main__':
    from exif_analyzer.cli.main import cli
    cli()