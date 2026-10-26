"""
Evidence Management REST API Routes
===================================
Provides evidence upload, metadata retrieval, secure download,
cryptographic SHA-256 integrity verification, and forensic module integration.
"""

from datetime import datetime, timezone
import json
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Case, Evidence, AuditLog, AnalysisRecord
from storage.evidence_storage import (
    save_evidence_file,
    get_evidence_file_path,
    verify_evidence_integrity,
    ALLOWED_EXTENSIONS,
    MIME_TYPE_MAP,
)
from api.routes.case_routes import log_audit_event

router = APIRouter()


def generate_evidence_id() -> str:
    """Generate a unique forensic Evidence ID: DL-EVD-YYYYMMDD-XXXX."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:6].upper()
    return f"DL-EVD-{date_str}-{unique_suffix}"


# ── Evidence Upload for a Specific Case ──────────────────────────────────────

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
    # 1. Verify case exists
    case = db.query(Case).filter(Case.case_id == case_id, Case.is_archived == False).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found or is archived.")

    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    original_filename = file.filename
    evidence_id = generate_evidence_id()

    # Read bytes safely
    file_bytes = await file.read()

    # Save to controlled storage, compute SHA-256, sanitize name, and validate
    storage_filename, storage_path, sha256_hash, file_size = save_evidence_file(
        evidence_id=evidence_id,
        original_filename=original_filename,
        file_bytes=file_bytes,
    )

    # Detect MIME type
    ext = Path(original_filename).suffix.lower()
    mime_type = file.content_type or MIME_TYPE_MAP.get(ext, "application/octet-stream")

    # Create Evidence Record
    now = datetime.now(timezone.utc)
    evidence_item = Evidence(
        evidence_id=evidence_id,
        case_id=case_id,
        evidence_name=evidence_name.strip(),
        description=description.strip() if description else "",
        evidence_type=evidence_type,
        original_filename=original_filename,
        storage_filename=storage_filename,
        storage_path=storage_path,
        file_size=file_size,
        mime_type=mime_type,
        sha256_hash=sha256_hash,
        status="Active",
        uploaded_at=now,
    )

    db.add(evidence_item)
    db.flush()

    # Log Audit Event
    log_audit_event(
        db=db,
        action_type="EVIDENCE_UPLOADED",
        actor=case.investigator,
        case_id=case.case_id,
        evidence_id=evidence_item.evidence_id,
        details={
            "evidence_name": evidence_item.evidence_name,
            "original_filename": original_filename,
            "file_size": file_size,
            "sha256_hash": sha256_hash,
            "evidence_type": evidence_type,
        },
    )

    db.commit()
    db.refresh(evidence_item)
    return evidence_item.to_dict()


# ── Evidence Listing by Case ─────────────────────────────────────────────────

@router.get("/cases/{case_id}/evidence")
def list_case_evidence(case_id: str, db: Session = Depends(get_db)):
    """
    List all active digital evidence associated with a case.
    """
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    items = (
        db.query(Evidence)
        .filter(Evidence.case_id == case_id, Evidence.status != "Archived")
        .order_by(desc(Evidence.uploaded_at))
        .all()
    )
    return {"evidence": [e.to_dict() for e in items], "total": len(items)}


# ── Global Evidence Listing ──────────────────────────────────────────────────

@router.get("/evidence")
def list_all_evidence(
    case_id: Optional[str] = Query(None, description="Filter by case ID"),
    evidence_type: Optional[str] = Query(None, description="Filter by evidence type"),
    search: Optional[str] = Query(None, description="Search by name or filename"),
    status_filter: str = Query("Active", alias="status", description="Active or Archived"),
    db: Session = Depends(get_db),
):
    """
    List all forensic evidence across cases with optional filters.
    """
    query = db.query(Evidence)

    if status_filter != "all":
        query = query.filter(Evidence.status == status_filter)

    if case_id and case_id.strip():
        query = query.filter(Evidence.case_id == case_id.strip())

    if evidence_type and evidence_type.strip():
        query = query.filter(Evidence.evidence_type == evidence_type.strip())

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            (Evidence.evidence_name.ilike(term))
            | (Evidence.original_filename.ilike(term))
            | (Evidence.evidence_id.ilike(term))
        )

    items = query.order_by(desc(Evidence.uploaded_at)).all()
    return {"evidence": [e.to_dict() for e in items], "total": len(items)}


# ── Evidence Details ─────────────────────────────────────────────────────────

@router.get("/evidence/{evidence_id}")
def get_evidence_details(evidence_id: str, db: Session = Depends(get_db)):
    """
    Retrieve complete evidence metadata, associated case info, and forensic analyses.
    """
    evidence = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail=f"Evidence '{evidence_id}' not found.")

    data = evidence.to_dict()
    data["case"] = evidence.case.to_dict() if evidence.case else None
    data["analysis_records"] = [a.to_dict() for a in evidence.analysis_records]
    return data


# ── Secure Download Endpoint ─────────────────────────────────────────────────

@router.get("/evidence/{evidence_id}/download")
def download_evidence(evidence_id: str, db: Session = Depends(get_db)):
    """
    Secure download endpoint with strict path traversal prevention,
    safe original filename restoration, and audit trail recording.
    """
    evidence = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail=f"Evidence '{evidence_id}' not found.")

    file_path = get_evidence_file_path(evidence.storage_filename)
    if not file_path or not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="The requested evidence file could not be found on the storage server.",
        )

    # Log Audit Event for Chain of Custody
    log_audit_event(
        db=db,
        action_type="EVIDENCE_DOWNLOADED",
        actor="Investigator / Client",
        case_id=evidence.case_id,
        evidence_id=evidence.evidence_id,
        details={
            "original_filename": evidence.original_filename,
            "sha256_hash": evidence.sha256_hash,
            "file_size": evidence.file_size,
        },
    )
    db.commit()

    return FileResponse(
        path=str(file_path),
        filename=evidence.original_filename,
        media_type=evidence.mime_type,
    )


# ── Safe Preview Endpoint ────────────────────────────────────────────────────

@router.get("/evidence/{evidence_id}/preview")
def preview_evidence(evidence_id: str, db: Session = Depends(get_db)):
    """
    Safe inline preview endpoint for images and documents.
    Prevents execution of uploaded files and serves correct MIME headers.
    """
    evidence = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail=f"Evidence '{evidence_id}' not found.")

    file_path = get_evidence_file_path(evidence.storage_filename)
    if not file_path or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Evidence file missing.")

    # Only allow safe media types inline
    safe_mime = evidence.mime_type
    if not (safe_mime.startswith("image/") or safe_mime == "application/pdf"):
        safe_mime = "application/octet-stream"

    return FileResponse(
        path=str(file_path),
        media_type=safe_mime,
        headers={"Content-Disposition": "inline"},
    )


# ── SHA-256 Integrity Verification Endpoint ──────────────────────────────────

@router.post("/evidence/{evidence_id}/verify-integrity")
def verify_integrity(evidence_id: str, db: Session = Depends(get_db)):
    """
    Recalculates the SHA-256 cryptographic hash of the physical file on disk
    and compares it with the recorded baseline in the database.
    Logs the verification event in the audit trail without modifying the original hash.
    """
    evidence = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail=f"Evidence '{evidence_id}' not found.")

    result = verify_evidence_integrity(
        storage_filename=evidence.storage_filename,
        recorded_sha256=evidence.sha256_hash,
    )

    now_iso = datetime.now(timezone.utc).isoformat()
    result["verified_at"] = now_iso

    # Log verification attempt in Audit Trail
    log_audit_event(
        db=db,
        action_type="INTEGRITY_CHECKED",
        actor="Investigator Verification Tool",
        case_id=evidence.case_id,
        evidence_id=evidence.evidence_id,
        details={
            "result_status": result["status"],
            "matches": result["matches"],
            "recorded_hash": result["recorded_hash"],
            "calculated_hash": result["calculated_hash"],
        },
    )
    db.commit()

    return result


# ── Evidence Status Update (Safe Archive) ────────────────────────────────────

@router.patch("/evidence/{evidence_id}/status")
def update_evidence_status(
    evidence_id: str,
    status_value: str = Query(..., alias="status", description="'Active' or 'Archived'"),
    reason: Optional[str] = Query(None, description="Reason for status change"),
    db: Session = Depends(get_db),
):
    """
    Soft-archive or restore evidence items from active case use.
    """
    if status_value not in {"Active", "Archived"}:
        raise HTTPException(status_code=400, detail="Status must be 'Active' or 'Archived'.")

    evidence = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail=f"Evidence '{evidence_id}' not found.")

    old_status = evidence.status
    evidence.status = status_value

    log_audit_event(
        db=db,
        action_type="EVIDENCE_STATUS_CHANGED",
        actor="Forensic Examiner",
        case_id=evidence.case_id,
        evidence_id=evidence.evidence_id,
        details={
            "old_status": old_status,
            "new_status": status_value,
            "reason": reason or "",
        },
    )
    db.commit()
    db.refresh(evidence)
    return evidence.to_dict()


# ── Run Forensic Analysis on Stored Evidence ─────────────────────────────────

@router.post("/evidence/{evidence_id}/run-analysis")
async def run_evidence_analysis(evidence_id: str, db: Session = Depends(get_db)):
    """
    Executes forensic analysis on stored evidence using the appropriate module:
    - Image -> modules.image pipeline (Entropy, ELA, Noise, Texture, Risk)
    - Signature -> modules.signature pipeline (Tremor, morphological screening)
    - Document -> modules.document_analysis pipeline (PyMuPDF, OCR, consistency check)
    Links the results permanently to the Case and Evidence.
    """
    evidence = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail=f"Evidence '{evidence_id}' not found.")

    file_path = get_evidence_file_path(evidence.storage_filename)
    if not file_path or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Physical evidence file not found on disk.")

    record_id = f"REC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    ev_type = (evidence.evidence_type or "").lower()

    result_summary = ""
    verdict = "INCONCLUSIVE"
    result_data = {}

    try:
        if "image" in ev_type:
            # Run image forgery pipeline
            from modules.image.preprocessing import load_image
            from modules.image.entropy_analysis import compute_entropy_stats, generate_entropy_heatmap
            from modules.image.ela_analysis import compute_ela_stats, perform_ela, save_ela_image
            from modules.image.noise_analysis import compute_noise_stats, estimate_noise_map, save_noise_map
            from modules.image.texture_analysis import compute_glcm_features
            from modules.image.metadata_analysis import extract_metadata
            from modules.image.forgery_detector import assess_risk

            pil_img, cv_img, gray = load_image(str(file_path))
            entropy_stats = compute_entropy_stats(gray)
            ela_image = perform_ela(str(file_path))
            ela_stats = compute_ela_stats(ela_image)
            noise_map = estimate_noise_map(gray)
            noise_stats = compute_noise_stats(noise_map)
            texture_stats = compute_glcm_features(gray)
            metadata = extract_metadata(str(file_path), pil_img)
            risk = assess_risk(entropy_stats, ela_stats, noise_stats, texture_stats)

            # Outputs
            uid = uuid.uuid4().hex[:12]
            entropy_out = Path(__file__).parent.parent.parent / "outputs" / "entropy" / f"{uid}.png"
            ela_out = Path(__file__).parent.parent.parent / "outputs" / "ela" / f"{uid}.png"
            noise_out = Path(__file__).parent.parent.parent / "outputs" / "noise" / f"{uid}.png"

            generate_entropy_heatmap(pil_img, gray, str(entropy_out))
            save_ela_image(ela_image, str(ela_out))
            save_noise_map(noise_map, str(noise_out))

            verdict = risk.get("risk_level", "UNKNOWN").upper()
            result_summary = f"Image Forgery Risk: {verdict}. Confidence: {risk.get('confidence_score', 0):.1f}%"
            result_data = {
                "entropy": {**entropy_stats, "heatmap_url": f"/outputs/entropy/{uid}.png"},
                "ela": {**ela_stats, "image_url": f"/outputs/ela/{uid}.png"},
                "noise": {**noise_stats, "image_url": f"/outputs/noise/{uid}.png"},
                "texture": texture_stats,
                "metadata": metadata,
                "risk_assessment": risk,
            }
            module_name = "Image Forgery"

        elif "signature" in ev_type:
            from modules.signature.signature_analysis import analyze_signature_pipeline
            sig_res = analyze_signature_pipeline(str(file_path), reference_path=None)
            verdict = sig_res.get("verdict", "INCONCLUSIVE")
            result_summary = f"Signature Screening: {verdict}. Tremor Index: {sig_res.get('standalone_analysis', {}).get('tremor_index', 0):.2f}"
            result_data = sig_res
            module_name = "Signature Verification"

        elif "document" in ev_type or evidence.original_filename.lower().endswith(".pdf"):
            from modules.document_analysis.analyzer import analyze_document
            with open(file_path, "rb") as f:
                content = f.read()
            doc_res = analyze_document(content, evidence.original_filename)
            inconsistencies = len(doc_res.get("inconsistencies", []))
            verdict = "SUSPICIOUS" if inconsistencies > 0 else "CONSISTENT"
            result_summary = f"Document Analysis: {inconsistencies} potential inconsistencies detected across {doc_res.get('total_pages', 1)} pages."
            result_data = doc_res
            module_name = "Document Analysis"

        else:
            verdict = "UNSUPPORTED"
            result_summary = f"Automated analysis not configured for evidence type '{evidence.evidence_type}'."
            result_data = {"status": "unsupported", "type": evidence.evidence_type}
            module_name = "Other"

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Forensic analysis failed: {str(exc)}",
        ) from exc

    # Save Analysis Record linked to this Case & Evidence
    record = AnalysisRecord(
        record_id=record_id,
        case_id=evidence.case_id,
        evidence_id=evidence.evidence_id,
        module_type=module_name,
        result_summary=result_summary,
        verdict=verdict,
        result_data=json.dumps(result_data),
        created_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.flush()

    # Log in Audit Trail
    log_audit_event(
        db=db,
        action_type="ANALYSIS_PERFORMED",
        actor="Forensic Engine",
        case_id=evidence.case_id,
        evidence_id=evidence.evidence_id,
        details={
            "module_type": module_name,
            "verdict": verdict,
            "record_id": record_id,
            "summary": result_summary,
        },
    )

    db.commit()
    db.refresh(record)
    return record.to_dict()
