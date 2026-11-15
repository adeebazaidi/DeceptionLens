"""
Secure Evidence Storage Manager
==============================
Handles controlled file storage, path-traversal prevention, safe naming,
and cryptographic SHA-256 integrity calculation & verification.
"""

import hashlib
import os
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

from fastapi import HTTPException

BASE_DIR = Path(__file__).parent.parent  # backend/
STORAGE_DIR = BASE_DIR / "evidence_storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Maximum file size allowed: 25 MB
MAX_EVIDENCE_SIZE_MB = float(os.getenv("MAX_EVIDENCE_SIZE_MB", "25"))
MAX_EVIDENCE_SIZE_BYTES = int(MAX_EVIDENCE_SIZE_MB * 1024 * 1024)

# Supported extensions across image, fingerprint, signature, and document forensics
ALLOWED_EXTENSIONS = {
    # Images / Fingerprints / Signatures
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff",
    # Documents
    ".pdf",
}

MIME_TYPE_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".pdf": "application/pdf",
}


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing dangerous directory traversal characters,
    null bytes, and special shell characters.
    """
    if not filename:
        return "unnamed_evidence"
    
    # Strip paths
    clean_name = os.path.basename(filename.strip().replace("\\", "/"))
    # Replace unsafe characters with underscore
    clean_name = re.sub(r"[^a-zA-Z0-9._-]", "_", clean_name)
    # Prevent hidden files
    clean_name = clean_name.lstrip(".")
    if not clean_name:
        clean_name = "unnamed_evidence"
    return clean_name[:120]  # Limit length


def is_safe_path(base_dir: Path, target_path: Path) -> bool:
    """
    Strictly verifies that target_path resolves inside base_dir
    to prevent path traversal attacks.
    """
    try:
        resolved_base = base_dir.resolve()
        resolved_target = target_path.resolve()
        return str(resolved_target).startswith(str(resolved_base))
    except Exception:
        return False


def calculate_sha256(file_path: Path) -> str:
    """
    Calculates SHA-256 hash of a file on disk using 64KB streaming chunks.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest().lower()


def calculate_bytes_sha256(content: bytes) -> str:
    """
    Calculates SHA-256 hash of byte buffer in memory.
    """
    return hashlib.sha256(content).hexdigest().lower()


def save_evidence_file(evidence_id: str, original_filename: str, file_bytes: bytes) -> Tuple[str, str, str, int]:
    """
    Validates, hashes, and saves evidence to the controlled storage directory.
    Returns: (safe_storage_filename, relative_storage_path, sha256_hash, file_size)
    """
    # 1. Size check
    file_size = len(file_bytes)
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Cannot upload empty file.")
    if file_size > MAX_EVIDENCE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Evidence file exceeds maximum allowed size of {MAX_EVIDENCE_SIZE_MB} MB.",
        )

    # 2. Extension check
    suffix = Path(original_filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file format '{suffix}'. "
                f"Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
            ),
        )

    # 3. Safe internal filename
    safe_name = sanitize_filename(original_filename)
    storage_filename = f"{evidence_id}_{safe_name}"
    target_path = STORAGE_DIR / storage_filename

    # 4. Strict Path Traversal Check
    if not is_safe_path(STORAGE_DIR, target_path):
        raise HTTPException(status_code=400, detail="Invalid file destination path detected.")

    # 5. Compute SHA-256 hash
    sha256_hash = calculate_bytes_sha256(file_bytes)

    # 6. Save original file content unmodified
    try:
        with open(target_path, "wb") as f:
            f.write(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store evidence file: {str(e)}")

    relative_path = str(target_path.relative_to(BASE_DIR)).replace("\\", "/")
    return storage_filename, relative_path, sha256_hash, file_size


def get_evidence_file_path(storage_filename: str) -> Optional[Path]:
    """
    Retrieves and validates the absolute path to a stored evidence file.
    Returns None if file is missing or traverses outside the storage directory.
    """
    target_path = STORAGE_DIR / storage_filename
    if not is_safe_path(STORAGE_DIR, target_path):
        return None
    if not target_path.is_file():
        return None
    return target_path


def verify_evidence_integrity(storage_filename: str, recorded_sha256: str) -> Dict[str, any]:
    """
    Recalculates the cryptographic SHA-256 hash of the stored file on disk
    and compares it to the hash recorded in the database during upload.
    """
    target_path = get_evidence_file_path(storage_filename)

    if target_path is None or not target_path.exists():
        return {
            "status": "File Unavailable",
            "matches": False,
            "recorded_hash": recorded_sha256,
            "calculated_hash": None,
            "explanation": "The physical evidence file cannot be found in the secure storage repository.",
        }

    try:
        calculated_hash = calculate_sha256(target_path)
    except Exception as e:
        return {
            "status": "Read Error",
            "matches": False,
            "recorded_hash": recorded_sha256,
            "calculated_hash": None,
            "explanation": f"Unable to read file for hashing: {str(e)}",
        }

    is_match = (calculated_hash.lower() == recorded_sha256.lower())

    if is_match:
        status_label = "Hash Matches"
        explanation = (
            "Cryptographic SHA-256 hash matches the recorded baseline. "
            "The physical file content on disk is identical to when it was first recorded. "
            "Note: A matching hash confirms file integrity since acquisition, but does not prove authenticity prior to upload."
        )
    else:
        status_label = "Hash Mismatch"
        explanation = (
            "WARNING: Cryptographic SHA-256 hash differs from the recorded baseline! "
            "The file on disk has been altered, corrupted, or replaced since initial evidence acquisition."
        )

    return {
        "status": status_label,
        "matches": is_match,
        "recorded_hash": recorded_sha256,
        "calculated_hash": calculated_hash,
        "explanation": explanation,
    }
