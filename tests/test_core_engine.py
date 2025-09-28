"""
Tests for the core metadata engine.
"""
import pytest
from pathlib import Path
import tempfile
from PIL import Image

from src.exif_analyzer.core.engine import MetadataEngine
from src.exif_analyzer.core.exceptions import UnsupportedFormatError, FileError


class TestMetadataEngine:
    """Test cases for MetadataEngine."""

    def setup_method(self):
        """Set up test environment."""
        self.engine = MetadataEngine()

    def test_engine_initialization(self):
        """Test engine initializes with adapters."""
        assert self.engine is not None
        supported = self.engine.get_supported_formats()
        assert 'jpg' in supported
        assert 'png' in supported

    def test_get_adapter_for_jpeg(self, sample_image_path):
        """Test getting adapter for JPEG file."""
        # Create a JPEG test file
        jpeg_path = sample_image_path.parent / "test.jpg"
        with Image.open(sample_image_path) as img:
            img.save(jpeg_path, "JPEG")

        adapter = self.engine.get_adapter(jpeg_path)
        assert adapter.format_name == "JPEG"
        assert adapter.supports_format(jpeg_path)

    def test_get_adapter_for_png(self, sample_image_path):
        """Test getting adapter for PNG file."""
        # Create a PNG test file
        png_path = sample_image_path.parent / "test.png"
        with Image.open(sample_image_path) as img:
            img.save(png_path, "PNG")

        adapter = self.engine.get_adapter(png_path)
        assert adapter.format_name == "PNG"
        assert adapter.supports_format(png_path)

    def test_unsupported_format(self, temp_dir):
        """Test error handling for unsupported format."""
        unsupported_file = temp_dir / "test.bmp"
        # Create a simple text file with .bmp extension
        unsupported_file.write_text("not an image")

        with pytest.raises(UnsupportedFormatError):
            self.engine.get_adapter(unsupported_file)

    def test_nonexistent_file(self, temp_dir):
        """Test error handling for non-existent file."""
        nonexistent = temp_dir / "nonexistent.jpg"

        with pytest.raises(FileError):
            self.engine.get_adapter(nonexistent)

    def test_read_metadata_basic(self, sample_image_path):
        """Test basic metadata reading."""
        metadata = self.engine.read_metadata(sample_image_path)

        assert metadata is not None
        assert metadata.file_path == sample_image_path
        assert metadata.format in ["JPEG", "PNG"]
        assert metadata.file_size > 0

    def test_has_metadata_detection(self, sample_image_path):
        """Test metadata detection."""
        # For a simple test image, may or may not have metadata
        has_meta = self.engine.has_metadata(sample_image_path)
        assert isinstance(has_meta, bool)

    def test_has_gps_data_detection(self, sample_image_path):
        """Test GPS data detection."""
        # For a simple test image, should not have GPS data
        has_gps = self.engine.has_gps_data(sample_image_path)
        assert isinstance(has_gps, bool)

    def test_strip_metadata_basic(self, sample_image_path, temp_dir):
        """Test basic metadata stripping."""
        output_path = temp_dir / f"stripped_{sample_image_path.name}"

        result_path = self.engine.strip_metadata(
            sample_image_path,
            output_path,
            create_backup=False
        )

        assert result_path == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_export_metadata_json(self, sample_image_path, temp_dir):
        """Test metadata export to JSON."""
        export_path = temp_dir / "metadata.json"

        result_path = self.engine.export_metadata(
            sample_image_path,
            export_path,
            format="json"
        )

        assert result_path == export_path
        assert export_path.exists()

        # Verify JSON content
        content = export_path.read_text()
        assert "file_path" in content
        assert "format" in content

    def test_batch_process_export(self, sample_images_dir, temp_dir):
        """Test batch processing for export."""
        image_files = list(sample_images_dir.glob("*.jpg"))
        assert len(image_files) > 0

        results = self.engine.batch_process(
            image_files,
            operation="export",
            output_dir=temp_dir
        )

        assert len(results) == len(image_files)

        # Check that all operations succeeded (no exceptions)
        for file_path, result in results.items():
            assert isinstance(result, Path)
            assert result.exists()

    def test_supported_formats_list(self):
        """Test getting supported formats."""
        formats = self.engine.get_supported_formats()
        assert isinstance(formats, list)
        assert len(formats) > 0
        assert 'jpg' in formats
        assert 'png' in formats

    def test_string_representations(self):
        """Test string representations of engine."""
        str_repr = str(self.engine)
        assert "MetadataEngine" in str_repr

        repr_str = repr(self.engine)
        assert "MetadataEngine" in repr_str
        assert "supported_formats" in repr_str