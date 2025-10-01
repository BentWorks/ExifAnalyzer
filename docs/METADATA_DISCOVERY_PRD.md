# Product Requirements Document: Metadata Discovery Feature

## Document Information
- **Project**: ExifAnalyzer
- **Feature**: AI Image Metadata Discovery Mode
- **Version**: 1.0
- **Date**: 2025-09-30
- **Status**: Draft

---

## Executive Summary

ExifAnalyzer will add an opt-in **Metadata Discovery Mode** that enables users to explore, identify, and extract metadata from AI-generated images across multiple platforms. This feature addresses the growing need in the AI art community to understand what metadata is embedded in images, especially when dealing with non-standard or custom metadata formats used by various AI image generation platforms.

---

## Problem Statement

### Current Challenges

1. **Inconsistent Metadata Standards**: AI image generation platforms embed metadata using different conventions:
   - Standard EXIF/IPTC/XMP fields
   - Custom PNG text chunks
   - Proprietary JSON structures
   - Platform-specific formats

2. **Lack of Visibility**: Users cannot easily determine:
   - What metadata exists in their AI-generated images
   - Which AI platform generated an image
   - What prompts, models, or parameters were used
   - Whether metadata was stripped during download/processing

3. **Manual Investigation Required**: Current tools either:
   - Show only standard metadata (missing custom fields)
   - Display raw hex dumps (too technical for most users)
   - Require multiple tools to check different metadata types

4. **AI Art Workflow Friction**: Artists and researchers need to:
   - Track prompt parameters across different platforms
   - Archive generation settings for reproducibility
   - Verify image provenance and creation details
   - Extract training data information

### User Pain Points

- "I don't know what metadata my Stable Diffusion images contain"
- "Midjourney strips some metadata—which fields are preserved?"
- "I need to extract all ComfyUI workflow data from my images"
- "How do I identify which AI platform created this image?"
- "I want to see ALL metadata, not just the standard fields"

---

## Goals & Objectives

### Primary Goals

1. **Discovery**: Enable users to see ALL metadata in an image, including non-standard fields
2. **Identification**: Automatically detect which AI platform generated an image
3. **Extraction**: Provide structured access to AI-specific metadata (prompts, models, parameters)
4. **Education**: Help users understand metadata formats and their implications

### Success Metrics

- **Adoption**: 30%+ of active users try Discovery Mode within first month
- **Detection Accuracy**: 90%+ correct platform identification for known AI platforms
- **User Satisfaction**: 4.5+ star rating for the feature
- **Support Coverage**: Support for top 5 AI platforms within 3 months

### Non-Goals (Out of Scope)

- ❌ Real-time monitoring of AI platform API changes
- ❌ Writing/injecting metadata into images (focus on discovery only)
- ❌ AI model evaluation or quality scoring
- ❌ Image generation capabilities
- ❌ Cloud-based metadata database/sharing

---

## User Personas

### Persona 1: AI Artist ("Creative Casey")
- **Background**: Uses Midjourney, Stable Diffusion, DALL-E regularly
- **Goal**: Track successful prompts and parameters for future reference
- **Pain Point**: Can't remember which settings produced favorite images
- **Use Case**: Bulk scan image collection to extract all prompts for archival

### Persona 2: AI Researcher ("Data-Driven Diana")
- **Background**: Studies AI image generation, analyzes outputs
- **Goal**: Understand what metadata different platforms embed
- **Pain Point**: No systematic way to compare metadata across platforms
- **Use Case**: Generate reports on metadata practices by platform

### Persona 3: Digital Archivist ("Archive Aaron")
- **Background**: Maintains digital art collections
- **Goal**: Preserve complete provenance information
- **Pain Point**: Metadata often lost during file transfers
- **Use Case**: Verify metadata integrity before and after processing

### Persona 4: Curious Beginner ("Newbie Nathan")
- **Background**: Just started with AI art, learning the tools
- **Goal**: Understand what's "inside" AI images
- **Pain Point**: Overwhelmed by technical jargon
- **Use Case**: Explore example images in a user-friendly interface

---

## Feature Requirements

### Functional Requirements

#### FR-1: Metadata Discovery Scan
**Priority**: P0 (Must Have)

- **FR-1.1**: Scan image file and extract ALL metadata blocks (EXIF, IPTC, XMP, custom)
- **FR-1.2**: Identify non-standard metadata chunks (PNG tEXt/iTXt/zTXt, JPEG APP markers)
- **FR-1.3**: Parse binary and text-based metadata into human-readable format
- **FR-1.4**: Handle images with no metadata gracefully (clear "No metadata found" message)
- **FR-1.5**: Support all existing file formats (JPEG, PNG, WebP, GIF, TIFF)

**Acceptance Criteria**:
- User can run discovery on any supported image format
- ALL metadata fields are extracted, including custom/unknown fields
- Binary data is presented with both hex and text representations
- Scan completes in <2 seconds for images up to 50MB

#### FR-2: AI Platform Detection
**Priority**: P0 (Must Have)

- **FR-2.1**: Detect Stable Diffusion images (PNG `parameters` chunk)
- **FR-2.2**: Detect Midjourney images (EXIF patterns, prompt fields)
- **FR-2.3**: Detect DALL-E images (XMP custom fields)
- **FR-2.4**: Detect ComfyUI images (JSON workflow in PNG chunks)
- **FR-2.5**: Report confidence level for platform detection (High/Medium/Low/Unknown)
- **FR-2.6**: Support "Unknown AI Platform" category for unrecognized patterns

**Acceptance Criteria**:
- Platform detection accuracy ≥90% for known platforms
- False positive rate <5%
- Unknown platforms are flagged for manual investigation
- Detection runs automatically during discovery scan

#### FR-3: Structured Metadata Extraction
**Priority**: P0 (Must Have)

- **FR-3.1**: Extract AI prompts (positive, negative, system prompts)
- **FR-3.2**: Extract model information (model name, version, hash)
- **FR-3.3**: Extract generation parameters (steps, CFG scale, sampler, seed)
- **FR-3.4**: Extract workflow data (for ComfyUI, Invoke AI)
- **FR-3.5**: Extract timestamps and versioning information
- **FR-3.6**: Present extracted data in categorized sections

**Acceptance Criteria**:
- All recognized fields are parsed into structured format
- Unknown fields are preserved in "Other/Custom" section
- Data types are correctly identified (string, number, JSON, binary)
- JSON workflow data is syntax-highlighted and formatted

#### FR-4: Discovery Report Output
**Priority**: P0 (Must Have)

- **FR-4.1**: Generate human-readable discovery report
- **FR-4.2**: Include summary section (platform, key findings)
- **FR-4.3**: Include detailed section (all fields with values)
- **FR-4.4**: Include raw section (hex dumps, binary data)
- **FR-4.5**: Support multiple output formats (TXT, JSON, HTML)
- **FR-4.6**: Allow export of discovery report to file

**Acceptance Criteria**:
- Report is clear and organized with logical sections
- Non-technical users can understand summary section
- Technical users can investigate raw data
- All output formats are valid and well-formed

#### FR-5: Batch Discovery Mode
**Priority**: P1 (Should Have)

- **FR-5.1**: Process multiple images in a single operation
- **FR-5.2**: Generate aggregate report (platforms detected, metadata summary)
- **FR-5.3**: Flag anomalies (missing expected fields, unusual patterns)
- **FR-5.4**: Export batch results to CSV or JSON
- **FR-5.5**: Display progress during batch processing

**Acceptance Criteria**:
- Can process 100+ images without crashing
- Progress indicator updates every 1 second
- Aggregate report summarizes findings across all images
- Individual reports available for each image

#### FR-6: Unknown Field Investigation Tools
**Priority**: P1 (Should Have)

- **FR-6.1**: Display unknown fields with multiple view modes (text, hex, JSON)
- **FR-6.2**: Provide field size and data type hints
- **FR-6.3**: Offer search/filter functionality for large metadata sets
- **FR-6.4**: Allow users to flag fields as "interesting" for further research
- **FR-6.5**: Export unknown fields separately for community pattern sharing

**Acceptance Criteria**:
- Users can easily switch between view modes
- Hex view shows offset addresses and ASCII representation
- Search highlights matching fields in real-time
- Export includes sufficient context for pattern identification

#### FR-7: CLI Integration
**Priority**: P0 (Must Have)

- **FR-7.1**: Add `discover` command to CLI
- **FR-7.2**: Support options: `--format`, `--output`, `--verbose`, `--batch`
- **FR-7.3**: Provide concise output by default, verbose on request
- **FR-7.4**: Return appropriate exit codes for scripting
- **FR-7.5**: Support piping output to other commands

**Acceptance Criteria**:
```bash
exifanalyzer discover image.png                    # Basic discovery
exifanalyzer discover image.png --format json      # JSON output
exifanalyzer discover *.png --batch --output report.html
exifanalyzer discover image.png --verbose          # Include raw data
```

#### FR-8: GUI Integration
**Priority**: P1 (Should Have)

- **FR-8.1**: Add "Discovery" tab to GUI
- **FR-8.2**: Display discovery results in expandable tree view
- **FR-8.3**: Provide tabbed interface (Summary / Details / Raw Data)
- **FR-8.4**: Enable copy-to-clipboard for any field
- **FR-8.5**: Visual indicator for detected AI platform (icon/badge)
- **FR-8.6**: Export button for saving discovery report

**Acceptance Criteria**:
- Tab is accessible and clearly labeled
- Tree view supports expand/collapse of sections
- Platform icon displays prominently when detected
- Export button offers format selection dialog

### Non-Functional Requirements

#### NFR-1: Performance
- Discovery scan completes in <2 seconds for images up to 50MB
- Batch processing handles 100 images in <60 seconds
- Memory usage stays under 500MB during batch operations
- UI remains responsive during processing

#### NFR-2: Compatibility
- Works on Windows 10+, macOS 10.14+, Linux (Ubuntu 20.04+)
- Supports Python 3.9+
- No breaking changes to existing ExifAnalyzer functionality
- Backward compatible with existing CLI commands

#### NFR-3: Usability
- Discovery mode accessible within 2 clicks from main screen
- Clear visual distinction between known and unknown fields
- Help text available for all options
- No technical knowledge required for basic usage

#### NFR-4: Reliability
- Handles corrupted or malformed metadata gracefully
- Never crashes on unexpected data formats
- Clear error messages for all failure modes
- Automatic recovery from parsing errors

#### NFR-5: Maintainability
- Platform detection patterns stored in external config file
- Easy to add new platform patterns without code changes
- Comprehensive logging for debugging
- Unit test coverage ≥80% for discovery module

#### NFR-6: Security
- No external network requests during discovery
- No data sent to external services
- Handles potentially malicious metadata safely
- Validates all inputs before processing

---

## User Stories

### Epic 1: Basic Discovery

**US-1.1**: As a user, I want to run discovery on a single image so that I can see all metadata it contains.
- **Acceptance**: User runs `exifanalyzer discover image.png` and sees complete metadata report

**US-1.2**: As a user, I want to know which AI platform created my image so that I can identify its source.
- **Acceptance**: Discovery report clearly indicates detected platform with confidence level

**US-1.3**: As a user, I want to see unknown metadata fields so that I can investigate custom data.
- **Acceptance**: Unknown fields are flagged and displayed with raw data views

### Epic 2: AI-Specific Extraction

**US-2.1**: As an AI artist, I want to extract all prompts from my images so that I can archive them.
- **Acceptance**: Prompts are clearly displayed in dedicated section, easily copyable

**US-2.2**: As a researcher, I want to see generation parameters so that I can understand how the image was created.
- **Acceptance**: Parameters are organized by category (model, sampling, guidance, etc.)

**US-2.3**: As a ComfyUI user, I want to extract full workflow JSON so that I can reuse it.
- **Acceptance**: JSON workflow is formatted, syntax-highlighted, and exportable

### Epic 3: Batch Operations

**US-3.1**: As a user, I want to discover metadata in 100+ images at once so that I can analyze my collection.
- **Acceptance**: Batch mode processes all images with progress indicator

**US-3.2**: As a user, I want an aggregate report showing patterns across my collection.
- **Acceptance**: Report shows platform distribution, common fields, anomalies

**US-3.3**: As a user, I want to export batch results for further analysis.
- **Acceptance**: CSV/JSON export includes all discovered metadata

### Epic 4: Advanced Investigation

**US-4.1**: As a technical user, I want to view raw hex dumps so that I can investigate unknown formats.
- **Acceptance**: Hex view shows offsets, hex bytes, and ASCII representation

**US-4.2**: As a user, I want to search through large metadata sets so that I can find specific fields.
- **Acceptance**: Search filters results in real-time

**US-4.3**: As a user, I want to compare metadata between two images so that I can spot differences.
- **Acceptance**: Side-by-side comparison highlights different fields

---

## User Interface & Experience

### CLI Interface

#### Basic Discovery Command
```
$ exifanalyzer discover image.png

=== METADATA DISCOVERY REPORT ===
File: image.png
Format: PNG
Size: 2.4 MB

[Platform Detection]
✓ Stable Diffusion (High Confidence)
  Model: stable-diffusion-v1-5
  Generator: AUTOMATIC1111

[AI Metadata - Prompts]
Positive: "a beautiful landscape, mountains, sunset, highly detailed"
Negative: "ugly, blurry, low quality"

[AI Metadata - Parameters]
Steps: 30
Sampler: DPM++ 2M Karras
CFG Scale: 7.5
Seed: 1234567890
Model: sd-v1-5-pruned-emaonly.safetensors

[Standard Metadata]
EXIF:
  - ImageWidth: 1024
  - ImageHeight: 768
  - Software: AUTOMATIC1111

[Custom/Unknown Fields]
PNG:tEXt:
  - parameters: [Raw text chunk, 1.2 KB]
  - workflow: [JSON data, 3.4 KB]

[Summary]
✓ Complete metadata found
✓ AI platform identified
✓ Extraction successful
! 2 unknown custom fields flagged

Export: exifanalyzer discover image.png --output report.json
```

#### Verbose Mode
```
$ exifanalyzer discover image.png --verbose

... (same as above) ...

[Raw Data Section]
PNG tEXt Chunk "parameters":
  Offset: 0x00012A4F
  Length: 1,234 bytes
  Content (text):
    a beautiful landscape, mountains, sunset...
    Steps: 30, Sampler: DPM++ 2M Karras...

  Content (hex):
    00000000: 61 20 62 65 61 75 74 69 66 75 6C 20 6C 61 6E 64  a beautiful land
    00000010: 73 63 61 70 65 2C 20 6D 6F 75 6E 74 61 69 6E 73  scape, mountains
    ...
```

#### Batch Mode
```
$ exifanalyzer discover *.png --batch --output report.html

Processing: [████████████████████] 100/100 images (100%)

=== BATCH DISCOVERY SUMMARY ===
Images Processed: 100
Time Elapsed: 45.2 seconds

[Platform Distribution]
Stable Diffusion: 75 (75%)
Midjourney: 20 (20%)
DALL-E: 3 (3%)
Unknown: 2 (2%)

[Common Fields Found]
- Prompt/Positive: 98/100
- Model Name: 95/100
- Generation Parameters: 93/100
- Timestamp: 87/100

[Anomalies Detected]
⚠ 2 images with no metadata
⚠ 5 images with truncated prompts
⚠ 1 image with unrecognized format

Report saved to: report.html
```

### GUI Interface

#### Discovery Tab Layout

```
┌─────────────────────────────────────────────────────────────┐
│ ExifAnalyzer - Metadata Discovery                           │
├─────────────────────────────────────────────────────────────┤
│ File: image.png                                   [Select File] │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [Summary] [Details] [Raw Data]                          │ │
│ │                                                          │ │
│ │ ╔═══════════════════════════════════════════════════╗  │ │
│ │ ║ Platform Detection                                ║  │ │
│ │ ╚═══════════════════════════════════════════════════╝  │ │
│ │ 🤖 Stable Diffusion (High Confidence)                  │ │
│ │    Model: stable-diffusion-v1-5                       │ │
│ │    Generator: AUTOMATIC1111                           │ │
│ │                                                          │ │
│ │ ╔═══════════════════════════════════════════════════╗  │ │
│ │ ║ AI Metadata                                       ║  │ │
│ │ ╚═══════════════════════════════════════════════════╝  │ │
│ │ ▼ Prompts                                              │ │
│ │   • Positive: "a beautiful landscape..."  [Copy]      │ │
│ │   • Negative: "ugly, blurry..."          [Copy]      │ │
│ │                                                          │ │
│ │ ▼ Generation Parameters                                │ │
│ │   • Steps: 30                                          │ │
│ │   • Sampler: DPM++ 2M Karras                          │ │
│ │   • CFG Scale: 7.5                                     │ │
│ │   • Seed: 1234567890                                   │ │
│ │                                                          │ │
│ │ ▶ Standard Metadata (EXIF, IPTC, XMP)                 │ │
│ │ ▶ Custom/Unknown Fields (2 found)                      │ │
│ │                                                          │ │
│ └─────────────────────────────────────────────────────────┘ │
│ [Run Discovery] [Export Report ▼] [Clear]                   │
└─────────────────────────────────────────────────────────────┘
```

#### Details Tab
- Expandable tree view showing all metadata hierarchically
- Color-coded by source (AI metadata = green, Standard = blue, Unknown = yellow)
- Right-click context menu: Copy Value, Copy Key, Copy Both
- Filter/search bar at top

#### Raw Data Tab
- Tabbed interface: Text | Hex | JSON
- Syntax highlighting for JSON data
- Hex view with offset, hex bytes, ASCII columns
- Export button for raw data

---

## Technical Considerations

### Platform Detection Patterns

Discovery mode will use pattern matching to identify AI platforms:

| Platform | Detection Method | Key Indicators |
|----------|------------------|----------------|
| Stable Diffusion | PNG tEXt chunk "parameters" | Contains "Steps:", "Sampler:", "CFG scale:" |
| ComfyUI | PNG tEXt chunk "workflow" | JSON with "nodes", "links", "groups" |
| Invoke AI | PNG tEXt chunk "invokeai_metadata" | JSON with "session_id", "model" |
| Midjourney | EXIF fields | Software="Midjourney", ImageDescription contains "/imagine" |
| DALL-E | XMP custom namespace | xmp:dalle3:prompt, xmp:dalle3:model |
| Leonardo AI | IPTC Caption/Keywords | Keywords contain "leonardo.ai" |
| Adobe Firefly | XMP firefly namespace | xmp:firefly:prompt, xmp:firefly:version |

### Extensibility

Pattern definitions stored in `discovery_patterns.yaml`:

```yaml
platforms:
  stable_diffusion:
    name: "Stable Diffusion"
    confidence_indicators:
      - field: "PNG:tEXt:parameters"
        pattern: "Steps: \\d+.*Sampler:"
        weight: 90
      - field: "EXIF:Software"
        value: "AUTOMATIC1111"
        weight: 50
    metadata_fields:
      prompt_positive: "PNG:tEXt:parameters:positive"
      prompt_negative: "PNG:tEXt:parameters:negative"
      steps: "PNG:tEXt:parameters:Steps"
      # ...
```

### Error Handling

Discovery mode must handle:
- Corrupted metadata chunks (partial reads)
- Invalid UTF-8 in text fields (fallback to hex)
- Extremely large metadata (>100MB workflows)
- Nested/recursive data structures
- Platform-specific quirks (Midjourney's non-standard EXIF)

---

## Dependencies & Integrations

### New Dependencies
- None required (uses existing PIL, piexif libraries)
- Optional: `pygments` for syntax highlighting in GUI/HTML export

### Integration Points
- **Core Engine**: Discovery mode uses existing adapter infrastructure
- **CLI**: New `discover` command alongside existing commands
- **GUI**: New tab in existing GUI window
- **Export**: Leverages existing export functionality

---

## Rollout Plan

### Phase 1: Core Discovery (v0.1.0)
- Basic discovery scan for all metadata
- CLI interface with text output
- Support for Stable Diffusion, Midjourney, DALL-E detection
- JSON export format
- **Timeline**: 2 weeks

### Phase 2: Enhanced Detection (v0.2.0)
- Add ComfyUI, Invoke AI, Leonardo AI patterns
- Batch processing mode
- HTML report generation
- **Timeline**: 1 week

### Phase 3: GUI Integration (v0.3.0)
- Discovery tab in GUI
- Interactive tree view
- Hex viewer
- **Timeline**: 2 weeks

### Phase 4: Advanced Features (v0.4.0)
- Image comparison mode
- Pattern community sharing
- Custom pattern creation UI
- **Timeline**: 2 weeks

### Phase 5: Polish & Release (v1.0.0)
- Documentation
- Tutorial videos
- User testing feedback integration
- **Timeline**: 1 week

---

## Success Criteria

### Launch Criteria (v1.0.0)
- ✅ All P0 functional requirements implemented
- ✅ Test coverage ≥80%
- ✅ CLI and GUI interfaces functional
- ✅ Documentation complete (user guide + API docs)
- ✅ Supports top 5 AI platforms (SD, MJ, DALL-E, ComfyUI, Invoke)
- ✅ Zero P0/P1 bugs in issue tracker
- ✅ Performance benchmarks met (2s scan, 60s batch)

### Post-Launch Success (3 months)
- 30% of users try Discovery mode
- 90% platform detection accuracy
- <5% false positive rate
- 4.5+ star user rating
- 10+ community-contributed patterns
- Featured in 3+ AI art community blogs/forums

---

## Open Questions

1. **Q**: Should discovery mode automatically update platform patterns from a central repository?
   - **Decision Needed By**: Phase 2
   - **Options**: (A) Manual updates only, (B) Opt-in auto-update, (C) Always auto-update
   - **Recommendation**: (B) Opt-in auto-update for security

2. **Q**: Should we support writing discovered patterns back to images?
   - **Decision Needed By**: Post-v1.0
   - **Options**: (A) Read-only forever, (B) Add write capability later
   - **Recommendation**: (A) Keep discovery read-only to maintain focus

3. **Q**: How to handle privacy concerns with prompt extraction?
   - **Decision Needed By**: Phase 1
   - **Options**: (A) Always show everything, (B) Add "sensitive data" blur option
   - **Recommendation**: (A) Show everything (user controls their files)

4. **Q**: Should we build a community pattern database?
   - **Decision Needed By**: Post-v1.0
   - **Options**: (A) GitHub repo for patterns, (B) Hosted service, (C) None
   - **Recommendation**: (A) GitHub repo (simple, maintainable)

---

## Appendix

### Glossary
- **Metadata Chunk**: A discrete block of metadata within an image file
- **Platform Detection**: Process of identifying which AI service generated an image
- **Discovery Scan**: Complete analysis of all metadata in an image
- **Pattern Matching**: Rule-based identification of metadata formats
- **Confidence Level**: Probability score for platform identification (High/Medium/Low)

### References
- PNG Specification: http://www.libpng.org/pub/png/spec/
- EXIF Standard: https://www.exif.org/
- XMP Specification: https://www.adobe.com/devnet/xmp.html
- Stable Diffusion Metadata Format: (community documentation)
- ComfyUI Workflow Format: https://github.com/comfyanonymous/ComfyUI

### Revision History
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-09-30 | Initial Draft | Complete PRD created |

