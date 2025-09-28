# ExifAnalyzer Installation Guide

**Version:** 1.0.0-beta
**Last Updated:** 2025-09-27
**Platforms:** Windows (macOS/Linux coming soon)

---

## 🎯 Quick Start (5 Minutes)

### Step 1: Download
1. Download the `ExifAnalyzer-1.0.0-beta.zip` file
2. Extract to any folder (e.g., `C:\ExifAnalyzer` or `Desktop\ExifAnalyzer`)

### Step 2: Run
**No installation required!** Just run the executable:

**For GUI (Recommended for most users):**
- Double-click `ExifAnalyzer-GUI.exe`

**For Command Line:**
- Open Command Prompt in the folder
- Type: `ExifAnalyzer-CLI.exe --help`

### Step 3: Start Using
- **GUI**: Use the "Browse" buttons to select images
- **CLI**: Type commands like `ExifAnalyzer-CLI.exe view photo.jpg`

That's it! No Python, no dependencies, no admin rights required.

---

## 📦 What's Included

```
ExifAnalyzer-1.0.0-beta/
├── ExifAnalyzer-CLI.exe       # Command line interface
├── ExifAnalyzer-GUI.exe       # Graphical interface
├── Instructions.md            # Detailed usage guide
├── QUICK_START.txt           # 2-minute tutorial
├── changelog.md              # Version history
└── README.md                 # Project overview
```

---

## 🖥️ System Requirements

### Windows
- **Minimum:** Windows 10 (64-bit)
- **Recommended:** Windows 11
- **RAM:** 100MB available memory
- **Disk:** 50MB free space

### macOS (Coming Soon)
- **Minimum:** macOS 10.14 Mojave
- **Recommended:** macOS 12 Monterey or later

### Linux (Coming Soon)
- **Minimum:** Ubuntu 18.04 LTS or equivalent
- **Recommended:** Ubuntu 20.04 LTS or later

---

## 🚀 Getting Started

### GUI Interface (Easiest)

1. **Launch**: Double-click `ExifAnalyzer-GUI.exe`
2. **Select Images**:
   - Click "Browse" next to "File:" to select a single image
   - OR click "Browse" next to "Folder:" to browse a folder of images
3. **View Metadata**: Select an image to see its metadata
4. **Remove Metadata**:
   - Click "Strip All Metadata" to remove everything
   - OR click "Strip GPS Only" to remove just location data

### Command Line Interface (Power Users)

1. **Open Command Prompt** in the ExifAnalyzer folder
2. **Basic Commands**:
   ```cmd
   # Get help
   ExifAnalyzer-CLI.exe --help

   # View image metadata
   ExifAnalyzer-CLI.exe view photo.jpg

   # Remove all metadata
   ExifAnalyzer-CLI.exe strip photo.jpg

   # Remove only GPS data
   ExifAnalyzer-CLI.exe strip --gps-only photo.jpg

   # Process multiple files
   ExifAnalyzer-CLI.exe batch C:\Photos --operation strip
   ```

---

## 🔧 Advanced Installation

### Custom Location
- Extract to any folder you prefer
- Add the folder to your PATH environment variable for global CLI access
- Create desktop shortcuts to the executables

### Antivirus Considerations
- Some antivirus software may flag the executables (false positive)
- Add the ExifAnalyzer folder to your antivirus exclusions if needed
- The executables are digitally signed and safe

### Multiple Versions
- You can have multiple versions in different folders
- Each version is completely self-contained

---

## 🆘 Troubleshooting

### GUI Won't Start
- **Problem**: Nothing happens when double-clicking
- **Solution**: Right-click → "Run as administrator"

### CLI Command Not Found
- **Problem**: `'ExifAnalyzer-CLI.exe' is not recognized`
- **Solution**:
  1. Open Command Prompt IN the ExifAnalyzer folder
  2. OR use full path: `C:\path\to\ExifAnalyzer-CLI.exe`

### No Images Showing in GUI
- **Problem**: Folder browser shows no files
- **Solution**:
  1. Use the "File" browser instead of "Folder" browser
  2. Ensure you're browsing to a folder with .jpg/.png images
  3. Check status bar for diagnostic information

### Windows SmartScreen Warning
- **Problem**: "Windows protected your PC" message
- **Solution**: Click "More info" → "Run anyway"

### Permission Denied Errors
- **Problem**: Can't modify images
- **Solution**:
  1. Ensure images aren't read-only
  2. Run as administrator if needed
  3. Move images out of protected folders

---

## 🔄 Updates

### Automatic Updates
- ExifAnalyzer does not auto-update
- Check for new versions manually

### Manual Updates
1. Download the new version
2. Extract to a new folder
3. Copy your images/settings if needed
4. Delete the old version

### Beta Versions
- Beta versions include "-beta" in the filename
- Beta versions are for testing - use with caution on important images
- Report issues to help improve the software

---

## 📞 Support

### Documentation
- **Quick Start**: `QUICK_START.txt`
- **Detailed Guide**: `Instructions.md`
- **Version History**: `changelog.md`

### Getting Help
- Read the error messages carefully
- Check this troubleshooting section
- Ensure you're using supported image formats (JPEG, PNG)

### Reporting Issues
- Include your Windows version
- Describe the exact steps that caused the problem
- Include any error messages
- Mention if you're using GUI or CLI

---

## 🛡️ Privacy & Security

### Your Data
- **Local Only**: All processing happens on your computer
- **No Internet**: ExifAnalyzer never connects to the internet
- **No Tracking**: No usage data is collected
- **Safe**: Original images are backed up before modification

### Supported Formats
- **Read/Write**: JPEG (.jpg, .jpeg, .jpe, .jfif)
- **Read/Write**: PNG (.png)
- **Future**: TIFF, WebP, GIF support planned

---

*Enjoy using ExifAnalyzer! 🎉*