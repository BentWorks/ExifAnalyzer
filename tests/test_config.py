"""
Tests for configuration management.
"""
import pytest
import json
import tempfile
from pathlib import Path

from src.exif_analyzer.core.config import ConfigManager
from src.exif_analyzer.core.exceptions import ValidationError


class TestConfigManager:
    """Test cases for ConfigManager."""

    def test_default_config_initialization(self):
        """Test that ConfigManager initializes with default values."""
        config = ConfigManager()

        # Check default values exist
        assert config.get("backup.enabled") is True
        assert config.get("backup.keep_count") == 5
        assert config.get("output.default_format") == "json"
        assert config.get("privacy.strip_gps_by_default") is False
        assert config.get("batch.max_concurrent") == 4
        assert config.get("logging.level") == "INFO"

    def test_get_with_dot_notation(self):
        """Test getting config values with dot notation."""
        config = ConfigManager()

        # Test nested access
        assert config.get("backup.enabled") is True
        assert config.get("backup.directory") is None
        assert config.get("privacy.privacy_sensitive_keys") is not None
        assert isinstance(config.get("privacy.privacy_sensitive_keys"), list)

    def test_get_with_default(self):
        """Test getting config values with default fallback."""
        config = ConfigManager()

        # Non-existent key should return default
        assert config.get("nonexistent.key", "default_value") == "default_value"
        assert config.get("backup.nonexistent", 42) == 42

        # Existing key should return actual value
        assert config.get("backup.enabled", False) is True

    def test_set_with_dot_notation(self):
        """Test setting config values with dot notation."""
        config = ConfigManager()

        # Set existing key
        config.set("backup.enabled", False)
        assert config.get("backup.enabled") is False

        # Set new nested key
        config.set("custom.new_setting", "test_value")
        assert config.get("custom.new_setting") == "test_value"

        # Set deep nested key
        config.set("level1.level2.level3", 123)
        assert config.get("level1.level2.level3") == 123

    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        config = ConfigManager()

        # Modify some values
        config.set("backup.enabled", False)
        config.set("batch.max_concurrent", 10)
        assert config.get("backup.enabled") is False
        assert config.get("batch.max_concurrent") == 10

        # Reset to defaults
        config.reset_to_defaults()

        # Values should be back to defaults
        assert config.get("backup.enabled") is True
        assert config.get("batch.max_concurrent") == 4

    def test_validate_config_valid(self):
        """Test validation with valid configuration."""
        config = ConfigManager()

        # Default config should be valid
        assert config.validate_config() is True

    def test_validate_backup_enabled_type(self):
        """Test validation fails for invalid backup.enabled type."""
        config = ConfigManager()

        config.set("backup.enabled", "not_a_boolean")

        with pytest.raises(ValidationError) as exc_info:
            config.validate_config()

        assert "backup.enabled must be boolean" in str(exc_info.value)

    def test_validate_backup_keep_count_type(self):
        """Test validation fails for invalid backup.keep_count type."""
        config = ConfigManager()

        config.set("backup.keep_count", "not_an_int")

        with pytest.raises(ValidationError) as exc_info:
            config.validate_config()

        assert "backup.keep_count must be non-negative integer" in str(exc_info.value)

    def test_validate_backup_keep_count_negative(self):
        """Test validation fails for negative backup.keep_count."""
        config = ConfigManager()

        config.set("backup.keep_count", -5)

        with pytest.raises(ValidationError) as exc_info:
            config.validate_config()

        assert "backup.keep_count must be non-negative integer" in str(exc_info.value)

    def test_validate_batch_max_concurrent_type(self):
        """Test validation fails for invalid batch.max_concurrent type."""
        config = ConfigManager()

        config.set("batch.max_concurrent", "not_an_int")

        with pytest.raises(ValidationError) as exc_info:
            config.validate_config()

        assert "batch.max_concurrent must be positive integer" in str(exc_info.value)

    def test_validate_batch_max_concurrent_zero(self):
        """Test validation fails for zero batch.max_concurrent."""
        config = ConfigManager()

        config.set("batch.max_concurrent", 0)

        with pytest.raises(ValidationError) as exc_info:
            config.validate_config()

        assert "batch.max_concurrent must be positive integer" in str(exc_info.value)

    def test_validate_logging_level_invalid(self):
        """Test validation fails for invalid logging level."""
        config = ConfigManager()

        config.set("logging.level", "INVALID_LEVEL")

        with pytest.raises(ValidationError) as exc_info:
            config.validate_config()

        assert "logging.level must be one of" in str(exc_info.value)

    def test_validate_logging_level_valid(self):
        """Test validation succeeds for valid logging levels."""
        config = ConfigManager()

        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            config.set("logging.level", level)
            assert config.validate_config() is True

    def test_get_backup_directory_custom(self):
        """Test getting custom backup directory."""
        config = ConfigManager()

        custom_dir = "/custom/backup/path"
        config.set("backup.directory", custom_dir)

        result = config.get_backup_directory(Path("/some/file.jpg"))
        assert result == Path(custom_dir)

    def test_get_backup_directory_default(self):
        """Test getting default backup directory (same as file location)."""
        config = ConfigManager()

        # Default is None
        config.set("backup.directory", None)

        file_path = Path("/some/directory/file.jpg")
        result = config.get_backup_directory(file_path)
        assert result == file_path.parent

    def test_should_create_backup_enabled(self):
        """Test should_create_backup when enabled."""
        config = ConfigManager()

        config.set("backup.enabled", True)
        assert config.should_create_backup() is True

    def test_should_create_backup_disabled(self):
        """Test should_create_backup when disabled."""
        config = ConfigManager()

        config.set("backup.enabled", False)
        assert config.should_create_backup() is False

    def test_get_privacy_patterns(self):
        """Test getting privacy-sensitive key patterns."""
        config = ConfigManager()

        patterns = config.get_privacy_patterns()

        assert isinstance(patterns, list)
        assert "gps" in patterns
        assert "location" in patterns
        assert len(patterns) > 0

    def test_should_warn_before_strip_enabled(self):
        """Test should_warn_before_strip when enabled."""
        config = ConfigManager()

        config.set("privacy.warn_before_strip", True)
        assert config.should_warn_before_strip() is True

    def test_should_warn_before_strip_disabled(self):
        """Test should_warn_before_strip when disabled."""
        config = ConfigManager()

        config.set("privacy.warn_before_strip", False)
        assert config.should_warn_before_strip() is False

    def test_get_max_concurrent_operations(self):
        """Test getting max concurrent operations."""
        config = ConfigManager()

        config.set("batch.max_concurrent", 8)
        assert config.get_max_concurrent_operations() == 8

        config.set("batch.max_concurrent", 2)
        assert config.get_max_concurrent_operations() == 2

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = ConfigManager()

        config_dict = config.to_dict()

        # Should be a dictionary
        assert isinstance(config_dict, dict)

        # Should contain main sections
        assert "backup" in config_dict
        assert "output" in config_dict
        assert "privacy" in config_dict
        assert "batch" in config_dict
        assert "logging" in config_dict

        # Should be a deep copy (modifying doesn't affect original)
        config_dict["backup"]["enabled"] = False
        assert config.get("backup.enabled") is True

    def test_str_representation(self):
        """Test string representation of config."""
        config = ConfigManager()

        str_repr = str(config)

        # Should be valid JSON
        parsed = json.loads(str_repr)
        assert isinstance(parsed, dict)
        assert "backup" in parsed

    def test_repr_representation(self):
        """Test repr representation of config."""
        config = ConfigManager()

        repr_str = repr(config)

        assert "ConfigManager" in repr_str
        assert "user_config" in repr_str
        assert "project_config" in repr_str

    def test_load_user_config_from_file(self, tmp_path):
        """Test loading configuration from user config file."""
        # Create temporary user config
        user_config_file = tmp_path / "config.json"
        user_config_data = {
            "backup": {
                "enabled": False,
                "keep_count": 10
            },
            "batch": {
                "max_concurrent": 8
            }
        }

        with open(user_config_file, 'w') as f:
            json.dump(user_config_data, f)

        # Create ConfigManager with custom user config path
        config = ConfigManager()
        config.user_config_path = user_config_file
        config._load_config()

        # Values from file should override defaults
        assert config.get("backup.enabled") is False
        assert config.get("backup.keep_count") == 10
        assert config.get("batch.max_concurrent") == 8

        # Other defaults should remain
        assert config.get("output.default_format") == "json"

    def test_load_project_config_from_file(self, tmp_path):
        """Test loading configuration from project config file."""
        # Create temporary project config
        project_config_file = tmp_path / ".exifanalyzer.json"
        project_config_data = {
            "privacy": {
                "strip_gps_by_default": True
            },
            "logging": {
                "level": "DEBUG"
            }
        }

        with open(project_config_file, 'w') as f:
            json.dump(project_config_data, f)

        # Create ConfigManager with custom project config path
        config = ConfigManager()
        config.project_config_path = project_config_file
        config._load_config()

        # Values from file should override defaults
        assert config.get("privacy.strip_gps_by_default") is True
        assert config.get("logging.level") == "DEBUG"

    def test_load_config_priority(self, tmp_path):
        """Test that project config overrides user config."""
        # Create user config
        user_config_file = tmp_path / "user_config.json"
        user_config_data = {
            "backup": {"enabled": False},
            "batch": {"max_concurrent": 6}
        }
        with open(user_config_file, 'w') as f:
            json.dump(user_config_data, f)

        # Create project config (should override)
        project_config_file = tmp_path / "project_config.json"
        project_config_data = {
            "backup": {"enabled": True}  # Overrides user config
        }
        with open(project_config_file, 'w') as f:
            json.dump(project_config_data, f)

        # Load configs
        config = ConfigManager()
        config.user_config_path = user_config_file
        config.project_config_path = project_config_file
        config._load_config()

        # Project config should override user config
        assert config.get("backup.enabled") is True  # From project

        # User config should apply where project doesn't override
        assert config.get("batch.max_concurrent") == 6  # From user

    def test_load_invalid_json_user_config(self, tmp_path):
        """Test handling of invalid JSON in user config file."""
        # Create invalid JSON file
        user_config_file = tmp_path / "config.json"
        with open(user_config_file, 'w') as f:
            f.write("{invalid json content")

        # Should handle gracefully without crashing
        config = ConfigManager()
        config.user_config_path = user_config_file
        config._load_config()

        # Should fall back to defaults
        assert config.get("backup.enabled") is True

    def test_load_invalid_json_project_config(self, tmp_path):
        """Test handling of invalid JSON in project config file."""
        # Create invalid JSON file
        project_config_file = tmp_path / "project.json"
        with open(project_config_file, 'w') as f:
            f.write("not valid json at all")

        # Should handle gracefully without crashing
        config = ConfigManager()
        config.project_config_path = project_config_file
        config._load_config()

        # Should fall back to defaults
        assert config.get("backup.enabled") is True

    def test_save_user_config(self, tmp_path):
        """Test saving user configuration to file."""
        config = ConfigManager()
        config.user_config_path = tmp_path / "saved_config.json"

        # Modify config
        config.set("backup.enabled", False)
        config.set("custom.value", "test")

        # Save
        config.save_user_config()

        # Verify file was created
        assert config.user_config_path.exists()

        # Load and verify content
        with open(config.user_config_path, 'r') as f:
            saved_data = json.load(f)

        assert saved_data["backup"]["enabled"] is False
        assert saved_data["custom"]["value"] == "test"

    def test_save_project_config(self, tmp_path):
        """Test saving project configuration to file."""
        config = ConfigManager()
        config.project_config_path = tmp_path / ".exifanalyzer.json"

        # Modify config
        config.set("privacy.strip_gps_by_default", True)
        config.set("logging.level", "WARNING")

        # Save
        config.save_project_config()

        # Verify file was created
        assert config.project_config_path.exists()

        # Load and verify content
        with open(config.project_config_path, 'r') as f:
            saved_data = json.load(f)

        assert saved_data["privacy"]["strip_gps_by_default"] is True
        assert saved_data["logging"]["level"] == "WARNING"

    def test_save_user_config_creates_directory(self, tmp_path):
        """Test that saving user config creates parent directories."""
        config = ConfigManager()
        config.user_config_path = tmp_path / "nested" / "dir" / "config.json"

        # Directory doesn't exist yet
        assert not config.user_config_path.parent.exists()

        # Save should create directory
        config.save_user_config()

        # Verify directory and file created
        assert config.user_config_path.parent.exists()
        assert config.user_config_path.exists()

    def test_deep_merge_config(self):
        """Test deep merging of configuration dictionaries."""
        config = ConfigManager()

        # Set some initial values
        config.set("backup.enabled", True)
        config.set("backup.keep_count", 5)
        config.set("privacy.strip_gps_by_default", False)

        # Merge new config
        new_config = {
            "backup": {
                "enabled": False  # Override
                # keep_count not specified, should remain
            },
            "new_section": {
                "new_value": 123
            }
        }

        config._merge_config(new_config)

        # Overridden value
        assert config.get("backup.enabled") is False

        # Preserved value
        assert config.get("backup.keep_count") == 5

        # New section
        assert config.get("new_section.new_value") == 123

    def test_all_default_sections_present(self):
        """Test that all default config sections are present."""
        config = ConfigManager()

        required_sections = ["backup", "output", "privacy", "batch", "logging", "display", "integrity"]

        for section in required_sections:
            assert config.get(section) is not None
            assert isinstance(config.get(section), dict)

    def test_integrity_settings(self):
        """Test integrity-related configuration settings."""
        config = ConfigManager()

        # Check integrity settings exist and have expected types
        assert isinstance(config.get("integrity.jpeg_mse_threshold"), (int, float))
        assert isinstance(config.get("integrity.file_size_change_ratio"), (int, float))
        assert isinstance(config.get("integrity.file_hash_chunk_size"), int)

        # Check reasonable defaults
        assert config.get("integrity.jpeg_mse_threshold") > 0
        assert config.get("integrity.file_size_change_ratio") > 0
        assert config.get("integrity.file_hash_chunk_size") > 0

    def test_display_settings(self):
        """Test display-related configuration settings."""
        config = ConfigManager()

        # Check display settings exist
        assert isinstance(config.get("display.max_value_length"), int)
        assert isinstance(config.get("display.truncation_suffix_length"), int)
        assert isinstance(config.get("display.preview_image_size"), int)
        assert isinstance(config.get("display.status_bar_width"), int)

        # Check reasonable values
        assert config.get("display.max_value_length") > 0
        assert config.get("display.preview_image_size") > 0

    def test_save_user_config_permission_error(self, tmp_path):
        """Test saving user config with permission error."""
        import os
        config = ConfigManager()

        # Try to save to a read-only location (simulated)
        readonly_path = tmp_path / "readonly" / "config.json"
        readonly_path.parent.mkdir()

        # Make parent directory read-only (Windows: use attrib, Unix: chmod)
        if os.name == 'nt':
            # On Windows, we can't easily simulate this, so just test the path
            config.user_config_path = Path("/invalid:\\/path/config.json")
        else:
            readonly_path.parent.chmod(0o444)
            config.user_config_path = readonly_path

        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            config.save_user_config()

        assert "Cannot save configuration" in str(exc_info.value)

    def test_save_project_config_permission_error(self, tmp_path):
        """Test saving project config with permission error."""
        config = ConfigManager()

        # Invalid path should cause save to fail
        config.project_config_path = Path("/invalid:\\/path/config.json")

        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            config.save_project_config()

        assert "Cannot save project configuration" in str(exc_info.value)

    def test_validate_config_unexpected_error(self):
        """Test validation with unexpected errors."""
        config = ConfigManager()

        # Corrupt internal config structure to cause validation error
        config._config = None  # This will cause TypeError

        with pytest.raises(ValidationError):
            config.validate_config()
            # Should raise ValidationError (either specific or generic)

    def test_user_config_path_exists(self):
        """Test that user config path is properly set."""
        config = ConfigManager()

        # Path should exist and contain config.json
        assert config.user_config_path is not None
        assert 'config.json' in str(config.user_config_path)

        # Path should be in a reasonable location
        path_str = str(config.user_config_path).lower()
        assert 'exifanalyzer' in path_str or '.config' in path_str

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Provide temporary directory for tests."""
        return tmp_path
