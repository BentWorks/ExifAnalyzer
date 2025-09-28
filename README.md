# ExifAnalyzer

> 🔒 **Privacy-First Image Metadata Tool**

A lightweight, cross-platform utility for viewing, editing, and stripping metadata from image files. Designed for both CLI power users and casual GUI users who need to sanitize, inspect, or modify metadata for privacy, security, or organizational purposes.

## ✨ Features

- **🔍 Metadata Viewing**: Human-readable and JSON outputs with unified view across EXIF, IPTC, XMP, and format-specific metadata
- **✏️ Selective Editing**: Modify specific tags while preserving others
- **🧹 Privacy Protection**: Remove all metadata or target GPS/location data specifically
- **📁 Batch Processing**: Process multiple files with directory recursion support
- **💾 Safe Operations**: Automatic backups with pixel data integrity verification
- **🔄 Export/Import**: Save metadata as JSON or XMP sidecar files for later restoration
- **🖥️ Cross-Platform**: Works on Windows, macOS, and Linux
- **⚡ Fast & Lightweight**: Operations complete in under 1 second for typical images

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/ExifAnalyzer.git
cd ExifAnalyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# View metadata from an image
python -m src.exif_analyzer.cli.main view image.jpg

# Strip all metadata
python -m src.exif_analyzer.cli.main strip image.jpg

# Remove only GPS/location data
python -m src.exif_analyzer.cli.main strip --gps-only image.jpg

# Export metadata to JSON
python -m src.exif_analyzer.cli.main export image.jpg metadata.json

# Batch process all JPEGs in a directory
python -m src.exif_analyzer.cli.main batch strip photos/ --recursive

# View supported formats
python -m src.exif_analyzer.cli.main formats
```

## 📋 Supported Formats

| Format | Read | Write | Strip | Notes |
|--------|------|-------|-------|-------|
| **JPEG** | ✅ | ✅ | ✅ | EXIF, IPTC, XMP support |
| **PNG** | ✅ | ✅ | ✅ | tEXt, iTXt, zTXt, XMP chunks |
| **TIFF** | 🚧 | 🚧 | 🚧 | Planned for v0.2 |
| **WebP** | 🚧 | 🚧 | 🚧 | Planned for v0.2 |
| **GIF** | 🚧 | 🚧 | 🚧 | Planned for v0.2 |

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

## 📊 Current Status

### ✅ Phase 1: Core Metadata Engine (Complete)

- [x] Metadata abstraction layer
- [x] JPEG adapter (EXIF, IPTC, XMP)
- [x] PNG adapter (text chunks, XMP)
- [x] File safety mechanisms
- [x] Basic CLI interface
- [x] Comprehensive test suite (23 tests, 52% coverage)

### 🚧 Phase 2: CLI Interface (In Progress)

- [ ] Enhanced command-line features
- [ ] Advanced batch processing
- [ ] Configuration management
- [ ] Performance optimizations

### 📅 Planned Features

- **Phase 3**: GUI Interface with PySimpleGUI
- **Phase 4**: Additional format support (TIFF, WebP, GIF)
- **Phase 5**: Advanced metadata editing
- **Phase 6**: Packaging and distribution

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
- 🐛 [Issue Tracker](https://github.com/your-username/ExifAnalyzer/issues)
- 💬 [Discussions](https://github.com/your-username/ExifAnalyzer/discussions)

---

**⚠️ Important**: Always backup your images before performing metadata operations. While ExifAnalyzer includes safety mechanisms, it's good practice to keep original copies of important files.

**🔒 Privacy Note**: This tool is designed to enhance your privacy by removing metadata from images. However, always verify that sensitive data has been completely removed before sharing images publicly.