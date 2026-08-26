"""
Noise Analysis Module
=====================
Estimates spatial noise in an image using a Gaussian blur subtraction method.

Pipeline:
  Grayscale → Gaussian Blur → Absolute Difference → Noise Map

The noise map is an approximation of high-frequency residuals.
It is an analytical indicator only.
"""

import os
from typing import Dict

import cv2
import numpy as np


def estimate_noise_map(gray: np.ndarray, blur_kernel: int = 3) -> np.ndarray:
    """
    Estimate per-pixel noise using Gaussian blur subtraction.

    Args:
        gray:         Grayscale image (uint8).
        blur_kernel:  Gaussian kernel size (must be odd, default 3).

    Returns:
        Noise map as float32 ndarray in [0, 255].
    """
    if blur_kernel % 2 == 0:
        blur_kernel += 1

    blurred = cv2.GaussianBlur(gray, (blur_kernel, blur_kernel), 0)
    noise_map = np.abs(gray.astype(np.float32) - blurred.astype(np.float32))
    return noise_map


def save_noise_map(noise_map: np.ndarray, output_path: str) -> None:
    """
    Save a false-color visualization of the noise map as PNG.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Normalize to 0-255 for display
    n_min, n_max = noise_map.min(), noise_map.max()
    if n_max > n_min:
        normalized = ((noise_map - n_min) / (n_max - n_min) * 255).astype(np.uint8)
    else:
        normalized = np.zeros_like(noise_map, dtype=np.uint8)

    colored = cv2.applyColorMap(normalized, cv2.COLORMAP_HOT)
    cv2.imwrite(output_path, colored)


def compute_noise_stats(noise_map: np.ndarray) -> Dict[str, float]:
    """
    Compute summary statistics from a noise map.

    Returns:
        mean: Average noise level.
        std:  Standard deviation of noise.
        max:  Maximum noise value.
    """
    return {
        "mean": round(float(noise_map.mean()), 4),
        "std": round(float(noise_map.std()), 4),
        "max": round(float(noise_map.max()), 4),
    }
