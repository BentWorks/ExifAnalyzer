"""
Simple test script for GUI functionality.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    import PySimpleGUI as sg
    print("✓ PySimpleGUI imported successfully")

    from src.exif_analyzer.gui.main import ExifAnalyzerGUI
    print("✓ ExifAnalyzerGUI class imported successfully")

    from src.exif_analyzer.core.engine import MetadataEngine
    engine = MetadataEngine()
    print(f"✓ MetadataEngine initialized with {len(engine.get_supported_formats())} formats")

    print("\\n🎉 GUI components are ready!")
    print("\\nTo run the GUI:")
    print("python -m src.exif_analyzer.gui.main")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)