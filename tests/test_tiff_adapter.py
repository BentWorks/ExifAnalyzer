"""
Tests for TIFF metadata adapter.
"""
import pytest
from pathlib import Path
from PIL import Image

from src.exif_analyzer.adapters.tiff_adapter import TIFFAdapter
from src.exif_analyzer.core.exceptions import UnsupportedFormatError, MetadataError
from src.exif_analyzer.core.metadata import ImageMetadata
from src.exif_analyzer.core.file_safety import FileSafetyManager


class TestTIFFAdapter:
    """Test cases for TIFF metadata adapter."""

    def setup_method(self):
        """Set up test environment."""
        self.safety_manager = FileSafetyManager()
        self.adapter = TIFFAdapter(safety_manager=self.safety_manager)

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for test files."""
        return tmp_path

    def create_test_tiff(self, path: Path, with_exif: bool = False) -> Path:
        """Create a test TIFF image."""
        img = Image.new('RGB', (100, 100), color='magenta')

        save_params = {'format': 'TIFF'}

        if with_exif:
            # Add basic EXIF data
            exif = img.getexif()
            exif[0x010F] = "Test Manufacturer"  # Make
            exif[0x0110] = "Test Model"  # Model
            exif[0x0132] = "2025:01:01 12:00:00"  # DateTime
            save_params['exif'] = exif.tobytes()

        img.save(path, **save_params)
        return path

    def test_adapter_properties(self):
        """Test adapter properties."""
        assert self.adapter.format_name == "TIFF"
        assert "tiff" in self.adapter.supported_formats
        assert "tif" in self.adapter.supported_formats
        assert len(self.adapter.supported_formats) == 2

    def test_supports_format(self, temp_dir):
        """Test format detection."""
        tiff_file = temp_dir / "test.tiff"
        self.create_test_tiff(tiff_file)

        assert self.adapter.supports_format(tiff_file) is True

        # Test with .tif extension
        tif_file = temp_dir / "test.tif"
        self.create_test_tiff(tif_file)

        assert self.adapter.supports_format(tif_file) is True

        # Test with non-TIFF file
        jpg_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(jpg_file, format='JPEG')

        assert self.adapter.supports_format(jpg_file) is False

    def test_read_metadata_basic(self, temp_dir):
        """Test reading basic TIFF metadata."""
        test_image = temp_dir / "test_basic.tiff"
        self.create_test_tiff(test_image)

        metadata = self.adapter.read_metadata(test_image)

        assert isinstance(metadata, ImageMetadata)
        assert metadata.format == "TIFF"
        assert metadata.file_path == test_image

    def test_read_metadata_with_exif(self, temp_dir):
        """Test reading TIFF with EXIF data."""
        test_image = temp_dir / "test_exif.tiff"
        self.create_test_tiff(test_image, with_exif=True)

        metadata = self.adapter.read_metadata(test_image)

        assert isinstance(metadata, ImageMetadata)
        # EXIF should be present
        assert not metadata.exif.is_empty() or not metadata.custom.is_empty()

    def test_read_nonexistent_file(self):
        """Test reading non-existent file."""
        nonexistent = Path("nonexistent.tiff")

        with pytest.raises((FileNotFoundError, MetadataError, Exception)):
            self.adapter.read_metadata(nonexistent)

    def test_read_invalid_file(self, temp_dir):
        """Test reading invalid TIFF file."""
        invalid_file = temp_dir / "invalid.tiff"
        invalid_file.write_text("This is not a valid TIFF file")

        with pytest.raises((UnsupportedFormatError, MetadataError, Exception)):
            self.adapter.read_metadata(invalid_file)

    def test_unsupported_format(self, temp_dir):
        """Test handling of unsupported format."""
        png_file = temp_dir / "test.png"
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(png_file, format='PNG')

        with pytest.raises(UnsupportedFormatError):
            self.adapter.read_metadata(png_file)

    def test_strip_metadata(self, temp_dir):
        """Test stripping metadata from TIFF."""
        test_image = temp_dir / "test_strip.tiff"
        output_image = temp_dir / "output_strip.tiff"
        self.create_test_tiff(test_image, with_exif=True)

        # Strip metadata
        result_path = self.adapter.strip_metadata(test_image, output_image)
        assert result_path == output_image
        assert output_image.exists()

        # Verify stripped version has minimal/no metadata
        stripped_metadata = self.adapter.read_metadata(output_image)
        assert isinstance(stripped_metadata, ImageMetadata)
        # Stripped file should have no EXIF
        assert stripped_metadata.exif.is_empty() or len(stripped_metadata.exif.keys()) == 0

    def test_strip_metadata_gps_only(self, temp_dir):
        """Test stripping all metadata (TIFF adapter doesn't support selective GPS stripping)."""
        test_image = temp_dir / "test_gps.tiff"
        output_image = temp_dir / "output_gps.tiff"
        self.create_test_tiff(test_image, with_exif=True)

        # Strip all metadata (gps_only parameter is ignored for TIFF)
        result_path = self.adapter.strip_metadata(test_image, output_image, gps_only=True)
        assert result_path == output_image

        # Verify file exists
        assert output_image.exists()

    def test_write_metadata(self, temp_dir):
        """Test writing metadata to TIFF."""
        test_image = temp_dir / "test_write.tiff"
        output_image = temp_dir / "output_write.tiff"
        self.create_test_tiff(test_image)

        # Read existing metadata and modify it
        metadata = self.adapter.read_metadata(test_image)
        metadata.exif.set("Make", "New Manufacturer")
        metadata.exif.set("Model", "New Model")

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
        test_image = temp_dir / "test_pixels.tiff"
        output_image = temp_dir / "output_pixels.tiff"
        self.create_test_tiff(test_image, with_exif=True)

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
        """Test GPS data detection in TIFF files."""
        test_image = temp_dir / "test_no_gps.tiff"
        self.create_test_tiff(test_image)

        metadata = self.adapter.read_metadata(test_image)

        # TIFF file without GPS should return False
        assert not metadata.has_gps_data()

    def test_xmp_metadata_handling(self, temp_dir):
        """Test XMP metadata handling in TIFF."""
        test_image = temp_dir / "test_xmp.tiff"

        # Create TIFF with XMP data if supported
        img = Image.new('RGB', (100, 100), color='yellow')
        try:
            xmp_data = b'<?xml version="1.0"?><x:xmpmeta>Test XMP</x:xmpmeta>'
            img.save(test_image, format='TIFF', xmp=xmp_data)
        except:
            # If XMP not supported, just save regular TIFF
            img.save(test_image, format='TIFF')

        metadata = self.adapter.read_metadata(test_image)

        assert isinstance(metadata, ImageMetadata)
        # XMP extraction depends on PIL support
        # Test passes if metadata object is valid

    def test_error_handling_corrupted_file(self, temp_dir):
        """Test error handling with corrupted TIFF file."""
        corrupted_file = temp_dir / "corrupted.tiff"

        # Create a file that starts like TIFF but is corrupted
        with open(corrupted_file, 'wb') as f:
            f.write(b'II*\x00')  # Little-endian TIFF header
            f.write(b'\x00' * 100)  # Incomplete/garbage data

        # TIFF adapter handles corrupted files gracefully
        with pytest.raises((MetadataError, Exception)):
            self.adapter.read_metadata(corrupted_file)

    def test_compressed_tiff_handling(self, temp_dir):
        """Test handling of compressed TIFF images."""
        test_image = temp_dir / "test_compressed.tiff"

        # Create compressed TIFF
        img = Image.new('RGB', (100, 100), color='orange')
        img.save(test_image, format='TIFF', compression='tiff_lzw')

        metadata = self.adapter.read_metadata(test_image)

        assert isinstance(metadata, ImageMetadata)
        assert metadata.format == "TIFF"

    def test_adapter_string_representations(self):
        """Test string representations of adapter."""
        adapter_str = str(self.adapter)
        adapter_repr = repr(self.adapter)

        assert "TIFF" in adapter_str or "tiff" in adapter_str.lower()
        assert "TIFF" in adapter_repr or "tiff" in adapter_repr.lower()

    def test_multiple_read_operations(self, temp_dir):
        """Test multiple sequential read operations on same file."""
        test_image = temp_dir / "test_multiple.tiff"
        self.create_test_tiff(test_image)

        # Read multiple times
        metadata1 = self.adapter.read_metadata(test_image)
        metadata2 = self.adapter.read_metadata(test_image)
        metadata3 = self.adapter.read_metadata(test_image)

        # All reads should succeed
        assert metadata1.format == metadata2.format == metadata3.format == "TIFF"

    def test_write_then_read_metadata(self, temp_dir):
        """Test writing metadata and reading it back."""
        test_image = temp_dir / "test_roundtrip.tiff"
        output_image = temp_dir / "output_roundtrip.tiff"
        self.create_test_tiff(test_image, with_exif=True)

        # Read original
        original_metadata = self.adapter.read_metadata(test_image)

        # Write to new file
        self.adapter.write_metadata(original_metadata, output_image)

        # Read back
        readback_metadata = self.adapter.read_metadata(output_image)

        assert readback_metadata.format == "TIFF"
        assert readback_metadata.file_path == output_image

    def test_tiff_tag_name_resolution(self):
        """Test TIFF tag name resolution."""
        # Test standard tag
        tag_name = self.adapter._get_tiff_tag_name(256)  # ImageWidth
        assert "width" in tag_name.lower() or "256" in tag_name

        # Test unknown tag
        tag_name = self.adapter._get_tiff_tag_name(99999)
        assert "Tag99999" in tag_name or "99999" in tag_name
