"""
Core metadata handling and normalization structures.
"""
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

from .exceptions import ValidationError, MetadataError
from .logger import logger


@dataclass
class MetadataBlock:
    """Represents a single metadata block (EXIF, IPTC, XMP, etc.)."""
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    raw_data: Optional[bytes] = None
    encoding: str = "utf-8"

    def get(self, key: str, default: Any = None) -> Any:
        """Get metadata value by key with optional default."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set metadata value."""
        self.data[key] = value

    def remove(self, key: str) -> bool:
        """Remove metadata key. Returns True if key existed."""
        return self.data.pop(key, None) is not None

    def keys(self) -> List[str]:
        """Get all metadata keys."""
        return list(self.data.keys())

    def is_empty(self) -> bool:
        """Check if metadata block is empty."""
        return len(self.data) == 0


@dataclass
class ImageMetadata:
    """
    Unified metadata structure for all image formats.

    Normalizes metadata from different sources (EXIF, IPTC, XMP, format-specific)
    into a consistent interface while preserving original data structure.
    """
    file_path: Path
    format: str
    exif: MetadataBlock = field(default_factory=lambda: MetadataBlock("exif"))
    iptc: MetadataBlock = field(default_factory=lambda: MetadataBlock("iptc"))
    xmp: MetadataBlock = field(default_factory=lambda: MetadataBlock("xmp"))
    custom: MetadataBlock = field(default_factory=lambda: MetadataBlock("custom"))

    # File metadata
    file_size: Optional[int] = None
    last_modified: Optional[datetime] = None
    pixel_hash: Optional[str] = None  # For integrity verification

    def __post_init__(self):
        """Post-initialization validation and setup."""
        if not isinstance(self.file_path, Path):
            self.file_path = Path(self.file_path)

        if not self.format:
            raise ValidationError("Image format must be specified")

    def get_block(self, block_name: str) -> Optional[MetadataBlock]:
        """Get metadata block by name."""
        blocks = {
            "exif": self.exif,
            "iptc": self.iptc,
            "xmp": self.xmp,
            "custom": self.custom
        }
        return blocks.get(block_name.lower())

    def has_metadata(self) -> bool:
        """Check if image has any metadata."""
        return any(not block.is_empty() for block in [self.exif, self.iptc, self.xmp, self.custom])

    def has_gps_data(self) -> bool:
        """Check if image contains GPS/location data."""
        gps_patterns = [
            "gps", "latitude", "longitude", "altitude", "location",
            "geotag", "coordinate", "position"
        ]

        for block in [self.exif, self.iptc, self.xmp, self.custom]:
            for key in block.keys():
                key_lower = key.lower()
                if any(pattern in key_lower for pattern in gps_patterns):
                    return True
        return False

    def get_privacy_sensitive_keys(self) -> List[tuple]:
        """
        Get list of privacy-sensitive metadata keys.

        Returns:
            List of (block_name, key) tuples for sensitive data
        """
        sensitive_keys = []

        # GPS and location data
        gps_patterns = ["gps", "location", "geotag", "coordinate"]

        # Device and software info
        device_patterns = ["make", "model", "software", "lens", "serial", "camera"]

        # Personal info
        personal_patterns = ["artist", "author", "creator", "owner", "copyright", "contact"]

        all_patterns = gps_patterns + device_patterns + personal_patterns

        for block_name, block in [("exif", self.exif), ("iptc", self.iptc),
                                 ("xmp", self.xmp), ("custom", self.custom)]:
            for key in block.keys():
                key_lower = key.lower()
                if any(pattern in key_lower for pattern in all_patterns):
                    sensitive_keys.append((block_name, key))

        return sensitive_keys

    def strip_gps_data(self) -> int:
        """
        Remove GPS/location data from metadata.

        Returns:
            Number of GPS-related keys removed
        """
        removed_count = 0
        gps_patterns = ["gps", "location", "geotag", "coordinate"]

        for block in [self.exif, self.iptc, self.xmp, self.custom]:
            keys_to_remove = []
            for key in block.keys():
                if any(pattern in key.lower() for pattern in gps_patterns):
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                if block.remove(key):
                    removed_count += 1
                    logger.debug(f"Removed GPS key: {key} from {block.name}")

        return removed_count

    def strip_all_metadata(self) -> int:
        """
        Remove all metadata from image.

        Returns:
            Total number of keys removed
        """
        removed_count = 0

        for block in [self.exif, self.iptc, self.xmp, self.custom]:
            keys = list(block.keys())
            for key in keys:
                if block.remove(key):
                    removed_count += 1

        logger.info(f"Removed {removed_count} metadata keys from {self.file_path}")
        return removed_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary format."""
        return {
            "file_path": str(self.file_path),
            "format": self.format,
            "file_size": self.file_size,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "pixel_hash": self.pixel_hash,
            "metadata": {
                "exif": self.exif.data,
                "iptc": self.iptc.data,
                "xmp": self.xmp.data,
                "custom": self.custom.data
            }
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert metadata to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImageMetadata":
        """Create ImageMetadata from dictionary."""
        metadata = cls(
            file_path=Path(data["file_path"]),
            format=data["format"],
            file_size=data.get("file_size"),
            pixel_hash=data.get("pixel_hash")
        )

        if data.get("last_modified"):
            metadata.last_modified = datetime.fromisoformat(data["last_modified"])

        # Load metadata blocks
        metadata_blocks = data.get("metadata", {})
        metadata.exif.data = metadata_blocks.get("exif", {})
        metadata.iptc.data = metadata_blocks.get("iptc", {})
        metadata.xmp.data = metadata_blocks.get("xmp", {})
        metadata.custom.data = metadata_blocks.get("custom", {})

        return metadata

    @classmethod
    def from_json(cls, json_str: str) -> "ImageMetadata":
        """Create ImageMetadata from JSON string."""
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise MetadataError(f"Invalid JSON format: {e}")

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"ImageMetadata({self.file_path}, {self.format}, {self.has_metadata()})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (f"ImageMetadata(file_path={self.file_path}, format={self.format}, "
                f"exif_keys={len(self.exif.keys())}, iptc_keys={len(self.iptc.keys())}, "
                f"xmp_keys={len(self.xmp.keys())}, custom_keys={len(self.custom.keys())})")