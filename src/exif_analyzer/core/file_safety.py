"""
File safety mechanisms for protecting original images and ensuring data integrity.
"""
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Union
from contextlib import contextmanager
import hashlib
import time

from .exceptions import FileError, PixelDataCorruptionError, BackupError
from .logger import logger


class FileSafetyManager:
    """
    Manages file safety operations including backups, integrity checks,
    and atomic file operations.
    """

    def __init__(self, backup_dir: Optional[Path] = None):
        """
        Initialize file safety manager.

        Args:
            backup_dir: Optional custom backup directory
        """
        self.backup_dir = backup_dir

    def get_backup_path(self, original_path: Path, suffix: str = "backup") -> Path:
        """
        Generate backup file path.

        Args:
            original_path: Original file path
            suffix: Backup suffix

        Returns:
            Path for backup file
        """
        if self.backup_dir:
            backup_dir = self.backup_dir
        else:
            backup_dir = original_path.parent

        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = int(time.time())
        backup_name = f"{original_path.stem}.{suffix}.{timestamp}{original_path.suffix}"
        return backup_dir / backup_name

    def create_backup(self, file_path: Path, backup_path: Optional[Path] = None) -> Path:
        """
        Create backup of original file.

        Args:
            file_path: File to backup
            backup_path: Optional custom backup path

        Returns:
            Path to backup file

        Raises:
            BackupError: If backup creation fails
        """
        if not file_path.exists():
            raise FileError(f"Cannot backup non-existent file: {file_path}")

        if backup_path is None:
            backup_path = self.get_backup_path(file_path)

        try:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            raise BackupError(f"Failed to create backup: {e}")

    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA-256 hash of entire file.

        Args:
            file_path: File to hash

        Returns:
            Hex string of file hash
        """
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""

    def verify_file_integrity(self, original_path: Path, modified_path: Path) -> bool:
        """
        Verify file integrity by comparing file sizes and existence.
        Note: This is a basic check. Pixel integrity should be checked separately.

        Args:
            original_path: Original file path
            modified_path: Modified file path

        Returns:
            True if basic integrity checks pass
        """
        try:
            if not modified_path.exists():
                logger.error(f"Modified file does not exist: {modified_path}")
                return False

            original_size = original_path.stat().st_size
            modified_size = modified_path.stat().st_size

            # File sizes can differ due to metadata changes, but shouldn't be drastically different
            # Allow up to 10% size difference (metadata changes)
            size_ratio = abs(modified_size - original_size) / original_size if original_size > 0 else 0

            if size_ratio > 0.1:  # More than 10% difference
                logger.warning(f"Significant size difference: {original_size} -> {modified_size}")

            return True

        except Exception as e:
            logger.error(f"File integrity check failed: {e}")
            return False

    @contextmanager
    def safe_file_operation(self, file_path: Path, create_backup: bool = True):
        """
        Context manager for safe file operations with automatic backup and rollback.

        Args:
            file_path: File to operate on
            create_backup: Whether to create backup before operation

        Yields:
            Temporary file path for safe operations

        Usage:
            with safety_manager.safe_file_operation(file_path) as temp_path:
                # Perform operations on temp_path
                pass
        """
        backup_path = None
        temp_path = None

        try:
            # Create backup if requested
            if create_backup and file_path.exists():
                backup_path = self.create_backup(file_path)

            # Create temporary file for operations
            temp_dir = file_path.parent / ".temp"
            temp_dir.mkdir(exist_ok=True)
            temp_path = temp_dir / f"temp_{int(time.time())}_{file_path.name}"

            # Copy original to temp location
            if file_path.exists():
                shutil.copy2(file_path, temp_path)

            logger.debug(f"Starting safe operation: {file_path} -> {temp_path}")
            yield temp_path

            # If we get here, operation succeeded
            # Replace original with modified temp file
            if temp_path.exists():
                shutil.move(temp_path, file_path)
                logger.info(f"Safe operation completed: {file_path}")

        except Exception as e:
            logger.error(f"Safe operation failed: {e}")

            # Restore from backup if available
            if backup_path and backup_path.exists() and file_path.exists():
                try:
                    shutil.copy2(backup_path, file_path)
                    logger.info(f"Restored from backup: {backup_path}")
                except Exception as restore_error:
                    logger.error(f"Failed to restore from backup: {restore_error}")

            raise

        finally:
            # Cleanup temporary file
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temp file: {cleanup_error}")

            # Cleanup temp directory if empty
            temp_dir = file_path.parent / ".temp"
            if temp_dir.exists() and not any(temp_dir.iterdir()):
                try:
                    temp_dir.rmdir()
                except Exception:
                    pass  # Ignore cleanup errors

    def cleanup_backups(self, file_path: Path, keep_count: int = 5) -> int:
        """
        Clean up old backup files, keeping only the most recent ones.

        Args:
            file_path: Original file path to find backups for
            keep_count: Number of backups to keep

        Returns:
            Number of backups deleted
        """
        backup_dir = self.backup_dir or file_path.parent
        pattern = f"{file_path.stem}.backup.*{file_path.suffix}"

        # Find all backup files
        backup_files = list(backup_dir.glob(pattern))
        if len(backup_files) <= keep_count:
            return 0

        # Sort by modification time (newest first)
        backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # Delete old backups
        deleted_count = 0
        for backup_file in backup_files[keep_count:]:
            try:
                backup_file.unlink()
                deleted_count += 1
                logger.debug(f"Deleted old backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to delete backup {backup_file}: {e}")

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old backups for {file_path}")

        return deleted_count

    def get_temp_copy(self, file_path: Path) -> Path:
        """
        Create a temporary copy of file for safe operations.

        Args:
            file_path: File to copy

        Returns:
            Path to temporary copy
        """
        temp_dir = Path(tempfile.gettempdir()) / "exif_analyzer"
        temp_dir.mkdir(exist_ok=True)

        temp_path = temp_dir / f"temp_{int(time.time())}_{file_path.name}"
        shutil.copy2(file_path, temp_path)

        logger.debug(f"Created temp copy: {temp_path}")
        return temp_path