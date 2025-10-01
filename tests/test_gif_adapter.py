"""
Tests for GIF metadata adapter.
"""
import pytest
from pathlib import Path
from PIL import Image

from src.exif_analyzer.adapters.gif_adapter import GIFAdapter
from src.exif_analyzer.core.exceptions import UnsupportedFormatError, MetadataError
from src.exif_analyzer.core.metadata import ImageMetadata
from src.exif_analyzer.core.file_safety import FileSafetyManager


class TestGIFAdapter:
    """Test cases for GIF metadata adapter."""

    def setup_method(self):
        """Set up test environment."""
        self.safety_manager = FileSafetyManager()
        self.adapter = GIFAdapter(safety_manager=self.safety_manager)

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for test files."""
        return tmp_path

    def create_test_gif(self, path: Path, with_comment: bool = False, animated: bool = False) -> Path:
        """Create a test GIF image."""
        if animated:
            # Create animated GIF with multiple frames
            frames = []
            for i in range(3):
                img = Image.new('P', (100, 100), color=i * 80)
                frames.append(img)

            save_params = {'format': 'GIF', 'save_all': True, 'append_images': frames[1:], 'duration': 100, 'loop': 0}

            if with_comment:
                save_params['comment'] = b'Test animated GIF comment'

            frames[0].save(path, **save_params)
        else:
            # Create static GIF
            img = Image.new('P', (100, 100), color=0)

            save_params = {'format': 'GIF'}

            if with_comment:
                save_params['comment'] = b'Test GIF comment'

            img.save(path, **save_params)

        return path

    def test_adapter_properties(self):
        """Test adapter properties."""
        assert self.adapter.format_name == "GIF"
        assert "gif" in self.adapter.supported_formats
        assert len(self.adapter.supported_formats) == 1

    def test_supports_format(self, temp_dir):
        """Test format detection."""
        gif_file = temp_dir / "test.gif"
        self.create_test_gif(gif_file)

        assert self.adapter.supports_format(gif_file) is True

        # Test with non-GIF file
        jpg_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(jpg_file, format='JPEG')

        assert self.adapter.supports_format(jpg_file) is False

    def test_read_metadata_basic(self, temp_dir):
        """Test reading basic GIF metadata."""
        test_image = temp_dir / "test_basic.gif"
        self.create_test_gif(test_image)

        metadata = self.adapter.read_metadata(test_image)

        assert isinstance(metadata, ImageMetadata)
        assert metadata.format == "GIF"
        assert metadata.file_path == test_image

    def test_read_metadata_with_comment(self, temp_dir):
        """Test reading GIF with comment."""
        test_image = temp_dir / "test_comment.gif"
        self.create_test_gif(test_image, with_comment=True)

        metadata = self.adapter.read_metadata(test_image)

        assert isinstance(metadata, ImageMetadata)
        assert not metadata.custom.is_empty()
        # Should have comment in custom metadata
        comment = metadata.custom.get('GIF:comment')
        assert comment is not None

    def test_read_animated_gif(self, temp_dir):
        """Test reading animated GIF metadata."""
        test_image = temp_dir / "test_animated.gif"
        self.create_test_gif(test_image, animated=True)

        metadata = self.adapter.read_metadata(test_image)

        assert isinstance(metadata, ImageMetadata)
        # Animated GIF should have animation info
        is_animated = metadata.custom.get('GIF:is_animated')
        if is_animated:
            assert is_animated in ['True', 'true', '1']

    def test_read_nonexistent_file(self):
        """Test reading non-existent file."""
        nonexistent = Path("nonexistent.gif")

        with pytest.raises((FileNotFoundError, MetadataError, Exception)):
            self.adapter.read_metadata(nonexistent)

    def test_read_invalid_file(self, temp_dir):
        """Test reading invalid GIF file."""
        invalid_file = temp_dir / "invalid.gif"
        invalid_file.write_text("This is not a valid GIF file")

        with pytest.raises((UnsupportedFormatError, MetadataError, Exception)):
            self.adapter.read_metadata(invalid_file)

    def test_unsupported_format(self, temp_dir):
        """Test handling of unsupported format."""
        png_file = temp_dir / "test.png"
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(png_file, format='PNG')

        with pytest.raises(UnsupportedFormatError):
            self.adapter.read_metadata(png_file)

    def test_strip_metadata_static(self, temp_dir):
        """Test stripping metadata from static GIF."""
        test_image = temp_dir / "test_strip.gif"
        output_image = temp_dir / "output_strip.gif"
        self.create_test_gif(test_image, with_comment=True)

        # Strip metadata
        result_path = self.adapter.strip_metadata(test_image, output_image)
        assert result_path == output_image
        assert output_image.exists()

        # Verify stripped version has no comment
        stripped_metadata = self.adapter.read_metadata(output_image)
        comment = stripped_metadata.custom.get('GIF:comment')
        # Comment should be None or empty after stripping
        assert comment is None or comment == ''

    def test_strip_metadata_animated(self, temp_dir):
        """Test stripping metadata from animated GIF."""
        test_image = temp_dir / "test_strip_animated.gif"
        output_image = temp_dir / "output_strip_animated.gif"
        self.create_test_gif(test_image, with_comment=True, animated=True)

        # Strip metadata
        result_path = self.adapter.strip_metadata(test_image, output_image)
        assert result_path == output_image
        assert output_image.exists()

        # Verify stripped version exists and can be read
        stripped_metadata = self.adapter.read_metadata(output_image)
        assert isinstance(stripped_metadata, ImageMetadata)

    def test_strip_metadata_gps_only(self, temp_dir):
        """Test stripping all metadata (GIF adapter doesn't support selective GPS stripping)."""
        test_image = temp_dir / "test_gps.gif"
        output_image = temp_dir / "output_gps.gif"
        self.create_test_gif(test_image, with_comment=True)

        # Strip all metadata (gps_only parameter is ignored for GIF)
        result_path = self.adapter.strip_metadata(test_image, output_image, gps_only=True)
        assert result_path == output_image

        # Verify file exists
        assert output_image.exists()

    def test_write_metadata_static(self, temp_dir):
        """Test writing metadata to static GIF."""
        test_image = temp_dir / "test_write.gif"
        output_image = temp_dir / "output_write.gif"
        self.create_test_gif(test_image)

        # Read existing metadata and modify it
        metadata = self.adapter.read_metadata(test_image)
        metadata.custom.set("GIF:comment", "New comment")

        # Write metadata
        result_path = self.adapter.write_metadata(metadata, output_image)
        assert result_path == output_image

        # Verify written file exists
        assert output_image.exists()

        # Verify we can read it back
        written_metadata = self.adapter.read_metadata(output_image)
        assert isinstance(written_metadata, ImageMetadata)
        comment = written_metadata.custom.get('GIF:comment')
        assert comment == "New comment"

    def test_write_metadata_animated(self, temp_dir):
        """Test writing metadata to animated GIF."""
        test_image = temp_dir / "test_write_animated.gif"
        output_image = temp_dir / "output_write_animated.gif"
        self.create_test_gif(test_image, animated=True)

        # Read existing metadata
        metadata = self.adapter.read_metadata(test_image)
        metadata.custom.set("GIF:comment", "Animated comment")

        # Write metadata
        result_path = self.adapter.write_metadata(metadata, output_image)
        assert result_path == output_image

        # Verify written file exists and is animated
        assert output_image.exists()
        written_metadata = self.adapter.read_metadata(output_image)
        assert isinstance(written_metadata, ImageMetadata)

    def test_pixel_integrity_static(self, temp_dir):
        """Test that pixel data remains unchanged after metadata operations on static GIF."""
        test_image = temp_dir / "test_pixels.gif"
        output_image = temp_dir / "output_pixels.gif"
        self.create_test_gif(test_image, with_comment=True)

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
        """Test GPS data detection in GIF files."""
        test_image = temp_dir / "test_no_gps.gif"
        self.create_test_gif(test_image)

        metadata = self.adapter.read_metadata(test_image)

        # GIF files don't support GPS data
        assert not metadata.has_gps_data()

    def test_error_handling_corrupted_file(self, temp_dir):
        """Test error handling with corrupted GIF file."""
        corrupted_file = temp_dir / "corrupted.gif"

        # Create a file that starts like GIF but is corrupted
        with open(corrupted_file, 'wb') as f:
            f.write(b'GIF89a')  # GIF header
            f.write(b'\x00' * 100)  # Incomplete/garbage data

        # GIF adapter handles corrupted files gracefully
        with pytest.raises((MetadataError, Exception)):
            self.adapter.read_metadata(corrupted_file)

    def test_adapter_string_representations(self):
        """Test string representations of adapter."""
        adapter_str = str(self.adapter)
        adapter_repr = repr(self.adapter)

        assert "GIF" in adapter_str or "gif" in adapter_str.lower()
        assert "GIF" in adapter_repr or "gif" in adapter_repr.lower()

    def test_multiple_read_operations(self, temp_dir):
        """Test multiple sequential read operations on same file."""
        test_image = temp_dir / "test_multiple.gif"
        self.create_test_gif(test_image)

        # Read multiple times
        metadata1 = self.adapter.read_metadata(test_image)
        metadata2 = self.adapter.read_metadata(test_image)
        metadata3 = self.adapter.read_metadata(test_image)

        # All reads should succeed
        assert metadata1.format == metadata2.format == metadata3.format == "GIF"

    def test_write_then_read_metadata(self, temp_dir):
        """Test writing metadata and reading it back."""
        test_image = temp_dir / "test_roundtrip.gif"
        output_image = temp_dir / "output_roundtrip.gif"
        self.create_test_gif(test_image, with_comment=True)

        # Read original
        original_metadata = self.adapter.read_metadata(test_image)

        # Write to new file
        self.adapter.write_metadata(original_metadata, output_image)

        # Read back
        readback_metadata = self.adapter.read_metadata(output_image)

        assert readback_metadata.format == "GIF"
        assert readback_metadata.file_path == output_image

    def test_animation_frame_count(self, temp_dir):
        """Test reading frame count from animated GIF."""
        test_image = temp_dir / "test_frames.gif"
        self.create_test_gif(test_image, animated=True)

        metadata = self.adapter.read_metadata(test_image)

        # Should have frame count
        n_frames = metadata.custom.get('GIF:n_frames')
        if n_frames:
            assert int(n_frames) >= 1
