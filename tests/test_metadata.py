"""
Tests for ImageMetadata and MetadataBlock classes.
"""
import pytest
from pathlib import Path
from src.exif_analyzer.core.metadata import ImageMetadata, MetadataBlock
from src.exif_analyzer.core.exceptions import ValidationError


class TestMetadataBlock:
    """Test cases for MetadataBlock."""

    def setup_method(self):
        """Set up test environment."""
        self.block = MetadataBlock(name="TestBlock")

    def test_initialization(self):
        """Test metadata block initialization."""
        assert self.block.name == "TestBlock"
        assert len(self.block.data) == 0
        assert self.block.is_empty()

    def test_set_and_get(self):
        """Test setting and getting values."""
        self.block.set("key1", "value1")
        assert self.block.get("key1") == "value1"
        assert self.block.get("nonexistent") is None
        assert self.block.get("nonexistent", "default") == "default"

    def test_contains(self):
        """Test key existence in data dict."""
        self.block.set("test_key", "test_value")
        assert "test_key" in self.block.data
        assert "nonexistent" not in self.block.data

    def test_remove(self):
        """Test removing keys."""
        self.block.set("key1", "value1")
        self.block.set("key2", "value2")

        assert self.block.remove("key1") is True
        assert "key1" not in self.block.data
        assert self.block.remove("nonexistent") is False

    def test_keys(self):
        """Test getting all keys."""
        self.block.set("key1", "value1")
        self.block.set("key2", "value2")

        keys = list(self.block.keys())
        assert len(keys) == 2
        assert "key1" in keys
        assert "key2" in keys

    def test_items(self):
        """Test getting all items via data dict."""
        self.block.set("key1", "value1")
        self.block.set("key2", "value2")

        items = dict(self.block.data.items())
        assert items == {"key1": "value1", "key2": "value2"}

    def test_is_empty(self):
        """Test is_empty method."""
        assert self.block.is_empty() is True

        self.block.set("key1", "value1")
        assert self.block.is_empty() is False

        self.block.remove("key1")
        assert self.block.is_empty() is True

    def test_clear(self):
        """Test clearing all data."""
        self.block.set("key1", "value1")
        self.block.set("key2", "value2")

        self.block.data.clear()
        assert self.block.is_empty()
        assert len(self.block.data) == 0


class TestImageMetadata:
    """Test cases for ImageMetadata."""

    def setup_method(self):
        """Set up test environment."""
        self.test_file = Path("test_image.jpg")

    def test_initialization_basic(self):
        """Test basic initialization."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")

        assert metadata.file_path == self.test_file
        assert metadata.format == "JPEG"
        assert metadata.exif.name == "exif"
        assert metadata.iptc.name == "iptc"
        assert metadata.xmp.name == "xmp"
        assert metadata.custom.name == "custom"

    def test_initialization_with_string_path(self):
        """Test initialization with string path (converts to Path)."""
        metadata = ImageMetadata(file_path="test_image.jpg", format="JPEG")

        assert isinstance(metadata.file_path, Path)
        assert metadata.file_path == Path("test_image.jpg")

    def test_initialization_without_format(self):
        """Test initialization fails without format."""
        with pytest.raises(ValidationError) as exc_info:
            ImageMetadata(file_path=self.test_file, format="")

        assert "format must be specified" in str(exc_info.value)

    def test_get_block(self):
        """Test get_block method."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")

        assert metadata.get_block("exif") == metadata.exif
        assert metadata.get_block("EXIF") == metadata.exif  # Case insensitive
        assert metadata.get_block("iptc") == metadata.iptc
        assert metadata.get_block("xmp") == metadata.xmp
        assert metadata.get_block("custom") == metadata.custom
        assert metadata.get_block("nonexistent") is None

    def test_iter_blocks(self):
        """Test iter_blocks method."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")

        blocks = list(metadata.iter_blocks())
        assert len(blocks) == 4
        assert blocks[0] == metadata.exif
        assert blocks[1] == metadata.iptc
        assert blocks[2] == metadata.xmp
        assert blocks[3] == metadata.custom

    def test_iter_named_blocks(self):
        """Test iter_named_blocks method."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")

        named_blocks = list(metadata.iter_named_blocks())
        assert len(named_blocks) == 4
        assert named_blocks[0] == ("EXIF", metadata.exif)
        assert named_blocks[1] == ("IPTC", metadata.iptc)
        assert named_blocks[2] == ("XMP", metadata.xmp)
        assert named_blocks[3] == ("Custom", metadata.custom)

    def test_get_all_blocks(self):
        """Test get_all_blocks method."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")

        blocks = metadata.get_all_blocks()
        assert len(blocks) == 4
        assert blocks == [metadata.exif, metadata.iptc, metadata.xmp, metadata.custom]

    def test_has_metadata_empty(self):
        """Test has_metadata with no metadata."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")

        assert metadata.has_metadata() is False

    def test_has_metadata_with_data(self):
        """Test has_metadata with data present."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")
        metadata.exif.set("Make", "Canon")

        assert metadata.has_metadata() is True

    def test_has_gps_data_none(self):
        """Test has_gps_data with no GPS data."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")
        metadata.exif.set("Make", "Canon")

        assert metadata.has_gps_data() is False

    def test_has_gps_data_with_gps(self):
        """Test has_gps_data with GPS data present."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")
        metadata.exif.set("GPSLatitude", "37.7749 N")

        assert metadata.has_gps_data() is True

    def test_has_gps_data_with_location(self):
        """Test has_gps_data with location keyword."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")
        metadata.xmp.set("Location", "San Francisco")

        assert metadata.has_gps_data() is True

    def test_get_privacy_sensitive_keys_gps(self):
        """Test get_privacy_sensitive_keys with GPS data."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")
        metadata.exif.set("GPSLatitude", "37.7749 N")
        metadata.exif.set("GPSLongitude", "122.4194 W")

        sensitive_keys = metadata.get_privacy_sensitive_keys()

        assert len(sensitive_keys) >= 2
        assert ("exif", "GPSLatitude") in sensitive_keys
        assert ("exif", "GPSLongitude") in sensitive_keys

    def test_get_privacy_sensitive_keys_device(self):
        """Test get_privacy_sensitive_keys with device data."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")
        metadata.exif.set("Make", "Canon")
        metadata.exif.set("Model", "EOS 5D")

        sensitive_keys = metadata.get_privacy_sensitive_keys()

        assert len(sensitive_keys) >= 2
        assert ("exif", "Make") in sensitive_keys
        assert ("exif", "Model") in sensitive_keys

    def test_get_privacy_sensitive_keys_personal(self):
        """Test get_privacy_sensitive_keys with personal data."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")
        metadata.iptc.set("Artist", "John Doe")
        metadata.xmp.set("Copyright", "Copyright 2025")

        sensitive_keys = metadata.get_privacy_sensitive_keys()

        assert len(sensitive_keys) >= 2
        assert ("iptc", "Artist") in sensitive_keys
        assert ("xmp", "Copyright") in sensitive_keys

    def test_strip_gps_data(self):
        """Test strip_gps_data removes only GPS data."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")
        metadata.exif.set("GPSLatitude", "37.7749 N")
        metadata.exif.set("GPSLongitude", "122.4194 W")
        metadata.exif.set("Make", "Canon")
        metadata.xmp.set("Location", "San Francisco")

        removed_count = metadata.strip_gps_data()

        assert removed_count == 3  # GPS Lat, Lon, Location
        assert "GPSLatitude" not in metadata.exif.data
        assert "GPSLongitude" not in metadata.exif.data
        assert "Location" not in metadata.xmp.data
        assert "Make" in metadata.exif.data  # Non-GPS data preserved

    def test_strip_gps_data_none_present(self):
        """Test strip_gps_data when no GPS data present."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")
        metadata.exif.set("Make", "Canon")

        removed_count = metadata.strip_gps_data()

        assert removed_count == 0
        assert "Make" in metadata.exif.data

    def test_strip_all_metadata(self):
        """Test strip_all_metadata removes all metadata."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")
        metadata.exif.set("Make", "Canon")
        metadata.exif.set("Model", "EOS 5D")
        metadata.iptc.set("Artist", "John Doe")
        metadata.xmp.set("Copyright", "2025")
        metadata.custom.set("Custom", "Value")

        removed_count = metadata.strip_all_metadata()

        assert removed_count == 5
        assert metadata.exif.is_empty()
        assert metadata.iptc.is_empty()
        assert metadata.xmp.is_empty()
        assert metadata.custom.is_empty()

    def test_strip_all_metadata_empty(self):
        """Test strip_all_metadata when no metadata present."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")

        removed_count = metadata.strip_all_metadata()

        assert removed_count == 0

    def test_to_dict(self):
        """Test to_dict conversion."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")
        metadata.exif.set("Make", "Canon")
        metadata.iptc.set("Artist", "John Doe")

        result = metadata.to_dict()

        assert result["file_path"] == str(self.test_file)
        assert result["format"] == "JPEG"
        assert "metadata" in result
        assert "exif" in result["metadata"]
        assert "iptc" in result["metadata"]
        assert "xmp" in result["metadata"]
        assert "custom" in result["metadata"]
        assert result["metadata"]["exif"]["Make"] == "Canon"
        assert result["metadata"]["iptc"]["Artist"] == "John Doe"

    def test_to_json(self):
        """Test to_json conversion."""
        import json

        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")
        metadata.exif.set("Make", "Canon")

        json_str = metadata.to_json()

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["format"] == "JPEG"
        assert parsed["metadata"]["exif"]["Make"] == "Canon"

    def test_to_json_with_indent(self):
        """Test to_json with indentation."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")
        metadata.exif.set("Make", "Canon")

        json_str = metadata.to_json(indent=2)

        # Should contain newlines when indented
        assert "\n" in json_str
        assert "  " in json_str  # Indentation spaces

    def test_str_representation(self):
        """Test string representation."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")

        str_repr = str(metadata)

        assert "JPEG" in str_repr
        assert "test_image.jpg" in str_repr

    def test_repr_representation(self):
        """Test repr representation."""
        metadata = ImageMetadata(file_path=self.test_file, format="JPEG")

        repr_str = repr(metadata)

        assert "ImageMetadata" in repr_str
        assert "JPEG" in repr_str
