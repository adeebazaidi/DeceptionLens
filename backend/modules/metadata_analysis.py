"""
Metadata Analysis Module
========================
Extracts available image metadata including EXIF data.

Missing metadata is returned as null.
Absence of metadata is NOT treated as suspicious —
many legitimate images lack EXIF data.
"""

import os
from typing import Any, Dict, Optional

from PIL import Image
from PIL.ExifTags import TAGS


def _safe_exif_value(val: Any) -> Any:
    """Convert EXIF value to a JSON-serializable type."""
    if isinstance(val, bytes):
        try:
            return val.decode("utf-8", errors="replace")
        except Exception:
            return None
    if isinstance(val, (int, float, str, bool, type(None))):
        return val
    return str(val)


def extract_metadata(image_path: str, pil_image: Image.Image) -> Dict[str, Any]:
    """
    Extract available metadata from an image.

    Returns a dictionary with:
      - format, width, height, file_size
      - exif: dict of human-readable EXIF tags (if available)
      - software: the Software EXIF tag (if present)

    All fields default to null if unavailable.
    Missing metadata does NOT indicate manipulation.
    """
    result: Dict[str, Any] = {
        "format": None,
        "width": None,
        "height": None,
        "file_size_bytes": None,
        "mode": None,
        "exif": None,
        "software": None,
    }

    try:
        result["format"] = pil_image.format
        result["width"], result["height"] = pil_image.size
        result["mode"] = pil_image.mode
        result["file_size_bytes"] = os.path.getsize(image_path) if os.path.exists(image_path) else None
    except Exception:
        pass

    # EXIF extraction
    try:
        raw_exif = pil_image._getexif()  # type: ignore[attr-defined]
        if raw_exif:
            exif_dict: Dict[str, Any] = {}
            for tag_id, value in raw_exif.items():
                tag_name = TAGS.get(tag_id, str(tag_id))
                safe_val = _safe_exif_value(value)
                if safe_val is not None:
                    exif_dict[tag_name] = safe_val

            result["exif"] = exif_dict if exif_dict else None
            result["software"] = exif_dict.get("Software")
    except (AttributeError, Exception):
        # PNG, WEBP, and other formats may not have EXIF via _getexif()
        try:
            info = pil_image.info or {}
            if info:
                # Filter to JSON-serializable values only
                safe_info = {
                    k: _safe_exif_value(v)
                    for k, v in info.items()
                    if isinstance(k, str)
                }
                result["exif"] = safe_info if safe_info else None
        except Exception:
            pass

    return result
