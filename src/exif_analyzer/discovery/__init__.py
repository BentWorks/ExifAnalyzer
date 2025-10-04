"""
Metadata Discovery Module for AI-Generated Images.

This module provides deep inspection and platform detection for AI-generated
image metadata across multiple platforms (Stable Diffusion, Midjourney, etc.).
"""
from .models import (
    DiscoveryResult,
    DetectionResult,
    AIMetadata,
    ExtractedMetadata,
    ConfidenceLevel,
)
from .engine import MetadataDiscoveryEngine

__all__ = [
    "MetadataDiscoveryEngine",
    "DiscoveryResult",
    "DetectionResult",
    "AIMetadata",
    "ExtractedMetadata",
    "ConfidenceLevel",
]
