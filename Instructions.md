# ExifAnalyzer - Complete Usage Guide

**Last Updated:** 2025-09-27
**Version:** 1.0.0-beta (Production Ready)

This document provides comprehensive instructions for using ExifAnalyzer's CLI and GUI interfaces.

---

## 🚀 Quick Start

### No Installation Required!
ExifAnalyzer comes as ready-to-run executables:
- **ExifAnalyzer-GUI.exe** - Easy-to-use graphical interface
- **ExifAnalyzer-CLI.exe** - Powerful command-line interface

### 30-Second Start
1. Extract the ExifAnalyzer folder anywhere
2. Double-click `ExifAnalyzer-GUI.exe` for point-and-click operation
3. OR open Command Prompt and run `ExifAnalyzer-CLI.exe --help`

---

## 🖼️ GUI Interface Guide

### Getting Started with GUI
1. **Launch**: Double-click `ExifAnalyzer-GUI.exe`
2. **Select Images**: Use either method:
   - **Single File**: Click "Browse" next to "File:" field
   - **Browse Folder**: Click "Browse" next to "Folder:" field

### Main Interface

#### File Selection Panel (Left)
- **File Browser**: Direct file selection with image filters
- **Folder Browser**: Browse folders to see all images
- **File List**: Shows all files in selected folder
- **Refresh Button**: Updates the file list

#### Image Preview Panel (Center)
- **Preview**: Automatic image preview with size info
- **File Details**: Image dimensions, color mode, file size

#### Metadata Panel (Right)
- **File Info**: Name, format, size, GPS status
- **Metadata Tree**: Expandable view of all metadata
- **Privacy Warnings**: GPS data highlighted in red

### Key Operations

#### Viewing Metadata
1. Select an image using File or Folder browse
2. Metadata appears automatically in the right panel
3. Expand categories (EXIF, IPTC, XMP) to see details
4. Privacy-sensitive data is marked with warning icons

#### Removing Metadata
- **Strip All Metadata**: Removes everything (EXIF, IPTC, XMP)
- **Strip GPS Only**: Removes only location data, keeps camera settings
- **Automatic Backup**: Original files are automatically backed up

#### Privacy Check
- Click "Show Privacy Check" to scan for sensitive data
- Shows all privacy-risky metadata (GPS, device info, etc.)
- Option to immediately remove GPS data

#### Export/Import
- **Export**: Save metadata to JSON file for backup
- **Import**: Restore metadata from previous export (future feature)

---

## 💻 CLI Interface Guide

### Basic Syntax
```cmd
ExifAnalyzer-CLI.exe [OPTIONS] COMMAND [ARGS]...
```

### Global Options
- `-v, --verbose` - Enable detailed output
- `-q, --quiet` - Show only errors
- `--help` - Show help message

---

## 🔍 Viewing Metadata

### View Image Metadata
```bash
# Human-readable format
python -m src.exif_analyzer.cli.main view image.jpg

# JSON format (for scripts/automation)
python -m src.exif_analyzer.cli.main view image.jpg --json

# Verbose output (shows more details)
python -m src.exif_analyzer.cli.main -v view image.jpg
```

**Example Output:**
```
File: C:\photos\vacation.jpg
Format: JPEG
Size: 2456789 bytes
Has metadata: True
Has GPS data: True

Metadata blocks:
  EXIF: 15 keys
  IPTC: 0 keys
  XMP: 3 keys
  Custom: 0 keys
```

---

## 🧹 Removing Metadata

### Strip All Metadata
```bash
# Creates automatic backup, overwrites original
python -m src.exif_analyzer.cli.main strip image.jpg

# Save to new file (keeps original unchanged)
python -m src.exif_analyzer.cli.main strip image.jpg --output cleaned_image.jpg

# Disable automatic backup (use with caution)
python -m src.exif_analyzer.cli.main strip image.jpg --no-backup
```

### Remove Only GPS/Location Data
```bash
# Strip only privacy-sensitive location data
python -m src.exif_analyzer.cli.main strip image.jpg --gps-only

# GPS stripping with custom output
python -m src.exif_analyzer.cli.main strip image.jpg --gps-only --output safe_image.jpg
```

---

## 💾 Export & Import Operations

### Export Metadata to File
```bash
# Export to JSON (default format)
python -m src.exif_analyzer.cli.main export image.jpg metadata.json

# Export to XMP sidecar (when available)
python -m src.exif_analyzer.cli.main export image.jpg metadata.xmp --format xmp
```

### Restore Metadata from File
```bash
# Restore from JSON backup
python -m src.exif_analyzer.cli.main restore image.jpg metadata.json

# Restore without creating backup
python -m src.exif_analyzer.cli.main restore image.jpg metadata.json --no-backup
```

---

## 📁 Batch Processing

### Process Multiple Files
```bash
# Strip metadata from all images in folder
python -m src.exif_analyzer.cli.main batch strip photos/

# Include subdirectories
python -m src.exif_analyzer.cli.main batch strip photos/ --recursive

# Process specific file types only
python -m src.exif_analyzer.cli.main batch strip photos/ --pattern "*.jpg"

# Save processed files to different directory
python -m src.exif_analyzer.cli.main batch strip photos/ --output-dir cleaned_photos/
```

### Batch Options
- `--recursive, -r` - Process subdirectories
- `--pattern` - File pattern to match (e.g., "*.jpg", "IMG_*")
- `--output-dir` - Directory for processed files
- `--gps-only` - Strip only GPS data from all files
- `--dry-run` - Preview what would be processed without making changes

### Dry Run Example
```bash
# See what files would be processed
python -m src.exif_analyzer.cli.main batch strip photos/ --recursive --dry-run
```

**Output:**
```
Found 15 image files
Dry run - would process:
  photos/IMG_001.jpg
  photos/IMG_002.jpg
  photos/vacation/beach.jpg
  ...
```

---

## 🔧 Utility Commands

### List Supported Formats
```bash
python -m src.exif_analyzer.cli.main formats
```

**Output:**
```
Supported image formats:
  .jpg
  .jpeg
  .png
```

---

## 📝 Common Usage Examples

### Privacy Protection Workflow
```bash
# 1. Check what metadata exists
python -m src.exif_analyzer.cli.main view photo.jpg

# 2. Export metadata for backup
python -m src.exif_analyzer.cli.main export photo.jpg backup.json

# 3. Remove GPS data only (keep camera settings)
python -m src.exif_analyzer.cli.main strip photo.jpg --gps-only

# 4. Verify GPS data is gone
python -m src.exif_analyzer.cli.main view photo.jpg
```

### Batch Privacy Cleaning
```bash
# Clean all photos before sharing
python -m src.exif_analyzer.cli.main batch strip photos_to_share/ --gps-only --recursive

# Process vacation photos
python -m src.exif_analyzer.cli.main batch strip vacation2023/ -r --output-dir vacation2023_clean/
```

### Metadata Analysis
```bash
# Verbose analysis with JSON output for processing
python -m src.exif_analyzer.cli.main -v view photo.jpg --json > analysis.json

# Quick check for GPS data across multiple files
for file in *.jpg; do
  echo "Checking $file..."
  python -m src.exif_analyzer.cli.main view "$file" | grep "Has GPS"
done
```

---

## ⚠️ Important Safety Notes

### Automatic Backups
- **Default behavior:** ExifAnalyzer creates automatic backups before modifying files
- **Backup location:** Same directory as original with timestamp
- **Backup format:** `filename.backup.timestamp.extension`
- **Disable with:** `--no-backup` flag (use carefully)

### File Safety
- **Pixel integrity:** Original image pixels are never modified
- **Atomic operations:** Changes are applied safely or not at all
- **Rollback:** Failed operations automatically restore from backup

### Best Practices
1. **Always test first:** Use `--dry-run` for batch operations
2. **Keep originals:** Don't disable backups for important files
3. **Verify results:** Check output files after processing
4. **Export metadata:** Save metadata before stripping for future reference

---

## 🐛 Troubleshooting

### Common Issues

**Error: "No adapter available for format"**
```bash
# Check supported formats
python -m src.exif_analyzer.cli.main formats
```

**Error: "File not found"**
- Verify file path is correct
- Use absolute paths if relative paths don't work
- Check file permissions

**Error: "Cannot read JPEG file"**
- File may be corrupted
- File extension may not match actual format
- Try opening file in image viewer to verify integrity

### Getting Help
```bash
# General help
python -m src.exif_analyzer.cli.main --help

# Command-specific help
python -m src.exif_analyzer.cli.main view --help
python -m src.exif_analyzer.cli.main strip --help
python -m src.exif_analyzer.cli.main batch --help
```

### Verbose Output
Use `-v` flag for detailed logging:
```bash
python -m src.exif_analyzer.cli.main -v strip photo.jpg
```

---

## 🔄 Updates & Version Notes

### Phase 1 (Current) - Core Engine
- ✅ JPEG metadata support (EXIF, IPTC, XMP)
- ✅ PNG metadata support (text chunks, XMP)
- ✅ CLI interface with all core commands
- ✅ Batch processing capabilities
- ✅ Privacy-focused GPS detection and removal

### Planned Features (Future Phases)
- **Phase 2:** Enhanced CLI with configuration files
- **Phase 3:** GUI interface for non-technical users
- **Phase 4:** TIFF, WebP, GIF format support
- **Phase 5:** Advanced metadata editing capabilities
- **Phase 6:** Packaging and distribution

---

---

## 🖥️ GUI Application

### Running the GUI
```bash
# Activate virtual environment
venv\Scripts\activate

# Launch GUI application
python -m src.exif_analyzer.gui.main
```

### GUI Features

#### Main Interface
- **Three-panel layout:**
  - Left: File browser with folder selection
  - Center: Image preview with automatic resizing
  - Right: Metadata tree view with detailed information

#### File Operations
1. **Select Folder**: Browse to folder containing images
2. **File List**: Automatically filters for supported formats (.jpg, .png, etc.)
3. **Image Preview**: Click any file to see preview and metadata

#### Metadata Operations
- **Strip All Metadata**: Remove all metadata with confirmation
- **Strip GPS Only**: Remove only location/GPS data (privacy-focused)
- **Export Metadata**: Save metadata to JSON file
- **Privacy Check**: Scan and highlight privacy-sensitive data

#### Privacy Features
- **GPS Detection**: Automatically highlights files with location data
- **Sensitive Data Warning**: Shows privacy-risky metadata entries
- **Color-coded Display**:
  - 🔴 Red: GPS data present (privacy risk)
  - 🟢 Green: No GPS data found
  - ⚠️ Yellow: Privacy-sensitive metadata detected

### GUI Workflow Example
1. **Open GUI**: `python -m src.exif_analyzer.gui.main`
2. **Select Folder**: Click "Browse" and choose photo directory
3. **Choose Image**: Click on any image file in the list
4. **Review Metadata**: Expand EXIF/IPTC/XMP blocks in tree view
5. **Privacy Check**: Click "Show Privacy Check" to scan for sensitive data
6. **Strip GPS**: Click "Strip GPS Only" to remove location data
7. **Export**: Click "Export Metadata" to save metadata before cleaning

---

## 📞 Support

### CLI Interface
If you encounter CLI issues:
1. Check this instructions document for solutions
2. Run with `-v` flag for detailed output
3. Verify file formats are supported
4. Use `--help` for command-specific assistance

### GUI Interface
If you encounter GUI issues:
1. Ensure PySimpleGUI is properly installed
2. Check console output for error messages
3. Verify image files are in supported formats
4. Try running CLI commands to isolate issues

### General Troubleshooting
- Check project documentation in repository
- Verify virtual environment is activated
- Ensure all dependencies are installed
- Test with sample images first

**Note:** This document is automatically maintained and updated as new features are added to ExifAnalyzer.