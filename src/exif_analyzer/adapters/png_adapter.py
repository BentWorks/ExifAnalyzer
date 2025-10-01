"""
PNG metadata adapter for handling tEXt, iTXt, zTXt chunks and XMP data.
"""
from pathlib import Path
from typing import Optional, List, Dict, Any
import struct
import zlib

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from ..core.base_adapter import BaseMetadataAdapter
from ..core.metadata import ImageMetadata, MetadataBlock
from ..core.exceptions import MetadataError, UnsupportedFormatError, PixelDataCorruptionError
from ..core.file_safety import FileSafetyManager
from ..core.logger import logger


class PNGAdapter(BaseMetadataAdapter):
    """Adapter for PNG image metadata operations."""

    def __init__(self, safety_manager: Optional[FileSafetyManager] = None):
        """
        Initialize PNG adapter.

        Args:
            safety_manager: Optional FileSafetyManager for file operations.
                           If None, creates a new instance.
        """
        super().__init__(safety_manager)
        if self.safety_manager is None:
            self.safety_manager = FileSafetyManager()

    @property
    def supported_formats(self) -> List[str]:
        """PNG format variants."""
        return ["png"]

    @property
    def format_name(self) -> str:
        """Human-readable format name."""
        return "PNG"

    def read_metadata(self, file_path: Path) -> ImageMetadata:
        """
        Read metadata from PNG file.

        Args:
            file_path: Path to PNG file

        Returns:
            ImageMetadata with extracted text chunks and XMP data
        """
        self.validate_file(file_path)

        try:
            metadata = ImageMetadata(
                file_path=file_path,
                format="PNG",
                file_size=file_path.stat().st_size,
                pixel_hash=self.get_pixel_hash(file_path)
            )

            # Read PNG chunks
            self._read_png_chunks(file_path, metadata)

            # Read PIL-accessible metadata
            self._read_pil_metadata(file_path, metadata)

            self.log_operation("READ", file_path)
            return metadata

        except Exception as e:
            self.log_operation("READ", file_path, success=False)
            raise MetadataError(f"Failed to read PNG metadata: {e}")

    def _read_png_chunks(self, file_path: Path, metadata: ImageMetadata) -> None:
        """Read PNG chunks directly from file."""
        try:
            with open(file_path, 'rb') as f:
                # Verify PNG signature
                signature = f.read(8)
                if signature != b'\\x89PNG\\r\\n\\x1a\\n':
                    raise MetadataError("Invalid PNG signature")

                while True:
                    # Read chunk header
                    chunk_header = f.read(8)
                    if len(chunk_header) < 8:
                        break

                    length = struct.unpack('>I', chunk_header[:4])[0]
                    chunk_type = chunk_header[4:8].decode('ascii', errors='ignore')

                    # Read chunk data
                    chunk_data = f.read(length)
                    crc = f.read(4)  # CRC (not used for metadata)

                    # Process metadata chunks
                    if chunk_type == 'tEXt':
                        self._process_text_chunk(chunk_data, metadata, 'tEXt')
                    elif chunk_type == 'iTXt':
                        self._process_itext_chunk(chunk_data, metadata)
                    elif chunk_type == 'zTXt':
                        self._process_ztext_chunk(chunk_data, metadata)
                    elif chunk_type == 'IEND':
                        break

        except Exception as e:
            logger.debug(f"Error reading PNG chunks: {e}")

    def _process_text_chunk(self, data: bytes, metadata: ImageMetadata, chunk_type: str) -> None:
        """Process tEXt chunk."""
        try:
            # Find null separator
            null_pos = data.find(b'\\x00')
            if null_pos == -1:
                return

            keyword = data[:null_pos].decode('latin1')
            text = data[null_pos + 1:].decode('latin1', errors='ignore')

            metadata.custom.set(f"{chunk_type}:{keyword}", text)
            logger.debug(f"Found {chunk_type} chunk: {keyword}")

        except Exception as e:
            logger.debug(f"Error processing {chunk_type} chunk: {e}")

    def _process_itext_chunk(self, data: bytes, metadata: ImageMetadata) -> None:
        """Process iTXt chunk (international text)."""
        try:
            # iTXt format: keyword\\0compression_flag\\0compression_method\\0language_tag\\0translated_keyword\\0text
            parts = data.split(b'\\x00', 4)
            if len(parts) < 5:
                return

            keyword = parts[0].decode('latin1')
            compression_flag = parts[1]
            compression_method = parts[2]
            language_tag = parts[3].decode('utf-8', errors='ignore')
            remaining = parts[4]

            # Find translated keyword separator
            translated_sep = remaining.find(b'\\x00')
            if translated_sep != -1:
                translated_keyword = remaining[:translated_sep].decode('utf-8', errors='ignore')
                text_data = remaining[translated_sep + 1:]
            else:
                translated_keyword = ""
                text_data = remaining

            # Decompress if needed
            if compression_flag == b'\\x01':
                try:
                    text_data = zlib.decompress(text_data)
                except zlib.error as e:
                    logger.debug(f"Failed to decompress iTXt chunk: {keyword}: {e}")

            text = text_data.decode('utf-8', errors='ignore')

            # Store with full context
            key = f"iTXt:{keyword}"
            if language_tag:
                key += f"[{language_tag}]"

            metadata.custom.set(key, text)

            # Check for XMP data
            if keyword.lower() in ['xml:com.adobe.xmp', 'xmp']:
                metadata.xmp.set("XMP_Raw", text)
                metadata.xmp.set("XMP_Present", True)

        except Exception as e:
            logger.debug(f"Error processing iTXt chunk: {e}")

    def _process_ztext_chunk(self, data: bytes, metadata: ImageMetadata) -> None:
        """Process zTXt chunk (compressed text)."""
        try:
            # zTXt format: keyword\\0compression_method\\0compressed_text
            null_pos = data.find(b'\\x00')
            if null_pos == -1:
                return

            keyword = data[:null_pos].decode('latin1')

            # Skip compression method byte
            if len(data) <= null_pos + 2:
                return

            compressed_text = data[null_pos + 2:]

            # Decompress
            text = zlib.decompress(compressed_text).decode('latin1', errors='ignore')

            metadata.custom.set(f"zTXt:{keyword}", text)

        except Exception as e:
            logger.debug(f"Error processing zTXt chunk: {e}")

    def _read_pil_metadata(self, file_path: Path, metadata: ImageMetadata) -> None:
        """Read metadata accessible through PIL."""
        try:
            with Image.open(file_path) as img:
                # PIL can access some PNG metadata through info dict
                if hasattr(img, 'text') and img.text:
                    for key, value in img.text.items():
                        if not metadata.custom.get(f"tEXt:{key}"):  # Don't overwrite chunk data
                            metadata.custom.set(f"PIL:{key}", value)

        except Exception as e:
            logger.debug(f"Error reading PIL PNG metadata: {e}")

    def write_metadata(self, metadata: ImageMetadata, output_path: Optional[Path] = None) -> Path:
        """
        Write metadata to PNG file.

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
                    # Prepare PNG info for text chunks
                    png_info = PngInfo()

                    # Add custom metadata as text chunks
                    for key, value in metadata.custom.data.items():
                        # Extract actual keyword (remove prefix if present)
                        if key.startswith(('tEXt:', 'PIL:')):
                            actual_key = key.split(':', 1)[1] if ':' in key else key
                        else:
                            # Key without prefix - use as is
                            actual_key = key

                        # Clean key name (PNG keywords have restrictions)
                        actual_key = self._clean_png_keyword(actual_key)
                        png_info.add_text(actual_key, str(value))

                    # Add XMP data if present
                    if metadata.xmp.get("XMP_Raw"):
                        png_info.add_text("XML:com.adobe.xmp", metadata.xmp.get("XMP_Raw"))

                    # Save with metadata
                    img.save(temp_path, format="PNG", pnginfo=png_info)

                # Verify pixel integrity
                if not self.verify_pixel_integrity(metadata.file_path, temp_path):
                    raise PixelDataCorruptionError("Pixel data corrupted during metadata write")

            self.log_operation("WRITE", output_path)
            return output_path

        except Exception as e:
            self.log_operation("WRITE", output_path, success=False)
            raise MetadataError(f"Failed to write PNG metadata: {e}")

    def _clean_png_keyword(self, keyword: str) -> str:
        """Clean PNG keyword to meet format requirements."""
        # PNG keywords must be 1-79 characters, printable Latin-1
        # Remove invalid characters and truncate if needed
        cleaned = ''.join(c for c in keyword if ord(c) >= 32 and ord(c) <= 126)
        return cleaned[:79] if len(cleaned) > 79 else cleaned

    def strip_metadata(self, file_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        Remove all metadata from PNG file.

        Args:
            file_path: Input PNG file
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
                    # Save without pnginfo to remove text chunks
                    img.save(temp_path, format="PNG")

                # Verify pixel integrity
                if not self.verify_pixel_integrity(file_path, temp_path):
                    raise PixelDataCorruptionError("Pixel data corrupted during metadata stripping")

            self.log_operation("STRIP", output_path)
            return output_path

        except Exception as e:
            self.log_operation("STRIP", output_path, success=False)
            raise MetadataError(f"Failed to strip PNG metadata: {e}")