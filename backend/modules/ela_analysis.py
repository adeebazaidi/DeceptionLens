"""
Error Level Analysis (ELA) Module
===================================
ELA compresses an image at a known quality, then computes the absolute
difference between the original and re-compressed versions.

Regions with significantly different error levels MAY suggest different
compression histories. However, many factors affect ELA output, including
natural JPEG artifacts, image content complexity, and original quality.

ELA is an ANALYTICAL INDICATOR — not proof of manipulation.
"""

import io
import os
from typing import Dict

import numpy as np
from PIL import Image


def perform_ela(
    image_path: str,
    quality: int = None,
    scale: int = None,
) -> Image.Image:
    """
    Perform Error Level Analysis on an image file.

    Steps:
      1. Open the image.
      2. Re-save to an in-memory buffer at the specified JPEG quality.
      3. Reload the re-compressed version.
      4. Compute absolute pixel difference, scaled for visibility.

    Args:
        image_path: Path to the original image.
        quality:    JPEG re-compression quality (default from env, 90).
        scale:      Multiplier to amplify the difference (default from env, 10).

    Returns:
        PIL Image representing the ELA difference map (RGB).
    """
    if quality is None:
        quality = int(os.getenv("ELA_QUALITY", "90"))
    if scale is None:
        scale = int(os.getenv("ELA_SCALE", "10"))

    original = Image.open(image_path).convert("RGB")

    # Re-compress to JPEG in memory
    buffer = io.BytesIO()
    original.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    recompressed = Image.open(buffer).convert("RGB")

    # Compute absolute difference, amplify for visibility
    orig_arr = np.array(original, dtype=np.float32)
    recomp_arr = np.array(recompressed, dtype=np.float32)
    diff = np.abs(orig_arr - recomp_arr) * scale
    diff = np.clip(diff, 0, 255).astype(np.uint8)

    return Image.fromarray(diff, mode="RGB")


def save_ela_image(ela_image: Image.Image, output_path: str) -> None:
    """Save the ELA image to disk as PNG."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    ela_image.save(output_path, format="PNG")


def compute_ela_stats(ela_image: Image.Image) -> Dict[str, float]:
    """
    Compute summary statistics from an ELA difference image.

    Returns:
        mean: Average pixel error level.
        std:  Standard deviation of error levels.
        max:  Maximum observed error level.
    """
    arr = np.array(ela_image, dtype=np.float32)
    # Use grayscale luminance for stats
    gray = arr.mean(axis=2)
    return {
        "mean": round(float(gray.mean()), 4),
        "std": round(float(gray.std()), 4),
        "max": round(float(gray.max()), 4),
    }
