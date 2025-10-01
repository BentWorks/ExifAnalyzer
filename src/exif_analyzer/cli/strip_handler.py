"""
Strip operation handler for CLI commands.

This module encapsulates the logic for stripping metadata from images,
used by both single-file and batch strip commands.
"""
from pathlib import Path
from typing import Optional, Tuple, List
import click

from ..core.engine import MetadataEngine
from ..core.metadata import ImageMetadata
from ..core.config import config
from ..core.exceptions import ExifAnalyzerError
from .progress import StyleFormatter


class StripOperationHandler:
    """
    Handles metadata stripping operations with preview, confirmation, and execution.

    This class consolidates the logic shared between single-file and batch
    strip operations, improving maintainability and testability.
    """

    def __init__(self, engine: MetadataEngine):
        """
        Initialize strip operation handler.

        Args:
            engine: MetadataEngine instance for metadata operations
        """
        self.engine = engine

    def preview_strip_operation(
        self,
        metadata: ImageMetadata,
        gps_only: bool,
        keep: Tuple[str, ...]
    ) -> None:
        """
        Preview what would be removed without actually doing it.

        Args:
            metadata: ImageMetadata to preview
            gps_only: Whether to strip only GPS data
            keep: Patterns to keep
        """
        if gps_only:
            self._preview_gps_strip(metadata)
        else:
            self._preview_full_strip(metadata, keep)

    def _preview_gps_strip(self, metadata: ImageMetadata) -> None:
        """Preview GPS data stripping."""
        if metadata.has_gps_data():
            sensitive_keys = metadata.get_privacy_sensitive_keys()
            gps_keys = [
                key for block, key in sensitive_keys
                if any(p in key.lower() for p in ImageMetadata.GPS_PATTERNS)
            ]
            click.echo(f"Would remove {len(gps_keys)} GPS-related keys:")
            for key in gps_keys[:10]:
                click.echo(f"  - {StyleFormatter.warning(key)}")
            if len(gps_keys) > 10:
                click.echo(f"  ... and {len(gps_keys) - 10} more")
        else:
            click.echo("No GPS data found to remove.")

    def _preview_full_strip(self, metadata: ImageMetadata, keep: Tuple[str, ...]) -> None:
        """Preview full metadata stripping."""
        total_keys = sum(len(block.keys()) for block in metadata.iter_blocks())

        if keep:
            keep_count = len([
                k for block in metadata.iter_blocks()
                for key in block.keys()
                if any(pattern in key.lower() for pattern in keep)
            ])
            click.echo(f"Would remove {total_keys - keep_count} of {total_keys} metadata keys")
            click.echo(f"Would keep {keep_count} keys matching: {', '.join(keep)}")
        else:
            click.echo(f"Would remove all {total_keys} metadata keys")

    def confirm_strip_operation(
        self,
        file_path: Path,
        metadata: ImageMetadata,
        gps_only: bool,
        force: bool
    ) -> bool:
        """
        Ask for user confirmation before stripping.

        Args:
            file_path: Path to file being processed
            metadata: ImageMetadata being stripped
            gps_only: Whether stripping only GPS data
            force: Whether to skip confirmation

        Returns:
            True if user confirmed or force=True, False otherwise
        """
        if not config.should_warn_before_strip() or force:
            return True

        if gps_only:
            message = f"Remove GPS/location data from {file_path.name}?"
            return self._confirm_operation(message, default=True)
        else:
            total_keys = sum(len(block.keys()) for block in metadata.iter_blocks())
            message = f"Remove all {total_keys} metadata entries from {file_path.name}?"
            return self._confirm_operation(message, default=False)

    def _confirm_operation(self, message: str, default: bool = False) -> bool:
        """Ask for confirmation with a default value."""
        prompt = f"{message} [{'Y/n' if default else 'y/N'}] "
        response = click.prompt(prompt, default='y' if default else 'n', show_default=False)
        return response.lower() in ['y', 'yes']

    def perform_strip_operation(
        self,
        file_path: Path,
        output_path: Optional[Path],
        gps_only: bool,
        keep: Tuple[str, ...],
        backup: bool
    ) -> Tuple[Path, str]:
        """
        Perform the actual stripping operation.

        Args:
            file_path: Input file path
            output_path: Optional output path
            gps_only: Whether to strip only GPS data
            keep: Patterns to keep
            backup: Whether to create backup

        Returns:
            Tuple of (result_path, success_message)
        """
        if gps_only:
            return self._strip_gps(file_path, output_path, backup)
        elif keep:
            return self._strip_selective(file_path, output_path, keep, backup)
        else:
            return self._strip_all(file_path, output_path, backup)

    def _strip_gps(
        self,
        file_path: Path,
        output_path: Optional[Path],
        backup: bool
    ) -> Tuple[Path, str]:
        """Strip only GPS data."""
        result_path = self.engine.strip_gps_data(file_path, output_path, create_backup=backup)
        message = f"GPS data stripped: {result_path}"
        return result_path, message

    def _strip_selective(
        self,
        file_path: Path,
        output_path: Optional[Path],
        keep: Tuple[str, ...],
        backup: bool
    ) -> Tuple[Path, str]:
        """Strip all except specified patterns."""
        metadata = self.engine.read_metadata(file_path)

        # Remove non-matching keys
        for block in metadata.iter_blocks():
            keys_to_remove = []
            for key in block.keys():
                if not any(pattern.lower() in key.lower() for pattern in keep):
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                block.remove(key)

        result_path = self.engine.write_metadata(metadata, output_path, create_backup=backup)
        kept_count = sum(len(block.keys()) for block in metadata.iter_blocks())
        message = f"Metadata filtered (kept {kept_count} keys): {result_path}"
        return result_path, message

    def _strip_all(
        self,
        file_path: Path,
        output_path: Optional[Path],
        backup: bool
    ) -> Tuple[Path, str]:
        """Strip all metadata."""
        result_path = self.engine.strip_metadata(file_path, output_path, create_backup=backup)
        message = f"All metadata stripped: {result_path}"
        return result_path, message
