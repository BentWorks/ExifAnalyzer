# Technical Specification Document

## 1. System Architecture
- **Core Engine**: Unified metadata abstraction layer.
- **Adapters**: Format-specific handlers (JPEGAdapter, PNGAdapter, WebPAdapter, etc.).
- **CLI Layer**: Command parser + dispatch.
- **GUI Layer**: Thin wrapper around core engine with preview/editor.
- **Backup Module**: Export/restore metadata as JSON.
- **Optional Wrapper**: Call `exiftool` when local libraries are insufficient.

## 2. Supported Formats & Metadata Blocks
- **JPEG/TIFF**: EXIF, IPTC, XMP.
- **PNG**: tEXt, iTXt, zTXt chunks; XMP chunks.
- **WebP**: RIFF-based metadata (XMP).
- **GIF**: Comment blocks.
- **Optional Future**: HEIC (EXIF, XMP), RAW formats.

## 3. Functional Components
- **Metadata Reader**
  - Extracts metadata blocks from supported formats.
  - Normalizes into a dictionary structure `{exif: {}, iptc: {}, xmp: {}, custom: {}}`.
- **Metadata Writer**
  - Updates/overwrites fields.
  - Preserves image data integrity.
- **Stripper**
  - Removes selected or all metadata blocks.
- **Backup/Restore**
  - Exports metadata to `.json` or `.xmp`.
  - Re-applies metadata to images.
- **Diff Tool**
  - Compare metadata across two files.

## 4. CLI Specification
- Binary name: `image-meta`
- Subcommands:
  - `view <file>` → human-readable output
  - `show <file> --json` → JSON
  - `edit <file> --set "Key=Value"`
  - `remove <file> --tag TAG`
  - `strip <file> [--inplace]`
  - `batch strip <dir> -r`
  - `export <file> --out file.json`
  - `restore <file> --from file.json`
- Options:
  - `--backup`, `--preserve`, `--dry-run`, `--out`

## 5. GUI Specification
- **Framework**: PySimpleGUI (prototype) or Tauri/Electron (later).
- **Layout**:
  - Left: File picker / list.
  - Center: Image preview.
  - Right: Metadata fields (editable).
- **Controls**:
  - Save, Strip, Export, Restore.
  - Status bar for file path & changes.

## 6. Technology Choices
- **Prototype Stack (Python)**
  - Metadata: Pillow, piexif, python-xmp-toolkit.
  - CLI: Click.
  - GUI: PySimpleGUI.
  - Packaging: PyInstaller.
- **Production Option (Rust/Go)**
  - For single-binary distribution.
  - Libraries: `rexiv2` (Rust), `goexif` (Go).
  - GUI: Tauri (Rust).

## 7. Data Flow
1. User action (CLI/GUI) → Command Router.
2. Router invokes Metadata Engine.
3. Engine loads format-specific adapter.
4. Adapter parses metadata → normalized structure.
5. Operation applied (view, edit, strip, export).
6. Result written back to file or sidecar.

## 8. File Handling & Safety
- Always load original image read-only.
- Changes written to new file unless `--inplace`.
- Maintain original pixel data (avoid re-encoding unless required).
- Backups stored as `.metadata.json`.

## 9. Testing Strategy
- Unit Tests:
  - Read/write metadata for each format.
  - Strip GPS/location tags.
- Integration Tests:
  - Roundtrip: read → edit → write → verify.
  - Batch processing in directories.
- Edge Cases:
  - Corrupted metadata.
  - Large files (>100MB).
  - Non-ASCII characters.

## 10. Security & Privacy
- Local-only processing (no cloud).
- Secure handling of user input (no shell injection when calling `exiftool`).
- Default behavior: strip sensitive tags (GPS, device ID) with warning.
- Hash validation to confirm pixel data unchanged.

## 11. Deployment
- **Prototype**: PyInstaller bundle per OS.
- **Future**: Rust/Go binary, optionally with embedded minimal GUI (Tauri).
- Distribution via GitHub Releases or package managers (brew, winget, apt).
