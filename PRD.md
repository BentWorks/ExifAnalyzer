# Product Requirements Document (PRD)

## 1. Product Overview
The tool is a **lightweight cross-platform utility** for viewing, editing, and stripping metadata from image files. It will serve both **power users (CLI)** and **casual users (minimal GUI)** who need to sanitize, inspect, or modify metadata for privacy, security, or organizational purposes.

## 2. Objectives
- Provide a **simple CLI** for metadata manipulation and batch operations.
- Provide a **minimal GUI** for previewing images and editing metadata fields.
- Support **common image formats**: JPEG, PNG, TIFF, WebP, GIF (MVP); optional HEIC and RAW later.
- Guarantee **no accidental data loss** of image pixels (metadata operations only).
- Make it **portable**: single-binary packaging or easy installer.

## 3. Target Users
- **Photographers / Journalists**: sanitize GPS/location data before publishing.
- **Privacy-focused users**: strip identifying info before sharing.
- **Developers / Researchers**: batch metadata inspection in pipelines.
- **Casual users**: simple GUI for one-off edits.

## 4. Key Features
- **Metadata Viewing**
  - Human-readable and JSON outputs.
  - Unified view across EXIF, IPTC, XMP, PNG text chunks.
- **Editing**
  - Modify specific tags (e.g., Artist, Copyright).
  - Preserve selected tags while stripping others.
- **Stripping**
  - Remove all metadata (“sanitize”).
  - Batch processing with recursion.
- **GUI**
  - Minimal: Image preview + side panel with metadata.
  - Editable fields with save/strip buttons.
- **Export / Backup**
  - Export metadata to `.json` or `.xmp` sidecar.
  - Option to restore metadata later.
- **Safety**
  - Default to saving a copy instead of overwriting.
  - `--inplace` option with confirmation.

## 5. Non-Goals
- Not a full-featured image editor.
- Not focused on rare/proprietary RAW formats in MVP.
- No cloud sync or remote features (privacy-first).

## 6. Success Metrics
- Usability: CLI commands complete in < 1s for typical images.
- Accuracy: 100% removal of GPS and EXIF blocks when stripping.
- Adoption: positive feedback from privacy/security communities.
- Stability: 0% pixel corruption from metadata operations.

## 7. Constraints
- Must run on Windows, macOS, Linux.
- Must work offline.
- File size of distributable under ~50MB (if possible).
- GUI should remain minimal (no feature creep).
