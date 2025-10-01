"""
GIF metadata adapter for handling comments and basic metadata in GIF images.
"""
from pathlib import Path
from typing import Optional, List

from PIL import Image

from ..core.base_adapter import BaseMetadataAdapter
from ..core.metadata import ImageMetadata, MetadataBlock
from ..core.exceptions import MetadataError, UnsupportedFormatError
from ..core.file_safety import FileSafetyManager
from ..core.logger import logger


class GIFAdapter(BaseMetadataAdapter):
    """Adapter for GIF image metadata operations."""

    def __init__(self, safety_manager: Optional[FileSafetyManager] = None):
        """
        Initialize GIF adapter.

        Args:
            safety_manager: Optional FileSafetyManager for file operations.
                           If None, creates a new instance.
        """
        super().__init__(safety_manager)
        if self.safety_manager is None:
            self.safety_manager = FileSafetyManager()

    @property
    def supported_formats(self) -> List[str]:
        """GIF format variants."""
        return ["gif"]

    @property
    def format_name(self) -> str:
        """Human-readable format name."""
        return "GIF"

    def read_metadata(self, file_path: Path) -> ImageMetadata:
        """
        Read metadata from GIF file.

        Args:
            file_path: Path to GIF file

        Returns:
            ImageMetadata object with extracted metadata

        Raises:
            UnsupportedFormatError: If file is not GIF format
            MetadataError: If metadata reading fails
        """
        if not self.supports_format(file_path):
            raise UnsupportedFormatError(f"File {file_path} is not a GIF image")

        metadata = ImageMetadata(file_path=file_path, format=self.format_name)

        try:
            with Image.open(file_path) as img:
                # Extract comment if present
                if hasattr(img, 'info'):
                    for key, value in img.info.items():
                        if key == 'comment':
                            # Decode bytes to string if needed
                            if isinstance(value, bytes):
                                metadata.custom.set('GIF:comment', value.decode('utf-8', errors='ignore'))
                            else:
                                metadata.custom.set('GIF:comment', str(value))
                        elif key == 'duration':
                            metadata.custom.set('GIF:duration', str(value))
                        elif key == 'loop':
                            metadata.custom.set('GIF:loop', str(value))
                        else:
                            metadata.custom.set(f'GIF:{key}', str(value))

                # Store animation info if available
                if hasattr(img, 'is_animated'):
                    metadata.custom.set('GIF:is_animated', str(img.is_animated))

                if hasattr(img, 'n_frames'):
                    metadata.custom.set('GIF:n_frames', str(img.n_frames))

            logger.info(f"GIF READ SUCCESS: {file_path}")
            return metadata

        except Exception as e:
            logger.error(f"Error reading GIF metadata from {file_path}: {e}")
            raise MetadataError(f"Failed to read GIF metadata: {e}")

    def write_metadata(self, metadata: ImageMetadata, output_path: Path) -> Path:
        """
        Write metadata to GIF file.

        Args:
            metadata: ImageMetadata object containing metadata to write
            output_path: Path where output file should be saved

        Returns:
            Path to output file

        Raises:
            MetadataError: If metadata writing fails
        """
        try:
            source_path = metadata.file_path

            with Image.open(source_path) as img:
                # Prepare save parameters
                save_params = {'format': 'GIF'}

                # Preserve animation settings if present
                if hasattr(img, 'info'):
                    if 'duration' in img.info:
                        save_params['duration'] = img.info['duration']
                    if 'loop' in img.info:
                        save_params['loop'] = img.info['loop']

                # Add comment from custom metadata if present
                comment = metadata.custom.get('GIF:comment')
                if comment:
                    # Convert to bytes if string
                    if isinstance(comment, str):
                        save_params['comment'] = comment.encode('utf-8')
                    else:
                        save_params['comment'] = comment

                # Ensure parent directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Handle animated GIFs
                if hasattr(img, 'is_animated') and img.is_animated:
                    frames = []
                    try:
                        for frame_num in range(img.n_frames):
                            img.seek(frame_num)
                            frames.append(img.copy())

                        # Save all frames
                        if frames:
                            frames[0].save(
                                output_path,
                                save_all=True,
                                append_images=frames[1:],
                                **save_params
                            )
                    except Exception as e:
                        logger.warning(f"Error handling animated GIF, saving as static: {e}")
                        img.seek(0)
                        img.save(output_path, **save_params)
                else:
                    # Save static GIF
                    img.save(output_path, **save_params)

            logger.info(f"GIF WRITE SUCCESS: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error writing GIF metadata to {output_path}: {e}")
            raise MetadataError(f"Failed to write GIF metadata: {e}")

    def strip_metadata(self, file_path: Path, output_path: Path, gps_only: bool = False) -> Path:
        """
        Strip metadata from GIF file.

        Args:
            file_path: Path to source GIF file
            output_path: Path where stripped file should be saved
            gps_only: If True, only strip GPS data (GIF adapter strips all metadata regardless)

        Returns:
            Path to output file

        Raises:
            MetadataError: If stripping fails
        """
        try:
            with Image.open(file_path) as img:
                # Ensure parent directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Handle animated GIFs
                if hasattr(img, 'is_animated') and img.is_animated:
                    frames = []
                    durations = []

                    try:
                        for frame_num in range(img.n_frames):
                            img.seek(frame_num)
                            frame = img.copy()
                            frames.append(frame)

                            # Preserve frame duration if available
                            if 'duration' in img.info:
                                durations.append(img.info['duration'])

                        # Save all frames without metadata
                        if frames:
                            save_params = {'format': 'GIF', 'save_all': True, 'append_images': frames[1:]}

                            # Preserve animation timing but not metadata
                            if durations:
                                save_params['duration'] = durations[0] if len(durations) == 1 else durations

                            frames[0].save(output_path, **save_params)
                    except Exception as e:
                        logger.warning(f"Error handling animated GIF, saving first frame: {e}")
                        img.seek(0)
                        new_img = Image.new(img.mode, img.size)
                        new_img.frombytes(img.tobytes())
                        new_img.save(output_path, format='GIF')
                else:
                    # Strip metadata from static GIF
                    new_img = Image.new(img.mode, img.size)
                    new_img.frombytes(img.tobytes())
                    new_img.save(output_path, format='GIF')

                # Verify file integrity
                self.safety_manager.verify_file_integrity(file_path, output_path)

            logger.info(f"GIF STRIP SUCCESS: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error stripping GIF metadata from {file_path}: {e}")
            raise MetadataError(f"Failed to strip GIF metadata: {e}")
