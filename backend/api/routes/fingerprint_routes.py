"""
DeceptionLens — Fingerprint Comparison API Route
================================================
Provides POST /api/fingerprint/compare endpoint for forensic fingerprint verification.
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from fingerprint.service import compare_fingerprints
from fingerprint.matching import DEFAULT_MATCH_THRESHOLD

router = APIRouter()

MAX_SIZE_MB = float(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
MAX_SIZE_BYTES = int(MAX_SIZE_MB * 1024 * 1024)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def _validate_file_metadata(file: UploadFile, label: str) -> str:
    """Validates filename extension and returns the lowercase suffix."""
    if not file or not file.filename:
        raise HTTPException(
            status_code=400,
            detail=f"{label} image is missing or has no filename.",
        )

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file format '{suffix}' for {label}. "
                f"Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
            ),
        )
    return suffix


@router.post("/compare")
async def compare_fingerprint_endpoint(
    reference: Optional[UploadFile] = File(None),
    questioned: Optional[UploadFile] = File(None),
    reference_image: Optional[UploadFile] = File(None),
    questioned_image: Optional[UploadFile] = File(None),
    threshold: Optional[float] = Form(None),
):
    """
    Compare two fingerprint images using minutiae-based forensic feature matching.

    Accepts:
    - **reference** (or **reference_image**): Reference fingerprint impression
    - **questioned** (or **questioned_image**): Questioned / latent / query fingerprint impression
    - **threshold** (optional): Custom match threshold percentage (default: 45.0%)

    Returns:
    - **success**: bool
    - **result**: 'Likely Match' or 'Likely Non-Match'
    - **similarity_score**: float (0.0 to 100.0)
    - **reference_minutiae**: int
    - **questioned_minutiae**: int
    - **matched_minutiae**: int
    - **threshold**: float
    - **processing_time**: float (seconds)
    - **visualizations**: URLs for enhanced images, skeletons, minutiae, and correspondence map
    """
    # Accept either parameter name alias
    ref_file = reference or reference_image
    quest_file = questioned or questioned_image

    if ref_file is None:
        raise HTTPException(
            status_code=400,
            detail="Reference fingerprint image is required. Please provide 'reference' file.",
        )

    if quest_file is None:
        raise HTTPException(
            status_code=400,
            detail="Questioned fingerprint image is required. Please provide 'questioned' file.",
        )

    # 1. Validate file types
    _validate_file_metadata(ref_file, "Reference")
    _validate_file_metadata(quest_file, "Questioned")

    # 2. Read contents and check sizes
    try:
        ref_bytes = await ref_file.read()
        quest_bytes = await quest_file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded files: {str(exc)}") from exc

    if len(ref_bytes) == 0:
        raise HTTPException(status_code=400, detail="Reference image file is empty.")
    if len(quest_bytes) == 0:
        raise HTTPException(status_code=400, detail="Questioned image file is empty.")

    if len(ref_bytes) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Reference file exceeds maximum size of {MAX_SIZE_MB} MB.",
        )
    if len(quest_bytes) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Questioned file exceeds maximum size of {MAX_SIZE_MB} MB.",
        )

    match_threshold = float(threshold) if threshold is not None else DEFAULT_MATCH_THRESHOLD

    # 3. Execute comparison pipeline
    try:
        result = compare_fingerprints(
            ref_source=ref_bytes,
            quest_source=quest_bytes,
            threshold=match_threshold,
            generate_visualizations=True,
        )
        return JSONResponse(content=result)
    except ValueError as val_err:
        # Expected domain errors (e.g. image corrupt, insufficient minutiae)
        raise HTTPException(status_code=422, detail=str(val_err)) from val_err
    except Exception as exc:
        # Unexpected processing errors - clean user friendly message
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during fingerprint comparison: {str(exc)}",
        ) from exc


@router.get("/samples/{dataset}/{filename}")
async def get_sample_fingerprint(dataset: str, filename: str):
    """
    Serves bundled demonstration sample fingerprints for offline demonstration.
    Supports 'fvc2002' and 'socofing'.
    """
    if dataset not in ("fvc2002", "socofing"):
        raise HTTPException(status_code=404, detail="Unknown dataset.")

    safe_filename = Path(filename).name
    sample_path = (
        Path(__file__).resolve().parent.parent.parent
        / "dataset"
        / "fingerprints"
        / dataset
        / "sample_pairs"
        / safe_filename
    )

    if not sample_path.exists() or not sample_path.is_file():
        raise HTTPException(status_code=404, detail=f"Sample '{safe_filename}' not found.")

    media_type = "image/png" if sample_path.suffix.lower() == ".png" else "image/bmp"
    return FileResponse(str(sample_path), media_type=media_type)
