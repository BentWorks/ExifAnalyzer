"""
Progress reporting utilities for CLI operations.
"""
import time
from pathlib import Path
from typing import Optional, Iterator, List, Any
import click
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from ..core.logger import logger


class ProgressReporter:
    """
    Handles progress reporting for CLI operations.
    """

    def __init__(self, show_progress: bool = True):
        """Initialize progress reporter."""
        self.show_progress = show_progress
        self._lock = Lock()
        self._start_time = None
        self._completed = 0
        self._total = 0
        self._errors = 0

    def start(self, total: int, operation: str = "Processing") -> None:
        """Start progress tracking."""
        self._start_time = time.time()
        self._completed = 0
        self._total = total
        self._errors = 0

        if self.show_progress and total > 1:
            click.echo(f"{operation} {total} files...")

    def update(self, filename: Optional[str] = None, error: bool = False) -> None:
        """Update progress."""
        with self._lock:
            self._completed += 1
            if error:
                self._errors += 1

            if self.show_progress and self._total > 1:
                percent = (self._completed / self._total) * 100
                status = "ERROR" if error else "OK"

                if filename:
                    filename_display = Path(filename).name
                    if len(filename_display) > 30:
                        filename_display = f"...{filename_display[-27:]}"
                    click.echo(f"  [{self._completed:3d}/{self._total}] {percent:5.1f}% - {status:5s} - {filename_display}")
                else:
                    click.echo(f"  [{self._completed:3d}/{self._total}] {percent:5.1f}% - {status}")

    def finish(self, operation: str = "Operation") -> None:
        """Finish progress tracking and show summary."""
        if self._start_time:
            elapsed = time.time() - self._start_time
            successful = self._completed - self._errors

            if self.show_progress:
                click.echo()
                click.echo(f"{operation} completed in {elapsed:.2f}s")
                click.echo(f"  Total: {self._completed}")
                click.echo(f"  Successful: {successful}")
                if self._errors > 0:
                    click.echo(f"  Errors: {self._errors}")


class BatchProcessor:
    """
    Handles batch processing with progress reporting and concurrency.
    """

    def __init__(self, max_workers: int = 4, show_progress: bool = True):
        """Initialize batch processor."""
        self.max_workers = max_workers
        self.progress = ProgressReporter(show_progress)

    def process_files(
        self,
        files: List[Path],
        operation_func,
        operation_name: str = "Processing",
        **kwargs
    ) -> dict:
        """
        Process files with concurrent execution and progress reporting.

        Args:
            files: List of file paths to process
            operation_func: Function to call for each file
            operation_name: Name of operation for progress display
            **kwargs: Additional arguments for operation_func

        Returns:
            Dictionary mapping file paths to results or exceptions
        """
        results = {}

        if not files:
            click.echo("No files to process.")
            return results

        self.progress.start(len(files), operation_name)

        if len(files) == 1 or self.max_workers == 1:
            # Single-threaded processing
            for file_path in files:
                try:
                    result = operation_func(file_path, **kwargs)
                    results[str(file_path)] = result
                    self.progress.update(str(file_path), error=False)
                except Exception as e:
                    results[str(file_path)] = e
                    self.progress.update(str(file_path), error=True)
                    logger.error(f"Failed to process {file_path}: {e}")
        else:
            # Multi-threaded processing
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_file = {
                    executor.submit(operation_func, file_path, **kwargs): file_path
                    for file_path in files
                }

                # Process completed tasks
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        result = future.result()
                        results[str(file_path)] = result
                        self.progress.update(str(file_path), error=False)
                    except Exception as e:
                        results[str(file_path)] = e
                        self.progress.update(str(file_path), error=True)
                        logger.error(f"Failed to process {file_path}: {e}")

        self.progress.finish(operation_name)
        return results


def confirm_operation(message: str, default: bool = False) -> bool:
    """
    Ask user for confirmation with improved UX.

    Args:
        message: Confirmation message
        default: Default value if user just presses Enter

    Returns:
        True if user confirms
    """
    suffix = " [Y/n]" if default else " [y/N]"
    response = click.prompt(f"{message}{suffix}", default="y" if default else "n", type=str)
    return response.lower().startswith('y')


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def validate_output_path(output_path: Path, input_path: Path, force: bool = False) -> bool:
    """
    Validate output path and handle conflicts.

    Args:
        output_path: Proposed output path
        input_path: Input file path
        force: Skip confirmation prompts

    Returns:
        True if output path is valid and can be used
    """
    # Check if output exists
    if output_path.exists() and not force:
        if output_path == input_path:
            if not confirm_operation(f"Overwrite original file {input_path}?"):
                return False
        else:
            if not confirm_operation(f"Overwrite existing file {output_path}?"):
                return False

    # Check if output directory exists
    output_dir = output_path.parent
    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            click.echo(f"Created directory: {output_dir}")
        except Exception as e:
            click.echo(f"Error: Cannot create directory {output_dir}: {e}", err=True)
            return False

    return True


class StyleFormatter:
    """Provides consistent styling for CLI output."""

    @staticmethod
    def success(text: str) -> str:
        """Format success message."""
        return click.style(text, fg='green')

    @staticmethod
    def error(text: str) -> str:
        """Format error message."""
        return click.style(text, fg='red')

    @staticmethod
    def warning(text: str) -> str:
        """Format warning message."""
        return click.style(text, fg='yellow')

    @staticmethod
    def info(text: str) -> str:
        """Format info message."""
        return click.style(text, fg='blue')

    @staticmethod
    def highlight(text: str) -> str:
        """Format highlighted text."""
        return click.style(text, bold=True)

    @staticmethod
    def dim(text: str) -> str:
        """Format dimmed text."""
        return click.style(text, dim=True)