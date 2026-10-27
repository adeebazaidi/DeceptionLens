"""
Evidence Management REST API Routes
=====================================
Thin FastAPI route handlers for Evidence operations.
All business logic lives in modules.case_management.evidence.
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from database.connection import get_db
from modules.case_management import (
    upload_evidence,
    list_case_evidence,
    list_all_evidence,
    get_evidence_details,
    download_evidence,
    preview_evidence,
    verify_integrity,
    update_evidence_status,
    run_evidence_analysis,
)

router = APIRouter()


# ── Evidence Upload for a Specific Case ───────────────────────────────────────

@router.post("/cases/{case_id}/evidence", status_code=status.HTTP_201_CREATED)
async def upload_evidence_for_case(
    case_id: str,
    file: UploadFile = File(...),
    evidence_name: str = Form(...),
    description: Optional[str] = Form(""),
    evidence_type: str = Form("Image"),
    db: Session = Depends(get_db),
):
    """
    Securely uploads digital evidence and associates it with the specified forensic case.
    Calculates SHA-256 hash immediately upon arrival and creates an immutable baseline.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    file_bytes = await file.read()

    return await upload_evidence(
        db=db,
        case_id=case_id,
        file_bytes=file_bytes,
        original_filename=file.filename,
        content_type=file.content_type,
        evidence_name=evidence_name,
        description=description or "",
        evidence_type=evidence_type,
    )


# ── Evidence Listing by Case ──────────────────────────────────────────────────

@router.get("/cases/{case_id}/evidence")
def list_case_evidence_route(case_id: str, db: Session = Depends(get_db)):
    """
    List all active digital evidence associated with a case.
    """
    return list_case_evidence(db=db, case_id=case_id)


# ── Global Evidence Listing ───────────────────────────────────────────────────

@router.get("/evidence")
def list_all_evidence_route(
    case_id: Optional[str] = Query(None, description="Filter by case ID"),
    evidence_type: Optional[str] = Query(None, description="Filter by evidence type"),
    search: Optional[str] = Query(None, description="Search by name or filename"),
    status_filter: str = Query("Active", alias="status", description="Active or Archived"),
    db: Session = Depends(get_db),
):
    """
    List all forensic evidence across cases with optional filters.
    """
    return list_all_evidence(
        db=db,
        case_id=case_id,
        evidence_type=evidence_type,
        search=search,
        status_filter=status_filter,
    )


# ── Evidence Details ──────────────────────────────────────────────────────────

@router.get("/evidence/{evidence_id}")
def get_evidence_details_route(evidence_id: str, db: Session = Depends(get_db)):
    """
    Retrieve complete evidence metadata, associated case info, and forensic analyses.
    """
    return get_evidence_details(db=db, evidence_id=evidence_id)


# ── Secure Download Endpoint ──────────────────────────────────────────────────

@router.get("/evidence/{evidence_id}/download")
def download_evidence_route(evidence_id: str, db: Session = Depends(get_db)):
    """
    Secure download endpoint with strict path traversal prevention,
    safe original filename restoration, and audit trail recording.
    """
    return download_evidence(db=db, evidence_id=evidence_id)


# ── Safe Preview Endpoint ─────────────────────────────────────────────────────

@router.get("/evidence/{evidence_id}/preview")
def preview_evidence_route(evidence_id: str, db: Session = Depends(get_db)):
    """
    Safe inline preview endpoint for images and documents.
    Prevents execution of uploaded files and serves correct MIME headers.
    """
    return preview_evidence(db=db, evidence_id=evidence_id)


# ── SHA-256 Integrity Verification Endpoint ───────────────────────────────────

@router.post("/evidence/{evidence_id}/verify-integrity")
def verify_integrity_route(evidence_id: str, db: Session = Depends(get_db)):
    """
    Recalculates the SHA-256 cryptographic hash of the physical file on disk
    and compares it with the recorded baseline in the database.
    Logs the verification event in the audit trail without modifying the original hash.
    """
    return verify_integrity(db=db, evidence_id=evidence_id)


# ── Evidence Status Update (Safe Archive) ─────────────────────────────────────

@router.patch("/evidence/{evidence_id}/status")
def update_evidence_status_route(
    evidence_id: str,
    status_value: str = Query(..., alias="status", description="'Active' or 'Archived'"),
    reason: Optional[str] = Query(None, description="Reason for status change"),
    db: Session = Depends(get_db),
):
    """
    Soft-archive or restore evidence items from active case use.
    """
    return update_evidence_status(
        db=db,
        evidence_id=evidence_id,
        status_value=status_value,
        reason=reason,
    )


# ── Run Forensic Analysis on Stored Evidence ──────────────────────────────────

@router.post("/evidence/{evidence_id}/run-analysis")
async def run_evidence_analysis_route(evidence_id: str, db: Session = Depends(get_db)):
    """
    Executes forensic analysis on stored evidence using the appropriate module:
    - Image     -> modules.image pipeline (Entropy, ELA, Noise, Texture, Risk)
    - Signature -> modules.signature pipeline (Tremor, morphological screening)
    - Document  -> modules.document_analysis pipeline (PyMuPDF, OCR, consistency check)
    Links the results permanently to the Case and Evidence.
    """
    return await run_evidence_analysis(db=db, evidence_id=evidence_id)
