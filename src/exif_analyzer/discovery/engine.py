"""
Main discovery engine - Phase 1 MVP implementation.
"""
import re
from pathlib import Path
from typing import Union, Optional
import time

from .models import (
    DiscoveryResult,
    DetectionResult,
    AIMetadata,
    ModelInfo,
    ConfidenceLevel,
)
from .extractor import MetadataExtractor
from ..core.engine import MetadataEngine


class MetadataDiscoveryEngine:
    """Main engine for metadata discovery operations."""

    def __init__(self, metadata_engine: Optional[MetadataEngine] = None):
        """Initialize discovery engine."""
        self.metadata_engine = metadata_engine or MetadataEngine()
        self.extractor = MetadataExtractor(self.metadata_engine)

    def discover(
        self,
        file_path: Union[str, Path],
        verbose: bool = False,
    ) -> DiscoveryResult:
        """
        Perform discovery on single image.

        Args:
            file_path: Path to image file
            verbose: Include raw data in result

        Returns:
            DiscoveryResult with complete findings
        """
        start_time = time.time()
        file_path = Path(file_path)

        # Extract all metadata
        extracted = self.extractor.extract_all(file_path)

        # Detect platform
        detection = self._detect_platform(extracted)

        # Extract AI-specific metadata
        ai_metadata = self._extract_ai_metadata(extracted, detection)

        # Identify unknown fields
        unknown_fields = [
            chunk for chunk in extracted.raw_chunks
            if chunk.chunk_type not in ["PNG:IHDR", "PNG:IDAT", "PNG:IEND",
                                         "JPEG:APP0", "JPEG:APP1"]
        ]

        discovery_time = time.time() - start_time

        return DiscoveryResult(
            file_path=file_path,
            extracted_metadata=extracted,
            detection=detection,
            ai_metadata=ai_metadata,
            unknown_fields=unknown_fields if verbose else [],
            discovery_time=discovery_time
        )

    def _detect_platform(self, extracted) -> DetectionResult:
        """Detect AI platform (simplified initial implementation)."""
        metadata = extracted.standard_metadata

        # Check for Civitai/Stable Diffusion in EXIF UserComment
        user_comment = metadata.exif.get("PIL:UserComment") or metadata.exif.get("UserComment")

        if user_comment and isinstance(user_comment, str):
            # Decode if it's a bytes representation
            if user_comment.startswith("b'"):
                user_comment = eval(user_comment)  # Safe here, we control the input
                if isinstance(user_comment, bytes):
                    user_comment = user_comment.decode('utf-16-le', errors='ignore')

            # Check for Civitai/SD indicators
            if "Civitai" in user_comment or "Steps:" in user_comment:
                return DetectionResult(
                    platform_id="civitai_sd",
                    platform_name="Civitai (Stable Diffusion)",
                    confidence=ConfidenceLevel.HIGH,
                    confidence_score=95.0,
                    metadata={"source": "EXIF:UserComment"}
                )

        # Check PNG parameters chunk
        for chunk in extracted.raw_chunks:
            if chunk.chunk_type == "PNG:tEXt" and chunk.decoded_text:
                if "parameters:" in chunk.decoded_text.lower():
                    return DetectionResult(
                        platform_id="stable_diffusion",
                        platform_name="Stable Diffusion",
                        confidence=ConfidenceLevel.HIGH,
                        confidence_score=90.0,
                        metadata={"source": "PNG:tEXt:parameters"}
                    )

        # Default: unknown
        return DetectionResult(
            platform_id="unknown",
            platform_name="Unknown",
            confidence=ConfidenceLevel.UNKNOWN,
            confidence_score=0.0
        )

    def _extract_ai_metadata(self, extracted, detection) -> Optional[AIMetadata]:
        """Extract AI-specific metadata based on detected platform."""
        if detection.platform_id == "unknown":
            return None

        ai_meta = AIMetadata()
        metadata = extracted.standard_metadata

        # Extract from EXIF UserComment (Civitai format)
        user_comment = metadata.exif.get("PIL:UserComment") or metadata.exif.get("UserComment")

        if user_comment:
            # Decode if needed
            if isinstance(user_comment, str) and user_comment.startswith("b'"):
                user_comment = eval(user_comment)
                if isinstance(user_comment, bytes):
                    user_comment = user_comment.decode('utf-16-le', errors='ignore')

            # Parse Civitai format
            if isinstance(user_comment, str):
                # Extract prompt (before "Negative prompt:")
                prompt_match = re.search(r'^(.+?)(?=\nNegative prompt:|$)', user_comment, re.DOTALL)
                if prompt_match:
                    ai_meta.prompts['positive'] = prompt_match.group(1).strip()

                # Extract negative prompt
                neg_match = re.search(r'Negative prompt:\s*(.+?)(?=\nSteps:|$)', user_comment, re.DOTALL)
                if neg_match:
                    ai_meta.prompts['negative'] = neg_match.group(1).strip()

                # Extract parameters
                if 'Steps:' in user_comment:
                    steps_match = re.search(r'Steps:\s*(\d+)', user_comment)
                    if steps_match:
                        ai_meta.parameters['steps'] = int(steps_match.group(1))

                    sampler_match = re.search(r'Sampler:\s*([^,]+)', user_comment)
                    if sampler_match:
                        ai_meta.parameters['sampler'] = sampler_match.group(1).strip()

                    cfg_match = re.search(r'CFG scale:\s*([\d.]+)', user_comment)
                    if cfg_match:
                        ai_meta.parameters['cfg_scale'] = float(cfg_match.group(1))

                    seed_match = re.search(r'Seed:\s*(\d+)', user_comment)
                    if seed_match:
                        ai_meta.parameters['seed'] = int(seed_match.group(1))

                    size_match = re.search(r'Size:\s*(\d+x\d+)', user_comment)
                    if size_match:
                        ai_meta.parameters['size'] = size_match.group(1)

                # Extract Civitai model info
                model_match = re.search(r'"modelName":"([^"]+)"', user_comment)
                if model_match:
                    version_match = re.search(r'"modelVersionName":"([^"]+)"', user_comment)
                    ai_meta.model = ModelInfo(
                        name=model_match.group(1),
                        version=version_match.group(1) if version_match else None,
                        source="Civitai"
                    )

        return ai_meta if (ai_meta.prompts or ai_meta.parameters) else None
