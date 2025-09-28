"""
Main GUI application for ExifAnalyzer using PySimpleGUI.
"""
import PySimpleGUI as sg
from pathlib import Path
from typing import Optional, Dict, Any, List
import io
from PIL import Image
import base64

from ..core.engine import MetadataEngine
from ..core.exceptions import ExifAnalyzerError
from ..core.config import config
from ..core.logger import setup_logger


class ExifAnalyzerGUI:
    """
    Main GUI application for ExifAnalyzer.

    Provides a user-friendly interface for viewing, editing, and stripping
    metadata from image files.
    """

    def __init__(self):
        """Initialize the GUI application."""
        try:
            self.engine = MetadataEngine()
            self.logger = setup_logger('exif_analyzer_gui', level=config.get('logging.level', 'INFO'))

            # Application state
            self.current_file: Optional[Path] = None
            self.current_metadata = None
            self.supported_formats = self.engine.get_supported_formats()

            # Debug: Check what formats were loaded
            if not self.supported_formats:
                sg.popup_error('Error: No image format adapters loaded!\nSupported formats list is empty.')
            else:
                self.logger.info(f"Loaded {len(self.supported_formats)} format adapters: {self.supported_formats}")
        except Exception as e:
            sg.popup_error(f'Error initializing ExifAnalyzer engine: {e}')
            self.supported_formats = []

        # GUI theme and settings
        sg.theme('DefaultNoMoreNagging')
        self.window = None

        # Create main window
        self._create_main_window()

    def _create_main_window(self) -> None:
        """Create the main application window."""
        # File browser column
        file_column = [
            [sg.Text('Select Image File:', font=('Arial', 12, 'bold'))],
            [sg.Text('File:'), sg.In(key='-FILE-', enable_events=True),
             sg.FileBrowse(target='-FILE-', file_types=(("Image Files", "*.jpg *.jpeg *.png *.tiff *.webp *.gif"), ("All Files", "*.*")))],
            [sg.Text('Folder:'), sg.In(key='-FOLDER-', enable_events=True),
             sg.FolderBrowse(target='-FOLDER-')],
            [sg.Listbox(values=[], key='-FILE_LIST-', size=(30, 20),
                       enable_events=True, select_mode=sg.LISTBOX_SELECT_MODE_SINGLE)],
            [sg.Button('Refresh', key='-REFRESH-'),
             sg.Button('Recent Files', key='-RECENT-')],
        ]

        # Image preview column
        preview_column = [
            [sg.Text('Image Preview:', font=('Arial', 12, 'bold'))],
            [sg.Image(key='-IMAGE-', size=(300, 300), background_color='lightgray')],
            [sg.Text('', key='-IMAGE_INFO-', size=(40, 3), font=('Arial', 9))],
        ]

        # Metadata panel
        metadata_column = [
            [sg.Text('Metadata Information:', font=('Arial', 12, 'bold'))],
            [sg.Text('File:', size=(8, 1)), sg.Text('No file selected', key='-FILE_NAME-', size=(30, 1))],
            [sg.Text('Format:', size=(8, 1)), sg.Text('', key='-FORMAT-', size=(15, 1)),
             sg.Text('Size:', size=(5, 1)), sg.Text('', key='-SIZE-', size=(10, 1))],
            [sg.Text('Has GPS:', size=(8, 1)), sg.Text('', key='-GPS_STATUS-', size=(15, 1), text_color='black')],
            [sg.HSeparator()],

            # Metadata blocks
            [sg.Text('Metadata Blocks:', font=('Arial', 10, 'bold'))],
            [sg.Tree(data=sg.TreeData(), key='-METADATA_TREE-',
                    headings=['Value'], auto_size_columns=True,
                    col0_width=25, col_widths=[40], num_rows=15,
                    enable_events=True, expand_x=True)],

            [sg.HSeparator()],

            # Action buttons
            [sg.Text('Actions:', font=('Arial', 10, 'bold'))],
            [sg.Button('Strip All Metadata', key='-STRIP_ALL-', button_color=('white', 'red')),
             sg.Button('Strip GPS Only', key='-STRIP_GPS-', button_color=('white', 'orange'))],
            [sg.Button('Export Metadata', key='-EXPORT-'),
             sg.Button('Import Metadata', key='-IMPORT-')],
            [sg.Button('Show Privacy Check', key='-PRIVACY-'),
             sg.Button('Backup File', key='-BACKUP-')],
        ]

        # Main layout
        layout = [
            [sg.Menu([
                ['File', ['Open File...', 'Open Folder...', '---', 'Recent Files', '---', 'Exit']],
                ['Edit', ['Copy Metadata', 'Paste Metadata', '---', 'Preferences']],
                ['Tools', ['Batch Process...', 'Configuration...', '---', 'Privacy Audit']],
                ['Help', ['User Manual', 'About ExifAnalyzer']]
            ])],

            [sg.Text('ExifAnalyzer - Image Metadata Tool', font=('Arial', 16, 'bold'),
                    justification='center', expand_x=True)],

            [sg.HSeparator()],

            [sg.Column(file_column, vertical_alignment='top'),
             sg.VSeparator(),
             sg.Column(preview_column, vertical_alignment='top'),
             sg.VSeparator(),
             sg.Column(metadata_column, vertical_alignment='top', expand_x=True)],

            [sg.HSeparator()],

            # Status bar
            [sg.Text('Ready', key='-STATUS-', size=(50, 1), relief=sg.RELIEF_SUNKEN),
             sg.Text('', key='-PROGRESS-', size=(20, 1), justification='right')]
        ]

        self.window = sg.Window('ExifAnalyzer', layout,
                               resizable=True, size=(1200, 800),
                               icon=None, finalize=True)

    def _update_file_list(self, folder_path: str) -> None:
        """Update the file list with all files (no filtering for debugging)."""
        try:
            folder = Path(folder_path)
            if not folder.exists() or not folder.is_dir():
                self.window['-STATUS-'].update(f'Path does not exist or is not a directory: {folder_path}')
                return

            # Show ALL items for debugging
            all_items = []
            files_count = 0
            dirs_count = 0

            for item_path in folder.iterdir():
                if item_path.is_file():
                    files_count += 1
                    ext = item_path.suffix.lower().lstrip('.')
                    display_name = f"{item_path.name} ({ext}) [FILE]"
                    all_items.append(display_name)
                elif item_path.is_dir():
                    dirs_count += 1
                    display_name = f"{item_path.name} [FOLDER]"
                    all_items.append(display_name)
                else:
                    display_name = f"{item_path.name} [UNKNOWN]"
                    all_items.append(display_name)

            # Update the listbox with all items
            all_items.sort()
            self.window['-FILE_LIST-'].update(values=all_items)

            # Update status with detailed debugging info
            total_items = len(all_items)
            supported_exts = ', '.join(sorted(self.supported_formats)) if self.supported_formats else "NONE!"
            self.window['-STATUS-'].update(f'Found: {files_count} files, {dirs_count} folders, {total_items} total. Formats: {supported_exts}')

        except Exception as e:
            self.logger.error(f"Error updating file list: {e}")
            self.window['-STATUS-'].update(f'Error: {e}')

    def _load_image_preview(self, file_path: Path) -> None:
        """Load and display image preview."""
        try:
            # Load image
            with Image.open(file_path) as img:
                # Get image info
                width, height = img.size
                mode = img.mode

                # Resize for preview while maintaining aspect ratio
                preview_size = (300, 300)
                img.thumbnail(preview_size, Image.Resampling.LANCZOS)

                # Convert to bytes for PySimpleGUI
                bio = io.BytesIO()
                img.save(bio, format='PNG')
                image_bytes = bio.getvalue()

                # Update preview
                self.window['-IMAGE-'].update(data=image_bytes)

                # Update image info
                file_size = file_path.stat().st_size
                size_str = self._format_file_size(file_size)
                info_text = f'{width}x{height} ({mode})\n{size_str}'
                self.window['-IMAGE_INFO-'].update(info_text)

        except Exception as e:
            self.logger.error(f"Error loading image preview: {e}")
            self.window['-IMAGE-'].update(data=b'')
            self.window['-IMAGE_INFO-'].update(f'Preview error: {str(e)[:50]}')

    def _load_metadata(self, file_path: Path) -> None:
        """Load and display metadata for the selected file."""
        try:
            self.current_file = file_path
            self.current_metadata = self.engine.read_metadata(file_path)

            # Update file info
            self.window['-FILE_NAME-'].update(file_path.name)
            self.window['-FORMAT-'].update(self.current_metadata.format)
            self.window['-SIZE-'].update(self._format_file_size(self.current_metadata.file_size or 0))

            # Update GPS status
            has_gps = self.current_metadata.has_gps_data()
            gps_text = 'Yes (Privacy Risk!)' if has_gps else 'No'
            gps_color = 'red' if has_gps else 'green'
            self.window['-GPS_STATUS-'].update(gps_text, text_color=gps_color)

            # Update metadata tree
            self._update_metadata_tree()

            # Update status
            total_keys = sum(len(block.keys()) for block in
                           [self.current_metadata.exif, self.current_metadata.iptc,
                            self.current_metadata.xmp, self.current_metadata.custom])
            self.window['-STATUS-'].update(f'Loaded {total_keys} metadata entries')

        except Exception as e:
            self.logger.error(f"Error loading metadata: {e}")
            self.window['-STATUS-'].update(f'Error loading metadata: {e}')
            self._clear_metadata_display()

    def _update_metadata_tree(self) -> None:
        """Update the metadata tree view."""
        if not self.current_metadata:
            return

        tree_data = sg.TreeData()

        # Add metadata blocks
        for block_name, block in [
            ('EXIF', self.current_metadata.exif),
            ('IPTC', self.current_metadata.iptc),
            ('XMP', self.current_metadata.xmp),
            ('Custom', self.current_metadata.custom)
        ]:
            if not block.is_empty():
                # Add block header
                block_key = f'{block_name}_BLOCK'
                tree_data.Insert('', block_key, f'{block_name} ({len(block.keys())} keys)', [''])

                # Add metadata entries
                for key in sorted(block.keys()):
                    value = str(block.get(key))
                    # Truncate long values
                    if len(value) > 50:
                        value = value[:47] + '...'

                    # Check if key is privacy-sensitive
                    is_sensitive = any(pattern in key.lower() for pattern in config.get_privacy_patterns())
                    display_key = f'{key} (⚠)' if is_sensitive else key

                    tree_data.Insert(block_key, f'{block_name}_{key}', display_key, [value])

        self.window['-METADATA_TREE-'].update(tree_data)

    def _clear_metadata_display(self) -> None:
        """Clear the metadata display."""
        self.window['-FILE_NAME-'].update('No file selected')
        self.window['-FORMAT-'].update('')
        self.window['-SIZE-'].update('')
        self.window['-GPS_STATUS-'].update('')
        self.window['-METADATA_TREE-'].update(sg.TreeData())
        self.window['-IMAGE-'].update(data=b'')
        self.window['-IMAGE_INFO-'].update('')

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def _handle_strip_metadata(self, gps_only: bool = False) -> None:
        """Handle metadata stripping operations."""
        if not self.current_file:
            sg.popup_error('No file selected!')
            return

        # Confirmation dialog
        operation = 'GPS/location data' if gps_only else 'all metadata'
        if not sg.popup_yes_no(f'Remove {operation} from {self.current_file.name}?',
                              title='Confirm Operation'):
            return

        try:
            # Show progress
            self.window['-STATUS-'].update('Processing...')
            self.window['-PROGRESS-'].update('Working...')

            # Perform operation
            if gps_only:
                result_path = self.engine.strip_gps_data(
                    self.current_file,
                    create_backup=config.should_create_backup()
                )
            else:
                result_path = self.engine.strip_metadata(
                    self.current_file,
                    create_backup=config.should_create_backup()
                )

            # Reload metadata
            self._load_metadata(self.current_file)

            # Success message
            operation_name = 'GPS data stripped' if gps_only else 'All metadata stripped'
            sg.popup_quick_message(f'{operation_name} successfully!', auto_close_duration=2)
            self.window['-STATUS-'].update(f'{operation_name}: {result_path.name}')

        except Exception as e:
            self.logger.error(f"Error stripping metadata: {e}")
            sg.popup_error(f'Error: {e}')
            self.window['-STATUS-'].update('Error occurred')
        finally:
            self.window['-PROGRESS-'].update('')

    def _handle_export_metadata(self) -> None:
        """Handle metadata export."""
        if not self.current_file:
            sg.popup_error('No file selected!')
            return

        # Get export filename
        export_file = sg.popup_get_file(
            'Save metadata as:',
            save_as=True,
            default_extension='.json',
            file_types=(('JSON Files', '*.json'), ('All Files', '*.*'))
        )

        if not export_file:
            return

        try:
            self.window['-STATUS-'].update('Exporting metadata...')
            export_path = self.engine.export_metadata(self.current_file, export_file)

            sg.popup_quick_message('Metadata exported successfully!', auto_close_duration=2)
            self.window['-STATUS-'].update(f'Exported to: {Path(export_path).name}')

        except Exception as e:
            self.logger.error(f"Error exporting metadata: {e}")
            sg.popup_error(f'Export error: {e}')
            self.window['-STATUS-'].update('Export failed')

    def _handle_privacy_check(self) -> None:
        """Show privacy-sensitive data found in current file."""
        if not self.current_metadata:
            sg.popup_error('No file loaded!')
            return

        sensitive_keys = self.current_metadata.get_privacy_sensitive_keys()

        if not sensitive_keys:
            sg.popup('No privacy-sensitive data found!', title='Privacy Check')
            return

        # Create detailed privacy report
        report_lines = [f'Found {len(sensitive_keys)} privacy-sensitive metadata entries:']
        report_lines.append('')

        for block_name, key in sensitive_keys[:20]:  # Limit display
            report_lines.append(f'{block_name.upper()}: {key}')

        if len(sensitive_keys) > 20:
            report_lines.append(f'... and {len(sensitive_keys) - 20} more entries')

        report_text = '\n'.join(report_lines)

        # Show privacy report with option to strip
        result = sg.popup_yes_no(
            report_text + '\n\nWould you like to remove GPS/location data now?',
            title='Privacy-Sensitive Data Found'
        )

        if result == 'Yes':
            self._handle_strip_metadata(gps_only=True)

    def run(self) -> None:
        """Run the main GUI event loop."""
        try:
            while True:
                event, values = self.window.read()

                if event == sg.WIN_CLOSED or event == 'Exit':
                    break

                # Handle folder selection
                elif event == '-FOLDER-':
                    folder_path = values['-FOLDER-']
                    if folder_path:
                        self._update_file_list(folder_path)

                # Handle file selection
                elif event == '-FILE_LIST-':
                    selected_files = values['-FILE_LIST-']
                    if selected_files:
                        folder_path = values['-FOLDER-']
                        if folder_path:
                            # Extract actual filename from display format "filename.ext (ext)"
                            display_name = selected_files[0]
                            if ' (' in display_name:
                                actual_filename = display_name.split(' (')[0]
                            else:
                                actual_filename = display_name

                            file_path = Path(folder_path) / actual_filename
                            self._load_image_preview(file_path)
                            self._load_metadata(file_path)

                # Handle refresh
                elif event == '-REFRESH-':
                    folder_path = values['-FOLDER-']
                    if folder_path:
                        self._update_file_list(folder_path)

                # Handle strip operations
                elif event == '-STRIP_ALL-':
                    self._handle_strip_metadata(gps_only=False)

                elif event == '-STRIP_GPS-':
                    self._handle_strip_metadata(gps_only=True)

                # Handle export
                elif event == '-EXPORT-':
                    self._handle_export_metadata()

                # Handle privacy check
                elif event == '-PRIVACY-':
                    self._handle_privacy_check()

                # Handle menu items
                elif event == 'Open File...':
                    file_path = sg.popup_get_file(
                        'Select image file:',
                        file_types=(
                            ('Image Files', '*.jpg *.jpeg *.png *.tiff *.webp *.gif'),
                            ('JPEG Files', '*.jpg *.jpeg'),
                            ('PNG Files', '*.png'),
                            ('All Files', '*.*')
                        )
                    )
                    if file_path:
                        file_path = Path(file_path)
                        self.window['-FOLDER-'].update(str(file_path.parent))
                        self._update_file_list(str(file_path.parent))
                        self.window['-FILE_LIST-'].update(set_to_index=[0] if file_path.name in
                                                         self.window['-FILE_LIST-'].get_list_values() else [])
                        self._load_image_preview(file_path)
                        self._load_metadata(file_path)

                elif event == 'About ExifAnalyzer':
                    sg.popup(
                        'ExifAnalyzer v0.1.0\n\n'
                        'Cross-platform Image Metadata Tool\n'
                        'Privacy-focused metadata viewing and editing\n\n'
                        'Built with Python and PySimpleGUI',
                        title='About ExifAnalyzer'
                    )

        except Exception as e:
            self.logger.error(f"GUI error: {e}")
            sg.popup_error(f'Application error: {e}')

        finally:
            if self.window:
                self.window.close()


def main():
    """Main entry point for the GUI application."""
    try:
        app = ExifAnalyzerGUI()
        app.run()
    except Exception as e:
        sg.popup_error(f'Failed to start ExifAnalyzer GUI: {e}')


if __name__ == '__main__':
    main()