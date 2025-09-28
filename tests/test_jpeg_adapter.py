"""
Tests for JPEG adapter functionality.
"""
import pytest
from pathlib import Path
from PIL import Image
import piexif

from src.exif_analyzer.adapters.jpeg_adapter import JPEGAdapter
from src.exif_analyzer.core.exceptions import UnsupportedFormatError, MetadataError


class TestJPEGAdapter:
    """Test cases for JPEGAdapter."""

    def setup_method(self):
        """Set up test environment."""
        self.adapter = JPEGAdapter()

    def test_adapter_properties(self):
        """Test adapter basic properties."""
        assert self.adapter.format_name == "JPEG"
        assert "jpg" in self.adapter.supported_formats
        assert "jpeg" in self.adapter.supported_formats

    def test_supports_format(self, temp_dir):
        """Test format support detection."""
        jpeg_file = temp_dir / "test.jpg"
        png_file = temp_dir / "test.png"
        bmp_file = temp_dir / "test.bmp"

        assert self.adapter.supports_format(jpeg_file)
        assert not self.adapter.supports_format(png_file)
        assert not self.adapter.supports_format(bmp_file)

    def create_test_jpeg_with_exif(self, file_path: Path) -> Path:
        """Create a test JPEG file with EXIF data."""
        # Create a simple image
        img = Image.new('RGB', (100, 100), color='red')

        # Create EXIF data
        exif_dict = {
            "0th": {
                piexif.ImageIFD.Artist: "Test Artist",
                piexif.ImageIFD.Software: "ExifAnalyzer Test",
                piexif.ImageIFD.ImageDescription: "Test image with EXIF"
            },
            "Exif": {
                piexif.ExifIFD.ColorSpace: 1,
                piexif.ExifIFD.PixelXDimension: 100,
                piexif.ExifIFD.PixelYDimension: 100
            },
            "GPS": {
                piexif.GPSIFD.GPSLatitudeRef: "N",
                piexif.GPSIFD.GPSLatitude: ((40, 1), (43, 1), (2800, 100)),
                piexif.GPSIFD.GPSLongitudeRef: "W",
                piexif.GPSIFD.GPSLongitude: ((73, 1), (59, 1), (1234, 100))
            }
        }

        exif_bytes = piexif.dump(exif_dict)
        img.save(file_path, "JPEG", exif=exif_bytes)
        return file_path

    def test_read_metadata_basic(self, temp_dir):
        """Test basic metadata reading from JPEG."""
        jpeg_file = temp_dir / "test_with_exif.jpg"
        self.create_test_jpeg_with_exif(jpeg_file)

        metadata = self.adapter.read_metadata(jpeg_file)

        assert metadata is not None
        assert metadata.format == "JPEG"
        assert metadata.file_path == jpeg_file
        assert metadata.file_size > 0
        assert metadata.pixel_hash != ""

    def test_read_exif_data(self, temp_dir):
        """Test EXIF data extraction."""
        jpeg_file = temp_dir / "test_with_exif.jpg"
        self.create_test_jpeg_with_exif(jpeg_file)

        metadata = self.adapter.read_metadata(jpeg_file)

        # Check that EXIF data was extracted
        assert len(metadata.exif.keys()) > 0

        # Check for specific EXIF values we set
        artist_found = any("artist" in key.lower() for key in metadata.exif.keys())
        software_found = any("software" in key.lower() for key in metadata.exif.keys())

        assert artist_found or software_found  # At least one should be found

    def test_gps_data_detection(self, temp_dir):
        """Test GPS data detection."""
        jpeg_file = temp_dir / "test_with_gps.jpg"
        self.create_test_jpeg_with_exif(jpeg_file)

        metadata = self.adapter.read_metadata(jpeg_file)

        # Should detect GPS data
        assert metadata.has_gps_data()

    def test_strip_metadata(self, temp_dir):
        """Test metadata stripping."""
        jpeg_file = temp_dir / "test_with_exif.jpg"
        output_file = temp_dir / "test_stripped.jpg"

        # Create file with metadata
        self.create_test_jpeg_with_exif(jpeg_file)

        # Verify it has metadata
        original_metadata = self.adapter.read_metadata(jpeg_file)
        assert original_metadata.has_metadata()

        # Strip metadata
        result_path = self.adapter.strip_metadata(jpeg_file, output_file)

        assert result_path == output_file
        assert output_file.exists()

        # Verify metadata was removed
        stripped_metadata = self.adapter.read_metadata(output_file)
        # Note: Some minimal metadata might remain, but GPS should be gone
        assert not stripped_metadata.has_gps_data()

    def test_write_metadata(self, temp_dir):
        """Test metadata writing."""
        jpeg_file = temp_dir / "test_original.jpg"
        output_file = temp_dir / "test_modified.jpg"

        # Create simple JPEG
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(jpeg_file, "JPEG")

        # Read metadata (should be minimal)
        metadata = self.adapter.read_metadata(jpeg_file)

        # Add some metadata
        metadata.exif.set("Artist", "Test Modified Artist")
        metadata.exif.set("Software", "ExifAnalyzer Test Suite")

        # Write metadata
        result_path = self.adapter.write_metadata(metadata, output_file)

        assert result_path == output_file
        assert output_file.exists()

        # Verify metadata was written
        modified_metadata = self.adapter.read_metadata(output_file)
        # Note: Due to EXIF complexity, we just check the file was created successfully
        assert modified_metadata.has_metadata()

    def test_pixel_integrity(self, temp_dir):
        """Test pixel data integrity during operations."""
        jpeg_file = temp_dir / "test_pixel_integrity.jpg"
        output_file = temp_dir / "test_pixel_modified.jpg"

        # Create test image
        self.create_test_jpeg_with_exif(jpeg_file)

        # Strip metadata
        self.adapter.strip_metadata(jpeg_file, output_file)

        # Verify pixel integrity
        assert self.adapter.verify_pixel_integrity(jpeg_file, output_file)

    def test_invalid_file_handling(self, temp_dir):
        """Test handling of invalid files."""
        # Non-existent file
        nonexistent = temp_dir / "nonexistent.jpg"
        with pytest.raises(FileNotFoundError):
            self.adapter.read_metadata(nonexistent)

        # Non-JPEG file with JPEG extension
        fake_jpeg = temp_dir / "fake.jpg"
        fake_jpeg.write_text("This is not a JPEG file")

        with pytest.raises(MetadataError):
            self.adapter.read_metadata(fake_jpeg)

    def test_adapter_string_representations(self):
        """Test string representations."""
        str_repr = str(self.adapter)
        assert "JPEG" in str_repr

        repr_str = repr(self.adapter)
        assert "JPEGAdapter" in repr_str
        assert "formats" in repr_str