"""
DeceptionLens — Secure Evidence Storage
=======================================
Stores original evidence files on disk under server-generated names,
computes SHA-256 baselines, resolves stored files without allowing path
traversal, and re-verifies file integrity against the recorded hash.

The storage directory is configurable via EVIDENCE_STORAGE_DIR
(default: backend/evidence_storage); the Docker setup and the test suite
rely on this. Maximum upload size is configurable via MAX_EVIDENCE_SIZE_MB
(default: 25, matching the frontend limit).
"""

import hashlib
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from fastapi import HTTPException

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
STORAGE_DIR = Path(
    os.getenv("EVIDENCE_STORAGE_DIR", str(BASE_DIR / "evidence_storage"))
).resolve()
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

MAX_EVIDENCE_SIZE_MB = float(os.getenv("MAX_EVIDENCE_SIZE_MB", "25"))
MAX_EVIDENCE_SIZE_BYTES = int(MAX_EVIDENCE_SIZE_MB * 1024 * 1024)

# Supported formats across image, fingerprint, signature, and document forensics
MIME_TYPE_MAP: Dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".pdf": "application/pdf",
}
ALLOWED_EXTENSIONS = set(MIME_TYPE_MAP)

_HASH_CHUNK_SIZE = 64 * 1024


def is_safe_path(base_dir: Path, target_path: Path) -> bool:
    """True if target_path resolves inside base_dir (prevents path traversal)."""
    try:
        target_path.resolve().relative_to(base_dir.resolve())
        return True
    except (ValueError, OSError):
        return False


def calculate_sha256(file_path: Path) -> str:
    """SHA-256 of a file on disk, streamed in 64 KB chunks."""
    digest = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(_HASH_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def calculate_bytes_sha256(content: bytes) -> str:
    """SHA-256 of an in-memory byte buffer."""
    return hashlib.sha256(content).hexdigest()


def save_evidence_file(
    evidence_id: str,
    original_filename: str,
    file_bytes: bytes,
) -> Tuple[str, str, str, int]:
    """
    Validate and persist an evidence file, leaving its content unmodified.

    The stored name is derived only from the server-generated evidence_id and
    a whitelisted extension, so the client-supplied filename never influences
    the on-disk path.

    Returns (storage_filename, storage_path, sha256_hash, file_size).
    Raises HTTPException 400 for unsupported/empty files, 413 if too large,
    500 if the file cannot be written.
    """
    file_size = len(file_bytes)
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Cannot upload empty file.")
    if file_size > MAX_EVIDENCE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Evidence file exceeds maximum allowed size of {MAX_EVIDENCE_SIZE_MB:g} MB.",
        )

    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file format '{ext or original_filename}'. "
                f"Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
            ),
        )

    storage_filename = f"{evidence_id}{ext}"
    storage_path = STORAGE_DIR / storage_filename
    if not is_safe_path(STORAGE_DIR, storage_path):
        raise HTTPException(status_code=400, detail="Invalid file destination path detected.")

    sha256_hash = calculate_bytes_sha256(file_bytes)

    try:
        # "xb" refuses to overwrite an existing evidence file.
        with open(storage_path, "xb") as f:
            f.write(file_bytes)
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Failed to store evidence file on the server.") from exc

    return storage_filename, str(storage_path), sha256_hash, file_size


def get_evidence_file_path(storage_filename: Optional[str]) -> Optional[Path]:
    """
    Resolve a stored filename to its absolute path directly inside STORAGE_DIR.
    Returns None if the name is empty or would resolve anywhere else.
    """
    if not storage_filename:
        return None
    candidate = (STORAGE_DIR / storage_filename).resolve()
    if candidate.parent != STORAGE_DIR:
        return None
    return candidate


def verify_evidence_integrity(storage_filename: str, recorded_sha256: str) -> Dict[str, Any]:
    """
    Recalculate the SHA-256 of the stored file and compare it to the baseline.

    Returns a dict with: status ("Hash Matches" | "Hash Mismatch" |
    "File Unavailable" | "Read Error"), matches, recorded_hash,
    calculated_hash, explanation.
    """
    file_path = get_evidence_file_path(storage_filename)
    if not file_path or not file_path.is_file():
        return {
            "status": "File Unavailable",
            "matches": False,
            "recorded_hash": recorded_sha256,
            "calculated_hash": None,
            "explanation": "The physical evidence file cannot be found in the secure storage repository.",
        }

    try:
        calculated = calculate_sha256(file_path)
    except OSError as exc:
        return {
            "status": "Read Error",
            "matches": False,
            "recorded_hash": recorded_sha256,
            "calculated_hash": None,
            "explanation": f"Unable to read file for hashing: {exc}",
        }

    if calculated.lower() == recorded_sha256.lower():
        return {
            "status": "Hash Matches",
            "matches": True,
            "recorded_hash": recorded_sha256,
            "calculated_hash": calculated,
            "explanation": (
                "Cryptographic SHA-256 hash matches the recorded baseline. "
                "The file on disk is identical to when it was first recorded. "
                "Note: a matching hash confirms integrity since acquisition, "
                "but does not prove authenticity prior to upload."
            ),
        }

    return {
        "status": "Hash Mismatch",
        "matches": False,
        "recorded_hash": recorded_sha256,
        "calculated_hash": calculated,
        "explanation": (
            "WARNING: Cryptographic SHA-256 hash differs from the recorded baseline. "
            "The file on disk has been altered, corrupted, or replaced since acquisition."
        ),
    }
