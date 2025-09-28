"""
Test configuration and fixtures for ExifAnalyzer.
"""
import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_image_path(temp_dir):
    """Create a simple test image for metadata operations."""
    from PIL import Image

    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    image_path = temp_dir / "test_image.jpg"
    img.save(image_path, "JPEG")
    return image_path


@pytest.fixture
def sample_images_dir(temp_dir):
    """Create multiple test images for batch operations."""
    from PIL import Image

    images_dir = temp_dir / "images"
    images_dir.mkdir()

    # Create multiple test images
    for i in range(3):
        img = Image.new('RGB', (50, 50), color=['red', 'green', 'blue'][i])
        image_path = images_dir / f"test_{i}.jpg"
        img.save(image_path, "JPEG")

    return images_dir