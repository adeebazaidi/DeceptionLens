"""
DeceptionLens — Fingerprint Ridge Enhancement Module
====================================================
Enhances ridge clarity, estimates local ridge orientation field,
and segments the active fingerprint region from background noise.
"""

from typing import Tuple
import cv2
import numpy as np


def compute_foreground_mask(gray: np.ndarray, block_size: int = 16, threshold: float = 0.1) -> np.ndarray:
    """
    Computes a binary mask isolating the fingerprint impression from blank sensor background
    using local block intensity variance.

    Args:
        gray: 8-bit grayscale image.
        block_size: Size of blocks to evaluate variance.
        threshold: Normalized variance threshold below which a block is considered background.

    Returns:
        Binary mask (uint8, 255 for foreground, 0 for background).
    """
    h, w = gray.shape
    mask = np.zeros((h, w), dtype=np.uint8)

    # Standardize image to [0, 1]
    norm = gray.astype(np.float32) / 255.0

    for y in range(0, h, block_size):
        for x in range(0, w, block_size):
            block = norm[y:min(y + block_size, h), x:min(x + block_size, w)]
            var = np.var(block)
            if var > threshold:
                mask[y:min(y + block_size, h), x:min(x + block_size, w)] = 255

    # Smooth the mask to remove isolated noise holes and smooth boundaries
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    eroded = cv2.erode(closed, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))

    # Fallback if erosion eliminated too much of the fingerprint area
    if np.count_nonzero(eroded) >= (h * w * 0.15):
        return eroded
    if np.count_nonzero(closed) >= (h * w * 0.15):
        return closed
    return np.full((h, w), 255, dtype=np.uint8)


def estimate_orientation_field(gray: np.ndarray, block_size: int = 16) -> np.ndarray:
    """
    Estimates the dominant ridge orientation field using gradient covariance (Rao / Hong method).

    For each block, computes:
        Vx = sum(2 * Gx * Gy)
        Vy = sum(Gx^2 - Gy^2)
        theta = 0.5 * atan2(Vx, Vy) + pi / 2

    Returns:
        2D numpy array of angles in radians [-pi/2, pi/2] sized (h // block_size, w // block_size).
    """
    h, w = gray.shape
    grad_x = cv2.Sobel(gray.astype(np.float32), cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray.astype(np.float32), cv2.CV_32F, 0, 1, ksize=3)

    out_h = (h + block_size - 1) // block_size
    out_w = (w + block_size - 1) // block_size
    orientations = np.zeros((out_h, out_w), dtype=np.float32)

    vx = 2.0 * grad_x * grad_y
    vy = grad_x ** 2 - grad_y ** 2

    for by in range(out_h):
        y0 = by * block_size
        y1 = min(y0 + block_size, h)
        for bx in range(out_w):
            x0 = bx * block_size
            x1 = min(x0 + block_size, w)

            block_vx = np.sum(vx[y0:y1, x0:x1])
            block_vy = np.sum(vy[y0:y1, x0:x1])

            # Ridge direction is orthogonal to gradient direction
            theta = 0.5 * np.arctan2(block_vx, block_vy) + np.pi / 2.0
            # Wrap to [-pi/2, pi/2]
            if theta > np.pi / 2.0:
                theta -= np.pi
            elif theta < -np.pi / 2.0:
                theta += np.pi
            orientations[by, bx] = theta

    return orientations


def enhance_ridges(
    gray: np.ndarray,
    foreground_mask: np.ndarray = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Enhances fingerprint ridge patterns using a modular, explainable pipeline:
    1. Unsharp masking to accentuate ridge edges.
    2. Morphological Black-Hat and Top-Hat filtering to separate dark ridges from light valleys.
    3. Foreground masking to suppress background sensor artifacts.

    Returns:
        (enhanced_grayscale_image, foreground_mask)
    """
    if foreground_mask is None:
        foreground_mask = compute_foreground_mask(gray, block_size=16, threshold=0.005)

    # 1. Unsharp masking: enhances ridge transitions
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.0)
    unsharp = cv2.addWeighted(gray, 1.6, blurred, -0.6, 0)
    unsharp = np.clip(unsharp, 0, 255).astype(np.uint8)

    # 2. Morphological filtering (Top-hat highlights ridges/bright peaks; Black-hat highlights dark valleys)
    # Using an elliptical structuring element matching typical ridge width (3-5 pixels)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    top_hat = cv2.morphologyEx(unsharp, cv2.MORPH_TOPHAT, kernel)
    black_hat = cv2.morphologyEx(unsharp, cv2.MORPH_BLACKHAT, kernel)

    # Combined enhanced ridge map: original + top_hat - black_hat
    enhanced = cv2.add(unsharp, top_hat)
    enhanced = cv2.subtract(enhanced, black_hat)

    # Normalize dynamic range to [0, 255]
    enhanced = cv2.normalize(enhanced, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)

    # Apply foreground mask
    enhanced = cv2.bitwise_and(enhanced, enhanced, mask=foreground_mask)

    return enhanced, foreground_mask
