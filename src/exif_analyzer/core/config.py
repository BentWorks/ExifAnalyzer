"""
Configuration management for ExifAnalyzer.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
import os

from .exceptions import ValidationError
from .logger import logger


class ConfigManager:
    """
    Manages configuration settings for ExifAnalyzer.

    Supports both user-specific and project-specific configuration files.
    """

    DEFAULT_CONFIG = {
        "backup": {
            "enabled": True,
            "directory": None,  # None means same directory as original
            "keep_count": 5,
            "auto_cleanup": True
        },
        "output": {
            "default_format": "json",
            "preserve_timestamps": True,
            "compression_quality": "keep"
        },
        "privacy": {
            "strip_gps_by_default": False,
            "warn_before_strip": True,
            "privacy_sensitive_keys": [
                "gps", "location", "geotag", "coordinate",
                "make", "model", "serial", "owner", "artist", "creator"
            ]
        },
        "batch": {
            "max_concurrent": 4,
            "show_progress": True,
            "continue_on_error": True,
            "default_recursive": False
        },
        "logging": {
            "level": "INFO",
            "file_logging": False,
            "log_directory": "logs"
        }
    }

    def __init__(self):
        """Initialize configuration manager."""
        self.user_config_path = self._get_user_config_path()
        self.project_config_path = Path.cwd() / ".exifanalyzer.json"
        self._config = self.DEFAULT_CONFIG.copy()
        self._load_config()

    def _get_user_config_path(self) -> Path:
        """Get user-specific configuration file path."""
        if os.name == 'nt':  # Windows
            config_dir = Path(os.environ.get('APPDATA', Path.home())) / "ExifAnalyzer"
        else:  # macOS/Linux
            config_dir = Path.home() / ".config" / "exifanalyzer"

        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"

    def _load_config(self) -> None:
        """Load configuration from files."""
        # Load user config first
        if self.user_config_path.exists():
            try:
                with open(self.user_config_path, 'r') as f:
                    user_config = json.load(f)
                self._merge_config(user_config)
                logger.debug(f"Loaded user config from {self.user_config_path}")
            except Exception as e:
                logger.warning(f"Failed to load user config: {e}")

        # Load project config (overrides user config)
        if self.project_config_path.exists():
            try:
                with open(self.project_config_path, 'r') as f:
                    project_config = json.load(f)
                self._merge_config(project_config)
                logger.debug(f"Loaded project config from {self.project_config_path}")
            except Exception as e:
                logger.warning(f"Failed to load project config: {e}")

    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """Merge new configuration with existing configuration."""
        def deep_merge(base: Dict, update: Dict) -> Dict:
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
            return base

        deep_merge(self._config, new_config)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'backup.enabled')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        try:
            keys = key.split('.')
            value = self._config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'backup.enabled')
            value: Value to set
        """
        keys = key.split('.')
        config = self._config

        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set the final key
        config[keys[-1]] = value

    def save_user_config(self) -> None:
        """Save current configuration to user config file."""
        try:
            self.user_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.user_config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
            logger.info(f"Saved user configuration to {self.user_config_path}")
        except Exception as e:
            logger.error(f"Failed to save user config: {e}")
            raise ValidationError(f"Cannot save configuration: {e}")

    def save_project_config(self) -> None:
        """Save current configuration to project config file."""
        try:
            with open(self.project_config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
            logger.info(f"Saved project configuration to {self.project_config_path}")
        except Exception as e:
            logger.error(f"Failed to save project config: {e}")
            raise ValidationError(f"Cannot save project configuration: {e}")

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self._config = self.DEFAULT_CONFIG.copy()
        logger.info("Configuration reset to defaults")

    def validate_config(self) -> bool:
        """Validate current configuration."""
        try:
            # Validate backup settings
            backup_enabled = self.get("backup.enabled")
            if not isinstance(backup_enabled, bool):
                raise ValidationError("backup.enabled must be boolean")

            keep_count = self.get("backup.keep_count")
            if not isinstance(keep_count, int) or keep_count < 0:
                raise ValidationError("backup.keep_count must be non-negative integer")

            # Validate batch settings
            max_concurrent = self.get("batch.max_concurrent")
            if not isinstance(max_concurrent, int) or max_concurrent < 1:
                raise ValidationError("batch.max_concurrent must be positive integer")

            # Validate logging level
            log_level = self.get("logging.level")
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if log_level not in valid_levels:
                raise ValidationError(f"logging.level must be one of {valid_levels}")

            return True

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Configuration validation failed: {e}")

    def get_backup_directory(self, file_path: Path) -> Path:
        """Get backup directory for a given file."""
        backup_dir = self.get("backup.directory")
        if backup_dir:
            return Path(backup_dir)
        return file_path.parent

    def should_create_backup(self) -> bool:
        """Check if backups should be created."""
        return self.get("backup.enabled", True)

    def get_privacy_patterns(self) -> list:
        """Get privacy-sensitive key patterns."""
        return self.get("privacy.privacy_sensitive_keys", [])

    def should_warn_before_strip(self) -> bool:
        """Check if user should be warned before stripping metadata."""
        return self.get("privacy.warn_before_strip", True)

    def get_max_concurrent_operations(self) -> int:
        """Get maximum concurrent operations for batch processing."""
        return self.get("batch.max_concurrent", 4)

    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary."""
        return self._config.copy()

    def __str__(self) -> str:
        """String representation of configuration."""
        return json.dumps(self._config, indent=2)

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"ConfigManager(user_config={self.user_config_path}, project_config={self.project_config_path})"


# Global configuration instance
config = ConfigManager()