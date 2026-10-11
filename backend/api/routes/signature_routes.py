"""
Signature Analysis API Routes
=============================
POST /api/signature/analyze — accepts query signature image (and optional reference signature)
and runs standalone screening and 1-vs-1 verification.
"""

import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from modules.image.preprocessing import validate_image
from modules.signature.signature_analysis import analyze_signature_pipeline

router = APIRouter()

MAX_SIZE_MB = float(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
MAX_SIZE_BYTES = int(MAX_SIZE_MB * 1024 * 1024)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

BASE_DIR = Path(__file__).parent.parent.parent  # backend/
OUTPUTS_DIR = BASE_DIR / "outputs" / "signature"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def _unique_id() -> str:
    return uuid.uuid4().hex[:12]


@router.post("/analyze")
async def analyze_signature(
    file: UploadFile = File(...),
    reference_file: Optional[UploadFile] = File(None),
):
    """
    Analyze an uploaded signature for forgery indicators.
    If `reference_file` is provided, performs a 1-vs-1 comparison against the reference signature.
    Otherwise, performs standalone tremor and morphological screening.
    """
    # 1. Validate Query File extension
    query_ext = Path(file.filename or "").suffix.lower()
    if query_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{query_ext}' for query signature. Supported: JPG, JPEG, PNG, WEBP.",
        )

    # 2. Read and size check Query File
    query_bytes = await file.read()
    if len(query_bytes) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Query file exceeds maximum size of {MAX_SIZE_MB} MB.",
        )

    ref_bytes: Optional[bytes] = None
    if reference_file and reference_file.filename:
        ref_ext = Path(reference_file.filename or "").suffix.lower()
        if ref_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{ref_ext}' for reference signature. Supported: JPG, JPEG, PNG, WEBP.",
            )
        ref_bytes = await reference_file.read()
        if len(ref_bytes) > MAX_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Reference file exceeds maximum size of {MAX_SIZE_MB} MB.",
            )

    # 3. Save to temp files
    q_tmp_path: Optional[str] = None
    r_tmp_path: Optional[str] = None
    uid = _unique_id()

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=query_ext) as tmp_q:
            tmp_q.write(query_bytes)
            q_tmp_path = tmp_q.name

        validate_image(q_tmp_path)

        if ref_bytes:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(reference_file.filename).suffix.lower()) as tmp_r:
                tmp_r.write(ref_bytes)
                r_tmp_path = tmp_r.name
            validate_image(r_tmp_path)

        # 4. Execute Analysis Pipeline
        result = analyze_signature_pipeline(
            query_path=q_tmp_path,
            ref_path=r_tmp_path,
            output_dir=str(OUTPUTS_DIR),
            uid=uid,
        )

        return JSONResponse(
            content={
                "success": True,
                "query_filename": file.filename,
                "reference_filename": reference_file.filename if reference_file else None,
                "analysis": result,
            }
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Signature analysis error: {str(exc)}") from exc
    finally:
        # Cleanup temp files
        if q_tmp_path and os.path.exists(q_tmp_path):
            os.unlink(q_tmp_path)
        if r_tmp_path and os.path.exists(r_tmp_path):
            os.unlink(r_tmp_path)
