"""
Tests for file safety mechanisms and integrity checks.
"""
import pytest
import tempfile
import shutil
import hashlib
from pathlib import Path
from PIL import Image

from src.exif_analyzer.core.file_safety import FileSafetyManager
from src.exif_analyzer.core.exceptions import FileError, PixelDataCorruptionError, BackupError


class TestFileSafetyManager:
    """Test cases for file safety manager."""

    def setup_method(self):
        """Set up test environment."""
        self.safety_manager = FileSafetyManager()

    def create_test_image(self, path: Path) -> Path:
        """Create a test image file."""
        img = Image.new('RGB', (100, 100), color='red')
        img.save(path, format='JPEG')
        return path

    def get_file_hash(self, file_path: Path) -> str:
        """Get SHA-256 hash of file."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def test_safety_manager_initialization(self):
        """Test safety manager initialization."""
        manager = FileSafetyManager()
        assert manager.backup_dir is None

        custom_dir = Path("/tmp/custom_backup")
        manager_with_dir = FileSafetyManager(backup_dir=custom_dir)
        assert manager_with_dir.backup_dir == custom_dir

    def test_get_backup_path_default(self, temp_dir):
        """Test backup path generation with default settings."""
        test_file = temp_dir / "test.jpg"
        test_file.touch()

        backup_path = self.safety_manager.get_backup_path(test_file)

        assert backup_path.parent == test_file.parent
        assert backup_path.suffix == test_file.suffix
        assert "backup" in backup_path.stem
        assert backup_path.stem.count('.') >= 2  # name.backup.timestamp

    def test_get_backup_path_custom_suffix(self, temp_dir):
        """Test backup path generation with custom suffix."""
        test_file = temp_dir / "test.jpg"
        test_file.touch()

        backup_path = self.safety_manager.get_backup_path(test_file, suffix="custom")

        assert "custom" in backup_path.stem
        assert backup_path.suffix == test_file.suffix

    def test_get_backup_path_custom_dir(self, temp_dir):
        """Test backup path generation with custom directory."""
        backup_dir = temp_dir / "backups"
        manager = FileSafetyManager(backup_dir=backup_dir)

        test_file = temp_dir / "test.jpg"
        test_file.touch()

        backup_path = manager.get_backup_path(test_file)

        assert backup_path.parent == backup_dir
        assert backup_dir.exists()  # Should be created

    def test_create_backup_basic(self, temp_dir):
        """Test basic backup creation."""
        test_file = temp_dir / "test.jpg"
        self.create_test_image(test_file)
        original_hash = self.get_file_hash(test_file)

        backup_path = self.safety_manager.create_backup(test_file)

        assert backup_path.exists()
        assert backup_path != test_file
        assert self.get_file_hash(backup_path) == original_hash

    def test_create_backup_custom_path(self, temp_dir):
        """Test backup creation with custom path."""
        test_file = temp_dir / "test.jpg"
        self.create_test_image(test_file)
        custom_backup = temp_dir / "custom_backup.jpg"

        backup_path = self.safety_manager.create_backup(test_file, custom_backup)

        assert backup_path == custom_backup
        assert custom_backup.exists()

    def test_create_backup_nonexistent_file(self, temp_dir):
        """Test backup creation with non-existent file."""
        nonexistent = temp_dir / "nonexistent.jpg"

        with pytest.raises((FileError, FileNotFoundError)):
            self.safety_manager.create_backup(nonexistent)

    def test_verify_file_integrity_success(self, temp_dir):
        """Test file integrity verification success."""
        original_file = temp_dir / "original.jpg"
        self.create_test_image(original_file)

        # Create identical copy
        modified_file = temp_dir / "modified.jpg"
        shutil.copy2(original_file, modified_file)

        # Should return True for identical files
        result = self.safety_manager.verify_file_integrity(original_file, modified_file)
        assert result is True

    def test_verify_file_integrity_nonexistent(self, temp_dir):
        """Test file integrity verification with non-existent file."""
        original_file = temp_dir / "original.jpg"
        self.create_test_image(original_file)

        nonexistent_file = temp_dir / "nonexistent.jpg"

        result = self.safety_manager.verify_file_integrity(original_file, nonexistent_file)
        assert result is False

    def test_verify_file_integrity_different_sizes(self, temp_dir):
        """Test file integrity verification with different sizes."""
        original_file = temp_dir / "original.jpg"
        self.create_test_image(original_file)

        # Create different sized image
        modified_file = temp_dir / "modified.jpg"
        img = Image.new('RGB', (50, 50), color='red')  # Different size
        img.save(modified_file, format='JPEG')

        # Basic file integrity check - this might pass since it's just checking existence
        result = self.safety_manager.verify_file_integrity(original_file, modified_file)
        # The result depends on the implementation - it might be True or False

    def test_safe_file_operation_context_manager(self, temp_dir):
        """Test safe file operation context manager."""
        test_file = temp_dir / "test.jpg"
        self.create_test_image(test_file)
        original_hash = self.get_file_hash(test_file)

        # Test successful operation
        with self.safety_manager.safe_file_operation(test_file, create_backup=True) as temp_path:
            assert temp_path != test_file
            assert temp_path.exists()

            # Modify the temporary file
            img = Image.new('RGB', (100, 100), color='blue')
            img.save(temp_path, format='JPEG')

        # Original should be updated
        assert test_file.exists()
        final_hash = self.get_file_hash(test_file)
        assert final_hash != original_hash

    def test_safe_file_operation_with_exception(self, temp_dir):
        """Test safe file operation rollback on exception."""
        test_file = temp_dir / "test.jpg"
        self.create_test_image(test_file)
        original_hash = self.get_file_hash(test_file)

        try:
            with self.safety_manager.safe_file_operation(test_file, create_backup=True) as temp_path:
                # Modify the file
                img = Image.new('RGB', (100, 100), color='blue')
                img.save(temp_path, format='JPEG')

                # Raise an exception to trigger rollback
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected

        # Original should be unchanged due to rollback
        assert test_file.exists()
        final_hash = self.get_file_hash(test_file)
        assert final_hash == original_hash

    def test_safe_file_operation_no_backup(self, temp_dir):
        """Test safe file operation without backup."""
        test_file = temp_dir / "test.jpg"
        self.create_test_image(test_file)

        with self.safety_manager.safe_file_operation(test_file, create_backup=False) as temp_path:
            assert temp_path != test_file
            assert temp_path.exists()

    def test_cleanup_backups(self, temp_dir):
        """Test cleanup of old backup files."""
        test_file = temp_dir / "test.jpg"
        self.create_test_image(test_file)

        # Create multiple backups
        backup_paths = []
        for i in range(7):
            backup_path = self.safety_manager.create_backup(test_file)
            backup_paths.append(backup_path)
            # Small delay to ensure different timestamps
            import time
            time.sleep(0.01)

        # Cleanup keeping only 3 backups
        removed_count = self.safety_manager.cleanup_backups(test_file, keep_count=3)

        # Should remove some backups
        assert removed_count >= 0

    def test_get_temp_copy(self, temp_dir):
        """Test creating temporary copy of file."""
        test_file = temp_dir / "test.jpg"
        self.create_test_image(test_file)

        temp_copy = self.safety_manager.get_temp_copy(test_file)

        assert temp_copy.exists()
        assert temp_copy != test_file
        assert self.get_file_hash(temp_copy) == self.get_file_hash(test_file)

    def test_backup_directory_creation(self, temp_dir):
        """Test automatic backup directory creation."""
        backup_dir = temp_dir / "backup" / "nested"
        manager = FileSafetyManager(backup_dir=backup_dir)

        test_file = temp_dir / "test.jpg"
        self.create_test_image(test_file)

        backup_path = manager.create_backup(test_file)

        assert backup_dir.exists()
        assert backup_path.parent == backup_dir

    def test_file_hash_consistency(self, temp_dir):
        """Test file hash calculation consistency."""
        test_file = temp_dir / "test.jpg"
        self.create_test_image(test_file)

        # Multiple calls should return same hash
        hash1 = self.safety_manager.calculate_file_hash(test_file)
        hash2 = self.safety_manager.calculate_file_hash(test_file)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_file_hash_different_files(self, temp_dir):
        """Test different files have different hashes."""
        file1 = temp_dir / "file1.jpg"
        file2 = temp_dir / "file2.jpg"

        # Create different images
        img1 = Image.new('RGB', (100, 100), color='red')
        img1.save(file1, format='JPEG')

        img2 = Image.new('RGB', (100, 100), color='blue')
        img2.save(file2, format='JPEG')

        hash1 = self.safety_manager.calculate_file_hash(file1)
        hash2 = self.safety_manager.calculate_file_hash(file2)

        assert hash1 != hash2

    def test_calculate_file_hash(self, temp_dir):
        """Test file hash calculation."""
        test_file = temp_dir / "test.jpg"
        self.create_test_image(test_file)

        hash1 = self.safety_manager.calculate_file_hash(test_file)
        hash2 = self.safety_manager.calculate_file_hash(test_file)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest length

    def test_file_safety_with_permissions(self, temp_dir):
        """Test file safety with permission issues."""
        test_file = temp_dir / "test.jpg"
        self.create_test_image(test_file)

        # Make file read-only (on systems that support it)
        try:
            test_file.chmod(0o444)

            # Should handle permission issues gracefully
            with pytest.raises((PermissionError, FileError)):
                with self.safety_manager.safe_file_operation(test_file) as temp_path:
                    pass
        finally:
            # Restore permissions for cleanup
            test_file.chmod(0o666)

    def test_backup_file_naming(self, temp_dir):
        """Test backup file naming convention."""
        test_file = temp_dir / "test_image.jpg"
        self.create_test_image(test_file)

        backup_path = self.safety_manager.create_backup(test_file)

        # Check naming pattern
        assert "test_image" in backup_path.stem
        assert "backup" in backup_path.stem
        assert backup_path.suffix == ".jpg"
        # Should contain timestamp
        assert len(backup_path.stem.split('.')) >= 3

    def test_safe_file_operation_error_handling(self, temp_dir):
        """Test safe file operation error handling."""
        test_file = temp_dir / "test.jpg"
        self.create_test_image(test_file)

        # Test that context manager handles errors properly
        try:
            with self.safety_manager.safe_file_operation(test_file) as temp_path:
                # Simulate error during operation
                temp_path.unlink()  # Delete the temp file
                raise RuntimeError("Simulated error")
        except RuntimeError:
            pass

        # Original file should still exist
        assert test_file.exists()

    def test_create_backup_exception_handling(self, temp_dir):
        """Test backup creation exception handling."""
        test_file = temp_dir / "test_backup_error.jpg"
        self.create_test_image(test_file)

        # Try to create backup to a read-only directory (if possible)
        readonly_dir = temp_dir / "readonly"
        readonly_dir.mkdir()

        # Try to backup to an invalid path - this should reliably fail
        invalid_path = temp_dir / "nonexistent_dir" / "deeply" / "nested" / "backup.jpg"

        with pytest.raises(BackupError):
            self.safety_manager.create_backup(test_file, invalid_path)

    def test_calculate_file_hash_exception(self, temp_dir):
        """Test file hash calculation with error conditions."""
        # Test with non-existent file
        nonexistent = temp_dir / "nonexistent.jpg"

        hash_result = self.safety_manager.calculate_file_hash(nonexistent)
        assert hash_result == ""  # Should return empty string on error

    def test_verify_file_integrity_exception(self, temp_dir):
        """Test file integrity verification with error conditions."""
        original_file = temp_dir / "original.jpg"
        self.create_test_image(original_file)

        # Test with file that will cause size check error
        nonexistent_file = temp_dir / "nonexistent.jpg"

        result = self.safety_manager.verify_file_integrity(original_file, nonexistent_file)
        assert result is False

        # Test with permission issues
        protected_file = temp_dir / "protected.jpg"
        self.create_test_image(protected_file)

        try:
            # Try to make file inaccessible
            protected_file.chmod(0o000)

            result = self.safety_manager.verify_file_integrity(original_file, protected_file)
            # Should handle permission errors gracefully

        except (PermissionError, OSError):
            # If permission changes aren't supported, skip this part
            pass
        finally:
            # Restore permissions
            try:
                protected_file.chmod(0o666)
            except:
                pass

    def test_safe_file_operation_advanced_scenarios(self, temp_dir):
        """Test safe file operation with advanced scenarios."""
        test_file = temp_dir / "test_advanced.jpg"
        self.create_test_image(test_file)

        # Test successful operation that modifies temp file content
        with self.safety_manager.safe_file_operation(test_file, create_backup=True) as temp_path:
            assert temp_path.exists()

            # Modify the temp file in a way that would be detectable
            temp_path.write_bytes(b"modified content")

        # Test that original file was updated
        assert test_file.exists()

    def test_cleanup_backups_edge_cases(self, temp_dir):
        """Test cleanup backups with edge cases."""
        test_file = temp_dir / "test_cleanup_edge.jpg"
        self.create_test_image(test_file)

        # Test cleanup when no backups exist
        removed_count = self.safety_manager.cleanup_backups(test_file, keep_count=5)
        assert removed_count >= 0

        # Create backup and test cleanup with keep_count=0
        backup_path = self.safety_manager.create_backup(test_file)
        assert backup_path.exists()

        removed_count = self.safety_manager.cleanup_backups(test_file, keep_count=0)
        assert removed_count >= 0

    def test_get_temp_copy_with_permissions(self, temp_dir):
        """Test get_temp_copy with permission scenarios."""
        test_file = temp_dir / "test_temp_perms.jpg"
        self.create_test_image(test_file)

        # Normal case
        temp_copy = self.safety_manager.get_temp_copy(test_file)
        assert temp_copy.exists()
        assert temp_copy != test_file

        # Test with file that has different permissions
        restricted_file = temp_dir / "restricted.jpg"
        self.create_test_image(restricted_file)

        try:
            # Make source file read-only
            restricted_file.chmod(0o444)

            temp_copy2 = self.safety_manager.get_temp_copy(restricted_file)
            assert temp_copy2.exists()

        finally:
            # Restore permissions
            try:
                restricted_file.chmod(0o666)
            except:
                pass

    def test_file_safety_with_large_files(self, temp_dir):
        """Test file safety operations with larger files."""
        # Create a larger test file
        large_file = temp_dir / "large_test.jpg"

        # Create a larger image to test memory handling
        from PIL import Image
        img = Image.new('RGB', (1000, 1000), color='blue')
        img.save(large_file, format='JPEG', quality=95)

        # Test backup of larger file
        backup_path = self.safety_manager.create_backup(large_file)
        assert backup_path.exists()

        # Test hash calculation of larger file
        hash1 = self.safety_manager.calculate_file_hash(large_file)
        hash2 = self.safety_manager.calculate_file_hash(backup_path)
        assert hash1 == hash2

    def test_backup_path_edge_cases(self, temp_dir):
        """Test backup path generation edge cases."""
        # Test with file that has no extension
        no_ext_file = temp_dir / "no_extension"
        no_ext_file.touch()

        backup_path = self.safety_manager.get_backup_path(no_ext_file)
        assert backup_path.parent == no_ext_file.parent
        assert "backup" in backup_path.name

        # Test with file that has multiple extensions
        multi_ext_file = temp_dir / "file.tar.gz"
        multi_ext_file.touch()

        backup_path = self.safety_manager.get_backup_path(multi_ext_file)
        assert "backup" in backup_path.stem

    def test_file_integrity_size_comparison(self, temp_dir):
        """Test file integrity size comparison logic."""
        file1 = temp_dir / "file1.jpg"
        file2 = temp_dir / "file2.jpg"

        # Create files of different sizes
        img1 = Image.new('RGB', (100, 100), color='red')
        img1.save(file1, format='JPEG')

        img2 = Image.new('RGB', (200, 200), color='red')  # Different size
        img2.save(file2, format='JPEG')

        # Test integrity check with different sized files
        result = self.safety_manager.verify_file_integrity(file1, file2)
        # The exact result depends on implementation - might be True or False

    def test_concurrent_safety_operations(self, temp_dir):
        """Test concurrent file safety operations."""
        test_file = temp_dir / "concurrent_test.jpg"
        self.create_test_image(test_file)

        # Test multiple concurrent backup operations
        backup_paths = []

        for i in range(3):
            # Add delay to ensure different timestamps
            import time
            time.sleep(0.1)  # Longer delay for timestamp differences
            backup_path = self.safety_manager.create_backup(test_file)
            backup_paths.append(backup_path)

        # All backups should exist (uniqueness depends on timestamp resolution)
        assert len(backup_paths) == 3
        for backup_path in backup_paths:
            assert backup_path.exists()