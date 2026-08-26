"""
Image Analysis Route
====================
POST /api/image/analyze — accepts an image file, runs all forensic
analysis modules, and returns a structured JSON result.
"""

import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from modules.preprocessing import get_image_info, load_image, validate_image
from modules.entropy_analysis import compute_entropy_stats, generate_entropy_heatmap
from modules.ela_analysis import compute_ela_stats, perform_ela, save_ela_image
from modules.noise_analysis import compute_noise_stats, estimate_noise_map, save_noise_map
from modules.texture_analysis import compute_glcm_features
from modules.metadata_analysis import extract_metadata
from modules.forgery_detector import assess_risk
from ml.predict import load_model, predict

router = APIRouter()

# ── Config ────────────────────────────────────────────────────────────────────
MAX_SIZE_MB = float(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
MAX_SIZE_BYTES = int(MAX_SIZE_MB * 1024 * 1024)
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

BASE_DIR = Path(__file__).parent.parent.parent  # backend/
OUTPUTS_DIR = BASE_DIR / "outputs"


def _unique_id() -> str:
    return uuid.uuid4().hex[:12]


@router.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """
    Analyze an uploaded image for forensic indicators.

    Returns entropy, ELA, noise, texture, metadata, and a preliminary
    risk assessment. ML prediction is included if a trained model exists.

    This endpoint provides **preliminary forensic screening** for
    research and educational purposes only.
    """

    # ── 1. Validate content type ──────────────────────────────────────────────
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Supported: JPG, JPEG, PNG, WEBP.",
        )

    # ── 2. Read and size-check ────────────────────────────────────────────────
    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {MAX_SIZE_MB} MB.",
        )

    # ── 3. Save to temp file ──────────────────────────────────────────────────
    tmp_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # ── 4. Validate image (can PIL open it?) ──────────────────────────────
        validate_image(tmp_path)

        # ── 5. Load image ─────────────────────────────────────────────────────
        pil_img, cv_img, gray = load_image(tmp_path)

        # ── 6. Basic image info ───────────────────────────────────────────────
        image_info = get_image_info(tmp_path, file, content)

        # ── 7. Entropy ────────────────────────────────────────────────────────
        uid = _unique_id()
        entropy_out = OUTPUTS_DIR / "entropy" / f"{uid}.png"
        entropy_stats = compute_entropy_stats(gray)
        generate_entropy_heatmap(pil_img, gray, str(entropy_out))

        # ── 8. ELA ────────────────────────────────────────────────────────────
        ela_out = OUTPUTS_DIR / "ela" / f"{uid}.png"
        ela_image = perform_ela(tmp_path)
        save_ela_image(ela_image, str(ela_out))
        ela_stats = compute_ela_stats(ela_image)

        # ── 9. Noise ──────────────────────────────────────────────────────────
        noise_out = OUTPUTS_DIR / "noise" / f"{uid}.png"
        noise_map = estimate_noise_map(gray)
        save_noise_map(noise_map, str(noise_out))
        noise_stats = compute_noise_stats(noise_map)

        # ── 10. Texture ───────────────────────────────────────────────────────
        texture_stats = compute_glcm_features(gray)

        # ── 11. Metadata ──────────────────────────────────────────────────────
        metadata = extract_metadata(tmp_path, pil_img)

        # ── 12. Risk assessment ───────────────────────────────────────────────
        preliminary_result = assess_risk(entropy_stats, ela_stats, noise_stats, texture_stats)

        # ── 13. ML prediction (optional) ──────────────────────────────────────
        model = load_model()
        ml_prediction = predict(model, entropy_stats, ela_stats, noise_stats, texture_stats)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(exc)}") from exc
    finally:
        # Always remove the temp upload file
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # ── 14. Build response ────────────────────────────────────────────────────
    return JSONResponse(
        content={
            "success": True,
            "filename": file.filename,
            "image_info": image_info,
            "entropy": {
                **entropy_stats,
                "heatmap_url": f"/outputs/entropy/{uid}.png",
            },
            "ela": {
                **ela_stats,
                "image_url": f"/outputs/ela/{uid}.png",
            },
            "noise": {
                **noise_stats,
                "image_url": f"/outputs/noise/{uid}.png",
            },
            "texture": texture_stats,
            "metadata": metadata,
            "preliminary_result": preliminary_result,
            "ml_prediction": ml_prediction,
        }
    )
