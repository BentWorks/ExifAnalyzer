"""
Data models for metadata discovery.
"""
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional


class ConfidenceLevel(Enum):
    """Platform detection confidence levels."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNKNOWN = "Unknown"


@dataclass
class RawChunk:
    """Raw metadata chunk from image file."""
    chunk_type: str  # e.g., "PNG:tEXt", "JPEG:APP1", "EXIF:UserComment"
    offset: int  # Byte offset in file
    length: int  # Chunk size in bytes
    raw_data: bytes  # Raw binary data
    decoded_text: Optional[str] = None  # Decoded text if applicable
    encoding: Optional[str] = None  # Detected encoding
    parse_error: Optional[str] = None  # Error if parsing failed


@dataclass
class ExtractedMetadata:
    """Complete metadata extraction result."""
    file_path: Path
    file_format: str
    file_size: int
    standard_metadata: Any  # ImageMetadata from existing system
    raw_chunks: List[RawChunk] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    extraction_errors: List[str] = field(default_factory=list)
    extraction_time: float = 0.0


@dataclass
class PatternIndicator:
    """Single indicator for platform detection."""
    field_path: str  # e.g., "PNG:tEXt:parameters"
    pattern_type: str  # "exact", "regex", "contains", "exists"
    pattern_value: str  # Pattern to match
    weight: int  # Importance score (0-100)
    is_required: bool = False  # Must match for platform to be detected


@dataclass
class PlatformPattern:
    """Platform detection pattern definition."""
    platform_id: str  # e.g., "stable_diffusion"
    platform_name: str  # Human-readable name
    version: Optional[str] = None  # Version if pattern is version-specific
    indicators: List[PatternIndicator] = field(default_factory=list)
    field_mappings: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    documentation_url: str = ""


@dataclass
class ModelInfo:
    """AI model information."""
    name: str
    version: Optional[str] = None
    hash: Optional[str] = None
    architecture: Optional[str] = None
    source: Optional[str] = None


@dataclass
class AIMetadata:
    """Structured AI-specific metadata."""
    prompts: Dict[str, str] = field(default_factory=dict)  # positive, negative, system
    model: Optional[ModelInfo] = None
    parameters: Dict[str, Any] = field(default_factory=dict)  # steps, sampler, cfg, seed
    workflow: Optional[str] = None  # JSON workflow for ComfyUI, etc.
    generation_info: Dict[str, Any] = field(default_factory=dict)  # timestamps, version
    raw_data: Dict[str, Any] = field(default_factory=dict)  # Unstructured additional data


@dataclass
class DetectionResult:
    """Platform detection result."""
    platform_id: str
    platform_name: str
    confidence: ConfidenceLevel
    confidence_score: float  # 0-100
    matched_indicators: List[PatternIndicator] = field(default_factory=list)
    version: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiscoveryResult:
    """Complete discovery result for single image."""
    file_path: Path
    extracted_metadata: ExtractedMetadata
    detection: DetectionResult
    ai_metadata: Optional[AIMetadata] = None
    unknown_fields: List[RawChunk] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    discovery_time: float = 0.0


@dataclass
class BatchDiscoveryResult:
    """Aggregated results for multiple images."""
    results: List[DiscoveryResult] = field(default_factory=list)
    total_images: int = 0
    successful: int = 0
    failed: int = 0
    platform_distribution: Dict[str, int] = field(default_factory=dict)
    common_fields: Dict[str, int] = field(default_factory=dict)
    anomalies: List[str] = field(default_factory=list)
    total_time: float = 0.0
