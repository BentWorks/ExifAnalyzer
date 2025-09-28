"""
Custom exceptions for ExifAnalyzer metadata operations.
"""


class ExifAnalyzerError(Exception):
    """Base exception for all ExifAnalyzer errors."""
    pass


class MetadataError(ExifAnalyzerError):
    """Base exception for metadata-related errors."""
    pass


class UnsupportedFormatError(MetadataError):
    """Raised when an image format is not supported."""
    pass


class CorruptedMetadataError(MetadataError):
    """Raised when metadata is corrupted or invalid."""
    pass


class MetadataNotFoundError(MetadataError):
    """Raised when expected metadata is not found."""
    pass


class FileError(ExifAnalyzerError):
    """Base exception for file-related errors."""
    pass


class FileNotFoundError(FileError):
    """Raised when a file cannot be found."""
    pass


class FilePermissionError(FileError):
    """Raised when file permissions prevent operation."""
    pass


class PixelDataCorruptionError(ExifAnalyzerError):
    """Raised when pixel data integrity is compromised."""
    pass


class BackupError(ExifAnalyzerError):
    """Raised when backup operations fail."""
    pass


class ValidationError(ExifAnalyzerError):
    """Raised when data validation fails."""
    pass