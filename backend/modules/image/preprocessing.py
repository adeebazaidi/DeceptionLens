"""
Preprocessing Module
====================
Loads images from disk and extracts basic metadata.
"""

from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError


def validate_image(path: str) -> None:
    """
    Attempt to open and verify the image with Pillow.
    Raises HTTPException if the file is not a valid image.
    """
    try:
        with Image.open(path) as img:
            img.verify()  # Does not decode — fast check
    except (UnidentifiedImageError, Exception) as exc:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is not a valid image or is corrupted.",
        ) from exc


def load_image(path: str) -> Tuple[Image.Image, np.ndarray, np.ndarray]:
    """
    Load an image and return:
      - PIL Image (RGB)
      - OpenCV image (BGR uint8)
      - Grayscale image (uint8)
    """
    pil_img = Image.open(path).convert("RGB")
    cv_img = cv2.imread(path)
    if cv_img is None:
        # Fallback: convert from PIL
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    return pil_img, cv_img, gray


def get_image_info(path: str, upload_file: UploadFile, content: bytes) -> dict:
    """
    Return basic image metadata: format, dimensions, file size.
    """
    try:
        with Image.open(path) as img:
            width, height = img.size
            fmt = img.format or Path(upload_file.filename or "").suffix.upper().lstrip(".")
    except Exception:
        width, height, fmt = 0, 0, "UNKNOWN"

    return {
        "width": width,
        "height": height,
        "format": fmt,
        "file_size": len(content),
    }
