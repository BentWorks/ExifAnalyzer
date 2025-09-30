"""
Main CLI interface for ExifAnalyzer.
"""
import click
from pathlib import Path
from typing import Optional, List
import sys
import json

from ..core.engine import MetadataEngine
from ..core.exceptions import ExifAnalyzerError
from ..core.logger import setup_logger
from ..core.config import config
from .progress import BatchProcessor, ProgressReporter, confirm_operation, StyleFormatter, validate_output_path


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress non-error output')
@click.option('--config-file', type=click.Path(path_type=Path), help='Custom configuration file')
@click.option('--no-backup', is_flag=True, help='Disable automatic backups')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompts')
@click.pass_context
def cli(ctx, verbose, quiet, config_file, no_backup, force):
    """
    ExifAnalyzer - Cross-platform Image Metadata Tool

    A lightweight utility for viewing, editing, and stripping metadata from image files.
    Focus on privacy, security, and ease of use.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Load custom config if specified
    if config_file:
        try:
            with open(config_file, 'r') as f:
                custom_config = json.load(f)
            config._merge_config(custom_config)
            click.echo(f"Loaded configuration from {config_file}")
        except Exception as e:
            click.echo(f"Warning: Failed to load config file {config_file}: {e}", err=True)

    # Override config with command line options
    if no_backup:
        config.set('backup.enabled', False)

    # Set up logging
    if quiet:
        log_level = "ERROR"
    elif verbose:
        log_level = "DEBUG"
    else:
        log_level = config.get('logging.level', 'INFO')

    # For JSON output, suppress console logging to avoid interfering with JSON
    console_logging = not quiet
    logger = setup_logger(level=log_level, console=console_logging)

    # Store context
    ctx.obj['logger'] = logger
    ctx.obj['engine'] = MetadataEngine()
    ctx.obj['force'] = force
    ctx.obj['show_progress'] = config.get('batch.show_progress', True) and not quiet


@cli.command()
@click.argument('file_path', type=click.Path(exists=True, path_type=Path))
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
@click.option('--show-all', is_flag=True, help='Show all metadata keys and values')
@click.option('--privacy-check', is_flag=True, help='Highlight privacy-sensitive data')
@click.option('--export', type=click.Path(path_type=Path), help='Export metadata to file')
@click.pass_context
def view(ctx, file_path: Path, output_json: bool, show_all: bool, privacy_check: bool, export: Optional[Path]):
    """View metadata from image file with enhanced formatting."""
    try:
        # For JSON output, temporarily suppress logging to console
        if output_json:
            import logging
            logging.getLogger('exif_analyzer').handlers = []

        engine = ctx.obj['engine']
        metadata = engine.read_metadata(file_path)

        if output_json:
            output = metadata.to_json()
            click.echo(output)

            if export:
                with open(export, 'w') as f:
                    f.write(output)
                click.echo(f"\\nMetadata exported to: {export}")
        else:
            # Enhanced human-readable output
            from .progress import format_file_size

            click.echo(StyleFormatter.highlight(f"File: {metadata.file_path.name}"))
            click.echo(f"   Path: {metadata.file_path}")
            click.echo(f"   Format: {StyleFormatter.info(metadata.format)}")
            click.echo(f"   Size: {format_file_size(metadata.file_size or 0)}")

            # Metadata status
            has_meta = metadata.has_metadata()
            has_gps = metadata.has_gps_data()

            meta_status = StyleFormatter.success("Yes") if has_meta else StyleFormatter.dim("No")
            gps_status = StyleFormatter.error("Yes (Privacy Risk)") if has_gps else StyleFormatter.success("No")

            click.echo(f"   Has metadata: {meta_status}")
            click.echo(f"   Has GPS data: {gps_status}")

            if has_meta:
                click.echo(f"\\n{StyleFormatter.highlight('Metadata Summary:')}")

                total_keys = 0
                for block_name, block in metadata.iter_named_blocks():
                    if not block.is_empty():
                        count = len(block.keys())
                        total_keys += count
                        click.echo(f"   {block_name}: {StyleFormatter.info(str(count))} keys")

                click.echo(f"   Total: {StyleFormatter.highlight(str(total_keys))} metadata entries")

                # Privacy check
                if privacy_check:
                    sensitive_keys = metadata.get_privacy_sensitive_keys()
                    if sensitive_keys:
                        click.echo(f"\\n{StyleFormatter.warning('Privacy-Sensitive Data Found:')}")
                        for block_name, key in sensitive_keys[:10]:  # Show first 10
                            click.echo(f"   {block_name.upper()}: {StyleFormatter.warning(key)}")
                        if len(sensitive_keys) > 10:
                            click.echo(f"   ... and {len(sensitive_keys) - 10} more sensitive keys")

                # Show detailed metadata if requested
                if show_all:
                    click.echo(f"\\n{StyleFormatter.highlight('Detailed Metadata:')}")
                    for block_name, block in metadata.iter_named_blocks():
                        if not block.is_empty():
                            click.echo(f"\\n   {StyleFormatter.highlight(block_name)}:")
                            for key in sorted(block.keys()):
                                value = str(block.get(key))
                                if len(value) > 100:
                                    value = value[:97] + "..."

                                # Highlight sensitive keys
                                if privacy_check and any(pattern in key.lower() for pattern in config.get_privacy_patterns()):
                                    key_display = StyleFormatter.warning(key)
                                else:
                                    key_display = key

                                click.echo(f"     {key_display}: {value}")

            if export and not output_json:
                engine.export_metadata(file_path, export)
                click.echo(f"\\nMetadata exported to: {export}")

    except ExifAnalyzerError as e:
        click.echo(StyleFormatter.error(f"Error: {e}"), err=True)
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path), help='Output file path')
@click.option('--backup/--no-backup', default=None, help='Create backup before stripping')
@click.option('--gps-only', is_flag=True, help='Strip only GPS/location data')
@click.option('--preview', is_flag=True, help='Preview what would be removed without doing it')
@click.option('--keep', multiple=True, help='Keep specific metadata keys (can be used multiple times)')
@click.pass_context
def strip(ctx, file_path: Path, output: Optional[Path], backup: Optional[bool], gps_only: bool, preview: bool, keep: tuple):
    """Strip metadata from image file with enhanced options."""
    try:
        engine = ctx.obj['engine']
        force = ctx.obj['force']

        # Determine backup setting
        if backup is None:
            backup = config.should_create_backup()

        # Read current metadata for preview/confirmation
        metadata = engine.read_metadata(file_path)

        if not metadata.has_metadata():
            click.echo(StyleFormatter.info("File has no metadata to strip."))
            # If output path specified, still copy the file
            if output:
                import shutil
                shutil.copy2(file_path, output)
                click.echo(f"File copied to: {output}")
            return

        # Preview mode
        if preview:
            if gps_only:
                if metadata.has_gps_data():
                    sensitive_keys = metadata.get_privacy_sensitive_keys()
                    gps_keys = [key for block, key in sensitive_keys if any(p in key.lower() for p in ['gps', 'location', 'coordinate'])]
                    click.echo(f"Would remove {len(gps_keys)} GPS-related keys:")
                    for key in gps_keys[:10]:
                        click.echo(f"  - {StyleFormatter.warning(key)}")
                    if len(gps_keys) > 10:
                        click.echo(f"  ... and {len(gps_keys) - 10} more")
                else:
                    click.echo("No GPS data found to remove.")
            else:
                total_keys = sum(len(block.keys()) for block in metadata.iter_blocks())
                if keep:
                    keep_count = len([k for block in metadata.iter_blocks()
                                    for key in block.keys() if any(pattern in key.lower() for pattern in keep)])
                    click.echo(f"Would remove {total_keys - keep_count} of {total_keys} metadata keys")
                    click.echo(f"Would keep {keep_count} keys matching: {', '.join(keep)}")
                else:
                    click.echo(f"Would remove all {total_keys} metadata keys")
            return

        # Confirmation for destructive operations
        if config.should_warn_before_strip() and not force:
            if gps_only:
                if not confirm_operation(f"Remove GPS/location data from {file_path.name}?", default=True):
                    click.echo("Operation cancelled.")
                    return
            else:
                total_keys = sum(len(block.keys()) for block in metadata.iter_blocks())
                if not confirm_operation(f"Remove all {total_keys} metadata entries from {file_path.name}?", default=False):
                    click.echo("Operation cancelled.")
                    return

        # Validate output path
        if output and not validate_output_path(output, file_path, force):
            click.echo("Operation cancelled.")
            return

        # Perform stripping operation
        if gps_only:
            result_path = engine.strip_gps_data(file_path, output, create_backup=backup)
            click.echo(StyleFormatter.success(f"GPS data stripped: {result_path}"))
        else:
            # Handle keep patterns
            if keep:
                original_metadata = engine.read_metadata(file_path)
                # Remove non-matching keys
                for block in original_metadata.iter_blocks():
                    keys_to_remove = []
                    for key in block.keys():
                        if not any(pattern.lower() in key.lower() for pattern in keep):
                            keys_to_remove.append(key)
                    for key in keys_to_remove:
                        block.remove(key)

                result_path = engine.write_metadata(original_metadata, output, create_backup=backup)
                kept_count = sum(len(block.keys()) for block in original_metadata.iter_blocks())
                click.echo(StyleFormatter.success(f"Metadata filtered (kept {kept_count} keys): {result_path}"))
            else:
                result_path = engine.strip_metadata(file_path, output, create_backup=backup)
                click.echo(StyleFormatter.success(f"All metadata stripped: {result_path}"))

        # Show backup info
        if backup and result_path == file_path:
            backup_dir = config.get_backup_directory(file_path)
            click.echo(StyleFormatter.dim(f"   Backup created in: {backup_dir}"))

    except ExifAnalyzerError as e:
        click.echo(StyleFormatter.error(f"Error: {e}"), err=True)
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True, path_type=Path))
@click.argument('export_path', type=click.Path(path_type=Path))
@click.option('--format', 'export_format', default='json',
              type=click.Choice(['json', 'xmp']), help='Export format')
@click.pass_context
def export(ctx, file_path: Path, export_path: Path, export_format: str):
    """Export metadata to external file."""
    try:
        engine = ctx.obj['engine']
        result_path = engine.export_metadata(file_path, export_path, format=export_format)
        click.echo(f"Metadata exported: {result_path}")

    except ExifAnalyzerError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True, path_type=Path))
@click.argument('metadata_path', type=click.Path(exists=True, path_type=Path))
@click.option('--backup/--no-backup', default=True, help='Create backup before restoring')
@click.pass_context
def restore(ctx, file_path: Path, metadata_path: Path, backup: bool):
    """Restore metadata from external file."""
    try:
        engine = ctx.obj['engine']
        result_path = engine.restore_metadata(file_path, metadata_path, create_backup=backup)
        click.echo(f"Metadata restored: {result_path}")

    except ExifAnalyzerError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
def batch():
    """Batch operations on multiple files."""
    pass


@batch.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option('--recursive', '-r', is_flag=True, help='Process subdirectories recursively')
@click.option('--pattern', default='*', help='File pattern to match (e.g., "*.jpg", "IMG_*")')
@click.option('--output-dir', type=click.Path(path_type=Path), help='Output directory for processed files')
@click.option('--gps-only', is_flag=True, help='Strip only GPS/location data')
@click.option('--keep', multiple=True, help='Keep specific metadata patterns (can be used multiple times)')
@click.option('--dry-run', is_flag=True, help='Show what would be done without doing it')
@click.option('--threads', type=int, help='Number of concurrent threads (default from config)')
@click.option('--backup/--no-backup', default=None, help='Create backups before processing')
@click.option('--continue-on-error/--stop-on-error', default=None, help='Continue processing if errors occur')
@click.pass_context
def strip(ctx, directory: Path, recursive: bool, pattern: str, output_dir: Optional[Path],
          gps_only: bool, keep: tuple, dry_run: bool, threads: Optional[int],
          backup: Optional[bool], continue_on_error: Optional[bool]):
    """Strip metadata from multiple files with enhanced batch processing."""
    try:
        engine = ctx.obj['engine']
        force = ctx.obj['force']
        show_progress = ctx.obj['show_progress']

        # Set defaults from config
        if threads is None:
            threads = config.get_max_concurrent_operations()
        if backup is None:
            backup = config.should_create_backup()
        if continue_on_error is None:
            continue_on_error = config.get('batch.continue_on_error', True)

        # Find files
        click.echo(f"Scanning {directory}{'/' + pattern if pattern != '*' else ''}")
        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))

        # Filter for supported formats
        supported_formats = engine.get_supported_formats()
        image_files = []
        skipped_files = []

        for file_path in files:
            if file_path.is_file():
                ext = file_path.suffix.lower().lstrip('.')
                if ext in supported_formats:
                    image_files.append(file_path)
                elif file_path.suffix:  # Has extension but not supported
                    skipped_files.append(file_path)

        if not image_files:
            click.echo(StyleFormatter.warning("No supported image files found."))
            if skipped_files:
                click.echo(f"Skipped {len(skipped_files)} unsupported files.")
            return

        # Show discovery results
        click.echo(f"Found {StyleFormatter.highlight(str(len(image_files)))} supported image files")
        if skipped_files:
            click.echo(f"Skipped {len(skipped_files)} unsupported files")

        # Prepare output directory
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            click.echo(f"Output directory: {output_dir}")

        # Dry run mode
        if dry_run:
            click.echo(f"\\n{StyleFormatter.info('DRY RUN - No files will be modified:')}")

            # Show sample of files that would be processed
            sample_size = min(10, len(image_files))
            for i, file_path in enumerate(image_files[:sample_size]):
                rel_path = file_path.relative_to(directory) if file_path.is_relative_to(directory) else file_path
                click.echo(f"  {rel_path}")

            if len(image_files) > sample_size:
                click.echo(f"  ... and {len(image_files) - sample_size} more files")

            # Show what operation would be performed
            if gps_only:
                click.echo(f"\\n{StyleFormatter.warning('Would remove GPS/location data from all files')}")
            elif keep:
                keep_patterns = ', '.join(keep)
                click.echo(f"\\n{StyleFormatter.info(f'Would keep metadata matching: {keep_patterns}')}")
            else:
                click.echo(f"\\n{StyleFormatter.warning('Would remove ALL metadata from all files')}")

            return

        # Confirmation for batch operations
        if not force and len(image_files) > 5:
            operation_desc = "GPS data" if gps_only else "all metadata"
            if not confirm_operation(f"Process {len(image_files)} files and remove {operation_desc}?", default=False):
                click.echo("Operation cancelled.")
                return

        # Set up batch processor
        processor = BatchProcessor(max_workers=threads, show_progress=show_progress)

        # Define operation function
        def process_file(file_path: Path, **kwargs) -> Path:
            try:
                if gps_only:
                    return engine.strip_gps_data(
                        file_path,
                        output_dir / file_path.name if output_dir else None,
                        create_backup=backup
                    )
                elif keep:
                    # Handle selective stripping
                    metadata = engine.read_metadata(file_path)
                    for block in metadata.iter_blocks():
                        keys_to_remove = []
                        for key in block.keys():
                            if not any(pattern.lower() in key.lower() for pattern in keep):
                                keys_to_remove.append(key)
                        for key in keys_to_remove:
                            block.remove(key)

                    return engine.write_metadata(
                        metadata,
                        output_dir / file_path.name if output_dir else None,
                        create_backup=backup
                    )
                else:
                    return engine.strip_metadata(
                        file_path,
                        output_dir / file_path.name if output_dir else None,
                        create_backup=backup
                    )
            except Exception as e:
                if not continue_on_error:
                    raise
                return e

        # Process files
        operation_name = "Removing GPS data" if gps_only else "Stripping metadata"
        results = processor.process_files(image_files, process_file, operation_name)

        # Analyze results
        successful = sum(1 for result in results.values() if isinstance(result, Path))
        failed = len(results) - successful

        # Show final summary
        click.echo(f"\\n{StyleFormatter.highlight('Batch Processing Summary:')}")
        click.echo(f"   Total files: {len(image_files)}")
        click.echo(f"   Successful: {StyleFormatter.success(str(successful))}")
        if failed > 0:
            click.echo(f"   Failed: {StyleFormatter.error(str(failed))}")

        # Show backup information
        if backup and successful > 0 and not output_dir:
            backup_dir = config.get_backup_directory(directory)
            click.echo(f"   Backups: {StyleFormatter.dim(str(backup_dir))}")

        # Show failed files
        if failed > 0:
            click.echo(f"\\n{StyleFormatter.error('Failed Files:')}")
            for file_path, result in results.items():
                if isinstance(result, Exception):
                    rel_path = Path(file_path).name
                    click.echo(f"   {rel_path}: {StyleFormatter.error(str(result))}")

        # Exit with error code if any failures and not continuing on error
        if failed > 0 and not continue_on_error:
            sys.exit(1)

    except ExifAnalyzerError as e:
        click.echo(StyleFormatter.error(f"Error: {e}"), err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def formats(ctx):
    """List supported image formats."""
    engine = ctx.obj['engine']
    supported = engine.get_supported_formats()

    click.echo(StyleFormatter.highlight("Supported Image Formats:"))
    for fmt in sorted(supported):
        click.echo(f"   .{fmt}")


@cli.group()
def config_cmd():
    """Configuration management commands."""
    pass


@config_cmd.command(name="show")
@click.option('--section', help='Show specific configuration section')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
def config_show(section: Optional[str], output_json: bool):
    """Show current configuration."""
    try:
        if output_json:
            if section:
                section_config = {}
                for key, value in config.to_dict().items():
                    if key == section:
                        section_config[key] = value
                click.echo(json.dumps(section_config, indent=2))
            else:
                click.echo(json.dumps(config.to_dict(), indent=2))
        else:
            click.echo(StyleFormatter.highlight("ExifAnalyzer Configuration:"))
            config_dict = config.to_dict()

            if section:
                if section in config_dict:
                    click.echo(f"\\n{StyleFormatter.info(f'[{section}]')}")
                    _display_config_section(config_dict[section])
                else:
                    click.echo(StyleFormatter.error(f"Unknown configuration section: {section}"))
                    return
            else:
                for section_name, section_data in config_dict.items():
                    click.echo(f"\\n{StyleFormatter.info(f'[{section_name}]')}")
                    _display_config_section(section_data)

            click.echo(f"\\n{StyleFormatter.dim('User config:')} {config.user_config_path}")
            click.echo(f"{StyleFormatter.dim('Project config:')} {config.project_config_path}")

    except Exception as e:
        click.echo(StyleFormatter.error(f"Error reading configuration: {e}"), err=True)


@config_cmd.command(name="set")
@click.argument('key')
@click.argument('value')
@click.option('--user', is_flag=True, help='Save to user configuration')
@click.option('--project', is_flag=True, help='Save to project configuration')
def config_set(key: str, value: str, user: bool, project: bool):
    """Set configuration value."""
    try:
        # Parse value
        parsed_value = _parse_config_value(value)

        # Set the value
        config.set(key, parsed_value)

        # Save configuration
        if project:
            config.save_project_config()
            click.echo(f"Set {StyleFormatter.highlight(key)} = {StyleFormatter.info(str(parsed_value))} (project)")
        elif user:
            config.save_user_config()
            click.echo(f"Set {StyleFormatter.highlight(key)} = {StyleFormatter.info(str(parsed_value))} (user)")
        else:
            # Default to user config
            config.save_user_config()
            click.echo(f"Set {StyleFormatter.highlight(key)} = {StyleFormatter.info(str(parsed_value))} (user)")

    except Exception as e:
        click.echo(StyleFormatter.error(f"Error setting configuration: {e}"), err=True)


@config_cmd.command(name="reset")
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def config_reset(confirm: bool):
    """Reset configuration to defaults."""
    try:
        if not confirm:
            if not confirm_operation("Reset all configuration to defaults?", default=False):
                click.echo("Reset cancelled.")
                return

        config.reset_to_defaults()
        click.echo(StyleFormatter.success("Configuration reset to defaults"))

    except Exception as e:
        click.echo(StyleFormatter.error(f"Error resetting configuration: {e}"), err=True)


@config_cmd.command(name="validate")
def config_validate():
    """Validate current configuration."""
    try:
        if config.validate_config():
            click.echo(StyleFormatter.success("Configuration is valid"))
        else:
            click.echo(StyleFormatter.error("Configuration validation failed"))

    except Exception as e:
        click.echo(StyleFormatter.error(f"Configuration validation error: {e}"), err=True)


def _display_config_section(section_data: dict, indent: str = "   "):
    """Display a configuration section."""
    for key, value in section_data.items():
        if isinstance(value, dict):
            click.echo(f"{indent}{key}:")
            _display_config_section(value, indent + "  ")
        else:
            if isinstance(value, bool):
                value_display = StyleFormatter.success("true") if value else StyleFormatter.dim("false")
            elif value is None:
                value_display = StyleFormatter.dim("null")
            elif isinstance(value, (int, float)):
                value_display = StyleFormatter.info(str(value))
            else:
                value_display = str(value)

            click.echo(f"{indent}{key}: {value_display}")


def _parse_config_value(value: str):
    """Parse string value to appropriate type."""
    # Try boolean
    if value.lower() in ['true', 'yes', '1']:
        return True
    elif value.lower() in ['false', 'no', '0']:
        return False

    # Try null
    if value.lower() in ['null', 'none']:
        return None

    # Try number
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        pass

    # Return as string
    return value


# Add config command group to main CLI
cli.add_command(config_cmd, name="config")


if __name__ == '__main__':
    cli()