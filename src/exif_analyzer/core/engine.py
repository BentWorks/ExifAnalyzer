"""
Core metadata engine that orchestrates format-specific adapters.
"""
from pathlib import Path
from typing import Optional, List, Dict, Type, Union
import mimetypes
import json

from .base_adapter import BaseMetadataAdapter
from .metadata import ImageMetadata
from .exceptions import UnsupportedFormatError, MetadataError, FileError
from .file_safety import FileSafetyManager
from .logger import logger

# Import adapters
from ..adapters.jpeg_adapter import JPEGAdapter
from ..adapters.png_adapter import PNGAdapter


class MetadataEngine:
    """
    Central metadata engine that manages format-specific adapters
    and provides unified interface for metadata operations.
    """

    def __init__(self):
        """Initialize metadata engine with available adapters."""
        self.adapters: Dict[str, BaseMetadataAdapter] = {}
        self.safety_manager = FileSafetyManager()

        # Register built-in adapters
        self._register_adapters()

    def _register_adapters(self) -> None:
        """Register all available format adapters with shared safety manager."""
        adapters = [
            JPEGAdapter(safety_manager=self.safety_manager),
            PNGAdapter(safety_manager=self.safety_manager),
            # TODO: Add TIFF, WebP, GIF adapters
        ]

        for adapter in adapters:
            for format_ext in adapter.supported_formats:
                self.adapters[format_ext.lower()] = adapter
                logger.debug(f"Registered {adapter.format_name} adapter for .{format_ext}")

    def register_adapter(self, adapter: BaseMetadataAdapter) -> None:
        """
        Register a custom adapter.

        Args:
            adapter: Adapter instance to register
        """
        for format_ext in adapter.supported_formats:
            self.adapters[format_ext.lower()] = adapter
            logger.info(f"Registered custom {adapter.format_name} adapter for .{format_ext}")

    def get_adapter(self, file_path: Path) -> BaseMetadataAdapter:
        """
        Get appropriate adapter for file format.

        Args:
            file_path: Path to image file

        Returns:
            Format-specific adapter

        Raises:
            UnsupportedFormatError: If format is not supported
        """
        if not file_path.exists():
            raise FileError(f"File not found: {file_path}")

        # Get file extension
        extension = file_path.suffix.lower().lstrip('.')

        # Try direct extension lookup
        if extension in self.adapters:
            return self.adapters[extension]

        # Try MIME type detection as fallback
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            format_map = {
                'image/jpeg': 'jpg',
                'image/png': 'png',
                'image/tiff': 'tiff',
                'image/webp': 'webp',
                'image/gif': 'gif'
            }
            mapped_format = format_map.get(mime_type)
            if mapped_format and mapped_format in self.adapters:
                return self.adapters[mapped_format]

        raise UnsupportedFormatError(f"No adapter available for format: {extension}")

    def read_metadata(self, file_path: Union[str, Path]) -> ImageMetadata:
        """
        Read metadata from image file.

        Args:
            file_path: Path to image file

        Returns:
            ImageMetadata object with extracted metadata

        Raises:
            UnsupportedFormatError: If format is not supported
            MetadataError: If metadata cannot be read
            FileError: If file cannot be accessed
        """
        file_path = Path(file_path)
        adapter = self.get_adapter(file_path)

        try:
            logger.info(f"Reading metadata from {file_path} using {adapter.format_name} adapter")
            return adapter.read_metadata(file_path)
        except Exception as e:
            logger.error(f"Failed to read metadata from {file_path}: {e}")
            raise

    def write_metadata(
        self,
        metadata: ImageMetadata,
        output_path: Optional[Union[str, Path]] = None,
        create_backup: bool = True
    ) -> Path:
        """
        Write metadata to image file.

        Args:
            metadata: ImageMetadata to write
            output_path: Optional output path (defaults to original file)
            create_backup: Whether to create backup before writing

        Returns:
            Path to output file

        Raises:
            UnsupportedFormatError: If format is not supported
            MetadataError: If metadata cannot be written
        """
        if output_path:
            output_path = Path(output_path)
        else:
            output_path = metadata.file_path

        adapter = self.get_adapter(metadata.file_path)

        # Create backup if requested and output overwrites original
        if create_backup and output_path == metadata.file_path:
            self.safety_manager.create_backup(metadata.file_path)

        try:
            logger.info(f"Writing metadata to {output_path} using {adapter.format_name} adapter")
            return adapter.write_metadata(metadata, output_path)
        except Exception as e:
            logger.error(f"Failed to write metadata to {output_path}: {e}")
            raise

    def strip_metadata(
        self,
        file_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        create_backup: bool = True
    ) -> Path:
        """
        Remove all metadata from image file.

        Args:
            file_path: Path to input image file
            output_path: Optional output path (defaults to original file)
            create_backup: Whether to create backup before stripping

        Returns:
            Path to output file

        Raises:
            UnsupportedFormatError: If format is not supported
            MetadataError: If metadata cannot be stripped
        """
        file_path = Path(file_path)

        if output_path:
            output_path = Path(output_path)
        else:
            output_path = file_path

        adapter = self.get_adapter(file_path)

        # Create backup if requested and output overwrites original
        if create_backup and output_path == file_path:
            self.safety_manager.create_backup(file_path)

        try:
            logger.info(f"Stripping metadata from {file_path} using {adapter.format_name} adapter")
            return adapter.strip_metadata(file_path, output_path)
        except Exception as e:
            logger.error(f"Failed to strip metadata from {file_path}: {e}")
            raise

    def strip_gps_data(
        self,
        file_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        create_backup: bool = True
    ) -> Path:
        """
        Remove GPS/location data from image file.

        Args:
            file_path: Path to input image file
            output_path: Optional output path (defaults to original file)
            create_backup: Whether to create backup

        Returns:
            Path to output file
        """
        # Read current metadata
        metadata = self.read_metadata(file_path)

        # Strip GPS data
        removed_count = metadata.strip_gps_data()
        logger.info(f"Removed {removed_count} GPS-related metadata entries")

        # Write back modified metadata
        return self.write_metadata(metadata, output_path, create_backup)

    def export_metadata(
        self,
        file_path: Union[str, Path],
        export_path: Union[str, Path],
        format: str = "json"
    ) -> Path:
        """
        Export metadata to external file.

        Args:
            file_path: Path to image file
            export_path: Path for exported metadata
            format: Export format ('json' or 'xmp')

        Returns:
            Path to exported metadata file
        """
        metadata = self.read_metadata(file_path)
        export_path = Path(export_path)

        if format.lower() == "json":
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(metadata.to_json())
        elif format.lower() == "xmp":
            # TODO: Implement XMP export
            raise NotImplementedError("XMP export not yet implemented")
        else:
            raise ValueError(f"Unsupported export format: {format}")

        logger.info(f"Exported metadata to {export_path} in {format} format")
        return export_path

    def restore_metadata(
        self,
        file_path: Union[str, Path],
        metadata_path: Union[str, Path],
        create_backup: bool = True
    ) -> Path:
        """
        Restore metadata from external file.

        Args:
            file_path: Path to target image file
            metadata_path: Path to metadata file (JSON)
            create_backup: Whether to create backup

        Returns:
            Path to modified image file
        """
        metadata_path = Path(metadata_path)

        # Load and parse metadata from file
        if metadata_path.suffix.lower() == '.json':
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata_dict = json.load(f)
            restored_metadata = ImageMetadata.from_dict(metadata_dict)
        else:
            raise ValueError(f"Unsupported metadata format: {metadata_path.suffix}")

        # Update file path to target file
        restored_metadata.file_path = Path(file_path)

        # Write metadata
        return self.write_metadata(restored_metadata, create_backup=create_backup)

    def get_supported_formats(self) -> List[str]:
        """Get list of supported image formats."""
        return list(set(self.adapters.keys()))

    def has_metadata(self, file_path: Union[str, Path]) -> bool:
        """
        Check if image file has metadata.

        Args:
            file_path: Path to image file

        Returns:
            True if file has metadata
        """
        try:
            metadata = self.read_metadata(file_path)
            return metadata.has_metadata()
        except Exception:
            return False

    def has_gps_data(self, file_path: Union[str, Path]) -> bool:
        """
        Check if image file has GPS/location data.

        Args:
            file_path: Path to image file

        Returns:
            True if file has GPS data
        """
        try:
            metadata = self.read_metadata(file_path)
            return metadata.has_gps_data()
        except Exception:
            return False

    def batch_process(
        self,
        input_paths: List[Union[str, Path]],
        operation: str,
        output_dir: Optional[Path] = None,
        **kwargs
    ) -> Dict[str, Union[Path, Exception]]:
        """
        Process multiple files in batch.

        Args:
            input_paths: List of input file paths
            operation: Operation to perform ('strip', 'strip_gps', 'export')
            output_dir: Optional output directory for batch operations
            **kwargs: Additional arguments for the operation

        Returns:
            Dictionary mapping input paths to results (Path or Exception)
        """
        results = {}

        for input_path in input_paths:
            input_path = Path(input_path)

            try:
                if operation == "strip":
                    output_path = output_dir / input_path.name if output_dir else None
                    result = self.strip_metadata(input_path, output_path, **kwargs)
                elif operation == "strip_gps":
                    output_path = output_dir / input_path.name if output_dir else None
                    result = self.strip_gps_data(input_path, output_path, **kwargs)
                elif operation == "export":
                    export_name = f"{input_path.stem}_metadata.json"
                    export_path = output_dir / export_name if output_dir else input_path.parent / export_name
                    result = self.export_metadata(input_path, export_path, **kwargs)
                else:
                    raise ValueError(f"Unknown batch operation: {operation}")

                results[str(input_path)] = result

            except Exception as e:
                logger.error(f"Batch operation failed for {input_path}: {e}")
                results[str(input_path)] = e

        return results

    def __str__(self) -> str:
        """String representation."""
        return f"MetadataEngine(adapters={len(self.adapters)})"

    def __repr__(self) -> str:
        """Detailed representation."""
        formats = ", ".join(self.get_supported_formats())
        return f"MetadataEngine(supported_formats=[{formats}])"