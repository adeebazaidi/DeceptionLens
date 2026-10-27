"""
DeceptionLens — Evidence File Storage
=====================================
Stores original evidence files on disk under server-generated names,
computes SHA-256 baselines, resolves stored files without allowing path
traversal, and re-verifies file integrity against the recorded hash.

The storage directory is configurable via EVIDENCE_STORAGE_DIR
(default: backend/evidence_storage). Maximum upload size is configurable
via MAX_EVIDENCE_SIZE_MB (default: 50).
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

from fastapi import HTTPException

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
STORAGE_DIR = Path(
    os.getenv("EVIDENCE_STORAGE_DIR", str(BASE_DIR / "evidence_storage"))
).resolve()
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

MAX_EVIDENCE_SIZE_MB = float(os.getenv("MAX_EVIDENCE_SIZE_MB", "50"))
MAX_EVIDENCE_SIZE_BYTES = int(MAX_EVIDENCE_SIZE_MB * 1024 * 1024)

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

_HASH_CHUNK_SIZE = 1024 * 1024


def _sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_HASH_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_evidence_file(
    evidence_id: str,
    original_filename: str,
    file_bytes: bytes,
) -> Tuple[str, str, str, int]:
    """
    Validate and persist an evidence file.

    The stored name is derived only from the server-generated evidence_id and
    a whitelisted extension, so the client-supplied filename never influences
    the on-disk path.

    Returns (storage_filename, storage_path, sha256_hash, file_size).
    Raises HTTPException 400 for unsupported/empty files, 413 if too large,
    500 if the file cannot be written.
    """
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file format '{ext or original_filename}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )

    file_size = len(file_bytes)
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded evidence file is empty.")
    if file_size > MAX_EVIDENCE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Evidence file exceeds maximum size of {MAX_EVIDENCE_SIZE_MB:g} MB.",
        )

    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    storage_filename = f"{evidence_id}{ext}"
    storage_path = STORAGE_DIR / storage_filename

    try:
        # "xb" refuses to overwrite an existing evidence file.
        with open(storage_path, "xb") as f:
            f.write(file_bytes)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to store evidence file on the server.",
        ) from exc

    return storage_filename, str(storage_path), sha256_hash, file_size


def get_evidence_file_path(storage_filename: Optional[str]) -> Optional[Path]:
    """
    Resolve a stored filename to its absolute path inside STORAGE_DIR.
    Returns None if the name is empty or would resolve outside STORAGE_DIR.
    """
    if not storage_filename:
        return None
    candidate = (STORAGE_DIR / storage_filename).resolve()
    if candidate.parent != STORAGE_DIR:
        return None
    return candidate


def verify_evidence_integrity(storage_filename: str, recorded_sha256: str) -> Dict:
    """
    Recalculate the SHA-256 of the stored file and compare to the baseline.

    Returns a dict with: status ("Hash Matches" | "Hash Mismatch" |
    "File Unavailable"), matches, recorded_hash, calculated_hash, explanation.
    """
    file_path = get_evidence_file_path(storage_filename)
    if not file_path or not file_path.is_file():
        return {
            "status": "File Unavailable",
            "matches": False,
            "recorded_hash": recorded_sha256,
            "calculated_hash": None,
            "explanation": (
                "The stored evidence file could not be located, so its integrity "
                "cannot be verified against the recorded baseline."
            ),
        }

    calculated = _sha256_of_file(file_path)
    if calculated == recorded_sha256:
        return {
            "status": "Hash Matches",
            "matches": True,
            "recorded_hash": recorded_sha256,
            "calculated_hash": calculated,
            "explanation": (
                "The SHA-256 hash of the stored file matches the recorded baseline. "
                "The file is byte-for-byte identical to the evidence as originally acquired."
            ),
        }

    return {
        "status": "Hash Mismatch",
        "matches": False,
        "recorded_hash": recorded_sha256,
        "calculated_hash": calculated,
        "explanation": (
            "The SHA-256 hash of the stored file differs from the recorded baseline. "
            "The file has been modified or corrupted since it was acquired."
        ),
    }
