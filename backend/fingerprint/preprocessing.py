"""
DeceptionLens — Fingerprint Preprocessing Module
================================================
Handles image decoding, grayscale conversion, aspect-preserving dimension
normalization, noise reduction, and contrast enhancement.
"""

from typing import Tuple, Dict, Any, Optional
import cv2
import numpy as np


# Minimum allowable dimension for a valid fingerprint image
MIN_DIMENSION = 48
TARGET_MIN_DIMENSION = 260
MAX_NORMALIZED_DIMENSION = 640


def decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    """
    Decodes raw image bytes into an OpenCV BGR or grayscale numpy array.

    Raises:
        ValueError: If bytes cannot be decoded as an image.
    """
    if not image_bytes:
        raise ValueError("Image bytes are empty.")

    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

    if image is None:
        raise ValueError("Failed to decode image. File may be corrupted or unsupported.")

    return image


def load_image_from_path(image_path: str) -> np.ndarray:
    """
    Loads an image from filesystem using OpenCV.

    Raises:
        ValueError: If file cannot be read.
    """
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"Could not load image from '{image_path}'.")
    return image


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """
    Converts 3-channel BGR or 4-channel BGRA image into a single-channel 8-bit grayscale image.
    """
    if len(image.shape) == 2:
        return image.copy()

    if image.shape[2] == 4:
        # Convert BGRA to BGR then to Gray, or use Alpha channel composite
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

    if len(image.shape) == 3 and image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    raise ValueError(f"Unexpected image shape: {image.shape}")


def resize_preserve_aspect(
    image: np.ndarray,
    max_dim: int = MAX_NORMALIZED_DIMENSION,
    target_min: int = TARGET_MIN_DIMENSION,
) -> Tuple[np.ndarray, float]:
    """
    Resizes image maintaining aspect ratio:
    - Downscales large scans so neither width nor height exceeds max_dim.
    - Upscales small impressions (e.g., SOCOFing 96x103) so minimum dimension reaches target_min,
      ensuring optimal spatial frequency for minutiae extraction filters.
    - Leaves standard resolution impressions within [target_min, max_dim] unchanged (scale = 1.0).

    Returns:
        (resized_image, scale_factor)
    """
    h, w = image.shape[:2]
    if h < MIN_DIMENSION or w < MIN_DIMENSION:
        raise ValueError(
            f"Image dimensions ({w}x{h}) are too small. "
            f"Minimum allowable dimension is {MIN_DIMENSION}x{MIN_DIMENSION} pixels."
        )

    # Upscale small sensor impressions (e.g. SOCOFing)
    if min(h, w) < target_min:
        scale = target_min / float(min(h, w))
        new_w = max(int(round(w * scale)), 1)
        new_h = max(int(round(h * scale)), 1)
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        return resized, scale

    # Downscale overly large high-resolution scans
    if max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
        new_w = max(int(round(w * scale)), 1)
        new_h = max(int(round(h * scale)), 1)
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return resized, scale

    return image.copy(), 1.0


def reduce_noise(gray: np.ndarray, method: str = "median") -> np.ndarray:
    """
    Reduces high-frequency sensor noise while preserving fingerprint ridge edges.
    Uses median blur or subtle bilateral filtering.
    """
    if method == "median":
        # 3x3 median filter effectively removes salt-and-pepper sensor noise
        return cv2.medianBlur(gray, 3)
    elif method == "bilateral":
        # Bilateral filter smooths flat regions while preserving sharp ridge boundaries
        return cv2.bilateralFilter(gray, d=5, sigmaColor=35, sigmaSpace=35)
    elif method == "gaussian":
        return cv2.GaussianBlur(gray, (3, 3), 0.8)
    return cv2.medianBlur(gray, 3)


def enhance_contrast_clahe(gray: np.ndarray, clip_limit: float = 2.5, tile_size: int = 8) -> np.ndarray:
    """
    Enhances local contrast across unevenly illuminated fingerprint impressions using
    Contrast Limited Adaptive Histogram Equalization (CLAHE).
    """
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
    return clahe.apply(gray)


def preprocess_fingerprint(
    source: Any,
    max_dim: int = MAX_NORMALIZED_DIMENSION,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Executes complete fingerprint preprocessing pipeline:
    1. Read / decode image
    2. Convert to grayscale
    3. Normalize dimensions (preserve aspect ratio)
    4. Suppress sensor noise
    5. Enhance contrast using CLAHE

    Args:
        source: File path (str) or raw image bytes (bytes) or existing np.ndarray.
        max_dim: Maximum dimension for normalization.

    Returns:
        (original_bgr_or_gray, preprocessed_gray, metadata_dict)
    """
    if isinstance(source, bytes):
        raw_img = decode_image_bytes(source)
    elif isinstance(source, str):
        raw_img = load_image_from_path(source)
    elif isinstance(source, np.ndarray):
        raw_img = source.copy()
    else:
        raise TypeError(f"Unsupported source type: {type(source)}")

    orig_h, orig_w = raw_img.shape[:2]

    # Convert to grayscale
    gray = to_grayscale(raw_img)

    # Normalize dimensions
    resized_gray, scale = resize_preserve_aspect(gray, max_dim=max_dim)
    curr_h, curr_w = resized_gray.shape[:2]

    # Noise reduction
    denoised = reduce_noise(resized_gray, method="median")

    # Contrast enhancement (CLAHE)
    normalized = enhance_contrast_clahe(denoised, clip_limit=2.5, tile_size=8)

    meta = {
        "original_width": orig_w,
        "original_height": orig_h,
        "processed_width": curr_w,
        "processed_height": curr_h,
        "scale_factor": round(scale, 4),
    }

    return raw_img, normalized, meta
