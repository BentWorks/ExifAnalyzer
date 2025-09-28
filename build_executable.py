"""
Build script for creating distributable executables.
"""
import subprocess
import sys
import shutil
from pathlib import Path
from build_config import *

def install_build_dependencies():
    """Install required build dependencies."""
    dependencies = [
        "pyinstaller",
        "pillow",
        "piexif",
        "PySimpleGUI",
        "click",
    ]

    print("Installing build dependencies...")
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep],
                         check=True, capture_output=True)
            print(f"[OK] {dep}")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to install {dep}: {e}")
            return False
    return True

def create_cli_executable():
    """Create CLI executable."""
    print("\nBuilding CLI executable...")

    # Basic PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", f"{PROJECT_NAME}-CLI",
        "--onefile",
        "--console",
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--specpath", str(BUILD_DIR),
        "--paths", str(SRC_DIR),  # Add source directory to Python path
        str(CLI_ENTRY)
    ]

    # Add hidden imports
    for import_name in PYINSTALLER_OPTIONS["hidden_imports"]:
        cmd.extend(["--hidden-import", import_name])

    # Add platform-specific options
    platform_config = get_platform_config()
    if "icon" in platform_config and Path(platform_config["icon"]).exists():
        cmd.extend(["--icon", platform_config["icon"]])

    try:
        subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)
        print("[OK] CLI executable created successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to create CLI executable: {e}")
        return False

def create_gui_executable():
    """Create GUI executable."""
    print("\nBuilding GUI executable...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", f"{PROJECT_NAME}-GUI",
        "--onefile",
        "--windowed",  # No console window
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--specpath", str(BUILD_DIR),
        "--paths", str(SRC_DIR),  # Add source directory to Python path
        str(GUI_ENTRY)
    ]

    # Add hidden imports
    for import_name in PYINSTALLER_OPTIONS["hidden_imports"]:
        cmd.extend(["--hidden-import", import_name])

    # Add platform-specific options
    platform_config = get_platform_config()
    if "icon" in platform_config and Path(platform_config["icon"]).exists():
        cmd.extend(["--icon", platform_config["icon"]])

    try:
        subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)
        print("[OK] GUI executable created successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to create GUI executable: {e}")
        return False

def create_version_info():
    """Create version information file for Windows."""
    if not sys.platform.startswith('win'):
        return

    version_info = f"""
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({VERSION.replace('-beta', '').replace('.', ', ')}, 0),
    prodvers=({VERSION.replace('-beta', '').replace('.', ', ')}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [StringStruct(u'CompanyName', u'{AUTHOR}'),
           StringStruct(u'FileDescription', u'{DESCRIPTION}'),
           StringStruct(u'FileVersion', u'{VERSION}'),
           StringStruct(u'InternalName', u'{PROJECT_NAME}'),
           StringStruct(u'LegalCopyright', u'Copyright © 2025 {AUTHOR}'),
           StringStruct(u'OriginalFilename', u'{PROJECT_NAME}.exe'),
           StringStruct(u'ProductName', u'{PROJECT_NAME}'),
           StringStruct(u'ProductVersion', u'{VERSION}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)"""

    version_file = PROJECT_ROOT / "version_info.txt"
    version_file.write_text(version_info)
    print("Created version information file")

def create_release_package():
    """Create release package with documentation."""
    print("\nCreating release package...")

    # Create release directory
    release_dir = DIST_DIR / f"{PROJECT_NAME}-{VERSION}"
    release_dir.mkdir(exist_ok=True)

    # Copy executables
    for exe_file in DIST_DIR.glob("*.exe"):
        if exe_file.is_file():
            shutil.copy2(exe_file, release_dir)

    # Copy documentation
    docs_to_copy = [
        "README.md",
        "Instructions.md",
        "changelog.md",
        "LICENSE" if Path("LICENSE").exists() else None
    ]

    for doc in docs_to_copy:
        if doc and Path(doc).exists():
            shutil.copy2(doc, release_dir)

    # Create quick start guide
    quick_start = release_dir / "QUICK_START.txt"
    quick_start.write_text(f"""
{PROJECT_NAME} v{VERSION} - Quick Start Guide

=== Installation ===
1. Extract all files to a folder of your choice
2. No additional installation required!

=== Usage ===

Command Line Interface:
- Run: {PROJECT_NAME}-CLI.exe --help
- View image metadata: {PROJECT_NAME}-CLI.exe view image.jpg
- Remove metadata: {PROJECT_NAME}-CLI.exe strip image.jpg

Graphical Interface:
- Run: {PROJECT_NAME}-GUI.exe
- Use the file browser to select images
- Click operations to modify metadata

=== Documentation ===
- Full instructions: Instructions.md
- Change log: changelog.md
- Project info: README.md

=== Support ===
For help and bug reports, see the project documentation.

Enjoy using {PROJECT_NAME}!
""")

    print(f"Release package created: {release_dir}")
    return release_dir

def main():
    """Main build process."""
    print(f"Building {PROJECT_NAME} v{VERSION}")
    print("=" * 50)

    # Create build directories
    create_build_directories()

    # Install dependencies
    if not install_build_dependencies():
        return False

    # Create version info for Windows
    create_version_info()

    # Build executables
    cli_success = create_cli_executable()
    gui_success = create_gui_executable()

    if cli_success and gui_success:
        # Create release package
        release_dir = create_release_package()

        print("\n" + "=" * 50)
        print("Build completed successfully!")
        print(f"Release package: {release_dir}")
        print("\nNext steps:")
        print("1. Test executables on target platforms")
        print("2. Create installer packages")
        print("3. Prepare for beta distribution")

        return True
    else:
        print("\nBuild failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)