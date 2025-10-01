"""
TIFF metadata adapter for handling EXIF, IPTC, and XMP data in TIFF images.
"""
from pathlib import Path
from typing import Optional, List

from PIL import Image
from PIL.TiffImagePlugin import ImageFileDirectory_v2

from ..core.base_adapter import BaseMetadataAdapter
from ..core.metadata import ImageMetadata, MetadataBlock
from ..core.exceptions import MetadataError, UnsupportedFormatError
from ..core.file_safety import FileSafetyManager
from ..core.logger import logger


class TIFFAdapter(BaseMetadataAdapter):
    """Adapter for TIFF image metadata operations."""

    def __init__(self, safety_manager: Optional[FileSafetyManager] = None):
        """
        Initialize TIFF adapter.

        Args:
            safety_manager: Optional FileSafetyManager for file operations.
                           If None, creates a new instance.
        """
        super().__init__(safety_manager)
        if self.safety_manager is None:
            self.safety_manager = FileSafetyManager()

    @property
    def supported_formats(self) -> List[str]:
        """TIFF format variants."""
        return ["tiff", "tif"]

    @property
    def format_name(self) -> str:
        """Human-readable format name."""
        return "TIFF"

    def read_metadata(self, file_path: Path) -> ImageMetadata:
        """
        Read metadata from TIFF file.

        Args:
            file_path: Path to TIFF file

        Returns:
            ImageMetadata object with extracted metadata

        Raises:
            UnsupportedFormatError: If file is not TIFF format
            MetadataError: If metadata reading fails
        """
        if not self.supports_format(file_path):
            raise UnsupportedFormatError(f"File {file_path} is not a TIFF image")

        metadata = ImageMetadata(file_path=file_path, format=self.format_name)

        try:
            with Image.open(file_path) as img:
                # Extract EXIF data if present
                if hasattr(img, '_getexif') and img._getexif():
                    from PIL.ExifTags import TAGS
                    exif_data = img._getexif()

                    for tag_id, value in exif_data.items():
                        tag_name = TAGS.get(tag_id, f"Tag{tag_id}")
                        metadata.exif.set(tag_name, str(value))

                # Extract TIFF tags from tag_v2
                if hasattr(img, 'tag_v2'):
                    for tag_id, value in img.tag_v2.items():
                        tag_name = self._get_tiff_tag_name(tag_id)
                        # Skip if already in EXIF
                        if tag_name not in metadata.exif.keys():
                            metadata.custom.set(f"TIFF:{tag_name}", str(value))

                # Extract XMP data if present
                if hasattr(img, 'info') and 'xmp' in img.info:
                    xmp_data = img.info.get('xmp')
                    if xmp_data:
                        if isinstance(xmp_data, bytes):
                            metadata.xmp.set('raw_xmp', xmp_data.decode('utf-8', errors='ignore'))
                        else:
                            metadata.xmp.set('raw_xmp', str(xmp_data))

                # Extract other metadata from info dict
                if hasattr(img, 'info'):
                    for key, value in img.info.items():
                        if key not in ['xmp', 'exif']:
                            metadata.custom.set(f"TIFF:{key}", str(value))

            logger.info(f"TIFF READ SUCCESS: {file_path}")
            return metadata

        except Exception as e:
            logger.error(f"Error reading TIFF metadata from {file_path}: {e}")
            raise MetadataError(f"Failed to read TIFF metadata: {e}")

    def write_metadata(self, metadata: ImageMetadata, output_path: Path) -> Path:
        """
        Write metadata to TIFF file.

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
                save_params = {'format': 'TIFF'}

                # Preserve compression if present
                if hasattr(img, 'info') and 'compression' in img.info:
                    save_params['compression'] = img.info['compression']

                # Build EXIF data if present
                if not metadata.exif.is_empty():
                    exif_bytes = self._build_exif_from_block(metadata.exif)
                    if exif_bytes:
                        save_params['exif'] = exif_bytes

                # TIFF supports storing arbitrary tags
                # Create tag structure for custom metadata
                if not metadata.custom.is_empty():
                    # Note: This is simplified - full TIFF tag writing would need proper tag IDs
                    pass

                # Ensure parent directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Save with metadata
                img.save(output_path, **save_params)

            logger.info(f"TIFF WRITE SUCCESS: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error writing TIFF metadata to {output_path}: {e}")
            raise MetadataError(f"Failed to write TIFF metadata: {e}")

    def strip_metadata(self, file_path: Path, output_path: Path, gps_only: bool = False) -> Path:
        """
        Strip metadata from TIFF file.

        Args:
            file_path: Path to source TIFF file
            output_path: Path where stripped file should be saved
            gps_only: If True, only strip GPS data (TIFF adapter strips all metadata regardless)

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
                new_img.save(output_path, format='TIFF')

                # Verify pixel integrity
                self.safety_manager.verify_file_integrity(file_path, output_path)

            logger.info(f"TIFF STRIP SUCCESS: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error stripping TIFF metadata from {file_path}: {e}")
            raise MetadataError(f"Failed to strip TIFF metadata: {e}")

    def _get_tiff_tag_name(self, tag_id: int) -> str:
        """
        Get TIFF tag name from tag ID.

        Args:
            tag_id: TIFF tag identifier

        Returns:
            Tag name string
        """
        from PIL.TiffTags import TAGS_V2

        if tag_id in TAGS_V2:
            return TAGS_V2[tag_id].name
        return f"Tag{tag_id}"

    def _build_exif_from_block(self, exif_block: MetadataBlock) -> Optional[bytes]:
        """
        Build EXIF bytes from MetadataBlock.

        Args:
            exif_block: MetadataBlock containing EXIF data

        Returns:
            EXIF bytes or None if building fails
        """
        # This is a simplified implementation
        # For full EXIF support, would need proper EXIF encoding
        try:
            from PIL import Image as PILImage
            from PIL.ExifTags import TAGS

            # Create a new EXIF structure
            img = PILImage.new('RGB', (1, 1))
            exif = img.getexif()

            # Reverse lookup TAGS to get tag IDs
            tag_lookup = {v: k for k, v in TAGS.items()}

            for key, value in exif_block.data.items():
                if key in tag_lookup:
                    tag_id = tag_lookup[key]
                    try:
                        exif[tag_id] = value
                    except:
                        pass  # Skip tags that can't be set

            return exif.tobytes()
        except:
            return None
