"""
Tests for BaseMetadataAdapter.
"""
import pytest
from pathlib import Path
from PIL import Image

from src.exif_analyzer.core.base_adapter import BaseMetadataAdapter
from src.exif_analyzer.core.metadata import ImageMetadata
from src.exif_analyzer.core.exceptions import UnsupportedFormatError, MetadataError
from src.exif_analyzer.core.file_safety import FileSafetyManager


# Create a concrete implementation for testing
class TestAdapter(BaseMetadataAdapter):
    """Concrete adapter implementation for testing."""

    @property
    def supported_formats(self):
        return ["test", "tst"]

    @property
    def format_name(self):
        return "TEST"

    def read_metadata(self, file_path: Path) -> ImageMetadata:
        self.validate_file(file_path)
        return ImageMetadata(file_path=file_path, format="TEST")

    def write_metadata(self, metadata: ImageMetadata, output_path: Path = None) -> Path:
        return output_path or metadata.file_path

    def strip_metadata(self, file_path: Path, output_path: Path = None) -> Path:
        return output_path or file_path


class TestBaseMetadataAdapter:
    """Test cases for BaseMetadataAdapter."""

    def setup_method(self):
        """Set up test environment."""
        self.adapter = TestAdapter()
        self.safety_manager = FileSafetyManager()

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Provide temporary directory for tests."""
        return tmp_path

    def create_test_image(self, path: Path, format: str = "PNG") -> Path:
        """Create a test image file."""
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(path, format=format)
        return path

    def test_initialization_with_safety_manager(self):
        """Test adapter initialization with safety manager."""
        adapter = TestAdapter(safety_manager=self.safety_manager)

        assert adapter.safety_manager == self.safety_manager

    def test_initialization_without_safety_manager(self):
        """Test adapter initialization without safety manager."""
        adapter = TestAdapter(safety_manager=None)

        assert adapter.safety_manager is None

    def test_supported_formats_property(self):
        """Test supported_formats property."""
        formats = self.adapter.supported_formats

        assert isinstance(formats, list)
        assert "test" in formats
        assert "tst" in formats

    def test_format_name_property(self):
        """Test format_name property."""
        name = self.adapter.format_name

        assert name == "TEST"

    def test_supports_format_valid(self, temp_dir):
        """Test supports_format with valid format."""
        test_file = temp_dir / "file.test"
        test_file.touch()

        assert self.adapter.supports_format(test_file) is True

    def test_supports_format_valid_alternate(self, temp_dir):
        """Test supports_format with alternate valid format."""
        test_file = temp_dir / "file.tst"
        test_file.touch()

        assert self.adapter.supports_format(test_file) is True

    def test_supports_format_case_insensitive(self, temp_dir):
        """Test supports_format is case-insensitive."""
        test_file = temp_dir / "file.TEST"
        test_file.touch()

        assert self.adapter.supports_format(test_file) is True

    def test_supports_format_invalid(self, temp_dir):
        """Test supports_format with invalid format."""
        test_file = temp_dir / "file.jpg"
        test_file.touch()

        assert self.adapter.supports_format(test_file) is False

    def test_validate_file_exists(self, temp_dir):
        """Test validate_file with existing file."""
        test_file = temp_dir / "valid.test"
        test_file.write_text("test content")

        # Should not raise any exception
        self.adapter.validate_file(test_file)

    def test_validate_file_not_exists(self, temp_dir):
        """Test validate_file with non-existent file."""
        nonexistent = temp_dir / "nonexistent.test"

        with pytest.raises(FileNotFoundError) as exc_info:
            self.adapter.validate_file(nonexistent)

        assert "File not found" in str(exc_info.value)

    def test_validate_file_is_directory(self, temp_dir):
        """Test validate_file with directory path."""
        directory = temp_dir / "testdir"
        directory.mkdir()

        with pytest.raises(MetadataError) as exc_info:
            self.adapter.validate_file(directory)

        assert "Path is not a file" in str(exc_info.value)

    def test_validate_file_unsupported_format(self, temp_dir):
        """Test validate_file with unsupported format."""
        wrong_format = temp_dir / "file.jpg"
        wrong_format.write_text("content")

        with pytest.raises(UnsupportedFormatError) as exc_info:
            self.adapter.validate_file(wrong_format)

        assert "Format not supported" in str(exc_info.value)

    def test_validate_file_permission_error(self, temp_dir):
        """Test validate_file with permission error."""
        import os
        import stat

        test_file = temp_dir / "readonly.test"
        test_file.write_text("content")

        # Make file unreadable (Unix-like systems)
        if os.name != 'nt':
            os.chmod(test_file, 0o000)

            with pytest.raises(PermissionError) as exc_info:
                self.adapter.validate_file(test_file)

            assert "No read permission" in str(exc_info.value)

            # Restore permissions for cleanup
            os.chmod(test_file, stat.S_IRUSR | stat.S_IWUSR)
        else:
            # On Windows, permission testing is complex, skip
            pytest.skip("Permission test not applicable on Windows")

    def test_get_pixel_hash(self, temp_dir):
        """Test get_pixel_hash calculation."""
        test_image = temp_dir / "test.png"
        self.create_test_image(test_image)

        pixel_hash = self.adapter.get_pixel_hash(test_image)

        assert pixel_hash != ""
        assert len(pixel_hash) == 64  # SHA256 hex digest length

    def test_get_pixel_hash_consistent(self, temp_dir):
        """Test that get_pixel_hash is consistent."""
        test_image = temp_dir / "test.png"
        self.create_test_image(test_image)

        hash1 = self.adapter.get_pixel_hash(test_image)
        hash2 = self.adapter.get_pixel_hash(test_image)

        assert hash1 == hash2

    def test_get_pixel_hash_different_images(self, temp_dir):
        """Test that different images have different hashes."""
        image1 = temp_dir / "image1.png"
        image2 = temp_dir / "image2.png"

        img1 = Image.new('RGB', (100, 100), color='blue')
        img1.save(image1, format='PNG')

        img2 = Image.new('RGB', (100, 100), color='red')
        img2.save(image2, format='PNG')

        hash1 = self.adapter.get_pixel_hash(image1)
        hash2 = self.adapter.get_pixel_hash(image2)

        assert hash1 != hash2

    def test_get_pixel_hash_invalid_file(self, temp_dir):
        """Test get_pixel_hash with invalid image file."""
        invalid_file = temp_dir / "invalid.png"
        invalid_file.write_text("not an image")

        pixel_hash = self.adapter.get_pixel_hash(invalid_file)

        # Should return empty string on error
        assert pixel_hash == ""

    def test_check_image_dimensions_and_mode_match(self, temp_dir):
        """Test _check_image_dimensions_and_mode with matching images."""
        test_image = temp_dir / "test.png"
        self.create_test_image(test_image)

        with Image.open(test_image) as img1:
            with Image.open(test_image) as img2:
                result = self.adapter._check_image_dimensions_and_mode(img1, img2)

        assert result is True

    def test_check_image_dimensions_mismatch(self, temp_dir):
        """Test _check_image_dimensions_and_mode with size mismatch."""
        image1 = temp_dir / "image1.png"
        image2 = temp_dir / "image2.png"

        img1 = Image.new('RGB', (100, 100), color='blue')
        img1.save(image1, format='PNG')

        img2 = Image.new('RGB', (200, 200), color='blue')
        img2.save(image2, format='PNG')

        with Image.open(image1) as orig:
            with Image.open(image2) as modified:
                result = self.adapter._check_image_dimensions_and_mode(orig, modified)

        assert result is False

    def test_check_image_mode_mismatch(self, temp_dir):
        """Test _check_image_dimensions_and_mode with mode mismatch."""
        image1 = temp_dir / "image1.png"
        image2 = temp_dir / "image2.png"

        img1 = Image.new('RGB', (100, 100), color='blue')
        img1.save(image1, format='PNG')

        img2 = Image.new('L', (100, 100), color=128)  # Grayscale mode
        img2.save(image2, format='PNG')

        with Image.open(image1) as orig:
            with Image.open(image2) as modified:
                result = self.adapter._check_image_dimensions_and_mode(orig, modified)

        assert result is False

    def test_verify_pixel_integrity_identical(self, temp_dir):
        """Test verify_pixel_integrity with identical images."""
        original = temp_dir / "original.png"
        copy = temp_dir / "copy.png"

        # Create identical images
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(original, format='PNG')
        img.save(copy, format='PNG')

        result = self.adapter.verify_pixel_integrity(original, copy)

        assert result is True

    def test_verify_pixel_integrity_different(self, temp_dir):
        """Test verify_pixel_integrity with different images."""
        original = temp_dir / "original.png"
        modified = temp_dir / "modified.png"

        img1 = Image.new('RGB', (100, 100), color='blue')
        img1.save(original, format='PNG')

        img2 = Image.new('RGB', (100, 100), color='red')
        img2.save(modified, format='PNG')

        result = self.adapter.verify_pixel_integrity(original, modified)

        assert result is False

    def test_verify_pixel_integrity_invalid_file(self, temp_dir):
        """Test verify_pixel_integrity with invalid file."""
        original = temp_dir / "original.png"
        invalid = temp_dir / "invalid.png"

        self.create_test_image(original)
        invalid.write_text("not an image")

        result = self.adapter.verify_pixel_integrity(original, invalid)

        # Should return False on error
        assert result is False

    def test_verify_pixel_integrity_exception_handling(self, temp_dir):
        """Test verify_pixel_integrity exception handling."""
        nonexistent1 = temp_dir / "file1.png"
        nonexistent2 = temp_dir / "file2.png"

        result = self.adapter.verify_pixel_integrity(nonexistent1, nonexistent2)

        # Should return False on exception
        assert result is False

    def test_log_operation_success(self, temp_dir):
        """Test log_operation with success."""
        test_file = temp_dir / "test.test"
        test_file.touch()

        # Should not raise exception
        self.adapter.log_operation("TEST", test_file, success=True)

    def test_log_operation_failure(self, temp_dir):
        """Test log_operation with failure."""
        test_file = temp_dir / "test.test"
        test_file.touch()

        # Should not raise exception
        self.adapter.log_operation("TEST", test_file, success=False)

    def test_str_representation(self):
        """Test string representation."""
        str_repr = str(self.adapter)

        assert "TEST" in str_repr
        assert "Adapter" in str_repr

    def test_repr_representation(self):
        """Test repr representation."""
        repr_str = repr(self.adapter)

        assert "TestAdapter" in repr_str
        assert "formats=" in repr_str
        assert "test" in repr_str
