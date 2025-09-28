"""
Tests for PNG metadata adapter functionality.
"""
import pytest
from pathlib import Path
import tempfile
from PIL import Image, PngImagePlugin

from src.exif_analyzer.adapters.png_adapter import PNGAdapter
from src.exif_analyzer.core.metadata import ImageMetadata, MetadataBlock
from src.exif_analyzer.core.exceptions import UnsupportedFormatError, FileNotFoundError, CorruptedMetadataError


class TestPNGAdapter:
    """Test cases for PNG metadata adapter."""

    def setup_method(self):
        """Set up test environment."""
        self.adapter = PNGAdapter()

    def create_test_png(self, path: Path, with_metadata: bool = False) -> Path:
        """Create a test PNG file."""
        img = Image.new('RGB', (100, 100), color='blue')

        if with_metadata:
            # Add text metadata
            pnginfo = PngImagePlugin.PngInfo()
            pnginfo.add_text("Title", "Test Image")
            pnginfo.add_text("Author", "Test Author")
            pnginfo.add_text("Description", "A test PNG image")
            pnginfo.add_text("Software", "ExifAnalyzer Test Suite")
            img.save(path, format="PNG", pnginfo=pnginfo)
        else:
            img.save(path, format="PNG")

        return path

    def test_adapter_properties(self):
        """Test adapter basic properties."""
        assert self.adapter.format_name == "PNG"
        assert self.adapter.file_extensions == [".png"]
        assert "PNG" in str(self.adapter)

    def test_supports_format(self):
        """Test format support detection."""
        assert self.adapter.supports_format("png")
        assert self.adapter.supports_format("PNG")
        assert self.adapter.supports_format(".png")
        assert not self.adapter.supports_format("jpg")
        assert not self.adapter.supports_format("jpeg")

    def test_read_metadata_basic(self, temp_dir):
        """Test basic metadata reading."""
        test_image = temp_dir / "test.png"
        self.create_test_png(test_image)

        metadata = self.adapter.read_metadata(test_image)

        assert isinstance(metadata, ImageMetadata)
        assert metadata.format == "PNG"
        assert metadata.file_path == test_image

    def test_read_metadata_with_text(self, temp_dir):
        """Test reading PNG with text metadata."""
        test_image = temp_dir / "test_with_text.png"
        self.create_test_png(test_image, with_metadata=True)

        metadata = self.adapter.read_metadata(test_image)

        assert metadata.has_metadata()
        assert not metadata.custom.is_empty()
        assert "Title" in metadata.custom.keys()
        assert metadata.custom.get("Title") == "Test Image"
        assert metadata.custom.get("Author") == "Test Author"

    def test_read_nonexistent_file(self):
        """Test reading non-existent file."""
        with pytest.raises((FileNotFoundError, CorruptedMetadataError, Exception)):
            self.adapter.read_metadata(Path("nonexistent.png"))

    def test_read_invalid_file(self, temp_dir):
        """Test reading invalid PNG file."""
        invalid_file = temp_dir / "invalid.png"
        invalid_file.write_text("not a png file")

        with pytest.raises((CorruptedMetadataError, Exception)):
            self.adapter.read_metadata(invalid_file)

    def test_unsupported_format(self, temp_dir):
        """Test handling unsupported format."""
        jpg_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(jpg_file, format="JPEG")

        with pytest.raises(UnsupportedFormatError):
            self.adapter.read_metadata(jpg_file)

    def test_strip_metadata(self, temp_dir):
        """Test stripping metadata from PNG."""
        test_image = temp_dir / "test_strip.png"
        output_image = temp_dir / "output_strip.png"
        self.create_test_png(test_image, with_metadata=True)

        # Verify original has metadata
        original_metadata = self.adapter.read_metadata(test_image)
        assert original_metadata.has_metadata()

        # Strip metadata
        result_path = self.adapter.strip_metadata(test_image, output_image)
        assert result_path == output_image
        assert output_image.exists()

        # Verify stripped version has no metadata
        stripped_metadata = self.adapter.read_metadata(output_image)
        assert not stripped_metadata.has_metadata()

    def test_strip_metadata_gps_only(self, temp_dir):
        """Test stripping only GPS metadata from PNG."""
        test_image = temp_dir / "test_gps.png"
        output_image = temp_dir / "output_gps.png"

        # Create PNG with GPS-like metadata
        img = Image.new('RGB', (100, 100), color='green')
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("GPS_Latitude", "40.7128")
        pnginfo.add_text("GPS_Longitude", "-74.0060")
        pnginfo.add_text("Title", "Test Image")
        img.save(test_image, format="PNG", pnginfo=pnginfo)

        # Strip only GPS data
        result_path = self.adapter.strip_metadata(test_image, output_image, gps_only=True)
        assert result_path == output_image

        # Verify GPS data removed but other metadata remains
        stripped_metadata = self.adapter.read_metadata(output_image)
        assert "Title" in stripped_metadata.custom.keys()
        assert "GPS_Latitude" not in stripped_metadata.custom.keys()
        assert "GPS_Longitude" not in stripped_metadata.custom.keys()

    def test_write_metadata(self, temp_dir):
        """Test writing metadata to PNG."""
        test_image = temp_dir / "test_write.png"
        output_image = temp_dir / "output_write.png"
        self.create_test_png(test_image)

        # Create metadata to write
        metadata = ImageMetadata(file_path=test_image, format="PNG")
        metadata.custom.set("NewTitle", "Written Title")
        metadata.custom.set("NewDescription", "Written Description")

        # Write metadata
        result_path = self.adapter.write_metadata(test_image, metadata, output_image)
        assert result_path == output_image

        # Verify written metadata
        written_metadata = self.adapter.read_metadata(output_image)
        assert written_metadata.custom.get("NewTitle") == "Written Title"
        assert written_metadata.custom.get("NewDescription") == "Written Description"

    def test_pixel_integrity(self, temp_dir):
        """Test that pixel data remains unchanged after metadata operations."""
        test_image = temp_dir / "test_pixels.png"
        output_image = temp_dir / "output_pixels.png"
        self.create_test_png(test_image, with_metadata=True)

        # Get original pixel data
        original_img = Image.open(test_image)
        original_pixels = list(original_img.getdata())

        # Strip metadata
        self.adapter.strip_metadata(test_image, output_image)

        # Get processed pixel data
        processed_img = Image.open(output_image)
        processed_pixels = list(processed_img.getdata())

        # Verify pixels are identical
        assert original_pixels == processed_pixels
        assert original_img.size == processed_img.size

    def test_has_gps_data_detection(self, temp_dir):
        """Test GPS data detection in PNG metadata."""
        test_image = temp_dir / "test_gps_detect.png"

        # Create PNG with GPS metadata
        img = Image.new('RGB', (100, 100), color='yellow')
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("GPS_Latitude", "40.7128")
        pnginfo.add_text("Location", "New York")
        pnginfo.add_text("Title", "Non-GPS metadata")
        img.save(test_image, format="PNG", pnginfo=pnginfo)

        metadata = self.adapter.read_metadata(test_image)
        assert metadata.has_gps_data()

        # Test without GPS data
        test_image_no_gps = temp_dir / "test_no_gps.png"
        img = Image.new('RGB', (100, 100), color='cyan')
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("Title", "Just a title")
        img.save(test_image_no_gps, format="PNG", pnginfo=pnginfo)

        metadata_no_gps = self.adapter.read_metadata(test_image_no_gps)
        assert not metadata_no_gps.has_gps_data()

    def test_xmp_metadata_handling(self, temp_dir):
        """Test XMP metadata handling in PNG."""
        test_image = temp_dir / "test_xmp.png"

        # Create PNG with XMP-like metadata
        img = Image.new('RGB', (100, 100), color='magenta')
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("XMP", "<x:xmpmeta>test xmp data</x:xmpmeta>")
        pnginfo.add_text("XML:com.adobe.xmp", "adobe xmp data")
        img.save(test_image, format="PNG", pnginfo=pnginfo)

        metadata = self.adapter.read_metadata(test_image)
        assert not metadata.xmp.is_empty()
        assert "XMP" in metadata.xmp.keys() or "XML:com.adobe.xmp" in metadata.xmp.keys()

    def test_error_handling_corrupted_file(self, temp_dir):
        """Test error handling for corrupted PNG files."""
        corrupted_file = temp_dir / "corrupted.png"

        # Create a file that looks like PNG but is corrupted
        png_header = b'\x89PNG\r\n\x1a\n'
        corrupted_data = png_header + b'corrupted data here'
        corrupted_file.write_bytes(corrupted_data)

        with pytest.raises(MetadataReadError):
            self.adapter.read_metadata(corrupted_file)

    def test_large_metadata_handling(self, temp_dir):
        """Test handling of large metadata values."""
        test_image = temp_dir / "test_large.png"

        # Create PNG with large metadata
        img = Image.new('RGB', (100, 100), color='orange')
        pnginfo = PngImagePlugin.PngInfo()
        large_text = "x" * 10000  # 10KB text
        pnginfo.add_text("LargeField", large_text)
        img.save(test_image, format="PNG", pnginfo=pnginfo)

        metadata = self.adapter.read_metadata(test_image)
        assert metadata.custom.get("LargeField") == large_text

    def test_adapter_string_representations(self):
        """Test string representations of adapter."""
        adapter_str = str(self.adapter)
        adapter_repr = repr(self.adapter)

        assert "PNG" in adapter_str
        assert "PNGAdapter" in adapter_repr
        assert ".png" in adapter_str or ".png" in adapter_repr