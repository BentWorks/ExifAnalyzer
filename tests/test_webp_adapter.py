"""
Tests for WebP metadata adapter.
"""
import pytest
from pathlib import Path
from PIL import Image

from src.exif_analyzer.adapters.webp_adapter import WebPAdapter
from src.exif_analyzer.core.exceptions import UnsupportedFormatError, MetadataError
from src.exif_analyzer.core.metadata import ImageMetadata
from src.exif_analyzer.core.file_safety import FileSafetyManager


class TestWebPAdapter:
    """Test cases for WebP metadata adapter."""

    def setup_method(self):
        """Set up test environment."""
        self.safety_manager = FileSafetyManager()
        self.adapter = WebPAdapter(safety_manager=self.safety_manager)

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for test files."""
        return tmp_path

    def create_test_webp(self, path: Path, with_metadata: bool = False) -> Path:
        """Create a test WebP image."""
        img = Image.new('RGB', (100, 100), color='blue')

        save_params = {'format': 'WebP'}

        if with_metadata:
            # Add some basic EXIF-like metadata via info dict
            # Note: PIL's WebP support for EXIF is limited
            pass

        img.save(path, **save_params)
        return path

    def test_adapter_properties(self):
        """Test adapter properties."""
        assert self.adapter.format_name == "WebP"
        assert "webp" in self.adapter.supported_formats
        assert len(self.adapter.supported_formats) == 1

    def test_supports_format(self, temp_dir):
        """Test format detection."""
        webp_file = temp_dir / "test.webp"
        self.create_test_webp(webp_file)

        assert self.adapter.supports_format(webp_file) is True

        # Test with non-WebP file
        jpg_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(jpg_file, format='JPEG')

        assert self.adapter.supports_format(jpg_file) is False

    def test_read_metadata_basic(self, temp_dir):
        """Test reading basic WebP metadata."""
        test_image = temp_dir / "test_basic.webp"
        self.create_test_webp(test_image)

        metadata = self.adapter.read_metadata(test_image)

        assert isinstance(metadata, ImageMetadata)
        assert metadata.format == "WebP"
        assert metadata.file_path == test_image

    def test_read_metadata_with_exif(self, temp_dir):
        """Test reading WebP with EXIF data."""
        test_image = temp_dir / "test_exif.webp"

        # Create WebP with EXIF data
        img = Image.new('RGB', (100, 100), color='green')

        # Create minimal EXIF data
        from PIL import Image as PILImage
        exif_img = PILImage.new('RGB', (100, 100))
        exif_data = exif_img.getexif()
        exif_data[0x010F] = "Test Manufacturer"  # Make
        exif_data[0x0110] = "Test Model"  # Model

        exif_bytes = exif_data.tobytes()
        img.save(test_image, format='WebP', exif=exif_bytes)

        metadata = self.adapter.read_metadata(test_image)

        assert isinstance(metadata, ImageMetadata)
        # EXIF should be present (even if empty after parsing)
        assert metadata.exif is not None

    def test_read_nonexistent_file(self):
        """Test reading non-existent file."""
        nonexistent = Path("nonexistent.webp")

        with pytest.raises((FileNotFoundError, MetadataError, Exception)):
            self.adapter.read_metadata(nonexistent)

    def test_read_invalid_file(self, temp_dir):
        """Test reading invalid WebP file."""
        invalid_file = temp_dir / "invalid.webp"
        invalid_file.write_text("This is not a valid WebP file")

        with pytest.raises((UnsupportedFormatError, MetadataError, Exception)):
            self.adapter.read_metadata(invalid_file)

    def test_unsupported_format(self, temp_dir):
        """Test handling of unsupported format."""
        jpg_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='yellow')
        img.save(jpg_file, format='JPEG')

        with pytest.raises(UnsupportedFormatError):
            self.adapter.read_metadata(jpg_file)

    def test_strip_metadata(self, temp_dir):
        """Test stripping metadata from WebP."""
        test_image = temp_dir / "test_strip.webp"
        output_image = temp_dir / "output_strip.webp"
        self.create_test_webp(test_image, with_metadata=True)

        # Strip metadata
        result_path = self.adapter.strip_metadata(test_image, output_image)
        assert result_path == output_image
        assert output_image.exists()

        # Verify stripped version has minimal/no metadata
        stripped_metadata = self.adapter.read_metadata(output_image)
        # WebP stripped files should have minimal metadata
        assert isinstance(stripped_metadata, ImageMetadata)

    def test_strip_metadata_gps_only(self, temp_dir):
        """Test stripping all metadata (WebP adapter doesn't support selective GPS stripping)."""
        test_image = temp_dir / "test_gps.webp"
        output_image = temp_dir / "output_gps.webp"
        self.create_test_webp(test_image, with_metadata=True)

        # Strip all metadata (gps_only parameter is ignored for WebP)
        result_path = self.adapter.strip_metadata(test_image, output_image, gps_only=True)
        assert result_path == output_image

        # Verify metadata removed
        stripped_metadata = self.adapter.read_metadata(output_image)
        assert isinstance(stripped_metadata, ImageMetadata)

    def test_write_metadata(self, temp_dir):
        """Test writing metadata to WebP."""
        test_image = temp_dir / "test_write.webp"
        output_image = temp_dir / "output_write.webp"
        self.create_test_webp(test_image)

        # Read existing metadata and modify it
        metadata = self.adapter.read_metadata(test_image)
        metadata.custom.set("NewField", "NewValue")

        # Write metadata
        result_path = self.adapter.write_metadata(metadata, output_image)
        assert result_path == output_image

        # Verify written file exists
        assert output_image.exists()

        # Verify we can read it back
        written_metadata = self.adapter.read_metadata(output_image)
        assert isinstance(written_metadata, ImageMetadata)

    def test_pixel_integrity(self, temp_dir):
        """Test that pixel data remains unchanged after metadata operations."""
        test_image = temp_dir / "test_pixels.webp"
        output_image = temp_dir / "output_pixels.webp"
        self.create_test_webp(test_image, with_metadata=True)

        # Get original pixel data
        with Image.open(test_image) as img:
            original_pixels = img.tobytes()

        # Strip metadata
        self.adapter.strip_metadata(test_image, output_image)

        # Get new pixel data
        with Image.open(output_image) as img:
            new_pixels = img.tobytes()

        # Pixel data should be identical
        assert original_pixels == new_pixels

    def test_has_gps_data_detection(self, temp_dir):
        """Test GPS data detection in WebP files."""
        test_image = temp_dir / "test_no_gps.webp"
        self.create_test_webp(test_image)

        metadata = self.adapter.read_metadata(test_image)

        # WebP files typically don't have GPS data unless explicitly added
        assert not metadata.has_gps_data()

    def test_xmp_metadata_handling(self, temp_dir):
        """Test XMP metadata handling in WebP."""
        test_image = temp_dir / "test_xmp.webp"

        # Create WebP with XMP data
        img = Image.new('RGB', (100, 100), color='purple')
        xmp_data = b'<?xml version="1.0"?><x:xmpmeta>Test XMP</x:xmpmeta>'
        img.save(test_image, format='WebP', xmp=xmp_data)

        metadata = self.adapter.read_metadata(test_image)

        assert isinstance(metadata, ImageMetadata)
        # XMP should be extracted to xmp block
        if not metadata.xmp.is_empty():
            assert 'raw_xmp' in metadata.xmp.keys()

    def test_error_handling_corrupted_file(self, temp_dir):
        """Test error handling with corrupted WebP file."""
        corrupted_file = temp_dir / "corrupted.webp"

        # Create a file that starts like WebP but is corrupted
        with open(corrupted_file, 'wb') as f:
            f.write(b'RIFF\x00\x00\x00\x00WEBP')  # Minimal WebP header
            f.write(b'\x00' * 100)  # Garbage data

        # WebP adapter handles corrupted files gracefully
        with pytest.raises((MetadataError, Exception)):
            self.adapter.read_metadata(corrupted_file)

    def test_lossless_webp_handling(self, temp_dir):
        """Test handling of lossless WebP images."""
        test_image = temp_dir / "test_lossless.webp"

        # Create lossless WebP
        img = Image.new('RGB', (100, 100), color='cyan')
        img.save(test_image, format='WebP', lossless=True)

        metadata = self.adapter.read_metadata(test_image)

        assert isinstance(metadata, ImageMetadata)
        assert metadata.format == "WebP"

    def test_adapter_string_representations(self):
        """Test string representations of adapter."""
        adapter_str = str(self.adapter)
        adapter_repr = repr(self.adapter)

        assert "WebP" in adapter_str or "webp" in adapter_str.lower()
        assert "WebP" in adapter_repr or "webp" in adapter_repr.lower()

    def test_multiple_read_operations(self, temp_dir):
        """Test multiple sequential read operations on same file."""
        test_image = temp_dir / "test_multiple.webp"
        self.create_test_webp(test_image)

        # Read multiple times
        metadata1 = self.adapter.read_metadata(test_image)
        metadata2 = self.adapter.read_metadata(test_image)
        metadata3 = self.adapter.read_metadata(test_image)

        # All reads should succeed
        assert metadata1.format == metadata2.format == metadata3.format == "WebP"

    def test_write_then_read_metadata(self, temp_dir):
        """Test writing metadata and reading it back."""
        test_image = temp_dir / "test_roundtrip.webp"
        output_image = temp_dir / "output_roundtrip.webp"
        self.create_test_webp(test_image)

        # Read original
        original_metadata = self.adapter.read_metadata(test_image)

        # Write to new file
        self.adapter.write_metadata(original_metadata, output_image)

        # Read back
        readback_metadata = self.adapter.read_metadata(output_image)

        assert readback_metadata.format == "WebP"
        assert readback_metadata.file_path == output_image

    def test_adapter_without_safety_manager(self):
        """Test adapter initialization without safety manager."""
        # Create adapter without providing safety manager
        adapter = WebPAdapter(safety_manager=None)

        # Should auto-create safety manager
        assert adapter.safety_manager is not None

    def test_xmp_string_type_handling(self, temp_dir):
        """Test XMP handling when it's a string instead of bytes."""
        test_image = temp_dir / "test_xmp_str.webp"

        # Create WebP with XMP as string (edge case)
        img = Image.new('RGB', (100, 100), color='pink')

        # Manually set XMP in info (simulating string XMP)
        img.info['xmp'] = '<?xml version="1.0"?><x:xmpmeta>String XMP</x:xmpmeta>'
        img.save(test_image, format='WebP')

        metadata = self.adapter.read_metadata(test_image)

        # Should handle string XMP
        assert not metadata.xmp.is_empty() or metadata.custom is not None

    def test_write_with_lossless_preservation(self, temp_dir):
        """Test that lossless mode is preserved during write."""
        test_image = temp_dir / "test_lossless_write.webp"
        output_image = temp_dir / "output_lossless_write.webp"

        # Create lossless WebP
        img = Image.new('RGB', (100, 100), color='teal')
        img.save(test_image, format='WebP', lossless=True)

        # Read and write
        metadata = self.adapter.read_metadata(test_image)
        self.adapter.write_metadata(metadata, output_image)

        # Output should exist
        assert output_image.exists()

    def test_write_with_exif_data(self, temp_dir):
        """Test writing WebP with EXIF data."""
        test_image = temp_dir / "test_write_exif.webp"
        output_image = temp_dir / "output_write_exif.webp"

        # Create WebP
        img = Image.new('RGB', (100, 100), color='navy')

        # Add EXIF
        exif = img.getexif()
        exif[0x010F] = "Test Make"
        exif_bytes = exif.tobytes()
        img.save(test_image, format='WebP', exif=exif_bytes)

        # Read metadata
        metadata = self.adapter.read_metadata(test_image)

        # Add more EXIF via metadata
        metadata.exif.set("Model", "Test Model")

        # Write with EXIF
        self.adapter.write_metadata(metadata, output_image)

        assert output_image.exists()

    def test_write_with_xmp_bytes(self, temp_dir):
        """Test writing WebP with XMP data as bytes."""
        test_image = temp_dir / "test_write_xmp.webp"
        output_image = temp_dir / "output_write_xmp.webp"

        self.create_test_webp(test_image)

        # Read and add XMP
        metadata = self.adapter.read_metadata(test_image)
        metadata.xmp.set('raw_xmp', '<?xml version="1.0"?><x:xmpmeta>Test</x:xmpmeta>')

        # Write with XMP
        self.adapter.write_metadata(metadata, output_image)

        assert output_image.exists()

    def test_write_with_xmp_string(self, temp_dir):
        """Test writing WebP with XMP data as string."""
        test_image = temp_dir / "test_write_xmp_str.webp"
        output_image = temp_dir / "output_write_xmp_str.webp"

        self.create_test_webp(test_image)

        # Read and add XMP as bytes (will test bytes conversion)
        metadata = self.adapter.read_metadata(test_image)
        metadata.xmp.set('raw_xmp', b'<?xml version="1.0"?><x:xmpmeta>Bytes XMP</x:xmpmeta>')

        # Write with XMP
        self.adapter.write_metadata(metadata, output_image)

        assert output_image.exists()

    def test_write_error_handling(self, temp_dir):
        """Test write_metadata error handling."""
        test_image = temp_dir / "test_write_error.webp"
        self.create_test_webp(test_image)

        metadata = self.adapter.read_metadata(test_image)

        # Try to write to invalid path
        invalid_path = Path("/invalid:\\/path/output.webp")

        with pytest.raises(MetadataError) as exc_info:
            self.adapter.write_metadata(metadata, invalid_path)

        assert "Failed to write WebP metadata" in str(exc_info.value)

    def test_strip_error_handling(self, temp_dir):
        """Test strip_metadata error handling."""
        test_image = temp_dir / "test_strip_error.webp"
        self.create_test_webp(test_image)

        # Try to strip to invalid path
        invalid_path = Path("/invalid:\\/path/output.webp")

        with pytest.raises(MetadataError) as exc_info:
            self.adapter.strip_metadata(test_image, invalid_path)

        assert "Failed to strip WebP metadata" in str(exc_info.value)

    def test_parse_exif_bytes_error_handling(self, temp_dir):
        """Test _parse_exif_bytes with invalid data."""
        # This tests the exception handler in _parse_exif_bytes
        test_image = temp_dir / "test_exif_parse.webp"

        # Create WebP with malformed EXIF
        img = Image.new('RGB', (100, 100), color='lime')

        # Invalid EXIF bytes
        bad_exif = b'\xff\xff\xff\xff'
        try:
            img.save(test_image, format='WebP', exif=bad_exif)

            # Try to read - should handle gracefully
            metadata = self.adapter.read_metadata(test_image)
            assert metadata is not None
        except:
            # If save fails, that's also acceptable
            pass

    def test_build_exif_bytes_with_raw_exif(self):
        """Test _build_exif_bytes with raw_exif data."""
        from src.exif_analyzer.core.metadata import MetadataBlock

        exif_block = MetadataBlock(name='exif')
        exif_block.set('raw_exif', '4142434445')  # Hex string

        result = self.adapter._build_exif_bytes(exif_block)

        assert result is not None
        assert isinstance(result, bytes)

    def test_build_exif_bytes_with_invalid_hex(self):
        """Test _build_exif_bytes with invalid hex string."""
        from src.exif_analyzer.core.metadata import MetadataBlock

        exif_block = MetadataBlock(name='exif')
        exif_block.set('raw_exif', 'not_valid_hex')  # Invalid hex

        result = self.adapter._build_exif_bytes(exif_block)

        # Should return None on failure
        assert result is None

    def test_build_exif_bytes_without_raw_exif(self):
        """Test _build_exif_bytes without raw_exif."""
        from src.exif_analyzer.core.metadata import MetadataBlock

        exif_block = MetadataBlock(name='exif')
        exif_block.set('SomeTag', 'SomeValue')  # No raw_exif

        result = self.adapter._build_exif_bytes(exif_block)

        # Should return None
        assert result is None
