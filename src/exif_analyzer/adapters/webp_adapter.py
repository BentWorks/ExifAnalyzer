"""
WebP metadata adapter for handling EXIF and XMP data in WebP images.
"""
from pathlib import Path
from typing import Optional, List

from PIL import Image

from ..core.base_adapter import BaseMetadataAdapter
from ..core.metadata import ImageMetadata, MetadataBlock
from ..core.exceptions import MetadataError, UnsupportedFormatError
from ..core.file_safety import FileSafetyManager
from ..core.logger import logger


class WebPAdapter(BaseMetadataAdapter):
    """Adapter for WebP image metadata operations."""

    def __init__(self, safety_manager: Optional[FileSafetyManager] = None):
        """
        Initialize WebP adapter.

        Args:
            safety_manager: Optional FileSafetyManager for file operations.
                           If None, creates a new instance.
        """
        super().__init__(safety_manager)
        if self.safety_manager is None:
            self.safety_manager = FileSafetyManager()

    @property
    def supported_formats(self) -> List[str]:
        """WebP format variants."""
        return ["webp"]

    @property
    def format_name(self) -> str:
        """Human-readable format name."""
        return "WebP"

    def read_metadata(self, file_path: Path) -> ImageMetadata:
        """
        Read metadata from WebP file.

        Args:
            file_path: Path to WebP file

        Returns:
            ImageMetadata object with extracted metadata

        Raises:
            UnsupportedFormatError: If file is not WebP format
            MetadataError: If metadata reading fails
        """
        if not self.supports_format(file_path):
            raise UnsupportedFormatError(f"File {file_path} is not a WebP image")

        metadata = ImageMetadata(file_path=file_path, format=self.format_name)

        try:
            with Image.open(file_path) as img:
                # Extract EXIF data if present
                if hasattr(img, 'info') and 'exif' in img.info:
                    exif_data = img.info.get('exif')
                    if exif_data:
                        metadata.exif = self._parse_exif_bytes(exif_data)

                # Extract XMP data if present
                if hasattr(img, 'info') and 'xmp' in img.info:
                    xmp_data = img.info.get('xmp')
                    if xmp_data:
                        # Store XMP as bytes in custom block
                        if isinstance(xmp_data, bytes):
                            metadata.xmp.set('raw_xmp', xmp_data.decode('utf-8', errors='ignore'))
                        else:
                            metadata.xmp.set('raw_xmp', str(xmp_data))

                # Extract other metadata from info dict
                if hasattr(img, 'info'):
                    for key, value in img.info.items():
                        if key not in ['exif', 'xmp']:
                            metadata.custom.set(f"WebP:{key}", str(value))

            logger.info(f"WebP READ SUCCESS: {file_path}")
            return metadata

        except Exception as e:
            logger.error(f"Error reading WebP metadata from {file_path}: {e}")
            raise MetadataError(f"Failed to read WebP metadata: {e}")

    def write_metadata(self, metadata: ImageMetadata, output_path: Path) -> Path:
        """
        Write metadata to WebP file.

        Args:
            metadata: ImageMetadata object containing metadata to write
            output_path: Path where output file should be saved

        Returns:
            Path to output file

        Raises:
            MetadataError: If metadata writing fails
        """
        try:
            source_path = metadata.file_path
            with Image.open(source_path) as img:
                # Prepare save parameters
                save_params = {'format': 'WebP'}

                # WebP supports lossless mode
                if hasattr(img, 'info') and 'lossless' in img.info:
                    save_params['lossless'] = img.info['lossless']

                # Add EXIF data if present
                if not metadata.exif.is_empty():
                    exif_bytes = self._build_exif_bytes(metadata.exif)
                    if exif_bytes:
                        save_params['exif'] = exif_bytes

                # Add XMP data if present
                if not metadata.xmp.is_empty():
                    xmp_str = metadata.xmp.get('raw_xmp')
                    if xmp_str:
                        save_params['xmp'] = xmp_str.encode('utf-8') if isinstance(xmp_str, str) else xmp_str

                # Ensure parent directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Save with metadata
                img.save(output_path, **save_params)

            logger.info(f"WebP WRITE SUCCESS: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error writing WebP metadata to {output_path}: {e}")
            raise MetadataError(f"Failed to write WebP metadata: {e}")

    def strip_metadata(self, file_path: Path, output_path: Path, gps_only: bool = False) -> Path:
        """
        Strip metadata from WebP file.

        Args:
            file_path: Path to source WebP file
            output_path: Path where stripped file should be saved
            gps_only: If True, only strip GPS data (WebP adapter strips all metadata regardless)

        Returns:
            Path to output file

        Raises:
            MetadataError: If stripping fails
        """
        try:
            with Image.open(file_path) as img:
                # Get original pixel data
                original_pixels = img.tobytes()

                # Create new image without metadata
                new_img = Image.new(img.mode, img.size)
                new_img.frombytes(original_pixels)

                # Ensure parent directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Save without any metadata
                new_img.save(output_path, format='WebP')

                # Verify pixel integrity
                self.safety_manager.verify_file_integrity(file_path, output_path)

            logger.info(f"WebP STRIP SUCCESS: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error stripping WebP metadata from {file_path}: {e}")
            raise MetadataError(f"Failed to strip WebP metadata: {e}")

    def _parse_exif_bytes(self, exif_bytes: bytes) -> MetadataBlock:
        """
        Parse EXIF bytes into MetadataBlock.

        Args:
            exif_bytes: Raw EXIF data

        Returns:
            MetadataBlock with parsed EXIF data
        """
        from PIL.ExifTags import TAGS
        from PIL import Image as PILImage

        exif_block = MetadataBlock(name='exif')

        try:
            # PIL can parse EXIF data from bytes
            img = PILImage.open(Path(exif_bytes))
            if hasattr(img, '_getexif') and img._getexif():
                exif_data = img._getexif()
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, f"Tag{tag_id}")
                    exif_block.set(tag_name, str(value))
        except:
            # If parsing fails, store as raw bytes
            exif_block.set('raw_exif', exif_bytes.hex())

        return exif_block

    def _build_exif_bytes(self, exif_block: MetadataBlock) -> Optional[bytes]:
        """
        Build EXIF bytes from MetadataBlock.

        Args:
            exif_block: MetadataBlock containing EXIF data

        Returns:
            EXIF bytes or None if building fails
        """
        # This is a simplified implementation
        # For full EXIF support, would need proper EXIF encoding
        raw_exif = exif_block.get('raw_exif')
        if raw_exif:
            try:
                return bytes.fromhex(raw_exif)
            except:
                pass
        return None
