"""
DeceptionLens — FastAPI Backend Entry Point
==========================================
Provides REST API for image forgery forensic analysis.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Load environment variables from .env
load_dotenv()

from api.routes.image_routes import router as image_router
from api.routes.fingerprint_routes import router as fingerprint_router
from api.routes.signature_routes import router as signature_router
from api.routes.document_routes import router as document_router
from api.routes.case_routes import router as case_router
from api.routes.evidence_routes import router as evidence_router
from api.routes.audit_routes import router as audit_router
from database.connection import init_db

# ── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="DeceptionLens API",
    description=(
        "Digital Forensics and Forgery Detection System API. "
        "Case and Evidence Management, Image Forgery, Fingerprint, Signature, and Document Forensics."
    ),
    version="1.0.0",
)

# Initialize persistent database schema safely
init_db()

# ── CORS ─────────────────────────────────────────────────────────────────────
# Frontend origin is configurable via environment variable.
# Do NOT use wildcard in production.
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static output files (generated heatmaps / ELA / noise / fingerprint maps) ──────────────
BASE_DIR = Path(__file__).parent
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
for sub in ("entropy", "ela", "noise", "fingerprint", "signature"):
    (OUTPUTS_DIR / sub).mkdir(parents=True, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

# Ensure evidence storage directory exists
EVIDENCE_STORAGE_DIR = BASE_DIR / "evidence_storage"
EVIDENCE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(image_router, prefix="/api/image", tags=["Image Analysis"])
app.include_router(fingerprint_router, prefix="/api/fingerprint", tags=["Fingerprint Comparison"])
app.include_router(signature_router, prefix="/api/signature", tags=["Signature Forgery"])
app.include_router(document_router, prefix="/api/document", tags=["Document Analysis"])
app.include_router(case_router, prefix="/api/cases", tags=["Case Management"])
app.include_router(evidence_router, prefix="/api", tags=["Evidence Management"])
app.include_router(audit_router, prefix="/api", tags=["Audit Trail"])


# ── Health ───────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "DeceptionLens API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

