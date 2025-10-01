"""
JPEG metadata adapter for handling EXIF, IPTC, and XMP data.
"""
from pathlib import Path
from typing import Optional, List, Dict, Any
import io

from PIL import Image
from PIL.ExifTags import TAGS
import piexif

from ..core.base_adapter import BaseMetadataAdapter
from ..core.metadata import ImageMetadata, MetadataBlock
from ..core.exceptions import MetadataError, UnsupportedFormatError, PixelDataCorruptionError
from ..core.file_safety import FileSafetyManager
from ..core.logger import logger


class JPEGAdapter(BaseMetadataAdapter):
    """Adapter for JPEG image metadata operations."""

    def __init__(self, safety_manager: Optional[FileSafetyManager] = None):
        """
        Initialize JPEG adapter.

        Args:
            safety_manager: Optional FileSafetyManager for file operations.
                           If None, creates a new instance.
        """
        super().__init__(safety_manager)
        if self.safety_manager is None:
            self.safety_manager = FileSafetyManager()

    @property
    def supported_formats(self) -> List[str]:
        """JPEG format variants."""
        return ["jpg", "jpeg", "jpe", "jfif"]

    @property
    def format_name(self) -> str:
        """Human-readable format name."""
        return "JPEG"

    def read_metadata(self, file_path: Path) -> ImageMetadata:
        """
        Read metadata from JPEG file.

        Args:
            file_path: Path to JPEG file

        Returns:
            ImageMetadata with extracted EXIF, IPTC, and XMP data
        """
        self.validate_file(file_path)

        # Verify it's actually a JPEG file by trying to open it
        try:
            with Image.open(file_path) as img:
                if img.format not in ['JPEG', 'JPG']:
                    raise MetadataError(f"File is not a valid JPEG: {file_path}")
        except Exception as e:
            raise MetadataError(f"Cannot read JPEG file {file_path}: {e}")

        try:
            metadata = ImageMetadata(
                file_path=file_path,
                format="JPEG",
                file_size=file_path.stat().st_size,
                pixel_hash=self.get_pixel_hash(file_path)
            )

            # Read EXIF data
            self._read_exif_data(file_path, metadata)

            # Read IPTC data (if available)
            self._read_iptc_data(file_path, metadata)

            # Read XMP data (if available)
            self._read_xmp_data(file_path, metadata)

            self.log_operation("READ", file_path)
            return metadata

        except Exception as e:
            self.log_operation("READ", file_path, success=False)
            raise MetadataError(f"Failed to read JPEG metadata: {e}")

    def _read_exif_data(self, file_path: Path, metadata: ImageMetadata) -> None:
        """Read EXIF data from JPEG file."""
        try:
            # Try piexif first for comprehensive EXIF support
            exif_dict = piexif.load(str(file_path))

            # Process each IFD (Image File Directory)
            for ifd_name in ["0th", "Exif", "GPS", "1st"]:
                if ifd_name in exif_dict:
                    ifd_data = exif_dict[ifd_name]
                    for tag_id, value in ifd_data.items():
                        try:
                            # Get human-readable tag name
                            if ifd_name == "GPS":
                                tag_name = piexif.GPSIFD.get(tag_id, f"GPS_Tag_{tag_id}")
                            elif ifd_name == "Exif":
                                tag_name = piexif.ExifIFD.get(tag_id, f"EXIF_Tag_{tag_id}")
                            else:
                                tag_name = piexif.ImageIFD.get(tag_id, f"IFD_Tag_{tag_id}")

                            # Convert value to appropriate format
                            if isinstance(value, bytes):
                                try:
                                    value = value.decode('utf-8', errors='ignore').strip('\x00')
                                except (UnicodeDecodeError, AttributeError):
                                    value = value.hex()

                            # Store with IFD prefix for clarity
                            key = f"{ifd_name}:{tag_name}" if ifd_name != "0th" else tag_name
                            metadata.exif.set(key, value)

                        except Exception as e:
                            logger.debug(f"Failed to process EXIF tag {tag_id}: {e}")

            # Also try PIL's EXIF reading as fallback/supplement
            with Image.open(file_path) as img:
                if hasattr(img, '_getexif') and img._getexif():
                    pil_exif = img._getexif()
                    for tag_id, value in pil_exif.items():
                        tag_name = TAGS.get(tag_id, f"Tag_{tag_id}")
                        if not metadata.exif.get(tag_name):  # Don't overwrite piexif data
                            metadata.exif.set(f"PIL:{tag_name}", value)

        except Exception as e:
            logger.debug(f"Could not read EXIF data: {e}")

    def _read_iptc_data(self, file_path: Path, metadata: ImageMetadata) -> None:
        """Read IPTC data from JPEG file."""
        try:
            # IPTC reading requires specialized library or manual parsing
            # For now, we'll implement basic IPTC detection
            with open(file_path, 'rb') as f:
                data = f.read()

            # Look for IPTC marker (Photoshop 3.0 8BIM)
            iptc_marker = b'Photoshop 3.0\x008BIM'
            if iptc_marker in data:
                logger.debug(f"IPTC data detected in {file_path}")
                metadata.iptc.set("IPTC_Present", True)
                # TODO: Implement full IPTC parsing if needed

        except Exception as e:
            logger.debug(f"Could not read IPTC data: {e}")

    def _read_xmp_data(self, file_path: Path, metadata: ImageMetadata) -> None:
        """Read XMP data from JPEG file."""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()

            # Look for XMP packet
            xmp_start = b'http://ns.adobe.com/xap/1.0/\x00'
            xmp_begin = b'<?xpacket begin='

            start_pos = data.find(xmp_start)
            if start_pos != -1:
                # Find the actual XMP data
                xmp_data_start = data.find(xmp_begin, start_pos)
                if xmp_data_start != -1:
                    xmp_end = data.find(b'<?xpacket end=', xmp_data_start)
                    if xmp_end != -1:
                        xmp_content = data[xmp_data_start:xmp_end].decode('utf-8', errors='ignore')
                        metadata.xmp.set("XMP_Raw", xmp_content)
                        metadata.xmp.set("XMP_Present", True)
                        logger.debug(f"XMP data found in {file_path}")

        except Exception as e:
            logger.debug(f"Could not read XMP data: {e}")

    def write_metadata(self, metadata: ImageMetadata, output_path: Optional[Path] = None) -> Path:
        """
        Write metadata to JPEG file.

        Args:
            metadata: ImageMetadata to write
            output_path: Optional output path

        Returns:
            Path to output file
        """
        if output_path is None:
            output_path = metadata.file_path

        try:
            with self.safety_manager.safe_file_operation(output_path) as temp_path:
                # Load original image
                with Image.open(metadata.file_path) as img:
                    # Prepare EXIF data
                    exif_dict = self._prepare_exif_data(metadata.exif)

                    # Convert to bytes
                    if exif_dict:
                        exif_bytes = piexif.dump(exif_dict)
                    else:
                        exif_bytes = None

                    # Save with new metadata
                    save_kwargs = {"format": "JPEG", "quality": "keep"}
                    if exif_bytes:
                        save_kwargs["exif"] = exif_bytes

                    img.save(temp_path, **save_kwargs)

                # Verify JPEG integrity (more lenient for JPEG compression)
                if not self.verify_jpeg_integrity(metadata.file_path, temp_path):
                    raise PixelDataCorruptionError("JPEG integrity check failed - image may be corrupted")

            self.log_operation("WRITE", output_path)
            return output_path

        except Exception as e:
            self.log_operation("WRITE", output_path, success=False)
            raise MetadataError(f"Failed to write JPEG metadata: {e}")

    def _prepare_exif_data(self, exif_block: MetadataBlock) -> Dict[str, Any]:
        """Prepare EXIF data for writing with piexif."""
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}

        for key, value in exif_block.data.items():
            try:
                # Parse key to determine IFD and tag
                if ":" in key:
                    ifd_name, tag_name = key.split(":", 1)
                else:
                    ifd_name = "0th"
                    tag_name = key

                # Skip PIL-specific keys
                if tag_name.startswith("PIL:"):
                    continue

                # Find tag ID
                tag_id = self._get_tag_id(ifd_name, tag_name)
                if tag_id is None:
                    continue

                # Convert value to appropriate format
                if isinstance(value, str) and len(value) > 0:
                    value = value.encode('utf-8')

                if ifd_name in exif_dict:
                    exif_dict[ifd_name][tag_id] = value

            except Exception as e:
                logger.debug(f"Failed to prepare EXIF tag {key}: {e}")

        # Remove empty IFDs
        return {k: v for k, v in exif_dict.items() if v}

    def _get_tag_id(self, ifd_name: str, tag_name: str) -> Optional[int]:
        """Get tag ID for given IFD and tag name."""
        try:
            if ifd_name == "GPS":
                return getattr(piexif.GPSIFD, tag_name, None)
            elif ifd_name == "Exif":
                return getattr(piexif.ExifIFD, tag_name, None)
            else:
                return getattr(piexif.ImageIFD, tag_name, None)
        except AttributeError:
            return None

    def strip_metadata(self, file_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        Remove all metadata from JPEG file.

        Args:
            file_path: Input JPEG file
            output_path: Optional output path

        Returns:
            Path to output file
        """
        self.validate_file(file_path)

        if output_path is None:
            output_path = file_path

        try:
            with self.safety_manager.safe_file_operation(output_path) as temp_path:
                # Load and save without metadata
                with Image.open(file_path) as img:
                    # Remove all metadata by not passing exif, icc_profile, etc.
                    img.save(temp_path, format="JPEG", quality="keep")

                # Verify JPEG integrity (more lenient for JPEG compression)
                if not self.verify_jpeg_integrity(file_path, temp_path):
                    raise PixelDataCorruptionError("JPEG integrity check failed - image may be corrupted")

            self.log_operation("STRIP", output_path)
            return output_path

        except Exception as e:
            self.log_operation("STRIP", output_path, success=False)
            raise MetadataError(f"Failed to strip JPEG metadata: {e}")

    def verify_jpeg_integrity(self, original_path: Path, modified_path: Path) -> bool:
        """
        Verify JPEG integrity using methods appropriate for lossy compression.

        This is more lenient than pixel-perfect comparison since JPEG
        recompression can cause minor pixel variations even with same quality.

        Args:
            original_path: Path to original JPEG
            modified_path: Path to modified JPEG

        Returns:
            True if images are substantially similar
        """
        try:
            from PIL import Image
            import numpy as np

            # Basic validation - files should open successfully
            with Image.open(original_path) as orig, Image.open(modified_path) as mod:
                # Check dimensions and mode using base method
                if not self._check_image_dimensions_and_mode(orig, mod):
                    return False

                # For JPEG integrity, we'll use a similarity check rather than exact match
                # Convert to numpy arrays for comparison
                orig_array = np.array(orig.convert('RGB'))
                mod_array = np.array(mod.convert('RGB'))

                # Calculate Mean Squared Error (MSE)
                mse = np.mean((orig_array - mod_array) ** 2)

                # JPEG recompression should have very low MSE (< 1.0 for same quality)
                # If MSE is higher, there might be actual corruption
                max_acceptable_mse = 2.0  # Conservative threshold

                if mse > max_acceptable_mse:
                    logger.error(f"High MSE detected: {mse:.2f} (threshold: {max_acceptable_mse})")
                    return False

                logger.debug(f"JPEG integrity check passed: MSE = {mse:.4f}")
                return True

        except ImportError:
            # Fall back to basic file validation if numpy isn't available
            logger.warning("NumPy not available, using basic integrity check")
            return self.verify_basic_jpeg_integrity(original_path, modified_path)
        except Exception as e:
            logger.error(f"JPEG integrity check failed: {e}")
            return False

    def verify_basic_jpeg_integrity(self, original_path: Path, modified_path: Path) -> bool:
        """
        Basic JPEG integrity check without numpy dependency.

        Args:
            original_path: Path to original JPEG
            modified_path: Path to modified JPEG

        Returns:
            True if basic checks pass
        """
        try:
            from PIL import Image

            # Basic validation - files should open successfully
            with Image.open(original_path) as orig, Image.open(modified_path) as mod:
                # Check dimensions and mode using base method
                if not self._check_image_dimensions_and_mode(orig, mod):
                    return False

                # If we can open both files and dimensions match, assume integrity is OK
                # This is less strict but more appropriate for JPEG recompression
                logger.debug("Basic JPEG integrity check passed")
                return True

        except Exception as e:
            logger.error(f"Basic JPEG integrity check failed: {e}")
            return False