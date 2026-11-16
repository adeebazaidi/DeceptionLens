"""
DeceptionLens — Case Management: Evidence Business Logic
========================================================
Handles evidence upload (with SHA-256 baseline), listing, secure download,
safe inline preview, cryptographic integrity verification, soft-archiving,
and automated forensic analysis dispatch across registered modules.

Route handlers in api/routes/evidence_routes.py delegate to these functions
after performing HTTP-layer concerns (file reception, dependency injection,
HTTP status codes).
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database.models import AnalysisRecord, Case, Evidence
from storage.evidence_storage import (
    MIME_TYPE_MAP,
    get_evidence_file_path,
    save_evidence_file,
    verify_evidence_integrity,
)
from modules.case_management.ids import generate_evidence_id
from modules.document_analysis.nlp_service import NLPUnavailableError
from modules.case_management.audit import log_audit_event


def _json_default(value):
    """Serialize numpy scalars/arrays produced by the forensic pipelines."""
    if hasattr(value, "tolist"):
        return value.tolist()
    return str(value)


# ── Upload ────────────────────────────────────────────────────────────────────

def upload_evidence(
    db: Session,
    case_id: str,
    file_bytes: bytes,
    original_filename: str,
    content_type: Optional[str],
    evidence_name: str,
    description: str = "",
    evidence_type: str = "Image",
) -> dict:
    """
    Securely stores digital evidence and associates it with the specified case.
    Computes SHA-256 hash immediately upon arrival and creates an immutable baseline.
    Raises HTTPException on missing case, missing file, or storage errors.
    """
    case = db.query(Case).filter(Case.case_id == case_id, Case.is_archived == False).first()
    if not case:
        raise HTTPException(
            status_code=404,
            detail=f"Case '{case_id}' not found or is archived.",
        )

    if not file_bytes or not original_filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    evidence_id = generate_evidence_id()

    storage_filename, storage_path, sha256_hash, file_size = save_evidence_file(
        evidence_id=evidence_id,
        original_filename=original_filename,
        file_bytes=file_bytes,
    )

    ext = Path(original_filename).suffix.lower()
    mime_type = content_type or MIME_TYPE_MAP.get(ext, "application/octet-stream")

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


# ── List ──────────────────────────────────────────────────────────────────────

def list_case_evidence(db: Session, case_id: str) -> dict:
    """
    List all active digital evidence associated with a specific case.
    Raises 404 if the case does not exist.
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


def list_all_evidence(
    db: Session,
    case_id: Optional[str] = None,
    evidence_type: Optional[str] = None,
    search: Optional[str] = None,
    status_filter: str = "Active",
) -> dict:
    """
    List all forensic evidence across cases with optional filters.
    Pass status_filter="all" to skip status filtering.
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


# ── Details ───────────────────────────────────────────────────────────────────

def get_evidence_details(db: Session, evidence_id: str) -> dict:
    """
    Retrieve complete evidence metadata, associated case info, and analyses.
    Raises 404 if not found.
    """
    evidence = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail=f"Evidence '{evidence_id}' not found.")

    data = evidence.to_dict()
    data["case"] = evidence.case.to_dict() if evidence.case else None
    data["analysis_records"] = [a.to_dict() for a in evidence.analysis_records]
    return data


# ── Secure Download ───────────────────────────────────────────────────────────

def download_evidence(db: Session, evidence_id: str) -> FileResponse:
    """
    Secure download with strict path traversal prevention, safe original
    filename restoration, and audit trail recording.
    Raises 404 on missing evidence or missing physical file.
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


# ── Safe Preview ──────────────────────────────────────────────────────────────

def preview_evidence(db: Session, evidence_id: str) -> FileResponse:
    """
    Safe inline preview for images and PDFs only.
    Prevents execution of uploaded files and serves correct MIME headers.
    Raises 404 on missing evidence or physical file.
    """
    evidence = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail=f"Evidence '{evidence_id}' not found.")

    file_path = get_evidence_file_path(evidence.storage_filename)
    if not file_path or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Evidence file missing.")

    safe_mime = evidence.mime_type
    if not (safe_mime.startswith("image/") or safe_mime == "application/pdf"):
        safe_mime = "application/octet-stream"

    return FileResponse(
        path=str(file_path),
        media_type=safe_mime,
        headers={"Content-Disposition": "inline"},
    )


# ── Integrity Verification ────────────────────────────────────────────────────

def verify_integrity(db: Session, evidence_id: str) -> dict:
    """
    Recalculates the SHA-256 hash of the physical file on disk and compares
    it to the recorded baseline in the database. Logs the verification event.
    Raises 404 if the evidence record is not found.
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


# ── Status Update ─────────────────────────────────────────────────────────────

def update_evidence_status(
    db: Session,
    evidence_id: str,
    status_value: str,
    reason: Optional[str] = None,
) -> dict:
    """
    Soft-archive or restore evidence items from active case use.
    status_value must be 'Active' or 'Archived'.
    Raises 400 on invalid status, 404 if not found.
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


# ── Run Forensic Analysis ─────────────────────────────────────────────────────

def run_evidence_analysis(db: Session, evidence_id: str) -> dict:
    """
    Executes forensic analysis on stored evidence using the appropriate module:
      - Image   -> modules.image pipeline (Entropy, ELA, Noise, Texture, Risk)
      - Signature -> modules.signature pipeline (Tremor, morphological screening)
      - Document  -> modules.document_analysis pipeline (PyMuPDF, OCR, consistency)
    Saves an AnalysisRecord linked to the Case & Evidence and writes an audit event.
    Raises 404 if evidence or physical file is missing, 500 on pipeline errors.
    """
    evidence = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail=f"Evidence '{evidence_id}' not found.")

    file_path = get_evidence_file_path(evidence.storage_filename)
    if not file_path or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Physical evidence file not found on disk.")

    record_id = (
        f"REC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-"
        f"{uuid.uuid4().hex[:6].upper()}"
    )
    ev_type = (evidence.evidence_type or "").lower()

    result_summary = ""
    verdict = "INCONCLUSIVE"
    result_data = {}

    try:
        if "image" in ev_type:
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

            uid = uuid.uuid4().hex[:12]
            # outputs/ lives two levels up from this file: backend/outputs/
            outputs_base = Path(__file__).resolve().parent.parent.parent / "outputs"
            entropy_out = outputs_base / "entropy" / f"{uid}.png"
            ela_out = outputs_base / "ela" / f"{uid}.png"
            noise_out = outputs_base / "noise" / f"{uid}.png"

            generate_entropy_heatmap(pil_img, gray, str(entropy_out))
            save_ela_image(ela_image, str(ela_out))
            save_noise_map(noise_map, str(noise_out))

            verdict = risk.get("risk_level", "UNKNOWN").upper()
            result_summary = (
                f"Image Forgery Risk: {verdict}. "
                f"{'; '.join(risk.get('reason', []))}"
            )
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

            sig_res = analyze_signature_pipeline(str(file_path), ref_path=None)
            verdict = sig_res.get("standalone_assessment", {}).get("risk_level", "INCONCLUSIVE")
            tremor = sig_res.get("query_features", {}).get("tremor_score", 0)
            result_summary = f"Signature Screening Risk: {verdict}. Tremor Score: {tremor:.2f}"
            result_data = sig_res
            module_name = "Signature Verification"

        elif "document" in ev_type or evidence.original_filename.lower().endswith(".pdf"):
            from modules.document_analysis.analyzer import analyze_document

            with open(file_path, "rb") as f:
                content = f.read()
            doc_res = analyze_document(content, evidence.original_filename)
            inconsistencies = len(doc_res.get("consistency_analysis", {}).get("issues", []))
            verdict = "SUSPICIOUS" if inconsistencies > 0 else "CONSISTENT"
            result_summary = (
                f"Document Analysis: {inconsistencies} potential inconsistencies detected "
                f"across {doc_res.get('document', {}).get('page_count', 1)} pages."
            )
            result_data = doc_res
            module_name = "Document Analysis"

        else:
            verdict = "UNSUPPORTED"
            result_summary = (
                f"Automated analysis not configured for evidence type '{evidence.evidence_type}'."
            )
            result_data = {"status": "unsupported", "type": evidence.evidence_type}
            module_name = "Other"

    except NLPUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Document analysis is temporarily unavailable. {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Forensic analysis failed: {str(exc)}",
        ) from exc

    record = AnalysisRecord(
        record_id=record_id,
        case_id=evidence.case_id,
        evidence_id=evidence.evidence_id,
        module_type=module_name,
        result_summary=result_summary,
        verdict=verdict,
        result_data=json.dumps(result_data, default=_json_default),
        created_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.flush()

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
