# Technical Specification: Metadata Discovery Feature

## Document Information
- **Project**: ExifAnalyzer
- **Feature**: AI Image Metadata Discovery Mode
- **Version**: 1.0
- **Date**: 2025-09-30
- **Status**: Draft

---

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Component Design](#component-design)
4. [Data Models](#data-models)
5. [API Specifications](#api-specifications)
6. [File Formats](#file-formats)
7. [Pattern Matching System](#pattern-matching-system)
8. [CLI Interface](#cli-interface)
9. [GUI Interface](#gui-interface)
10. [Error Handling](#error-handling)
11. [Performance Considerations](#performance-considerations)
12. [Testing Strategy](#testing-strategy)
13. [Security Considerations](#security-considerations)
14. [Migration & Deployment](#migration--deployment)

---

## 1. Overview

### 1.1 Purpose
This document provides comprehensive technical specifications for implementing the Metadata Discovery feature in ExifAnalyzer. Discovery mode enables deep inspection of image metadata, automatic detection of AI generation platforms, and extraction of platform-specific metadata fields.

### 1.2 Scope
- Core discovery engine and metadata extraction
- Pattern-based platform detection system
- CLI command implementation
- GUI tab integration
- Report generation in multiple formats
- Batch processing capabilities

### 1.3 Technical Stack
- **Language**: Python 3.9+
- **Core Libraries**: PIL/Pillow, piexif (existing)
- **New Dependencies**:
  - PyYAML (for pattern configuration)
  - Optional: Pygments (for syntax highlighting)
- **Testing**: pytest, pytest-cov
- **Documentation**: Sphinx, reStructuredText

---

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interfaces                         │
│  ┌──────────────┐              ┌──────────────┐            │
│  │  CLI         │              │  GUI         │            │
│  │  (discover)  │              │  (tab)       │            │
│  └──────┬───────┘              └──────┬───────┘            │
│         │                              │                     │
└─────────┼──────────────────────────────┼─────────────────────┘
          │                              │
          └──────────┬───────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│              Discovery Engine Facade                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  MetadataDiscoveryEngine                             │  │
│  │  - discover()                                        │  │
│  │  - batch_discover()                                  │  │
│  │  - generate_report()                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐
│  Metadata       │  │  Platform    │  │  Report         │
│  Extractor      │  │  Detector    │  │  Generator      │
│                 │  │              │  │                 │
│ - extract_all() │  │ - detect()   │  │ - to_text()     │
│ - parse_chunk() │  │ - score()    │  │ - to_json()     │
│ - decode_data() │  │ - patterns   │  │ - to_html()     │
└────────┬────────┘  └──────┬───────┘  └─────────────────┘
         │                  │
         ▼                  ▼
┌─────────────────┐  ┌──────────────────────────────┐
│  Existing       │  │  Pattern Configuration       │
│  Adapters       │  │  (YAML files)                │
│  (JPEG, PNG,    │  │  - platform_patterns.yaml    │
│   WebP, etc.)   │  │  - field_mappings.yaml       │
└─────────────────┘  └──────────────────────────────┘
```

### 2.2 Module Structure

```
src/exif_analyzer/
├── discovery/
│   ├── __init__.py
│   ├── engine.py              # MetadataDiscoveryEngine
│   ├── extractor.py           # MetadataExtractor
│   ├── detector.py            # PlatformDetector
│   ├── reporter.py            # ReportGenerator
│   ├── patterns/
│   │   ├── __init__.py
│   │   ├── loader.py          # Pattern file loader
│   │   ├── matcher.py         # Pattern matching logic
│   │   └── registry.py        # Platform pattern registry
│   └── models.py              # Data models (DiscoveryResult, etc.)
├── cli/
│   ├── discover_handler.py    # CLI command handler
│   └── formatters.py          # Output formatters
├── gui/
│   └── discovery_tab.py       # GUI tab implementation
└── config/
    └── patterns/
        ├── platform_patterns.yaml
        ├── field_mappings.yaml
        └── custom_patterns.yaml
```

### 2.3 Data Flow

```
1. User Request
   ↓
2. Discovery Engine receives image path
   ↓
3. Adapter reads image → ImageMetadata
   ↓
4. Extractor extracts ALL metadata (standard + custom)
   ↓
5. Detector matches patterns → Platform identification
   ↓
6. Parser extracts platform-specific fields
   ↓
7. Reporter generates formatted output
   ↓
8. Return DiscoveryResult to user
```

---

## 3. Component Design

### 3.1 MetadataDiscoveryEngine

**Responsibility**: Orchestrates discovery process, coordinates components

**Key Methods**:
- `discover(file_path: Path) -> DiscoveryResult`
- `batch_discover(file_paths: List[Path]) -> BatchDiscoveryResult`
- `register_custom_pattern(pattern: PlatformPattern) -> None`
- `get_supported_platforms() -> List[str]`

**Dependencies**:
- MetadataExtractor
- PlatformDetector
- ReportGenerator
- Existing MetadataEngine

**Design Pattern**: Facade

### 3.2 MetadataExtractor

**Responsibility**: Extract ALL metadata from images, including non-standard chunks

**Key Methods**:
- `extract_all(file_path: Path) -> ExtractedMetadata`
- `extract_raw_chunks(file_path: Path, format: str) -> List[RawChunk]`
- `parse_text_chunk(data: bytes, encoding: str) -> str`
- `parse_binary_chunk(data: bytes) -> HexDump`

**Special Handling**:
- PNG: Extract tEXt, iTXt, zTXt chunks beyond standard fields
- JPEG: Extract all APP markers (APP0-APP15), comments
- WebP: Extract VP8X, EXIF, XMP, ICCP chunks
- TIFF: Extract all IFD entries including unknown tags
- GIF: Extract comment extensions, application extensions

**Algorithm**:
```
1. Use existing adapter to read standard metadata
2. Open file in binary mode
3. Parse file format-specific structure:
   PNG: Read all chunks sequentially
   JPEG: Read all segments between markers
   WebP: Parse RIFF structure
   TIFF: Read all IFD entries
   GIF: Read all extension blocks
4. For each chunk/segment:
   - Extract raw bytes
   - Attempt text decoding (UTF-8, Latin-1, ASCII)
   - Store both raw and decoded versions
5. Return ExtractedMetadata with all findings
```

### 3.3 PlatformDetector

**Responsibility**: Identify AI generation platform using pattern matching

**Key Methods**:
- `detect(metadata: ExtractedMetadata) -> DetectionResult`
- `calculate_confidence(matches: List[PatternMatch]) -> ConfidenceLevel`
- `load_patterns(pattern_file: Path) -> List[PlatformPattern]`

**Detection Algorithm**:
```
1. Load all platform patterns from YAML
2. For each platform:
   a. Check required indicators
   b. Score each matched pattern (weighted)
   c. Calculate total confidence score
3. Rank platforms by score
4. Return top match if score > threshold:
   - High confidence: score ≥ 80
   - Medium confidence: 50 ≤ score < 80
   - Low confidence: 30 ≤ score < 50
   - Unknown: score < 30
5. Include matched indicators in result
```

**Confidence Scoring**:
```python
total_score = sum(indicator.weight for indicator in matched_indicators)
max_possible = sum(indicator.weight for indicator in all_indicators)
confidence_percent = (total_score / max_possible) * 100

if confidence_percent >= 80:
    return ConfidenceLevel.HIGH
elif confidence_percent >= 50:
    return ConfidenceLevel.MEDIUM
elif confidence_percent >= 30:
    return ConfidenceLevel.LOW
else:
    return ConfidenceLevel.UNKNOWN
```

### 3.4 ReportGenerator

**Responsibility**: Format discovery results for output

**Key Methods**:
- `generate_text_report(result: DiscoveryResult) -> str`
- `generate_json_report(result: DiscoveryResult) -> str`
- `generate_html_report(result: DiscoveryResult) -> str`
- `generate_csv_report(results: List[DiscoveryResult]) -> str`

**Report Sections**:
1. Header (file info, format, size)
2. Platform Detection (platform, confidence, version)
3. AI Metadata (prompts, parameters, model)
4. Standard Metadata (EXIF, IPTC, XMP)
5. Custom/Unknown Fields (with view options)
6. Raw Data (optional, verbose mode)
7. Summary (quick stats, flags)

---

## 4. Data Models

### 4.1 Core Models

```python
@dataclass
class RawChunk:
    """Raw metadata chunk from image file."""
    chunk_type: str          # e.g., "PNG:tEXt", "JPEG:APP1"
    offset: int              # Byte offset in file
    length: int              # Chunk size in bytes
    raw_data: bytes          # Raw binary data
    decoded_text: Optional[str]  # Decoded text if applicable
    encoding: Optional[str]  # Detected encoding
    parse_error: Optional[str]   # Error if parsing failed

@dataclass
class ExtractedMetadata:
    """Complete metadata extraction result."""
    file_path: Path
    file_format: str
    file_size: int
    standard_metadata: ImageMetadata  # From existing system
    raw_chunks: List[RawChunk]
    custom_fields: Dict[str, Any]
    extraction_errors: List[str]
    extraction_time: float

@dataclass
class PatternIndicator:
    """Single indicator for platform detection."""
    field_path: str          # e.g., "PNG:tEXt:parameters"
    pattern_type: str        # "exact", "regex", "contains", "exists"
    pattern_value: str       # Pattern to match
    weight: int              # Importance score (0-100)
    is_required: bool        # Must match for platform to be detected

@dataclass
class PlatformPattern:
    """Platform detection pattern definition."""
    platform_id: str         # e.g., "stable_diffusion"
    platform_name: str       # Human-readable name
    version: Optional[str]   # Version if pattern is version-specific
    indicators: List[PatternIndicator]
    field_mappings: Dict[str, str]  # Maps generic names to specific fields
    description: str
    documentation_url: str

@dataclass
class DetectionResult:
    """Platform detection result."""
    platform_id: str
    platform_name: str
    confidence: ConfidenceLevel  # HIGH, MEDIUM, LOW, UNKNOWN
    confidence_score: float      # 0-100
    matched_indicators: List[PatternIndicator]
    version: Optional[str]
    metadata: Dict[str, Any]     # Extracted platform-specific data

@dataclass
class AIMetadata:
    """Structured AI-specific metadata."""
    prompts: Dict[str, str]      # positive, negative, system
    model: Optional[ModelInfo]
    parameters: Dict[str, Any]   # steps, sampler, cfg, seed, etc.
    workflow: Optional[str]      # JSON workflow for ComfyUI, etc.
    generation_info: Dict[str, Any]  # timestamps, version, etc.
    raw_data: Dict[str, Any]     # Unstructured additional data

@dataclass
class ModelInfo:
    """AI model information."""
    name: str
    version: Optional[str]
    hash: Optional[str]
    architecture: Optional[str]
    source: Optional[str]

@dataclass
class DiscoveryResult:
    """Complete discovery result for single image."""
    file_path: Path
    extracted_metadata: ExtractedMetadata
    detection: DetectionResult
    ai_metadata: Optional[AIMetadata]
    unknown_fields: List[RawChunk]
    warnings: List[str]
    discovery_time: float

@dataclass
class BatchDiscoveryResult:
    """Aggregated results for multiple images."""
    results: List[DiscoveryResult]
    total_images: int
    successful: int
    failed: int
    platform_distribution: Dict[str, int]
    common_fields: Dict[str, int]
    anomalies: List[str]
    total_time: float

class ConfidenceLevel(Enum):
    """Platform detection confidence levels."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNKNOWN = "Unknown"
```

### 4.2 Pattern Configuration Schema

```yaml
# platform_patterns.yaml

version: "1.0"

platforms:
  stable_diffusion:
    name: "Stable Diffusion"
    description: "Open-source text-to-image diffusion model"
    documentation_url: "https://github.com/Stability-AI/stablediffusion"

    indicators:
      - field: "PNG:tEXt:parameters"
        type: "regex"
        pattern: "Steps:\\s*\\d+"
        weight: 90
        required: true

      - field: "PNG:tEXt:parameters"
        type: "contains"
        value: "Sampler:"
        weight: 50
        required: false

      - field: "EXIF:Software"
        type: "contains"
        value: "AUTOMATIC1111"
        weight: 40
        required: false

      - field: "EXIF:Software"
        type: "contains"
        value: "ComfyUI"
        weight: 40
        required: false

    field_mappings:
      prompt_positive: "PNG:tEXt:parameters:positive"
      prompt_negative: "PNG:tEXt:parameters:negative"
      steps: "PNG:tEXt:parameters:Steps"
      sampler: "PNG:tEXt:parameters:Sampler"
      cfg_scale: "PNG:tEXt:parameters:CFG scale"
      seed: "PNG:tEXt:parameters:Seed"
      model_name: "PNG:tEXt:parameters:Model"
      model_hash: "PNG:tEXt:parameters:Model hash"
      size: "PNG:tEXt:parameters:Size"
      clip_skip: "PNG:tEXt:parameters:Clip skip"

  comfyui:
    name: "ComfyUI"
    description: "Node-based UI for Stable Diffusion"
    documentation_url: "https://github.com/comfyanonymous/ComfyUI"

    indicators:
      - field: "PNG:tEXt:workflow"
        type: "exists"
        weight: 95
        required: true

      - field: "PNG:tEXt:workflow"
        type: "json_path"
        pattern: "$.nodes[*].type"
        weight: 85
        required: false

      - field: "PNG:tEXt:prompt"
        type: "json_path"
        pattern: "$[*].class_type"
        weight: 80
        required: false

    field_mappings:
      workflow: "PNG:tEXt:workflow"
      prompt_data: "PNG:tEXt:prompt"

  midjourney:
    name: "Midjourney"
    description: "Commercial AI image generation service"
    documentation_url: "https://docs.midjourney.com/"

    indicators:
      - field: "EXIF:Software"
        type: "exact"
        value: "Midjourney"
        weight: 100
        required: true

      - field: "EXIF:ImageDescription"
        type: "regex"
        pattern: "/imagine\\s+prompt:"
        weight: 90
        required: false

      - field: "IPTC:Caption"
        type: "contains"
        value: "midjourney"
        weight: 70
        required: false

    field_mappings:
      prompt: "EXIF:ImageDescription"
      version: "EXIF:Software"
      job_id: "EXIF:ImageUniqueID"

  dalle:
    name: "DALL-E"
    description: "OpenAI's image generation model"
    documentation_url: "https://openai.com/dall-e-3"

    indicators:
      - field: "XMP:dalle3:prompt"
        type: "exists"
        weight: 100
        required: true

      - field: "XMP:dalle3:model"
        type: "contains"
        value: "dall-e"
        weight: 90
        required: false

      - field: "EXIF:Software"
        type: "contains"
        value: "OpenAI"
        weight: 60
        required: false

    field_mappings:
      prompt: "XMP:dalle3:prompt"
      model: "XMP:dalle3:model"
      revised_prompt: "XMP:dalle3:revised_prompt"
      generation_id: "XMP:dalle3:generation_id"
```

---

## 5. API Specifications

### 5.1 Public API

```python
# Main Discovery API
class MetadataDiscoveryEngine:
    """
    Main engine for metadata discovery operations.

    Example:
        >>> engine = MetadataDiscoveryEngine()
        >>> result = engine.discover("image.png")
        >>> print(result.detection.platform_name)
        'Stable Diffusion'
    """

    def __init__(
        self,
        pattern_dir: Optional[Path] = None,
        metadata_engine: Optional[MetadataEngine] = None
    ):
        """
        Initialize discovery engine.

        Args:
            pattern_dir: Directory containing pattern YAML files
            metadata_engine: Existing MetadataEngine instance (optional)
        """

    def discover(
        self,
        file_path: Union[str, Path],
        verbose: bool = False,
        extract_raw: bool = True
    ) -> DiscoveryResult:
        """
        Perform discovery on single image.

        Args:
            file_path: Path to image file
            verbose: Include raw data in result
            extract_raw: Extract raw chunks (disable for faster scanning)

        Returns:
            DiscoveryResult with complete findings

        Raises:
            FileNotFoundError: Image file not found
            UnsupportedFormatError: Image format not supported
            MetadataError: Error during metadata extraction
        """

    def batch_discover(
        self,
        file_paths: List[Union[str, Path]],
        progress_callback: Optional[Callable[[int, int], None]] = None,
        continue_on_error: bool = True
    ) -> BatchDiscoveryResult:
        """
        Perform discovery on multiple images.

        Args:
            file_paths: List of image file paths
            progress_callback: Callback(current, total) for progress updates
            continue_on_error: Continue processing if individual files fail

        Returns:
            BatchDiscoveryResult with aggregated findings
        """

    def register_pattern(self, pattern: PlatformPattern) -> None:
        """
        Register custom platform detection pattern.

        Args:
            pattern: PlatformPattern definition

        Raises:
            ValidationError: Pattern is invalid
        """

    def load_patterns_from_file(self, file_path: Path) -> int:
        """
        Load platform patterns from YAML file.

        Args:
            file_path: Path to YAML pattern file

        Returns:
            Number of patterns loaded

        Raises:
            FileNotFoundError: Pattern file not found
            YAMLError: Invalid YAML format
        """

    def get_supported_platforms(self) -> List[str]:
        """
        Get list of supported platform IDs.

        Returns:
            List of platform IDs that can be detected
        """

# Report Generation API
class ReportGenerator:
    """Generate formatted reports from discovery results."""

    def generate_text_report(
        self,
        result: DiscoveryResult,
        include_raw: bool = False,
        include_hex: bool = False
    ) -> str:
        """Generate human-readable text report."""

    def generate_json_report(
        self,
        result: DiscoveryResult,
        indent: int = 2,
        include_binary: bool = False
    ) -> str:
        """Generate JSON report."""

    def generate_html_report(
        self,
        result: DiscoveryResult,
        template: Optional[str] = None,
        syntax_highlight: bool = True
    ) -> str:
        """Generate HTML report with styling."""

    def generate_csv_report(
        self,
        results: List[DiscoveryResult],
        fields: Optional[List[str]] = None
    ) -> str:
        """Generate CSV report for batch results."""

    def generate_markdown_report(
        self,
        result: DiscoveryResult,
        include_toc: bool = True
    ) -> str:
        """Generate Markdown report."""
```

### 5.2 CLI API

```python
# CLI Command Handler
class DiscoverCommandHandler:
    """Handle CLI discover command."""

    def execute(
        self,
        file_paths: List[Path],
        format: str = "text",
        output: Optional[Path] = None,
        verbose: bool = False,
        batch: bool = False,
        platform: Optional[str] = None,
        no_color: bool = False
    ) -> int:
        """
        Execute discover command.

        Args:
            file_paths: Images to analyze
            format: Output format (text, json, html, markdown)
            output: Output file (stdout if None)
            verbose: Include raw data
            batch: Batch mode (aggregate report)
            platform: Filter by specific platform
            no_color: Disable colored output

        Returns:
            Exit code (0 = success, 1 = error)
        """
```

### 5.3 GUI API

```python
# GUI Tab Interface
class DiscoveryTab(QWidget):
    """Discovery tab for GUI."""

    discovery_started = Signal()
    discovery_completed = Signal(DiscoveryResult)
    discovery_failed = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize discovery tab."""

    def load_image(self, file_path: Path) -> None:
        """Load image for discovery."""

    def run_discovery(self) -> None:
        """Run discovery on loaded image."""

    def display_result(self, result: DiscoveryResult) -> None:
        """Display discovery result in UI."""

    def export_report(self, format: str) -> None:
        """Export current result as report."""

    def copy_field(self, field_path: str) -> None:
        """Copy field value to clipboard."""
```

---

## 6. File Formats

### 6.1 Pattern File Format (YAML)

**File**: `platform_patterns.yaml`

```yaml
version: "1.0"
author: "ExifAnalyzer Team"
last_updated: "2025-09-30"

platforms:
  platform_id:
    name: string                    # Human-readable platform name
    description: string             # Brief description
    documentation_url: string       # Link to platform docs

    indicators:
      - field: string               # Field path (e.g., "PNG:tEXt:parameters")
        type: enum                  # exact, regex, contains, exists, json_path
        pattern: string             # Pattern to match (if applicable)
        value: string               # Exact value (if applicable)
        weight: int                 # Importance score (0-100)
        required: bool              # Must match for detection

    field_mappings:
      generic_name: field_path      # Map generic names to specific fields

    version_detection:              # Optional version identification
      field: string
      regex: string
      groups:
        major: int
        minor: int
        patch: int
```

**Validation Rules**:
- `platform_id` must be unique, lowercase, alphanumeric + underscores
- `indicators` must have at least one required indicator
- `weight` must be 0-100
- `type` must be one of: exact, regex, contains, exists, json_path
- Total weight of all indicators should sum to 100+ for meaningful scoring

### 6.2 Report Output Formats

#### Text Report Format
```
=== METADATA DISCOVERY REPORT ===
File: image.png
Format: PNG (24-bit RGB)
Size: 2.4 MB (2,453,901 bytes)
Scanned: 2025-09-30 14:32:15

[PLATFORM DETECTION]
✓ Stable Diffusion (High Confidence - 95%)
  Version: v1.5
  Generator: AUTOMATIC1111 v1.6.0

[AI METADATA]
┌─ Prompts ─────────────────────────────────────┐
│ Positive: a beautiful landscape, mountains... │
│ Negative: ugly, blurry, low quality          │
└───────────────────────────────────────────────┘

┌─ Generation Parameters ───────────────────────┐
│ Steps:      30                                │
│ Sampler:    DPM++ 2M Karras                   │
│ CFG Scale:  7.5                               │
│ Seed:       1234567890                        │
│ Model:      sd-v1-5-pruned-emaonly            │
│ Size:       1024x768                          │
└───────────────────────────────────────────────┘

[STANDARD METADATA]
EXIF (8 fields):
  • ImageWidth: 1024
  • ImageHeight: 768
  • Software: AUTOMATIC1111
  • DateTime: 2025:09:30 14:15:23
  ...

[CUSTOM/UNKNOWN FIELDS]
PNG:tEXt:workflow
  Type: JSON
  Size: 3.4 KB
  Preview: {"nodes": [{"id": 1, "type": "CLIPTextEncode"...

[SUMMARY]
✓ Complete metadata found (no corruption)
✓ AI platform identified with high confidence
✓ All standard fields extracted successfully
! 1 unknown custom field flagged for investigation
⚠ No GPS data found (privacy-safe)

Total Discovery Time: 0.234 seconds
```

#### JSON Report Format
```json
{
  "discovery_version": "1.0.0",
  "timestamp": "2025-09-30T14:32:15Z",
  "file": {
    "path": "image.png",
    "format": "PNG",
    "size_bytes": 2453901,
    "size_human": "2.4 MB"
  },
  "detection": {
    "platform_id": "stable_diffusion",
    "platform_name": "Stable Diffusion",
    "confidence": "HIGH",
    "confidence_score": 95.0,
    "version": "v1.5",
    "matched_indicators": [
      {
        "field": "PNG:tEXt:parameters",
        "pattern": "Steps:\\s*\\d+",
        "weight": 90,
        "matched": true
      }
    ]
  },
  "ai_metadata": {
    "prompts": {
      "positive": "a beautiful landscape, mountains, sunset",
      "negative": "ugly, blurry, low quality"
    },
    "model": {
      "name": "sd-v1-5-pruned-emaonly",
      "hash": "cc6cb27103",
      "architecture": "Stable Diffusion v1.5"
    },
    "parameters": {
      "steps": 30,
      "sampler": "DPM++ 2M Karras",
      "cfg_scale": 7.5,
      "seed": 1234567890,
      "size": "1024x768",
      "clip_skip": 2
    }
  },
  "standard_metadata": {
    "exif": {
      "ImageWidth": 1024,
      "ImageHeight": 768,
      "Software": "AUTOMATIC1111"
    },
    "iptc": {},
    "xmp": {}
  },
  "unknown_fields": [
    {
      "field": "PNG:tEXt:workflow",
      "type": "json",
      "size": 3456,
      "preview": "{\"nodes\": [...]}"
    }
  ],
  "summary": {
    "total_fields": 45,
    "standard_fields": 8,
    "ai_fields": 12,
    "unknown_fields": 1,
    "has_gps": false,
    "is_corrupted": false
  },
  "discovery_time_seconds": 0.234
}
```

#### HTML Report Template
```html
<!DOCTYPE html>
<html>
<head>
    <title>Metadata Discovery Report - {filename}</title>
    <style>
        /* Clean, modern CSS with syntax highlighting */
    </style>
</head>
<body>
    <header>
        <h1>Metadata Discovery Report</h1>
        <div class="file-info">
            <span class="filename">{filename}</span>
            <span class="format">{format}</span>
            <span class="size">{size}</span>
        </div>
    </header>

    <section class="detection">
        <h2>Platform Detection</h2>
        <div class="platform-badge {confidence-class}">
            <img src="icon/{platform_id}.svg" alt="{platform}">
            <span class="name">{platform_name}</span>
            <span class="confidence">{confidence}%</span>
        </div>
    </section>

    <section class="ai-metadata">
        <h2>AI Metadata</h2>
        <div class="prompts">
            <h3>Prompts</h3>
            <div class="prompt positive">
                <label>Positive:</label>
                <pre>{positive_prompt}</pre>
                <button class="copy">Copy</button>
            </div>
        </div>

        <div class="parameters">
            <h3>Generation Parameters</h3>
            <table>
                <tr><td>Steps</td><td>{steps}</td></tr>
                <tr><td>Sampler</td><td>{sampler}</td></tr>
                <!-- ... -->
            </table>
        </div>
    </section>

    <section class="raw-data">
        <h2>Raw Data</h2>
        <div class="tabs">
            <button class="tab active" data-view="text">Text</button>
            <button class="tab" data-view="hex">Hex</button>
            <button class="tab" data-view="json">JSON</button>
        </div>
        <div class="content">
            <pre class="syntax-highlighted">{raw_data}</pre>
        </div>
    </section>

    <footer>
        <p>Generated by ExifAnalyzer v{version}</p>
    </footer>
</body>
</html>
```

---

## 7. Pattern Matching System

### 7.1 Pattern Types

**Exact Match**
```yaml
- field: "EXIF:Software"
  type: "exact"
  value: "Midjourney"
  weight: 100
```
Match: Field value exactly equals "Midjourney"

**Contains Match**
```yaml
- field: "PNG:tEXt:parameters"
  type: "contains"
  value: "Sampler:"
  weight: 50
```
Match: Field value contains substring "Sampler:"

**Regex Match**
```yaml
- field: "PNG:tEXt:parameters"
  type: "regex"
  pattern: "Steps:\\s*\\d+"
  weight: 90
```
Match: Field value matches regex pattern

**Exists Match**
```yaml
- field: "PNG:tEXt:workflow"
  type: "exists"
  weight: 95
```
Match: Field exists (any value)

**JSON Path Match**
```yaml
- field: "PNG:tEXt:workflow"
  type: "json_path"
  pattern: "$.nodes[*].type"
  weight: 85
```
Match: JSON path exists and returns results

### 7.2 Field Path Syntax

Field paths use colon-separated hierarchical notation:

```
Format:Chunk:Key:Subkey

Examples:
PNG:tEXt:parameters              # PNG text chunk named "parameters"
PNG:iTXt:XML:com.adobe.xmp       # PNG international text chunk
JPEG:APP1:EXIF:ImageWidth        # JPEG APP1 segment, EXIF data
JPEG:COM                         # JPEG comment marker
WebP:EXIF:Make                   # WebP EXIF chunk
TIFF:IFD0:Model                  # TIFF IFD entry
EXIF:Software                    # Standard EXIF field (format-agnostic)
XMP:dalle3:prompt                # XMP custom namespace
```

### 7.3 Pattern Matching Algorithm

```
function match_pattern(metadata, pattern):
    1. Parse field path into components
    2. Navigate metadata structure to locate field
    3. If field not found:
        return Match(matched=false)

    4. Extract field value

    5. Apply pattern type logic:
        if pattern.type == "exact":
            matched = (value == pattern.value)
        elif pattern.type == "contains":
            matched = (pattern.value in value)
        elif pattern.type == "regex":
            matched = regex.match(pattern.pattern, value)
        elif pattern.type == "exists":
            matched = true  # Field exists
        elif pattern.type == "json_path":
            try:
                parsed = json.loads(value)
                result = jsonpath.find(parsed, pattern.pattern)
                matched = len(result) > 0
            except:
                matched = false

    6. return Match(
        matched=matched,
        field=pattern.field,
        weight=pattern.weight if matched else 0,
        value=value
    )

function detect_platform(metadata, platform_patterns):
    results = []

    for platform in platform_patterns:
        matches = []
        total_score = 0

        for indicator in platform.indicators:
            match = match_pattern(metadata, indicator)
            matches.append(match)

            if indicator.required and not match.matched:
                # Failed required indicator, skip platform
                break

            if match.matched:
                total_score += indicator.weight

        else:  # All required indicators matched
            confidence = calculate_confidence(total_score, platform)
            results.append(DetectionResult(
                platform=platform,
                score=total_score,
                confidence=confidence,
                matches=matches
            ))

    # Sort by score descending
    results.sort(key=lambda r: r.score, reverse=True)

    return results[0] if results else None
```

### 7.4 Confidence Calculation

```python
def calculate_confidence(score: int, pattern: PlatformPattern) -> ConfidenceLevel:
    """
    Calculate confidence level based on matched indicator scores.

    Logic:
    - HIGH: Score >= 80 AND at least 2 high-weight indicators matched
    - MEDIUM: 50 <= Score < 80 OR only 1 high-weight indicator
    - LOW: 30 <= Score < 50
    - UNKNOWN: Score < 30

    High-weight indicator: weight >= 70
    """
    high_weight_matches = sum(
        1 for indicator in pattern.indicators
        if indicator.matched and indicator.weight >= 70
    )

    if score >= 80 and high_weight_matches >= 2:
        return ConfidenceLevel.HIGH
    elif score >= 50:
        return ConfidenceLevel.MEDIUM
    elif score >= 30:
        return ConfidenceLevel.LOW
    else:
        return ConfidenceLevel.UNKNOWN
```

---

## 8. CLI Interface

### 8.1 Command Syntax

```bash
exifanalyzer discover [OPTIONS] IMAGE_PATH [IMAGE_PATH...]

Options:
  -f, --format FORMAT      Output format: text, json, html, markdown [default: text]
  -o, --output FILE        Write output to file instead of stdout
  -v, --verbose            Include raw data and hex dumps
  -b, --batch              Batch mode: aggregate report for multiple images
  -p, --platform PLATFORM  Filter by specific platform (e.g., stable_diffusion)
  --no-color               Disable colored output
  --pattern FILE           Load custom pattern file
  --list-platforms         List supported platforms and exit
  --version                Show version and exit
  -h, --help               Show help message and exit
```

### 8.2 Usage Examples

```bash
# Basic discovery
exifanalyzer discover image.png

# JSON output
exifanalyzer discover image.png --format json

# Save to file
exifanalyzer discover image.png --output report.html --format html

# Verbose with raw data
exifanalyzer discover image.png --verbose

# Batch mode
exifanalyzer discover *.png --batch --output batch_report.json --format json

# Filter by platform
exifanalyzer discover image.png --platform stable_diffusion

# Custom patterns
exifanalyzer discover image.png --pattern my_patterns.yaml

# List platforms
exifanalyzer discover --list-platforms
```

### 8.3 Exit Codes

```
0 - Success
1 - General error
2 - File not found
3 - Unsupported format
4 - Metadata error
5 - Pattern file error
```

### 8.4 Output Formatting

**Colored Terminal Output** (when TTY detected and --no-color not set):
- Platform name: Bold + platform-specific color
- Confidence HIGH: Green
- Confidence MEDIUM: Yellow
- Confidence LOW: Orange
- Unknown fields: Cyan
- Errors/warnings: Red
- Section headers: Bold blue

**Plain Text Output** (when piped or --no-color):
- Remove ANSI color codes
- Use ASCII box-drawing characters
- Maintain alignment and readability

---

## 9. GUI Interface

### 9.1 Tab Layout Structure

```
┌────────────────────────────────────────────────────────────┐
│ Discovery Tab                                              │
├────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────┐                      │
│ │ File Selection Area              │ [Select File]        │
│ │ Current: /path/to/image.png      │ [Run Discovery]      │
│ └──────────────────────────────────┘                      │
├────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────┐  │
│ │ Tab Bar: [Summary] [Details] [Raw Data] [Compare]   │  │
│ ├──────────────────────────────────────────────────────┤  │
│ │                                                       │  │
│ │  Summary Tab Content:                                │  │
│ │  ┌────────────────────────────────────────────────┐  │  │
│ │  │ Platform Badge:                                │  │  │
│ │  │  [Icon] Stable Diffusion                       │  │  │
│ │  │  Confidence: ████████░░ 95% (High)             │  │  │
│ │  └────────────────────────────────────────────────┘  │  │
│ │                                                       │  │
│ │  ┌────────────────────────────────────────────────┐  │  │
│ │  │ Quick Stats:                                   │  │  │
│ │  │  Total Fields: 45                              │  │  │
│ │  │  AI Fields: 12                                 │  │  │
│ │  │  Unknown: 1                                    │  │  │
│ │  └────────────────────────────────────────────────┘  │  │
│ │                                                       │  │
│ │  ┌────────────────────────────────────────────────┐  │  │
│ │  │ Key Findings:                                  │  │  │
│ │  │  ✓ Prompt extracted successfully               │  │  │
│ │  │  ✓ Model: sd-v1-5-pruned-emaonly               │  │  │
│ │  │  ! 1 unknown field flagged                     │  │  │
│ │  └────────────────────────────────────────────────┘  │  │
│ │                                                       │  │
│ └───────────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────────┤
│ [Export ▼] [Copy All] [Clear]                             │
└────────────────────────────────────────────────────────────┘
```

### 9.2 Widget Specifications

**Platform Badge Widget**
- Component: Custom QWidget
- Elements:
  - Platform icon (64x64 PNG)
  - Platform name (Bold, 18pt)
  - Confidence bar (QProgressBar with color gradient)
  - Version label (if detected)
- Colors:
  - HIGH: Green (#4CAF50)
  - MEDIUM: Yellow (#FFC107)
  - LOW: Orange (#FF9800)
  - UNKNOWN: Gray (#9E9E9E)

**Tree View Widget** (Details Tab)
- Component: QTreeWidget
- Features:
  - Expandable sections
  - Icon per node type
  - Copy on right-click
  - Double-click to expand
  - Search/filter bar
- Column Headers:
  - Field Name | Value | Type | Size

**Hex Viewer Widget** (Raw Data Tab)
- Component: Custom QTextEdit with monospace font
- Format:
  ```
  Offset    Hex                                             ASCII
  00000000  61 20 62 65 61 75 74 69 66 75 6C 20 6C 61 6E   a beautiful lan
  00000010  64 73 63 61 70 65 2C 20 6D 6F 75 6E 74 61 69   dscape, mountai
  ```
- Features:
  - Highlighting on hover
  - Copy selection
  - Jump to offset
  - Search for hex/text

**JSON Viewer Widget** (Raw Data Tab for JSON fields)
- Component: QTextEdit with syntax highlighter
- Features:
  - Collapsible sections
  - Line numbers
  - Copy selection
  - Format/Minify buttons

### 9.3 User Interactions

**File Selection Flow**:
1. User clicks "Select File" button
2. File dialog opens filtered to supported formats
3. File path displayed in selection area
4. "Run Discovery" button becomes enabled

**Discovery Execution Flow**:
1. User clicks "Run Discovery"
2. Progress spinner appears
3. Discovery runs in background thread (QThread)
4. Results populate tabs when complete
5. Summary tab auto-selected
6. Status message shows success/errors

**Export Flow**:
1. User clicks "Export" dropdown
2. Menu shows format options (Text, JSON, HTML, Markdown)
3. User selects format
4. File save dialog opens
5. Report written to selected file
6. Success/error notification displayed

**Copy Field Flow**:
1. User right-clicks field in tree view
2. Context menu appears
3. User selects "Copy Value" / "Copy Key" / "Copy Both"
4. Data copied to clipboard
5. Brief "Copied!" tooltip appears

---

## 10. Error Handling

### 10.1 Error Categories

| Category | Error Type | User Message | Recovery Action |
|----------|------------|--------------|-----------------|
| File Access | FileNotFoundError | "File not found: {path}" | Verify path, check permissions |
| File Access | PermissionError | "Permission denied: {path}" | Run with appropriate permissions |
| Format | UnsupportedFormatError | "Unsupported format: {format}" | Check file extension |
| Metadata | CorruptedMetadataError | "Corrupted metadata in {chunk}" | Continue with partial extraction |
| Metadata | MetadataParsingError | "Failed to parse {field}: {reason}" | Skip field, continue discovery |
| Pattern | PatternFileError | "Invalid pattern file: {reason}" | Fix YAML syntax, validate schema |
| Pattern | PatternValidationError | "Pattern validation failed: {reason}" | Fix pattern definition |
| System | MemoryError | "Insufficient memory for operation" | Process smaller batches |
| System | TimeoutError | "Operation timed out after {seconds}s" | Increase timeout or simplify operation |

### 10.2 Error Handling Strategy

**Graceful Degradation**:
```
Level 1: Complete failure (file not found, unsupported format)
  → Stop processing, return error

Level 2: Partial failure (corrupted chunk, parse error)
  → Continue with remaining data, flag error in warnings

Level 3: Minor issue (unknown field, missing optional data)
  → Continue normally, note in summary
```

**Error Context**:
- Include file path in all file-related errors
- Include field path in metadata errors
- Include line number in pattern file errors
- Provide suggested fixes when possible

**Logging**:
```python
# Error logging levels
ERROR: Complete failures that stop processing
WARNING: Partial failures that affect results
INFO: Noteworthy events (platform detected, large dataset)
DEBUG: Detailed processing information (verbose mode)
```

### 10.3 Error Recovery Examples

**Corrupted PNG Chunk**:
```python
try:
    chunk_data = parse_png_chunk(chunk_bytes)
except CorruptedChunkError as e:
    logger.warning(f"Corrupted chunk {chunk_type}: {e}")
    # Store as unknown chunk with raw bytes
    raw_chunks.append(RawChunk(
        chunk_type=chunk_type,
        raw_data=chunk_bytes[:1000],  # First 1KB
        parse_error=str(e)
    ))
    continue  # Process remaining chunks
```

**Invalid UTF-8 Text**:
```python
try:
    decoded = data.decode('utf-8')
except UnicodeDecodeError:
    try:
        decoded = data.decode('latin-1')
    except:
        # Fall back to hex representation
        decoded = f"<Binary: {data.hex()[:100]}...>"
```

**Pattern File Syntax Error**:
```python
try:
    patterns = yaml.safe_load(pattern_file)
except yaml.YAMLError as e:
    raise PatternFileError(
        f"Invalid YAML syntax at line {e.line}: {e.reason}\n"
        f"Fix: Check for proper indentation and quote strings"
    )
```

---

## 11. Performance Considerations

### 11.1 Performance Targets

| Operation | Target | Maximum |
|-----------|--------|---------|
| Single image discovery | <2s | 5s |
| Batch 100 images | <60s | 120s |
| Pattern matching | <100ms | 500ms |
| Report generation (text) | <50ms | 200ms |
| Report generation (HTML) | <500ms | 2s |
| Memory usage (single) | <100MB | 500MB |
| Memory usage (batch) | <500MB | 2GB |

### 11.2 Optimization Strategies

**Lazy Loading**:
- Don't extract raw chunks unless `extract_raw=True`
- Don't generate hex dumps unless `verbose=True`
- Don't parse JSON workflows unless matched by pattern

**Streaming Processing**:
```python
# Don't load entire file into memory
with open(file_path, 'rb') as f:
    # Process chunks sequentially
    while chunk := read_next_chunk(f):
        process_chunk(chunk)
        # Release memory immediately
        del chunk
```

**Caching**:
```python
# Cache compiled regex patterns
@lru_cache(maxsize=128)
def get_compiled_pattern(pattern: str) -> re.Pattern:
    return re.compile(pattern)

# Cache pattern files
@lru_cache(maxsize=8)
def load_pattern_file(file_path: Path) -> Dict:
    return yaml.safe_load(file_path.read_text())
```

**Parallel Processing** (Batch Mode):
```python
from concurrent.futures import ThreadPoolExecutor

def batch_discover(file_paths: List[Path]) -> BatchDiscoveryResult:
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(discover, file_paths)
    return aggregate_results(results)
```

**Memory Management**:
```python
# Limit raw data stored in memory
MAX_RAW_CHUNK_SIZE = 100_000  # 100KB

if len(chunk_data) > MAX_RAW_CHUNK_SIZE:
    # Store reference instead of full data
    chunk.raw_data = chunk_data[:1000]  # Preview only
    chunk.truncated = True
    chunk.full_size = len(chunk_data)
```

### 11.3 Profiling & Monitoring

**Instrumentation Points**:
- Discovery start/end (total time)
- Metadata extraction (per format)
- Pattern matching (per platform)
- Report generation (per format)
- Memory usage (peak)

**Performance Metrics**:
```python
@dataclass
class PerformanceMetrics:
    """Discovery performance metrics."""
    total_time: float
    extraction_time: float
    detection_time: float
    report_time: float
    peak_memory_mb: float
    file_size_mb: float

    @property
    def throughput_mbps(self) -> float:
        """MB processed per second."""
        return self.file_size_mb / self.total_time
```

---

## 12. Testing Strategy

### 12.1 Test Coverage Requirements

| Component | Target Coverage | Test Types |
|-----------|----------------|------------|
| Discovery Engine | 90%+ | Unit, Integration |
| Metadata Extractor | 85%+ | Unit, Format-specific |
| Platform Detector | 95%+ | Unit, Pattern tests |
| Report Generator | 80%+ | Unit, Output validation |
| CLI Handler | 85%+ | Integration, E2E |
| GUI Tab | 70%+ | Integration, UI tests |
| **Overall** | **85%+** | All types |

### 12.2 Test Categories

**Unit Tests**:
```python
# Test individual components in isolation
def test_pattern_exact_match():
    """Test exact pattern matching."""
    indicator = PatternIndicator(
        field="EXIF:Software",
        pattern_type="exact",
        pattern_value="Midjourney",
        weight=100
    )
    metadata = {"EXIF": {"Software": "Midjourney"}}

    result = match_pattern(metadata, indicator)

    assert result.matched == True
    assert result.weight == 100

def test_pattern_regex_match():
    """Test regex pattern matching."""
    # Test various regex patterns

def test_confidence_calculation():
    """Test confidence level calculation."""
    # Test edge cases for each level
```

**Integration Tests**:
```python
# Test component interactions
def test_full_discovery_flow():
    """Test complete discovery flow."""
    engine = MetadataDiscoveryEngine()
    result = engine.discover("tests/fixtures/sd_image.png")

    assert result.detection.platform_id == "stable_diffusion"
    assert result.detection.confidence == ConfidenceLevel.HIGH
    assert "prompt" in result.ai_metadata.prompts

def test_batch_discovery():
    """Test batch processing."""
    # Test multiple images, aggregation
```

**Format-Specific Tests**:
```python
# Test each image format
def test_png_chunk_extraction():
    """Test PNG tEXt/iTXt/zTXt extraction."""
    # Test all PNG chunk types

def test_jpeg_app_marker_extraction():
    """Test JPEG APP marker extraction."""
    # Test APP0-APP15 markers

def test_webp_chunk_extraction():
    """Test WebP RIFF chunk extraction."""
    # Test VP8X, EXIF, XMP chunks
```

**Pattern Tests**:
```python
# Test platform detection accuracy
def test_stable_diffusion_detection():
    """Test Stable Diffusion detection accuracy."""
    test_images = [
        ("sd_auto1111.png", "stable_diffusion", ConfidenceLevel.HIGH),
        ("sd_comfyui.png", "stable_diffusion", ConfidenceLevel.HIGH),
        ("sd_invokeai.png", "stable_diffusion", ConfidenceLevel.HIGH),
    ]

    for image, expected_platform, expected_confidence in test_images:
        result = detect_platform(image)
        assert result.platform_id == expected_platform
        assert result.confidence == expected_confidence

def test_pattern_priority():
    """Test pattern matching priority when multiple platforms match."""
    # Create ambiguous metadata that matches multiple patterns
    # Verify highest-scoring platform is selected
```

**Error Handling Tests**:
```python
def test_corrupted_metadata_handling():
    """Test graceful handling of corrupted metadata."""
    # Test various corruption scenarios

def test_missing_file_error():
    """Test error handling for missing files."""
    with pytest.raises(FileNotFoundError):
        engine.discover("nonexistent.png")

def test_unsupported_format_error():
    """Test error handling for unsupported formats."""
    with pytest.raises(UnsupportedFormatError):
        engine.discover("document.pdf")
```

**Performance Tests**:
```python
@pytest.mark.performance
def test_discovery_performance():
    """Test discovery completes within time limit."""
    start = time.time()
    engine.discover("tests/fixtures/large_image_50mb.png")
    elapsed = time.time() - start

    assert elapsed < 5.0, f"Discovery took {elapsed}s (limit: 5s)"

@pytest.mark.performance
def test_batch_performance():
    """Test batch processing performance."""
    images = [f"test_{i}.png" for i in range(100)]
    start = time.time()
    engine.batch_discover(images)
    elapsed = time.time() - start

    assert elapsed < 120.0, f"Batch took {elapsed}s (limit: 120s)"
```

**CLI Tests**:
```python
def test_cli_basic_discovery(capsys):
    """Test basic CLI discovery command."""
    result = subprocess.run(
        ["exifanalyzer", "discover", "test.png"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "METADATA DISCOVERY REPORT" in result.stdout

def test_cli_json_output():
    """Test CLI JSON output format."""
    # Verify valid JSON structure
```

**GUI Tests** (using pytest-qt):
```python
def test_gui_load_image(qtbot):
    """Test loading image in GUI."""
    tab = DiscoveryTab()
    qtbot.addWidget(tab)

    tab.load_image(Path("test.png"))

    assert tab.current_image == Path("test.png")

def test_gui_run_discovery(qtbot):
    """Test running discovery in GUI."""
    # Test UI updates, result display
```

### 12.3 Test Fixtures

**Test Image Repository**:
```
tests/fixtures/images/
├── stable_diffusion/
│   ├── auto1111_v1.5.png
│   ├── comfyui_workflow.png
│   └── invokeai_basic.png
├── midjourney/
│   ├── v5_basic.jpg
│   └── v6_detailed.jpg
├── dalle/
│   ├── dalle2_simple.png
│   └── dalle3_revised.png
├── unknown/
│   ├── no_metadata.png
│   └── stripped_metadata.jpg
└── corrupted/
    ├── truncated.png
    └── invalid_chunk.jpg
```

**Pattern Test Data**:
```yaml
# tests/fixtures/patterns/test_patterns.yaml
platforms:
  test_platform:
    name: "Test Platform"
    indicators:
      - field: "TEST:field1"
        type: "exact"
        value: "test_value"
        weight: 100
        required: true
```

### 12.4 Continuous Testing

**Pre-commit Checks**:
- Run unit tests (<30s)
- Check code coverage (must not decrease)
- Lint code (flake8, mypy)
- Format check (black)

**CI Pipeline**:
1. Run all unit tests
2. Run integration tests
3. Run format-specific tests
4. Generate coverage report
5. Run performance benchmarks
6. Build documentation

**Regression Testing**:
- Maintain test suite for each supported platform
- Add new test when bug is found
- Test against real-world images from community

---

## 13. Security Considerations

### 13.1 Threat Model

**Threat**: Malicious metadata in image files
- **Risk**: Code execution, memory corruption, DoS
- **Mitigation**:
  - Validate all input data
  - Limit resource consumption
  - Sandbox parsing operations
  - Use safe libraries (PIL, not custom parsers)

**Threat**: Pattern injection via custom pattern files
- **Risk**: Arbitrary code execution via unsafe YAML
- **Mitigation**:
  - Use `yaml.safe_load()` only
  - Validate pattern schema before execution
  - Limit pattern complexity (regex timeout)

**Threat**: Path traversal via file paths
- **Risk**: Reading arbitrary files
- **Mitigation**:
  - Validate file paths (reject ../, absolute paths if inappropriate)
  - Check file exists and is regular file
  - Verify file extension matches content

**Threat**: DoS via extremely large metadata
- **Risk**: Memory exhaustion, infinite loops
- **Mitigation**:
  - Limit max chunk size (100MB)
  - Timeout for regex matching (1s per pattern)
  - Limit pattern complexity (max 1000 chars)
  - Truncate large fields in reports

**Threat**: Privacy leakage via exported reports
- **Risk**: Sensitive metadata shared unintentionally
- **Mitigation**:
  - Clear warnings about what data is included
  - Option to redact sensitive fields
  - Default to summary report (not full raw data)

### 13.2 Input Validation

**File Path Validation**:
```python
def validate_file_path(path: Path) -> None:
    """Validate file path for security."""
    # Convert to absolute path
    path = path.resolve()

    # Check file exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Check is regular file (not directory, symlink, device)
    if not path.is_file():
        raise ValueError(f"Not a regular file: {path}")

    # Check file size reasonable (<1GB)
    if path.stat().st_size > 1_000_000_000:
        raise ValueError(f"File too large: {path.stat().st_size} bytes")

    # Check extension matches supported formats
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFormatError(f"Unsupported format: {path.suffix}")
```

**Metadata Validation**:
```python
def validate_chunk_data(data: bytes, max_size: int = 100_000_000) -> None:
    """Validate metadata chunk data."""
    if len(data) > max_size:
        raise ValueError(f"Chunk too large: {len(data)} bytes")

    # Check for NULL bytes in unexpected places
    # Check for control characters
    # Validate structure based on chunk type
```

**Pattern Validation**:
```python
def validate_pattern(pattern: dict) -> None:
    """Validate pattern definition."""
    required_fields = ["name", "indicators"]
    for field in required_fields:
        if field not in pattern:
            raise PatternValidationError(f"Missing required field: {field}")

    # Validate indicators
    for indicator in pattern["indicators"]:
        # Check weight 0-100
        if not 0 <= indicator["weight"] <= 100:
            raise PatternValidationError("Weight must be 0-100")

        # Validate regex patterns (check for catastrophic backtracking)
        if indicator["type"] == "regex":
            validate_safe_regex(indicator["pattern"])
```

**Regex Safety**:
```python
def validate_safe_regex(pattern: str) -> None:
    """Validate regex pattern is safe (no ReDoS)."""
    # Limit pattern length
    if len(pattern) > 1000:
        raise PatternValidationError("Regex pattern too long")

    # Check for dangerous patterns
    dangerous = [
        r'\(\.\*\)\+',  # (.*)+
        r'\(\.\+\)\*',  # (.+)*
        r'\(.\*\)\*',   # (.*)*
    ]
    for danger in dangerous:
        if re.search(danger, pattern):
            raise PatternValidationError(
                f"Dangerous regex pattern detected: {danger}"
            )

    # Test compile with timeout
    try:
        re.compile(pattern, timeout=0.1)
    except re.error as e:
        raise PatternValidationError(f"Invalid regex: {e}")
```

### 13.3 Resource Limits

```python
# Global limits
MAX_FILE_SIZE = 1_000_000_000      # 1GB
MAX_CHUNK_SIZE = 100_000_000       # 100MB
MAX_BATCH_SIZE = 1000              # 1000 images
MAX_PATTERN_LENGTH = 1000          # 1000 chars
MAX_FIELD_VALUE_LENGTH = 1_000_000 # 1MB

REGEX_TIMEOUT = 1.0                # 1 second
DISCOVERY_TIMEOUT = 300.0          # 5 minutes
BATCH_TIMEOUT = 3600.0             # 1 hour

# Apply limits during processing
@timeout(REGEX_TIMEOUT)
def match_regex(pattern, text):
    return re.match(pattern, text)
```

### 13.4 Safe Defaults

- Default to read-only operations (no file modification)
- Default to summary reports (not full raw data)
- Default to local pattern files (no network fetching)
- Default to safe YAML loading (`yaml.safe_load()`)
- Default to conservative timeouts
- Default to truncating large fields in UI

---

## 14. Migration & Deployment

### 14.1 Versioning Strategy

**Semantic Versioning**: MAJOR.MINOR.PATCH
- **MAJOR**: Breaking changes to API or data models
- **MINOR**: New features, new platform support
- **PATCH**: Bug fixes, pattern updates

**Pattern File Versioning**:
```yaml
version: "1.0"
schema_version: "1.0"  # Schema version for validation
```

### 14.2 Deployment Phases

**Phase 1: Alpha (Internal Testing)**
- Duration: 2 weeks
- Audience: Development team
- Scope: Core engine, CLI
- Success: All P0 tests pass

**Phase 2: Beta (Public Testing)**
- Duration: 4 weeks
- Audience: Volunteer users from community
- Scope: All features except GUI
- Success: <10 P1 bugs, 90% detection accuracy

**Phase 3: Release Candidate**
- Duration: 2 weeks
- Audience: All users (opt-in)
- Scope: Complete feature set
- Success: <5 P2 bugs, stable performance

**Phase 4: General Availability**
- Duration: Ongoing
- Audience: All users (default enabled)
- Scope: Production-ready
- Success: <1% error rate

### 14.3 Migration Path

**For Existing Users**:
1. Discovery feature added as new command/tab
2. No changes to existing functionality
3. Backward compatible with existing API
4. New dependencies installed automatically

**Configuration Migration**:
```python
# Auto-detect and migrate old pattern files
def migrate_pattern_file(old_file: Path, new_file: Path):
    """Migrate pattern file to new schema."""
    old_data = yaml.safe_load(old_file.read_text())

    if old_data.get("schema_version") == "1.0":
        return  # Already migrated

    # Apply migrations
    new_data = apply_migrations(old_data)
    new_file.write_text(yaml.dump(new_data))
```

### 14.4 Rollback Plan

**If Critical Issues Found**:
1. Disable discovery command via feature flag
2. Keep existing functionality working
3. Notify users via error message
4. Fix issue in patch release
5. Re-enable after testing

**Feature Flag**:
```python
# config/feature_flags.yaml
discovery_mode:
  enabled: true
  min_version: "2.0.0"
  max_version: null
```

### 14.5 Documentation Updates

**Required Documentation**:
- User guide: "Getting Started with Discovery Mode"
- CLI reference: `exifanalyzer discover` command
- API reference: `MetadataDiscoveryEngine` class
- Pattern creation guide: Writing custom patterns
- Platform support matrix: Supported AI platforms
- Troubleshooting guide: Common issues and solutions

**Examples Repository**:
- Sample images for each platform
- Sample pattern files
- Sample scripts using API
- Sample reports (text, JSON, HTML)

---

## 15. Appendix

### 15.1 Glossary

- **Discovery Mode**: Feature that performs deep inspection of image metadata
- **Platform Detection**: Process of identifying which AI service generated an image
- **Pattern Matching**: Rule-based identification of metadata formats
- **Confidence Level**: Probability score for platform identification
- **Field Path**: Hierarchical identifier for metadata location
- **Raw Chunk**: Binary metadata block from image file
- **Indicator**: Single rule in platform detection pattern

### 15.2 References

**Standards & Specifications**:
- PNG: http://www.libpng.org/pub/png/spec/
- JPEG: https://www.w3.org/Graphics/JPEG/
- EXIF: https://www.exif.org/Exif2-2.PDF
- XMP: https://www.adobe.com/devnet/xmp.html
- TIFF: https://www.adobe.io/open/standards/TIFF.html

**AI Platform Documentation**:
- Stable Diffusion: https://github.com/Stability-AI/stablediffusion
- ComfyUI: https://github.com/comfyanonymous/ComfyUI
- AUTOMATIC1111: https://github.com/AUTOMATIC1111/stable-diffusion-webui
- Midjourney: https://docs.midjourney.com/
- DALL-E: https://platform.openai.com/docs/guides/images

**Libraries**:
- Pillow: https://pillow.readthedocs.io/
- piexif: https://piexif.readthedocs.io/
- PyYAML: https://pyyaml.org/wiki/PyYAMLDocumentation

### 15.3 Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-09-30 | Development Team | Initial technical specification |

---

**Document Status**: Draft
**Review Status**: Pending
**Approval Status**: Pending

**Next Steps**:
1. Technical review by team
2. PRD/Tech Spec alignment check
3. Prototype implementation of core engine
4. Pattern file format validation
5. Begin Phase 1 implementation
