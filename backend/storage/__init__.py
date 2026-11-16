"""
DeceptionLens — Storage Package
===============================
Secure on-disk storage for original evidence files (see evidence_storage.py).
"""

from .evidence_storage import (
    STORAGE_DIR,
    calculate_sha256,
    get_evidence_file_path,
    is_safe_path,
    save_evidence_file,
    verify_evidence_integrity,
)

__all__ = [
    "save_evidence_file",
    "get_evidence_file_path",
    "calculate_sha256",
    "verify_evidence_integrity",
    "is_safe_path",
    "STORAGE_DIR",
]
