# AI Agent Onboarding Guide

> **For AI Assistants Taking Over ExifAnalyzer Development**

This document provides comprehensive information for AI agents to quickly understand and contribute to the ExifAnalyzer project. Everything you need to know to hit the ground running.

## 🎯 Project Overview

**ExifAnalyzer v1.0.0-beta** is a **production-ready** privacy-focused image metadata tool with both CLI and GUI interfaces. The project is **complete and functional** - all core features are implemented and tested.

### Current Status: ✅ PRODUCTION READY
- **116 tests** (67% coverage overall, 94% for critical file safety)
- **Working Windows executables** (self-contained, 32MB each)
- **Complete documentation** and user guides
- **GitHub repository** live at https://github.com/BentWorks/ExifAnalyzer
- **Zero known critical bugs** after fixing pixel corruption issue

## 🏗️ Architecture Overview

### Core Design Philosophy
- **Privacy-first**: Local processing only, no network connectivity
- **Safety-first**: Automatic backups, pixel integrity verification
- **Modular**: Format-specific adapters for extensibility
- **User-friendly**: Both technical CLI and intuitive GUI

### Key Components

```
ExifAnalyzer/
├── src/exif_analyzer/
│   ├── core/                    # Core engine and utilities
│   │   ├── engine.py           # Main metadata orchestrator
│   │   ├── metadata.py         # Unified metadata structures
│   │   ├── file_safety.py      # Critical: backup & integrity (94% coverage)
│   │   ├── base_adapter.py     # Abstract adapter interface
│   │   ├── config.py           # Configuration management
│   │   ├── exceptions.py       # Custom exception hierarchy
│   │   └── logger.py           # Centralized logging
│   ├── adapters/               # Format-specific handlers
│   │   ├── jpeg_adapter.py     # JPEG/EXIF/IPTC/XMP (CRITICAL FILE)
│   │   └── png_adapter.py      # PNG text chunks & XMP
│   ├── cli/                    # Command-line interface
│   │   ├── main.py            # CLI entry point (Click-based)
│   │   └── progress.py        # Progress indicators
│   └── gui/                    # Graphical interface
│       └── main.py            # GUI entry point (PySimpleGUI)
├── cli_launcher.py             # CLI executable entry point
├── gui_launcher.py             # GUI executable entry point
├── build_executable.py         # PyInstaller build script
├── tests/                      # Comprehensive test suite
└── dist/                       # Built executables and packages
```

## 🔧 Development Workflow

### Essential Commands
```bash
# Run tests (ALWAYS run before commits)
python -m pytest tests/ -v

# Build executables
python build_executable.py

# Run from source
python cli_launcher.py --help    # CLI
python gui_launcher.py           # GUI

# Test coverage
python -m pytest tests/ --cov=src/exif_analyzer --cov-report=html
```

### Build System
- **PyInstaller** creates self-contained executables
- **build_executable.py** handles both CLI and GUI builds
- **Build time**: ~30 seconds for both executables
- **Output**: `dist/ExifAnalyzer-CLI.exe` and `dist/ExifAnalyzer-GUI.exe`

## 🚨 Critical Information

### CRITICAL FILE: jpeg_adapter.py
The `src/exif_analyzer/adapters/jpeg_adapter.py` file contains **critical pixel corruption bug fix**:

- **Lines 204-205, 284-285**: Uses `verify_jpeg_integrity()` NOT `verify_pixel_integrity()`
- **Key Fix**: MSE-based integrity check for JPEG lossy compression
- **DO NOT CHANGE** without thorough testing - this prevents image corruption

### File Safety System
The `src/exif_analyzer/core/file_safety.py` module is **mission-critical**:
- **94% test coverage** - highest in the project
- Handles automatic backups before any file modifications
- Implements atomic file operations with rollback
- JPEG-specific integrity verification vs PNG pixel-perfect verification

### Test Requirements
- **Minimum 67% overall coverage** before any release
- **File safety must maintain 94%+ coverage**
- **All 116 tests must pass** before building executables
- Run `python -m pytest tests/ -v` for full test suite

## 📁 Key Files to Understand

### Entry Points
- **cli_launcher.py**: Sets up Python path, launches CLI
- **gui_launcher.py**: Sets up Python path, launches GUI

### Core Engine
- **core/engine.py**: Main `MetadataEngine` class
- **core/metadata.py**: `ImageMetadata`, `MetadataBlock` classes
- **core/file_safety.py**: `FileSafetyManager` - CRITICAL for data safety

### Format Adapters
- **adapters/jpeg_adapter.py**: JPEG/EXIF/IPTC/XMP - MOST COMPLEX
- **adapters/png_adapter.py**: PNG text chunks - SIMPLER

### Interfaces
- **cli/main.py**: Click-based CLI with view/strip commands
- **gui/main.py**: PySimpleGUI interface with file browser

## 🧪 Testing Strategy

### Test Structure
```
tests/
├── conftest.py              # Test fixtures and utilities
├── test_core_engine.py      # Engine orchestration tests
├── test_file_safety.py      # CRITICAL: File safety operations
├── test_jpeg_adapter.py     # JPEG adapter functionality
├── test_png_adapter.py      # PNG adapter functionality
└── test_cli_commands.py     # CLI interface tests
```

### Test Coverage Requirements
- **File Safety**: 94%+ (mission-critical)
- **Core Engine**: 80%+
- **CLI Interface**: 83%+ (current)
- **Overall Project**: 67%+ (current)

### Creating Test Images
```python
# Use conftest.py utilities for test images
def test_my_feature(jpeg_with_exif, png_with_text):
    # Test with pre-made images
    pass
```

## 🐛 Common Issues & Solutions

### Build Issues
1. **"Module not found"**: Check `hidden_imports` in `build_config.py`
2. **"Permission denied"**: Close running executables before rebuild
3. **Import errors**: Verify launcher scripts set Python path correctly

### JPEG Integrity Failures
- **Symptom**: "Pixel data corrupted during metadata stripping"
- **Cause**: Using pixel-perfect verification on lossy JPEG compression
- **Solution**: Ensure `verify_jpeg_integrity()` is used (MSE-based check)

### PNG vs JPEG Differences
- **PNG**: Lossless, can use pixel-perfect integrity verification
- **JPEG**: Lossy compression, requires MSE-based similarity check
- **Key**: Different integrity verification methods per format

## 🚀 Future Enhancement Areas

### High-Priority Additions (v1.1)
1. **TIFF Support**: Similar to JPEG but with different tag structure
2. **WebP Support**: Google's format with XMP embedding
3. **Batch Processing**: Enhanced CLI batch operations

### Medium-Priority (v1.2)
1. **Cross-platform Builds**: macOS and Linux executables
2. **Advanced Filtering**: Selective metadata preservation
3. **Metadata Editing**: Modify specific tags (currently view/strip only)

### Low-Priority (v1.3+)
1. **Plugin System**: Custom format adapters
2. **Configuration GUI**: User preference management
3. **Metadata Templates**: Bulk metadata application

## 📚 Documentation Ecosystem

### User Documentation
- **README.md**: Project overview and quick start
- **INSTALLATION_GUIDE.md**: Detailed setup instructions
- **Instructions.md**: Complete user manual
- **QUICK_START.txt**: 2-minute tutorial (in release package)

### Developer Documentation
- **TECH_SPEC.md**: Technical architecture specification
- **IMPLEMENTATION_PLAN.md**: Original development phases
- **RELEASE_CHECKLIST.md**: Quality assurance checklist
- **coverage_report.md**: Detailed test coverage analysis

### Project Management
- **changelog.md**: Complete development history
- **BETA_TESTING.md**: Beta testing framework

## 🔄 Git Workflow

### Repository Structure
- **Main branch**: Production-ready code
- **All commits**: Should include comprehensive commit messages
- **GitHub URL**: https://github.com/BentWorks/ExifAnalyzer

### Commit Guidelines
```bash
git add .
git commit -m "Descriptive commit message

Detailed explanation of changes and why they were made.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

## 🎯 Quick Start for New AI Agents

### 1. Initial Assessment (5 minutes)
```bash
# Check current status
python -m pytest tests/ -v          # All tests should pass
ls dist/                            # Check for executables
git status                          # Check repository state
```

### 2. Understand Key Components (10 minutes)
- Read `src/exif_analyzer/core/engine.py` - main orchestrator
- Examine `src/exif_analyzer/adapters/jpeg_adapter.py` - most complex adapter
- Review `tests/test_file_safety.py` - critical safety tests

### 3. Test Your Understanding (5 minutes)
```bash
# Run CLI
python cli_launcher.py --help

# Test GUI (if on Windows)
python gui_launcher.py

# Build executables
python build_executable.py
```

### 4. Ready to Contribute!
You now understand:
- ✅ Project architecture and philosophy
- ✅ Critical safety mechanisms
- ✅ Build and test processes
- ✅ File structure and responsibilities
- ✅ Common issues and solutions

## 🆘 Emergency Procedures

### If Tests Fail
1. **Never commit/build** with failing tests
2. Check recent changes to critical files
3. Review `jpeg_adapter.py` integrity verification
4. Ensure no file safety regressions

### If Executables Don't Work
1. Close any running executables
2. Check `build_executable.py` hidden imports
3. Verify launcher scripts are correct
4. Test with `python cli_launcher.py` first

### If Metadata Operations Fail
1. Check backup files are created (`*.bak`)
2. Verify pixel integrity checks are appropriate for format
3. Test with simple images first
4. Review `file_safety.py` logs

## 💡 Success Metrics

### Before Any Release
- ✅ All 116 tests pass
- ✅ 67%+ overall test coverage maintained
- ✅ 94%+ file safety coverage maintained
- ✅ Executables build without errors
- ✅ Manual testing of both CLI and GUI
- ✅ No pixel corruption on test images

### Code Quality Standards
- Clear, descriptive variable names
- Comprehensive docstrings for public methods
- Error handling with appropriate exceptions
- Logging for debugging and user feedback

---

**Welcome to ExifAnalyzer!** This is a mature, production-ready project with excellent test coverage and documentation. You're inheriting a solid foundation - build upon it confidently while maintaining the high quality standards already established.

**Questions?** Check the existing documentation first, then examine the test files for usage examples. The codebase is well-structured and self-documenting.

**Good luck!** 🚀