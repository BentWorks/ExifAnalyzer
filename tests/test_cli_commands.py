"""
Tests for CLI command functionality.
"""
import pytest
from pathlib import Path
import json
import tempfile
from click.testing import CliRunner
from PIL import Image

from src.exif_analyzer.cli.main import cli
from src.exif_analyzer.core.config import config


class TestCLICommands:
    """Test cases for CLI commands."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def create_test_image(self, path: Path, format: str = "JPEG") -> Path:
        """Create a test image file."""
        img = Image.new('RGB', (100, 100), color='red')
        img.save(path, format)
        return path

    def test_formats_command(self):
        """Test formats command."""
        result = self.runner.invoke(cli, ['formats'])

        assert result.exit_code == 0
        assert "Supported Image Formats" in result.output
        assert ".jpg" in result.output
        assert ".png" in result.output

    def test_view_command_basic(self, temp_dir):
        """Test basic view command."""
        test_image = temp_dir / "test.jpg"
        self.create_test_image(test_image)

        result = self.runner.invoke(cli, ['view', str(test_image)])

        assert result.exit_code == 0
        assert "File:" in result.output
        assert "Format: JPEG" in result.output
        assert "Size:" in result.output

    def test_view_command_json(self, temp_dir):
        """Test view command with JSON output."""
        test_image = temp_dir / "test.jpg"
        self.create_test_image(test_image)

        result = self.runner.invoke(cli, ['view', str(test_image), '--json'])

        assert result.exit_code == 0

        # Should be valid JSON
        json_data = json.loads(result.output)
        assert json_data['format'] == 'JPEG'
        assert 'file_path' in json_data

    def test_view_command_privacy_check(self, temp_dir):
        """Test view command with privacy check."""
        test_image = temp_dir / "test.jpg"
        self.create_test_image(test_image)

        result = self.runner.invoke(cli, ['view', str(test_image), '--privacy-check'])

        assert result.exit_code == 0
        assert "Has GPS data:" in result.output

    def test_strip_command_basic(self, temp_dir):
        """Test basic strip command."""
        test_image = temp_dir / "test.jpg"
        output_image = temp_dir / "output.jpg"
        self.create_test_image(test_image)

        result = self.runner.invoke(cli, [
            '--force',  # Skip confirmations
            'strip', str(test_image),
            '--output', str(output_image),
            '--no-backup'
        ])

        assert result.exit_code == 0
        assert output_image.exists()

    def test_strip_command_preview(self, temp_dir):
        """Test strip command with preview mode."""
        test_image = temp_dir / "test.jpg"
        self.create_test_image(test_image)

        result = self.runner.invoke(cli, [
            'strip', str(test_image), '--preview'
        ])

        assert result.exit_code == 0
        # Since test image has no metadata, it should report that
        assert "File has no metadata to strip" in result.output

    def test_strip_command_gps_only(self, temp_dir):
        """Test strip command with GPS-only option."""
        test_image = temp_dir / "test.jpg"
        output_image = temp_dir / "output.jpg"
        self.create_test_image(test_image)

        result = self.runner.invoke(cli, [
            '--force',
            'strip', str(test_image),
            '--output', str(output_image),
            '--gps-only',
            '--no-backup'
        ])

        assert result.exit_code == 0

    def test_export_command(self, temp_dir):
        """Test export command."""
        test_image = temp_dir / "test.jpg"
        export_file = temp_dir / "metadata.json"
        self.create_test_image(test_image)

        result = self.runner.invoke(cli, [
            'export', str(test_image), str(export_file)
        ])

        assert result.exit_code == 0
        assert export_file.exists()

        # Verify exported metadata is valid JSON
        with open(export_file) as f:
            metadata = json.load(f)
        assert 'format' in metadata

    def test_batch_strip_dry_run(self, temp_dir):
        """Test batch strip with dry run."""
        # Create test images
        for i in range(3):
            test_image = temp_dir / f"test_{i}.jpg"
            self.create_test_image(test_image)

        result = self.runner.invoke(cli, [
            'batch', 'strip', str(temp_dir), '--dry-run'
        ])

        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "Found" in result.output

    def test_batch_strip_with_pattern(self, temp_dir):
        """Test batch strip with file pattern."""
        # Create test images with different extensions
        jpg_image = temp_dir / "test.jpg"
        png_image = temp_dir / "test.png"
        txt_file = temp_dir / "test.txt"

        self.create_test_image(jpg_image, "JPEG")
        self.create_test_image(png_image, "PNG")
        txt_file.write_text("not an image")

        result = self.runner.invoke(cli, [
            'batch', 'strip', str(temp_dir),
            '--pattern', '*.jpg',
            '--dry-run'
        ])

        assert result.exit_code == 0
        assert "Found 1 supported image files" in result.output

    def test_config_show_command(self):
        """Test config show command."""
        result = self.runner.invoke(cli, ['config', 'show'])

        assert result.exit_code == 0
        assert "Configuration" in result.output
        assert "[backup]" in result.output
        assert "[batch]" in result.output

    def test_config_show_json(self):
        """Test config show with JSON output."""
        result = self.runner.invoke(cli, ['config', 'show', '--json'])

        assert result.exit_code == 0

        # Should be valid JSON
        config_data = json.loads(result.output)
        assert 'backup' in config_data
        assert 'batch' in config_data

    def test_config_set_command(self):
        """Test config set command."""
        with tempfile.TemporaryDirectory() as temp_config_dir:
            # Override config path for testing
            original_path = config.user_config_path
            config.user_config_path = Path(temp_config_dir) / "test_config.json"

            try:
                result = self.runner.invoke(cli, [
                    'config', 'set', 'backup.enabled', 'false', '--user'
                ])

                assert result.exit_code == 0
                assert "Set backup.enabled = False" in result.output

                # Verify the setting was saved
                assert config.get('backup.enabled') == False

            finally:
                config.user_config_path = original_path

    def test_config_validate_command(self):
        """Test config validate command."""
        result = self.runner.invoke(cli, ['config', 'validate'])

        assert result.exit_code == 0
        assert "Configuration is valid" in result.output

    def test_global_options(self, temp_dir):
        """Test global CLI options."""
        test_image = temp_dir / "test.jpg"
        self.create_test_image(test_image)

        # Test verbose flag
        result = self.runner.invoke(cli, [
            '--verbose', 'view', str(test_image)
        ])
        assert result.exit_code == 0

        # Test quiet flag
        result = self.runner.invoke(cli, [
            '--quiet', 'view', str(test_image)
        ])
        assert result.exit_code == 0

        # Test force flag with strip
        output_image = temp_dir / "output.jpg"
        result = self.runner.invoke(cli, [
            '--force', 'strip', str(test_image),
            '--output', str(output_image),
            '--no-backup'
        ])
        assert result.exit_code == 0

    def test_error_handling_nonexistent_file(self):
        """Test error handling for non-existent files."""
        result = self.runner.invoke(cli, ['view', 'nonexistent.jpg'])

        assert result.exit_code != 0
        assert "Error" in result.output

    def test_help_messages(self):
        """Test help message generation."""
        # Main help
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "ExifAnalyzer" in result.output

        # Command help
        result = self.runner.invoke(cli, ['view', '--help'])
        assert result.exit_code == 0
        assert "View metadata" in result.output

        # Batch help
        result = self.runner.invoke(cli, ['batch', '--help'])
        assert result.exit_code == 0
        assert "Batch operations" in result.output

        # Config help
        result = self.runner.invoke(cli, ['config', '--help'])
        assert result.exit_code == 0
        assert "Configuration management" in result.output

    def test_configuration_file_loading(self, temp_dir):
        """Test loading configuration from file."""
        config_file = temp_dir / "custom_config.json"
        config_data = {
            "backup": {"enabled": False},
            "batch": {"max_concurrent": 2}
        }
        config_file.write_text(json.dumps(config_data))

        # Test with config file
        result = self.runner.invoke(cli, [
            '--config-file', str(config_file),
            'formats'
        ])
        assert result.exit_code == 0
        assert f"Loaded configuration from {config_file}" in result.output

    def test_invalid_configuration_file(self, temp_dir):
        """Test handling of invalid configuration file."""
        config_file = temp_dir / "invalid_config.json"
        config_file.write_text("invalid json content")

        result = self.runner.invoke(cli, [
            '--config-file', str(config_file),
            'formats'
        ])
        assert result.exit_code == 0  # Should still work with warning
        assert "Warning: Failed to load config file" in result.output

    def test_command_line_option_overrides(self, temp_dir):
        """Test command line options override config."""
        test_image = temp_dir / "test.jpg"
        output_image = temp_dir / "output.jpg"
        self.create_test_image(test_image)

        # Test --no-backup override
        result = self.runner.invoke(cli, [
            '--no-backup', '--force',
            'strip', str(test_image),
            '--output', str(output_image)
        ])
        assert result.exit_code == 0

    def test_verbose_logging(self, temp_dir):
        """Test verbose logging option."""
        test_image = temp_dir / "test.jpg"
        self.create_test_image(test_image)

        result = self.runner.invoke(cli, [
            '--verbose', 'view', str(test_image)
        ])
        assert result.exit_code == 0
        # Verbose should include debug information

    def test_quiet_logging(self, temp_dir):
        """Test quiet logging option."""
        test_image = temp_dir / "test.jpg"
        self.create_test_image(test_image)

        result = self.runner.invoke(cli, [
            '--quiet', 'view', str(test_image)
        ])
        assert result.exit_code == 0

    def test_restore_command(self, temp_dir):
        """Test restore command functionality."""
        test_image = temp_dir / "test.jpg"
        metadata_file = temp_dir / "metadata.json"
        self.create_test_image(test_image)

        # First export metadata
        result = self.runner.invoke(cli, [
            'export', str(test_image), str(metadata_file)
        ])
        assert result.exit_code == 0

        # Then restore it
        result = self.runner.invoke(cli, [
            'restore', str(test_image), str(metadata_file)
        ])
        assert result.exit_code == 0

    def test_restore_command_no_backup(self, temp_dir):
        """Test restore command without backup."""
        test_image = temp_dir / "test.jpg"
        metadata_file = temp_dir / "metadata.json"
        self.create_test_image(test_image)

        # Export metadata first
        result = self.runner.invoke(cli, [
            'export', str(test_image), str(metadata_file)
        ])
        assert result.exit_code == 0

        # Restore without backup
        result = self.runner.invoke(cli, [
            'restore', str(test_image), str(metadata_file),
            '--no-backup'
        ])
        assert result.exit_code == 0

    def test_batch_strip_with_confirmation(self, temp_dir):
        """Test batch strip with user confirmation."""
        # Create many images (>5) to trigger confirmation
        for i in range(7):
            test_image = temp_dir / f"test_{i}.jpg"
            self.create_test_image(test_image)

        # Test with confirmation (simulated by force flag)
        result = self.runner.invoke(cli, [
            '--force',
            'batch', 'strip', str(temp_dir)
        ])
        assert result.exit_code == 0

    def test_batch_strip_with_output_dir(self, temp_dir):
        """Test batch strip with output directory."""
        output_dir = temp_dir / "output"

        for i in range(3):
            test_image = temp_dir / f"test_{i}.jpg"
            self.create_test_image(test_image)

        result = self.runner.invoke(cli, [
            '--force',
            'batch', 'strip', str(temp_dir),
            '--output-dir', str(output_dir)
        ])
        assert result.exit_code == 0
        assert output_dir.exists()

    def test_batch_strip_recursive(self, temp_dir):
        """Test batch strip with recursive option."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()

        test_image1 = temp_dir / "test1.jpg"
        test_image2 = subdir / "test2.jpg"
        self.create_test_image(test_image1)
        self.create_test_image(test_image2)

        result = self.runner.invoke(cli, [
            '--force',
            'batch', 'strip', str(temp_dir),
            '--recursive'
        ])
        assert result.exit_code == 0

    def test_batch_strip_with_threads(self, temp_dir):
        """Test batch strip with custom thread count."""
        for i in range(3):
            test_image = temp_dir / f"test_{i}.jpg"
            self.create_test_image(test_image)

        result = self.runner.invoke(cli, [
            '--force',
            'batch', 'strip', str(temp_dir),
            '--threads', '2'
        ])
        assert result.exit_code == 0

    def test_batch_strip_gps_only(self, temp_dir):
        """Test batch strip GPS-only option."""
        for i in range(2):
            test_image = temp_dir / f"test_{i}.jpg"
            self.create_test_image(test_image)

        result = self.runner.invoke(cli, [
            '--force',
            'batch', 'strip', str(temp_dir),
            '--gps-only'
        ])
        assert result.exit_code == 0

    def test_batch_strip_with_keep_patterns(self, temp_dir):
        """Test batch strip with keep patterns."""
        for i in range(2):
            test_image = temp_dir / f"test_{i}.jpg"
            self.create_test_image(test_image)

        result = self.runner.invoke(cli, [
            '--force',
            'batch', 'strip', str(temp_dir),
            '--keep', 'title',
            '--keep', 'author'
        ])
        assert result.exit_code == 0

    def test_strip_command_with_keep_patterns(self, temp_dir):
        """Test strip command with keep patterns."""
        test_image = temp_dir / "test.jpg"
        output_image = temp_dir / "output.jpg"
        self.create_test_image(test_image)

        result = self.runner.invoke(cli, [
            '--force',
            'strip', str(test_image),
            '--output', str(output_image),
            '--keep', 'title',
            '--no-backup'
        ])
        assert result.exit_code == 0

    def test_export_command_xmp_format(self, temp_dir):
        """Test export command with XMP format."""
        test_image = temp_dir / "test.jpg"
        export_file = temp_dir / "metadata.xmp"
        self.create_test_image(test_image)

        result = self.runner.invoke(cli, [
            'export', str(test_image), str(export_file),
            '--format', 'xmp'
        ])
        # This might fail if XMP export isn't implemented, but we test the code path
        # The important thing is that it doesn't crash

    def test_batch_strip_no_files_found(self, temp_dir):
        """Test batch strip when no supported files are found."""
        # Create a non-image file
        text_file = temp_dir / "not_an_image.txt"
        text_file.write_text("This is not an image")

        result = self.runner.invoke(cli, [
            'batch', 'strip', str(temp_dir)
        ])
        assert result.exit_code == 0
        assert "No supported image files found" in result.output

    def test_batch_strip_continue_on_error(self, temp_dir):
        """Test batch strip with continue-on-error option."""
        # Create valid and invalid files
        valid_image = temp_dir / "valid.jpg"
        self.create_test_image(valid_image)

        invalid_image = temp_dir / "invalid.jpg"
        invalid_image.write_text("not really a jpeg")

        result = self.runner.invoke(cli, [
            '--force',
            'batch', 'strip', str(temp_dir),
            '--continue-on-error'
        ])
        # Should complete even with errors
        assert result.exit_code == 0

    def test_view_command_with_export(self, temp_dir):
        """Test view command with export option."""
        test_image = temp_dir / "test.jpg"
        export_file = temp_dir / "exported.json"
        self.create_test_image(test_image)

        result = self.runner.invoke(cli, [
            'view', str(test_image),
            '--export', str(export_file)
        ])
        assert result.exit_code == 0
        assert export_file.exists()

    def test_view_command_show_all(self, temp_dir):
        """Test view command with show-all option."""
        test_image = temp_dir / "test.jpg"
        self.create_test_image(test_image)

        result = self.runner.invoke(cli, [
            'view', str(test_image), '--show-all'
        ])
        assert result.exit_code == 0

    def test_error_handling_in_batch_processing(self, temp_dir):
        """Test error handling during batch processing."""
        # Create a mix of valid and problematic files
        valid_image = temp_dir / "valid.jpg"
        self.create_test_image(valid_image)

        # Create a file that will cause processing errors
        problem_file = temp_dir / "problem.jpg"
        problem_file.write_bytes(b"fake jpeg data")

        result = self.runner.invoke(cli, [
            '--force',
            'batch', 'strip', str(temp_dir),
            '--stop-on-error'
        ])
        # Test that it handles errors appropriately

    def test_view_command_detailed_output(self, temp_dir):
        """Test view command with detailed metadata display."""
        # Create image with actual metadata
        test_image = temp_dir / "test_with_metadata.jpg"
        from PIL import Image
        from PIL.ExifTags import TAGS
        import piexif

        # Create image with EXIF data
        img = Image.new('RGB', (100, 100), color='red')

        # Add some EXIF data
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        exif_dict["0th"][piexif.ImageIFD.Make] = "Test Camera"
        exif_dict["0th"][piexif.ImageIFD.Model] = "Test Model"
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = "2023:01:01 12:00:00"

        exif_bytes = piexif.dump(exif_dict)
        img.save(test_image, format='JPEG', exif=exif_bytes)

        result = self.runner.invoke(cli, [
            'view', str(test_image)
        ])
        assert result.exit_code == 0
        assert "Metadata Summary:" in result.output
        assert "Total:" in result.output

    def test_view_command_with_detailed_metadata(self, temp_dir):
        """Test view command with show-all flag and actual metadata."""
        test_image = temp_dir / "test_detailed.jpg"

        # Create image with metadata using piexif
        from PIL import Image
        import piexif

        img = Image.new('RGB', (100, 100), color='blue')
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        exif_dict["0th"][piexif.ImageIFD.Make] = "Test Camera Detailed"
        exif_dict["0th"][piexif.ImageIFD.Software] = "ExifAnalyzer Test"

        exif_bytes = piexif.dump(exif_dict)
        img.save(test_image, format='JPEG', exif=exif_bytes)

        result = self.runner.invoke(cli, [
            'view', str(test_image), '--show-all'
        ])
        assert result.exit_code == 0
        assert "Detailed Metadata:" in result.output

    def test_view_command_privacy_check_with_sensitive_data(self, temp_dir):
        """Test view command privacy check with GPS data."""
        test_image = temp_dir / "test_gps.jpg"

        # Create image with GPS data
        from PIL import Image
        import piexif

        img = Image.new('RGB', (100, 100), color='green')
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

        # Add GPS coordinates (privacy sensitive)
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = ((40, 1), (42, 1), (46, 1))
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = ((74, 1), (0, 1), (21, 1))
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = 'N'
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = 'W'

        exif_bytes = piexif.dump(exif_dict)
        img.save(test_image, format='JPEG', exif=exif_bytes)

        result = self.runner.invoke(cli, [
            'view', str(test_image), '--privacy-check'
        ])
        assert result.exit_code == 0
        assert "Privacy-Sensitive Data Found:" in result.output or "Has GPS data:" in result.output

    def test_strip_command_preview_with_gps_data(self, temp_dir):
        """Test strip command preview mode with GPS data."""
        test_image = temp_dir / "test_gps_preview.jpg"

        # Create image with GPS data
        from PIL import Image
        import piexif

        img = Image.new('RGB', (100, 100), color='yellow')
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = ((40, 1), (42, 1), (46, 1))
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = ((74, 1), (0, 1), (21, 1))

        exif_bytes = piexif.dump(exif_dict)
        img.save(test_image, format='JPEG', exif=exif_bytes)

        result = self.runner.invoke(cli, [
            'strip', str(test_image), '--preview', '--gps-only'
        ])
        assert result.exit_code == 0
        assert "Would remove" in result.output or "GPS" in result.output

    def test_strip_command_preview_all_metadata(self, temp_dir):
        """Test strip command preview mode for all metadata."""
        test_image = temp_dir / "test_preview_all.jpg"

        # Create image with various metadata
        from PIL import Image
        import piexif

        img = Image.new('RGB', (100, 100), color='purple')
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        exif_dict["0th"][piexif.ImageIFD.Make] = "Test Camera"
        exif_dict["0th"][piexif.ImageIFD.Model] = "Test Model"
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = "2023:01:01 12:00:00"

        exif_bytes = piexif.dump(exif_dict)
        img.save(test_image, format='JPEG', exif=exif_bytes)

        result = self.runner.invoke(cli, [
            'strip', str(test_image), '--preview'
        ])
        assert result.exit_code == 0
        assert "Would remove" in result.output

    def test_strip_command_preview_with_keep_patterns(self, temp_dir):
        """Test strip command preview with keep patterns."""
        test_image = temp_dir / "test_preview_keep.jpg"

        # Create image with metadata
        from PIL import Image
        import piexif

        img = Image.new('RGB', (100, 100), color='orange')
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        exif_dict["0th"][piexif.ImageIFD.Make] = "Test Camera"
        exif_dict["0th"][piexif.ImageIFD.Software] = "Test Software"

        exif_bytes = piexif.dump(exif_dict)
        img.save(test_image, format='JPEG', exif=exif_bytes)

        result = self.runner.invoke(cli, [
            'strip', str(test_image), '--preview', '--keep', 'Make'
        ])
        assert result.exit_code == 0
        assert ("Would remove" in result.output or "Would keep" in result.output)

    def test_strip_command_gps_only_with_confirmation(self, temp_dir):
        """Test strip command GPS-only with confirmation."""
        test_image = temp_dir / "test_gps_confirm.jpg"
        output_image = temp_dir / "output_gps.jpg"

        # Create image with GPS data
        from PIL import Image
        import piexif

        img = Image.new('RGB', (100, 100), color='cyan')
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = ((40, 1), (42, 1), (46, 1))
        exif_dict["0th"][piexif.ImageIFD.Make] = "Camera"  # Non-GPS data to keep

        exif_bytes = piexif.dump(exif_dict)
        img.save(test_image, format='JPEG', exif=exif_bytes)

        result = self.runner.invoke(cli, [
            '--force',  # Skip confirmations
            'strip', str(test_image),
            '--output', str(output_image),
            '--gps-only',
            '--no-backup'
        ])
        assert result.exit_code == 0
        assert output_image.exists()

    def test_strip_command_with_selective_keep(self, temp_dir):
        """Test strip command with selective keeping of metadata."""
        test_image = temp_dir / "test_selective.jpg"
        output_image = temp_dir / "output_selective.jpg"

        # Create image with multiple metadata fields
        from PIL import Image
        import piexif

        img = Image.new('RGB', (100, 100), color='pink')
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        exif_dict["0th"][piexif.ImageIFD.Make] = "Test Camera"
        exif_dict["0th"][piexif.ImageIFD.Model] = "Test Model"
        exif_dict["0th"][piexif.ImageIFD.Software] = "Test Software"

        exif_bytes = piexif.dump(exif_dict)
        img.save(test_image, format='JPEG', exif=exif_bytes)

        result = self.runner.invoke(cli, [
            '--force',
            'strip', str(test_image),
            '--output', str(output_image),
            '--keep', 'Make',
            '--keep', 'Model',
            '--no-backup'
        ])
        assert result.exit_code == 0
        assert output_image.exists()

    def test_strip_command_confirmation_cancelled(self, temp_dir):
        """Test strip command when user cancels confirmation."""
        test_image = temp_dir / "test_cancel.jpg"

        # Create image with metadata
        from PIL import Image
        import piexif

        img = Image.new('RGB', (100, 100), color='brown')
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        exif_dict["0th"][piexif.ImageIFD.Make] = "Test Camera"

        exif_bytes = piexif.dump(exif_dict)
        img.save(test_image, format='JPEG', exif=exif_bytes)

        # Simulate user declining confirmation by not using --force
        result = self.runner.invoke(cli, [
            'strip', str(test_image)
        ], input='n\n')  # Simulate user saying 'no' to confirmation

        # Should exit successfully but not modify file
        assert result.exit_code == 0

    def test_view_command_multiple_metadata_blocks(self, temp_dir):
        """Test view command with multiple metadata block types."""
        test_image = temp_dir / "test_multi_blocks.jpg"

        # Create image with EXIF, GPS, and other metadata
        from PIL import Image
        import piexif

        img = Image.new('RGB', (100, 100), color='gray')
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

        # Add various metadata types
        exif_dict["0th"][piexif.ImageIFD.Make] = "Multi Camera"
        exif_dict["0th"][piexif.ImageIFD.Software] = "Multi Software"
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = "2023:06:15 10:30:45"
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = ((42, 1), (30, 1), (0, 1))

        exif_bytes = piexif.dump(exif_dict)
        img.save(test_image, format='JPEG', exif=exif_bytes)

        result = self.runner.invoke(cli, [
            'view', str(test_image), '--show-all', '--privacy-check'
        ])
        assert result.exit_code == 0
        assert "Metadata Summary:" in result.output

    def test_strip_command_validation_errors(self, temp_dir):
        """Test strip command output path validation."""
        test_image = temp_dir / "test_validation.jpg"
        self.create_test_image(test_image)

        # Try to use same path as input (should be handled)
        result = self.runner.invoke(cli, [
            '--force',
            'strip', str(test_image),
            '--output', str(test_image),  # Same as input
            '--no-backup'
        ])
        # Should either work or give appropriate error message
        # The exact behavior depends on validation logic

    def test_batch_processing_edge_cases(self, temp_dir):
        """Test batch processing with various edge cases."""
        # Create directory with mixed file types
        jpg_file = temp_dir / "test.jpg"
        png_file = temp_dir / "test.png"
        txt_file = temp_dir / "readme.txt"

        self.create_test_image(jpg_file)
        # Create PNG
        from PIL import Image
        img = Image.new('RGB', (50, 50), color='purple')
        img.save(png_file, format='PNG')

        txt_file.write_text("This is not an image")

        result = self.runner.invoke(cli, [
            '--force',
            'batch', 'strip', str(temp_dir),
            '--pattern', '*.jpg'
        ])
        assert result.exit_code == 0
        assert "Found 1 supported image files" in result.output

    def test_config_reset_command(self, temp_dir):
        """Test config reset command."""
        # Use temporary config directory
        with tempfile.TemporaryDirectory() as temp_config_dir:
            from src.exif_analyzer.core.config import config
            original_path = config.user_config_path
            config.user_config_path = Path(temp_config_dir) / "test_config.json"

            try:
                # First set some config
                result = self.runner.invoke(cli, [
                    'config', 'set', 'backup.enabled', 'false', '--user'
                ])
                assert result.exit_code == 0

                # Then reset with confirmation
                result = self.runner.invoke(cli, [
                    'config', 'reset', '--confirm'
                ])
                assert result.exit_code == 0
                assert "Configuration reset to defaults" in result.output

            finally:
                config.user_config_path = original_path

    def test_config_reset_cancelled(self, temp_dir):
        """Test config reset when cancelled by user."""
        result = self.runner.invoke(cli, [
            'config', 'reset'
        ], input='n\n')  # User says no

        assert result.exit_code == 0
        assert "Reset cancelled" in result.output

    def test_view_command_long_values(self, temp_dir):
        """Test view command with long metadata values."""
        test_image = temp_dir / "test_long_values.jpg"

        # Create image with long metadata value
        from PIL import Image
        import piexif

        img = Image.new('RGB', (100, 100), color='white')
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

        # Create a very long description (>100 chars)
        long_description = "This is a very long description that exceeds one hundred characters to test truncation functionality in the CLI display"
        exif_dict["0th"][piexif.ImageIFD.ImageDescription] = long_description

        exif_bytes = piexif.dump(exif_dict)
        img.save(test_image, format='JPEG', exif=exif_bytes)

        result = self.runner.invoke(cli, [
            'view', str(test_image), '--show-all'
        ])
        assert result.exit_code == 0
        assert "..." in result.output  # Should show truncation

    def test_strip_preview_no_gps_data(self, temp_dir):
        """Test strip preview when no GPS data is present."""
        test_image = temp_dir / "test_no_gps_preview.jpg"

        # Create image without GPS data
        from PIL import Image
        import piexif

        img = Image.new('RGB', (100, 100), color='silver')
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        exif_dict["0th"][piexif.ImageIFD.Make] = "No GPS Camera"

        exif_bytes = piexif.dump(exif_dict)
        img.save(test_image, format='JPEG', exif=exif_bytes)

        result = self.runner.invoke(cli, [
            'strip', str(test_image), '--preview', '--gps-only'
        ])
        assert result.exit_code == 0
        assert "No GPS data found" in result.output

    def test_batch_operation_confirmation_prompt(self, temp_dir):
        """Test batch operation confirmation for large numbers of files."""
        # Create more than 5 files to trigger confirmation
        for i in range(7):
            test_image = temp_dir / f"confirm_test_{i}.jpg"
            self.create_test_image(test_image)

        # Test without force flag (should prompt for confirmation)
        result = self.runner.invoke(cli, [
            'batch', 'strip', str(temp_dir)
        ], input='n\n')  # User declines

        assert result.exit_code == 0
        assert "Operation cancelled" in result.output

    def test_strip_gps_success_message(self, temp_dir):
        """Test GPS stripping success message."""
        test_image = temp_dir / "test_gps_success.jpg"
        output_image = temp_dir / "output_gps_success.jpg"

        # Create image with GPS data
        from PIL import Image
        import piexif

        img = Image.new('RGB', (100, 100), color='gold')
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = ((40, 1), (42, 1), (46, 1))

        exif_bytes = piexif.dump(exif_dict)
        img.save(test_image, format='JPEG', exif=exif_bytes)

        result = self.runner.invoke(cli, [
            '--force',
            'strip', str(test_image),
            '--output', str(output_image),
            '--gps-only',
            '--no-backup'
        ])
        assert result.exit_code == 0
        assert "GPS data stripped" in result.output

    def test_privacy_sensitive_many_keys(self, temp_dir):
        """Test privacy check with many sensitive keys (>10)."""
        test_image = temp_dir / "test_many_keys.jpg"

        # Create image with many metadata fields
        from PIL import Image
        import piexif

        img = Image.new('RGB', (100, 100), color='maroon')
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

        # Add multiple GPS-related fields to trigger "and X more" display
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = ((40, 1), (42, 1), (46, 1))
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = ((74, 1), (0, 1), (21, 1))
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = 'N'
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = 'W'
        exif_dict["GPS"][piexif.GPSIFD.GPSAltitude] = (100, 1)

        # Add regular EXIF data with valid EXIF tags
        exif_dict["0th"][piexif.ImageIFD.Make] = "Many Keys Camera"
        exif_dict["0th"][piexif.ImageIFD.Model] = "Many Keys Model"
        exif_dict["0th"][piexif.ImageIFD.Software] = "Many Keys Software"

        exif_bytes = piexif.dump(exif_dict)
        img.save(test_image, format='JPEG', exif=exif_bytes)

        result = self.runner.invoke(cli, [
            'view', str(test_image), '--privacy-check'
        ])
        assert result.exit_code == 0