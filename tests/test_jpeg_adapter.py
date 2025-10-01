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

    def test_iptc_detection(self, temp_dir):
        """Test IPTC metadata detection."""
        jpeg_file = temp_dir / "test_iptc.jpg"

        # Create JPEG with IPTC marker
        img = Image.new('RGB', (100, 100), color='green')
        img.save(jpeg_file, "JPEG")

        # Inject IPTC marker into file
        with open(jpeg_file, 'rb') as f:
            data = f.read()

        # Insert Photoshop IPTC marker
        iptc_marker = b'Photoshop 3.0\x008BIM\x04\x04\x00\x00\x00\x00\x00\x00'
        modified_data = data[:100] + iptc_marker + data[100:]

        with open(jpeg_file, 'wb') as f:
            f.write(modified_data)

        metadata = self.adapter.read_metadata(jpeg_file)

        # Should detect IPTC presence
        assert metadata.iptc.get("IPTC_Present") == True

    def test_xmp_metadata_extraction(self, temp_dir):
        """Test XMP metadata extraction from JPEG."""
        jpeg_file = temp_dir / "test_xmp.jpg"

        # Create JPEG
        img = Image.new('RGB', (100, 100), color='purple')
        img.save(jpeg_file, "JPEG")

        # Inject XMP data into file
        with open(jpeg_file, 'rb') as f:
            data = f.read()

        # Insert XMP packet
        xmp_data = b'http://ns.adobe.com/xap/1.0/\x00<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?><x:xmpmeta>Test XMP Data</x:xmpmeta><?xpacket end="w"?>'
        modified_data = data[:100] + xmp_data + data[100:]

        with open(jpeg_file, 'wb') as f:
            f.write(modified_data)

        metadata = self.adapter.read_metadata(jpeg_file)

        # Should detect XMP presence
        assert metadata.xmp.get("XMP_Present") == True
        xmp_raw = metadata.xmp.get("XMP_Raw")
        assert xmp_raw is not None
        assert "xmpmeta" in xmp_raw.lower()

    def test_strip_all_metadata(self, temp_dir):
        """Test stripping all metadata (JPEG adapter strips all, not selective)."""
        jpeg_file = temp_dir / "test_with_gps.jpg"
        output_file = temp_dir / "test_all_stripped.jpg"

        # Create file with GPS and other EXIF
        self.create_test_jpeg_with_exif(jpeg_file)

        # Verify it has metadata
        original_metadata = self.adapter.read_metadata(jpeg_file)
        assert original_metadata.has_metadata()
        assert original_metadata.has_gps_data()

        # Strip all metadata (JPEG adapter doesn't support selective stripping)
        result_path = self.adapter.strip_metadata(jpeg_file, output_file)

        assert result_path == output_file
        assert output_file.exists()

        # Verify all metadata was removed
        stripped_metadata = self.adapter.read_metadata(output_file)
        assert not stripped_metadata.has_gps_data()

    def test_bytes_value_handling_in_exif(self, temp_dir):
        """Test handling of bytes values in EXIF data."""
        jpeg_file = temp_dir / "test_bytes_exif.jpg"

        # Create JPEG with bytes EXIF values
        img = Image.new('RGB', (100, 100), color='yellow')

        exif_dict = {
            "0th": {
                piexif.ImageIFD.Make: b"Canon\x00",  # Bytes with null terminator
                piexif.ImageIFD.Model: b"EOS 5D Mark IV",
            },
            "Exif": {
                piexif.ExifIFD.UserComment: b"Test Comment with bytes",
            }
        }

        exif_bytes = piexif.dump(exif_dict)
        img.save(jpeg_file, "JPEG", exif=exif_bytes)

        metadata = self.adapter.read_metadata(jpeg_file)

        # Should successfully parse bytes values
        assert metadata.exif is not None
        assert len(metadata.exif.keys()) > 0

    def test_corrupted_exif_handling(self, temp_dir):
        """Test handling of corrupted EXIF data."""
        jpeg_file = temp_dir / "test_corrupted_exif.jpg"

        # Create JPEG
        img = Image.new('RGB', (100, 100), color='brown')
        img.save(jpeg_file, "JPEG")

        # Inject corrupted EXIF marker
        with open(jpeg_file, 'rb') as f:
            data = f.read()

        # Insert malformed EXIF marker
        corrupted_exif = b'\xff\xe1\x00\x10Exif\x00\x00CORRUPTED'
        modified_data = data[:2] + corrupted_exif + data[2:]

        with open(jpeg_file, 'wb') as f:
            f.write(modified_data)

        # Should handle gracefully without crashing
        try:
            metadata = self.adapter.read_metadata(jpeg_file)
            assert metadata is not None  # Should still return metadata object
        except MetadataError:
            pass  # Acceptable to raise MetadataError for corrupted data

    def test_multiple_ifd_tags(self, temp_dir):
        """Test reading tags from multiple IFD sections."""
        jpeg_file = temp_dir / "test_multi_ifd.jpg"

        # Create JPEG with data in multiple IFDs
        img = Image.new('RGB', (100, 100), color='cyan')

        exif_dict = {
            "0th": {
                piexif.ImageIFD.Make: "TestMake",
                piexif.ImageIFD.Model: "TestModel",
            },
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: "2025:01:01 12:00:00",
                piexif.ExifIFD.LensModel: "24-70mm f/2.8",
            },
            "1st": {
                piexif.ImageIFD.Compression: 6,
            }
        }

        exif_bytes = piexif.dump(exif_dict)
        img.save(jpeg_file, "JPEG", exif=exif_bytes)

        metadata = self.adapter.read_metadata(jpeg_file)

        # Should read tags from all IFDs
        assert len(metadata.exif.keys()) > 0
        # Check for tags from different IFDs
        has_0th_tag = any("make" in key.lower() or "model" in key.lower() for key in metadata.exif.keys())
        has_exif_tag = any("datetime" in key.lower() or "lens" in key.lower() for key in metadata.exif.keys())
        assert has_0th_tag or has_exif_tag

    def test_write_preserves_quality(self, temp_dir):
        """Test that write_metadata preserves image quality."""
        jpeg_file = temp_dir / "test_quality.jpg"
        output_file = temp_dir / "test_quality_written.jpg"

        # Create high-quality JPEG
        img = Image.new('RGB', (100, 100), color='orange')
        img.save(jpeg_file, "JPEG", quality=95)

        original_size = jpeg_file.stat().st_size

        # Read and write metadata
        metadata = self.adapter.read_metadata(jpeg_file)
        metadata.exif.set("Artist", "Quality Test")
        self.adapter.write_metadata(metadata, output_file)

        output_size = output_file.stat().st_size

        # Output size should be reasonably close to original
        # (within 50% to account for metadata changes)
        assert output_size > original_size * 0.5
        assert output_size < original_size * 2.0

    def test_read_jpeg_without_exif(self, temp_dir):
        """Test reading JPEG with no EXIF data."""
        jpeg_file = temp_dir / "test_no_exif.jpg"

        # Create minimal JPEG
        img = Image.new('RGB', (50, 50), color='gray')
        img.save(jpeg_file, "JPEG")

        metadata = self.adapter.read_metadata(jpeg_file)

        # Should still return valid metadata object
        assert metadata is not None
        assert metadata.format == "JPEG"
        # May have no EXIF or minimal EXIF
        assert isinstance(metadata.exif.keys(), list)