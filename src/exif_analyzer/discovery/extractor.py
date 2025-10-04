"""
Metadata extractor for deep inspection of image files.
"""
import struct
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

from ..core.metadata import ImageMetadata
from ..core.engine import MetadataEngine
from .models import RawChunk, ExtractedMetadata


class MetadataExtractor:
    """Extract ALL metadata from images, including non-standard chunks."""

    def __init__(self, metadata_engine: Optional[MetadataEngine] = None):
        """
        Initialize metadata extractor.

        Args:
            metadata_engine: Existing MetadataEngine instance (optional)
        """
        self.engine = metadata_engine or MetadataEngine()

    def extract_all(self, file_path: Path) -> ExtractedMetadata:
        """
        Extract all metadata from image file.

        Args:
            file_path: Path to image file

        Returns:
            ExtractedMetadata with complete findings
        """
        start_time = time.time()
        file_path = Path(file_path)

        # Get standard metadata using existing system
        standard_metadata = self.engine.read_metadata(file_path)

        # Get file info
        file_size = file_path.stat().st_size
        file_format = standard_metadata.format

        # Extract raw chunks based on format
        raw_chunks = []
        custom_fields = {}
        errors = []

        try:
            if file_format.upper() == "PNG":
                raw_chunks, custom_fields = self._extract_png_chunks(file_path)
            elif file_format.upper() in ["JPEG", "JPG"]:
                raw_chunks, custom_fields = self._extract_jpeg_segments(file_path)
            elif file_format.upper() == "WEBP":
                raw_chunks, custom_fields = self._extract_webp_chunks(file_path)
        except Exception as e:
            errors.append(f"Error extracting raw chunks: {e}")

        extraction_time = time.time() - start_time

        return ExtractedMetadata(
            file_path=file_path,
            file_format=file_format,
            file_size=file_size,
            standard_metadata=standard_metadata,
            raw_chunks=raw_chunks,
            custom_fields=custom_fields,
            extraction_errors=errors,
            extraction_time=extraction_time
        )

    def _extract_png_chunks(self, file_path: Path) -> tuple:
        """Extract all PNG chunks including custom text chunks."""
        chunks = []
        custom_fields = {}

        with open(file_path, 'rb') as f:
            # Skip PNG signature (8 bytes)
            f.read(8)

            offset = 8
            while True:
                # Read chunk length and type
                length_bytes = f.read(4)
                if len(length_bytes) < 4:
                    break

                length = struct.unpack('>I', length_bytes)[0]
                chunk_type = f.read(4).decode('ascii', errors='ignore')
                chunk_data = f.read(length)
                crc = f.read(4)  # CRC

                # Store raw chunk
                chunk = RawChunk(
                    chunk_type=f"PNG:{chunk_type}",
                    offset=offset,
                    length=length,
                    raw_data=chunk_data[:1000] if len(chunk_data) > 1000 else chunk_data
                )

                # Try to decode text chunks
                if chunk_type in ('tEXt', 'iTXt', 'zTXt'):
                    try:
                        if chunk_type == 'tEXt':
                            # Find null separator
                            null_pos = chunk_data.find(b'\x00')
                            if null_pos != -1:
                                keyword = chunk_data[:null_pos].decode('latin-1')
                                text = chunk_data[null_pos + 1:].decode('latin-1', errors='ignore')
                                chunk.decoded_text = f"{keyword}: {text}"
                                custom_fields[f"PNG:tEXt:{keyword}"] = text
                        elif chunk_type == 'iTXt':
                            # iTXt: keyword\0compression\0language\0translated_keyword\0text
                            null_pos = chunk_data.find(b'\x00')
                            if null_pos != -1:
                                keyword = chunk_data[:null_pos].decode('latin-1')
                                # Try to extract text (simplified)
                                try:
                                    text = chunk_data[null_pos:].decode('utf-8', errors='ignore')
                                    chunk.decoded_text = f"{keyword}: {text}"
                                    custom_fields[f"PNG:iTXt:{keyword}"] = text
                                except:
                                    pass
                    except Exception as e:
                        chunk.parse_error = str(e)

                chunks.append(chunk)
                offset += 12 + length  # 4(len) + 4(type) + data + 4(crc)

        return chunks, custom_fields

    def _extract_jpeg_segments(self, file_path: Path) -> tuple:
        """Extract all JPEG segments including APP markers and COM."""
        chunks = []
        custom_fields = {}

        with open(file_path, 'rb') as f:
            # Check JPEG signature
            if f.read(2) != b'\xff\xd8':
                return chunks, custom_fields

            offset = 2
            while True:
                marker_start = f.read(1)
                if not marker_start or marker_start != b'\xff':
                    break

                marker_type = f.read(1)
                if not marker_type:
                    break

                marker = marker_start + marker_type

                # EOI marker (end of image)
                if marker == b'\xff\xd9':
                    break

                # Read segment length
                if marker[1:2] in (b'\xd0', b'\xd1', b'\xd2', b'\xd3', b'\xd4', b'\xd5', b'\xd6', b'\xd7', b'\xd8'):
                    # RST markers have no length
                    continue

                length_bytes = f.read(2)
                if len(length_bytes) < 2:
                    break

                length = struct.unpack('>H', length_bytes)[0] - 2  # Subtract length bytes
                segment_data = f.read(length)

                # Determine segment type
                segment_type = f"JPEG:APP{marker[1] - 0xE0}" if 0xE0 <= marker[1] <= 0xEF else f"JPEG:{marker.hex()}"

                # Special handling for COM (comment) markers
                if marker == b'\xff\xfe':
                    segment_type = "JPEG:COM"
                    try:
                        comment = segment_data.decode('utf-8', errors='ignore')
                        custom_fields["JPEG:Comment"] = comment
                    except:
                        pass

                chunk = RawChunk(
                    chunk_type=segment_type,
                    offset=offset,
                    length=length,
                    raw_data=segment_data[:1000] if len(segment_data) > 1000 else segment_data
                )

                # Try to decode as text
                try:
                    decoded = segment_data.decode('utf-8', errors='ignore')
                    if decoded.isprintable() or '\n' in decoded:
                        chunk.decoded_text = decoded
                except:
                    pass

                chunks.append(chunk)
                offset += 4 + length  # marker + length + data

        return chunks, custom_fields

    def _extract_webp_chunks(self, file_path: Path) -> tuple:
        """Extract all WebP RIFF chunks."""
        chunks = []
        custom_fields = {}

        with open(file_path, 'rb') as f:
            # Read RIFF header
            riff = f.read(4)
            if riff != b'RIFF':
                return chunks, custom_fields

            file_size = struct.unpack('<I', f.read(4))[0]
            webp = f.read(4)
            if webp != b'WEBP':
                return chunks, custom_fields

            offset = 12
            while offset < file_size + 8:
                chunk_id = f.read(4)
                if len(chunk_id) < 4:
                    break

                chunk_size = struct.unpack('<I', f.read(4))[0]
                chunk_data = f.read(chunk_size)

                # Pad to even byte boundary
                if chunk_size % 2:
                    f.read(1)

                chunk_type = f"WebP:{chunk_id.decode('ascii', errors='ignore')}"
                chunk = RawChunk(
                    chunk_type=chunk_type,
                    offset=offset,
                    length=chunk_size,
                    raw_data=chunk_data[:1000] if len(chunk_data) > 1000 else chunk_data
                )

                chunks.append(chunk)
                offset += 8 + chunk_size + (chunk_size % 2)

        return chunks, custom_fields
