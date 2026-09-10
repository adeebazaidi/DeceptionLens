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

# ── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="DeceptionLens API",
    description=(
        "Preliminary image-forensic analysis API. "
        "Results are indicators for research and educational purposes only."
    ),
    version="1.0.0",
)

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

# ── Static output files (generated heatmaps / ELA / noise maps) ──────────────
BASE_DIR = Path(__file__).parent
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
for sub in ("entropy", "ela", "noise"):
    (OUTPUTS_DIR / sub).mkdir(parents=True, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(image_router, prefix="/api/image", tags=["Image Analysis"])


# ── Health ───────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "DeceptionLens API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

