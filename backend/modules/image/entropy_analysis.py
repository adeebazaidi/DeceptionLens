"""
Entropy Analysis Module
=======================
Calculates Shannon entropy globally and locally across image blocks.

Shannon entropy:  H(X) = -Σ p(xᵢ) · log₂(p(xᵢ))

All values are indicators for research/educational purposes only.
A high entropy anomaly score suggests local variation but does NOT
constitute proof of image manipulation.
"""

import os
from typing import Dict

import cv2
import numpy as np
from PIL import Image


# ── Core entropy functions ────────────────────────────────────────────────────

def calculate_global_entropy(gray: np.ndarray) -> float:
    """
    Compute Shannon entropy over the entire grayscale image histogram.

    Returns entropy in bits (0 = uniform constant image, max ~8 for random).
    """
    hist, _ = np.histogram(gray.ravel(), bins=256, range=(0, 256))
    hist = hist[hist > 0]  # Remove zero bins to avoid log(0)
    probs = hist / hist.sum()
    return float(-np.sum(probs * np.log2(probs)))


def calculate_local_entropy(
    gray: np.ndarray,
    grid_size: int = 8,
) -> np.ndarray:
    """
    Divide the image into (grid_size × grid_size) blocks and compute
    Shannon entropy for each block.

    Returns a 2D numpy array of per-block entropy values.
    """
    h, w = gray.shape
    block_h = max(1, h // grid_size)
    block_w = max(1, w // grid_size)

    rows = h // block_h
    cols = w // block_w
    entropy_map = np.zeros((rows, cols), dtype=np.float32)

    for r in range(rows):
        for c in range(cols):
            block = gray[
                r * block_h : (r + 1) * block_h,
                c * block_w : (c + 1) * block_w,
            ]
            entropy_map[r, c] = calculate_global_entropy(block)

    return entropy_map


def compute_entropy_stats(
    gray: np.ndarray,
    grid_size: int = None,
) -> Dict[str, float]:
    """
    Compute a full entropy statistics dictionary.

    anomaly_score: heuristic indicator = normalized std of local entropy.
    A higher value suggests greater local variation in image complexity.
    This is NOT a definitive indicator of manipulation.
    """
    if grid_size is None:
        grid_size = int(os.getenv("ENTROPY_GRID_SIZE", "8"))

    global_e = calculate_global_entropy(gray)
    local_map = calculate_local_entropy(gray, grid_size=grid_size)

    mean_local = float(np.mean(local_map))
    std_local = float(np.std(local_map))
    min_local = float(np.min(local_map))
    max_local = float(np.max(local_map))

    # Anomaly score: std relative to mean (coefficient of variation), clamped [0,1]
    # Heuristic only — higher values warrant closer inspection, not conclusions.
    if mean_local > 0:
        anomaly_score = float(min(std_local / mean_local, 1.0))
    else:
        anomaly_score = 0.0

    return {
        "global": round(global_e, 4),
        "mean_local": round(mean_local, 4),
        "std_local": round(std_local, 4),
        "min_local": round(min_local, 4),
        "max_local": round(max_local, 4),
        "anomaly_score": round(anomaly_score, 4),
    }


# ── Visualization ─────────────────────────────────────────────────────────────

def generate_entropy_heatmap(
    pil_image: Image.Image,
    gray: np.ndarray,
    output_path: str,
    grid_size: int = None,
) -> None:
    """
    Generate an entropy heatmap overlay and save it as a PNG.

    The heatmap is a false-color visualization of per-block Shannon entropy
    blended with the original image for context. It is an analytical aid only.
    """
    if grid_size is None:
        grid_size = int(os.getenv("ENTROPY_GRID_SIZE", "8"))

    local_map = calculate_local_entropy(gray, grid_size=grid_size)

    # Upscale entropy map to image size
    h, w = gray.shape
    entropy_upscaled = cv2.resize(
        local_map,
        (w, h),
        interpolation=cv2.INTER_NEAREST,
    )

    # Normalize to 0-255 for colormap
    e_min, e_max = entropy_upscaled.min(), entropy_upscaled.max()
    if e_max > e_min:
        normalized = ((entropy_upscaled - e_min) / (e_max - e_min) * 255).astype(np.uint8)
    else:
        normalized = np.zeros((h, w), dtype=np.uint8)

    heatmap_bgr = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)

    # Blend heatmap with original image
    original_bgr = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    original_bgr = cv2.resize(original_bgr, (w, h))
    overlay = cv2.addWeighted(original_bgr, 0.5, heatmap_bgr, 0.5, 0)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, overlay)
