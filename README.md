# ExifAnalyzer

> 🔒 **Privacy-First Image Metadata Tool**
> **✅ v1.0.0-beta - Production Ready**

A complete, cross-platform utility for viewing and stripping metadata from image files. Features both CLI and GUI interfaces for privacy-focused image processing. **Ready-to-use Windows executables included** - no installation required!

## ✨ Features

- **🔍 Metadata Viewing**: Comprehensive EXIF, IPTC, and XMP data display
- **🧹 Privacy Protection**: Remove all metadata or GPS/location data only
- **📁 Batch Processing**: Process multiple files and directories
- **💾 Safe Operations**: Automatic backups with pixel data integrity verification
- **🖥️ Dual Interface**: Command-line tool and user-friendly GUI
- **📦 Ready-to-Run**: Windows executables included, no installation needed
- **🏃 Fast & Lightweight**: Instant processing for typical images
- **🔒 Privacy-First**: Local processing only, no network connectivity

## 🚀 Quick Start

### Ready-to-Use Executables (Windows)

**Download the latest release** and extract the zip file:
- `ExifAnalyzer-GUI.exe` - User-friendly graphical interface
- `ExifAnalyzer-CLI.exe` - Command-line interface

### GUI Usage
```bash
# Run the GUI
ExifAnalyzer-GUI.exe

# 1. Click "File" to select an image
# 2. View metadata in the tree display
# 3. Use "Strip All Metadata" or "Strip GPS Only" buttons
# 4. Privacy warnings highlight sensitive data in red
```

### CLI Usage
```bash
# View metadata from an image
ExifAnalyzer-CLI.exe view image.jpg

# Strip all metadata
ExifAnalyzer-CLI.exe strip image.jpg

# Remove only GPS/location data
ExifAnalyzer-CLI.exe strip --gps-only image.jpg

# Batch process multiple files
ExifAnalyzer-CLI.exe strip *.jpg

# Get help
ExifAnalyzer-CLI.exe --help
```

### Development Installation

```bash
git clone https://github.com/BentWorks/ExifAnalyzer.git
cd ExifAnalyzer
pip install -r requirements.txt
python cli_launcher.py --help  # CLI
python gui_launcher.py          # GUI
```

## 📋 Supported Formats

| Format | View | Strip | Notes |
|--------|------|-------|-------|
| **JPEG** | ✅ | ✅ | Complete EXIF, IPTC, XMP support |
| **PNG** | ✅ | ✅ | Text chunks and XMP metadata |
| **TIFF** | 🚧 | 🚧 | Planned for v1.1 |
| **WebP** | 🚧 | 🚧 | Planned for v1.1 |

## 🏗️ Architecture

ExifAnalyzer uses a modular architecture with format-specific adapters:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI/GUI       │────│  Metadata Engine │────│  File Safety    │
│   Interface     │    │   Orchestrator   │    │   Manager       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
             ┌──────▼───┐ ┌───▼────┐ ┌──▼─────┐
             │  JPEG    │ │  PNG   │ │ Future │
             │ Adapter  │ │Adapter │ │Adapters│
             └──────────┘ └────────┘ └────────┘
```

### Core Components

- **`MetadataEngine`**: Central orchestrator that routes operations to format-specific adapters
- **`BaseMetadataAdapter`**: Abstract interface ensuring consistent behavior across formats
- **`ImageMetadata`**: Unified metadata structure with privacy-aware operations
- **`FileSafetyManager`**: Handles backups, integrity verification, and atomic operations

## 🛡️ Privacy & Security

ExifAnalyzer is designed with privacy as a core principle:

- **🔒 Local Processing Only**: No cloud connectivity or data transmission
- **🔐 GPS Detection**: Automatically identifies and removes location data
- **📱 Device Anonymization**: Strips camera make, model, and serial numbers
- **🔍 Privacy Audit**: Lists all privacy-sensitive metadata before removal
- **✅ Integrity Verification**: Ensures pixel data remains unchanged

### Privacy-Sensitive Data Detected

- GPS coordinates and altitude
- Camera make, model, serial numbers
- Software and lens information
- User names and copyright info
- Creation locations and addresses

## 🔧 Development

### Project Structure

```
ExifAnalyzer/
├── src/exif_analyzer/          # Main source code
│   ├── core/                   # Core metadata engine
│   ├── adapters/               # Format-specific handlers
│   ├── cli/                    # Command-line interface
│   └── gui/                    # GUI interface (planned)
├── tests/                      # Test suite
├── docs/                       # Documentation
└── examples/                   # Usage examples
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src/exif_analyzer --cov-report=html

# Run specific test file
python -m pytest tests/test_jpeg_adapter.py -v
```

### Code Quality

```bash
# Format code
python -m black src/ tests/

# Lint code
python -m flake8 src/ tests/

# Type checking
python -m mypy src/
```

## 📊 Project Status

### ✅ v1.0.0-beta Released (Production Ready)

**Complete Implementation:**
- [x] Full CLI interface with all commands
- [x] Complete GUI interface with file browser
- [x] JPEG metadata handling (EXIF, IPTC, XMP)
- [x] PNG metadata handling (text chunks, XMP)
- [x] Privacy-focused GPS/location detection
- [x] Safe file operations with automatic backups
- [x] Windows executables (32MB each, self-contained)
- [x] Comprehensive test suite (116 tests, 67% coverage)
- [x] Complete documentation and user guides

**Key Achievements:**
- **File Safety**: 94% test coverage for critical operations
- **Zero Installation**: Ready-to-run Windows executables
- **Production Quality**: Handles real-world image processing safely
- **User-Friendly**: Both technical CLI and intuitive GUI interfaces

### 🚀 What's Next

- **v1.1**: Additional format support (TIFF, WebP)
- **v1.2**: Cross-platform executables (macOS, Linux)
- **v1.3**: Advanced batch processing features

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`python -m pytest`)
6. Format code (`python -m black src/ tests/`)
7. Commit changes (`git commit -m 'Add amazing feature'`)
8. Push to branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **PIL (Pillow)**: Core image processing capabilities
- **piexif**: Comprehensive EXIF metadata handling
- **python-xmp-toolkit**: XMP metadata support
- **Click**: Elegant command-line interface framework
- **PySimpleGUI**: Simple and powerful GUI framework

## 📞 Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/BentWorks/ExifAnalyzer/issues)
- 💬 [Discussions](https://github.com/BentWorks/ExifAnalyzer/discussions)

---

**⚠️ Important**: Always backup your images before performing metadata operations. While ExifAnalyzer includes safety mechanisms, it's good practice to keep original copies of important files.

**🔒 Privacy Note**: This tool is designed to enhance your privacy by removing metadata from images. However, always verify that sensitive data has been completely removed before sharing images publicly.