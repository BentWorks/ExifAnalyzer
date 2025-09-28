"""
Base adapter interface for format-specific metadata handlers.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List

from .metadata import ImageMetadata
from .exceptions import UnsupportedFormatError, MetadataError
from .logger import logger


class BaseMetadataAdapter(ABC):
    """
    Abstract base class for format-specific metadata adapters.

    Each image format (JPEG, PNG, TIFF, etc.) should implement this interface
    to provide consistent metadata operations across different formats.
    """

    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """List of supported file formats (extensions)."""
        pass

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Human-readable format name."""
        pass

    def supports_format(self, file_path: Path) -> bool:
        """
        Check if this adapter supports the given file format.

        Args:
            file_path: Path to the image file

        Returns:
            True if format is supported
        """
        suffix = file_path.suffix.lower()
        return suffix in [f".{fmt.lower()}" for fmt in self.supported_formats]

    @abstractmethod
    def read_metadata(self, file_path: Path) -> ImageMetadata:
        """
        Read metadata from image file.

        Args:
            file_path: Path to the image file

        Returns:
            ImageMetadata object with extracted metadata

        Raises:
            UnsupportedFormatError: If format is not supported
            MetadataError: If metadata cannot be read
            FileNotFoundError: If file doesn't exist
        """
        pass

    @abstractmethod
    def write_metadata(self, metadata: ImageMetadata, output_path: Optional[Path] = None) -> Path:
        """
        Write metadata to image file.

        Args:
            metadata: ImageMetadata object to write
            output_path: Optional output path (if None, overwrites original)

        Returns:
            Path to the output file

        Raises:
            MetadataError: If metadata cannot be written
            PixelDataCorruptionError: If pixel data is corrupted
        """
        pass

    @abstractmethod
    def strip_metadata(self, file_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        Remove all metadata from image file.

        Args:
            file_path: Path to the input image file
            output_path: Optional output path (if None, overwrites original)

        Returns:
            Path to the output file

        Raises:
            MetadataError: If metadata cannot be stripped
            PixelDataCorruptionError: If pixel data is corrupted
        """
        pass

    def validate_file(self, file_path: Path) -> None:
        """
        Validate that file exists and is readable.

        Args:
            file_path: Path to validate

        Raises:
            FileNotFoundError: If file doesn't exist
            FilePermissionError: If file is not readable
            UnsupportedFormatError: If format is not supported
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise MetadataError(f"Path is not a file: {file_path}")

        if not self.supports_format(file_path):
            raise UnsupportedFormatError(
                f"Format not supported by {self.format_name}: {file_path.suffix}"
            )

        try:
            with open(file_path, 'rb') as f:
                f.read(1)  # Try to read one byte
        except PermissionError:
            raise PermissionError(f"No read permission for file: {file_path}")

    def get_pixel_hash(self, file_path: Path) -> str:
        """
        Calculate hash of pixel data for integrity verification.

        Args:
            file_path: Path to image file

        Returns:
            Hash string of pixel data
        """
        import hashlib
        from PIL import Image

        try:
            with Image.open(file_path) as img:
                # Convert to consistent format for hashing
                img_rgb = img.convert('RGB')
                pixel_bytes = img_rgb.tobytes()
                return hashlib.sha256(pixel_bytes).hexdigest()
        except Exception as e:
            logger.warning(f"Could not calculate pixel hash for {file_path}: {e}")
            return ""

    def verify_pixel_integrity(self, original_path: Path, modified_path: Path) -> bool:
        """
        Verify that pixel data hasn't been corrupted.

        Args:
            original_path: Path to original image
            modified_path: Path to modified image

        Returns:
            True if pixel data is identical
        """
        try:
            original_hash = self.get_pixel_hash(original_path)
            modified_hash = self.get_pixel_hash(modified_path)
            return original_hash == modified_hash and original_hash != ""
        except Exception as e:
            logger.error(f"Pixel integrity check failed: {e}")
            return False

    def log_operation(self, operation: str, file_path: Path, success: bool = True) -> None:
        """Log metadata operation for auditing."""
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"{self.format_name} {operation} {status}: {file_path}")

    def __str__(self) -> str:
        """String representation."""
        return f"{self.format_name}Adapter"

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"{self.__class__.__name__}(formats={self.supported_formats})"