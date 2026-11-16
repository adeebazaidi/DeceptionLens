"""
DeceptionLens — Report Management: Saved Forensic Reports
=========================================================
Generates a case report, freezes it as an immutable snapshot sealed with a
SHA-256 hash of its canonical JSON, and provides listing, retrieval,
download, integrity verification, and archiving. Every action is written
to the case audit trail.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from fastapi.responses import Response
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database.models import Case, ForensicReport
from modules.case_management.audit import log_audit_event
from modules.case_management.cases import generate_case_report

VALID_REPORT_STATUSES = {"Final", "Archived"}


def generate_report_id() -> str:
    """Generate a unique report ID: DL-REP-YYYYMMDD-XXXXXX."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"DL-REP-{date_str}-{uuid.uuid4().hex[:6].upper()}"


def _canonical_json(content: dict) -> str:
    """Stable serialization so the same content always hashes the same."""
    return json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _get_report_or_404(db: Session, report_id: str) -> ForensicReport:
    report = db.query(ForensicReport).filter(ForensicReport.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")
    return report


# ── Create ────────────────────────────────────────────────────────────────────

def create_report(
    db: Session,
    case_id: str,
    generated_by: str,
    title: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """
    Snapshot the current state of a case into a saved, hash-sealed report.
    Raises 404 if the case does not exist, 400 if it is archived.
    """
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    if case.is_archived:
        raise HTTPException(status_code=400, detail=f"Case '{case_id}' is archived; reports cannot be generated.")

    report_id = generate_report_id()
    while db.query(ForensicReport).filter(ForensicReport.report_id == report_id).first() is not None:
        report_id = generate_report_id()

    content = generate_case_report(db=db, case_id=case_id)
    content["report_id"] = report_id
    canonical = _canonical_json(content)
    sha256_hash = _sha256(canonical)

    report = ForensicReport(
        report_id=report_id,
        case_id=case_id,
        title=(title or "").strip() or f"Forensic Report — {case.title}",
        generated_by=generated_by.strip(),
        notes=(notes or "").strip(),
        content=canonical,
        sha256_hash=sha256_hash,
        evidence_count=content["evidence_summary"]["total_items"],
        analysis_count=len(content["forensic_analysis_records"]),
        status="Final",
        created_at=datetime.now(timezone.utc),
    )
    db.add(report)
    db.flush()

    log_audit_event(
        db=db,
        action_type="REPORT_GENERATED",
        actor=report.generated_by,
        case_id=case_id,
        details={"report_id": report_id, "sha256_hash": sha256_hash, "title": report.title},
    )
    db.commit()
    db.refresh(report)
    return report.to_dict()


# ── Read ──────────────────────────────────────────────────────────────────────

def list_reports(
    db: Session,
    case_id: Optional[str] = None,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> dict:
    """List saved reports, newest first. status_filter="all" includes archived."""
    query = db.query(ForensicReport)

    if not status_filter:
        query = query.filter(ForensicReport.status == "Final")
    elif status_filter != "all":
        query = query.filter(ForensicReport.status == status_filter)

    if case_id and case_id.strip():
        query = query.filter(ForensicReport.case_id == case_id.strip())

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            ForensicReport.report_id.ilike(term)
            | ForensicReport.title.ilike(term)
            | ForensicReport.case_id.ilike(term)
            | ForensicReport.generated_by.ilike(term)
        )

    reports = query.order_by(desc(ForensicReport.created_at)).all()
    return {"reports": [r.to_dict() for r in reports], "total": len(reports)}


def get_report(db: Session, report_id: str) -> dict:
    """Return report metadata plus its full saved content."""
    return _get_report_or_404(db, report_id).to_dict(include_content=True)


# ── Download ──────────────────────────────────────────────────────────────────

def download_report(db: Session, report_id: str, actor: str = "Investigator / Client") -> Response:
    """Return the saved report as a JSON attachment and log the download."""
    report = _get_report_or_404(db, report_id)

    log_audit_event(
        db=db,
        action_type="REPORT_DOWNLOADED",
        actor=actor,
        case_id=report.case_id,
        details={"report_id": report.report_id, "sha256_hash": report.sha256_hash},
    )
    db.commit()

    body = json.dumps(
        {"report": report.to_dict(), "content": json.loads(report.content)},
        indent=2,
        ensure_ascii=False,
    )
    return Response(
        content=body,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{report.report_id}.json"'},
    )


# ── Integrity ─────────────────────────────────────────────────────────────────

def verify_report(db: Session, report_id: str) -> dict:
    """Recompute the hash of the stored content and compare it to the seal."""
    report = _get_report_or_404(db, report_id)
    calculated = _sha256(report.content)
    matches = calculated == report.sha256_hash

    result = {
        "report_id": report.report_id,
        "status": "Hash Matches" if matches else "Hash Mismatch",
        "matches": matches,
        "recorded_hash": report.sha256_hash,
        "calculated_hash": calculated,
        "explanation": (
            "The saved report content matches its SHA-256 seal; it has not been altered since generation."
            if matches
            else "The saved report content differs from its SHA-256 seal; it has been altered since generation."
        ),
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }

    log_audit_event(
        db=db,
        action_type="REPORT_VERIFIED",
        actor="Report Verification Tool",
        case_id=report.case_id,
        details={"report_id": report.report_id, "matches": matches},
    )
    db.commit()
    return result


# ── Status ────────────────────────────────────────────────────────────────────

def update_report_status(db: Session, report_id: str, status_value: str, reason: Optional[str] = None) -> dict:
    """Archive or restore a report. Reports are never deleted."""
    if status_value not in VALID_REPORT_STATUSES:
        raise HTTPException(status_code=400, detail="Status must be 'Final' or 'Archived'.")

    report = _get_report_or_404(db, report_id)
    old_status = report.status
    if old_status != status_value:
        report.status = status_value
        log_audit_event(
            db=db,
            action_type="REPORT_STATUS_CHANGED",
            actor="Forensic Examiner",
            case_id=report.case_id,
            details={
                "report_id": report.report_id,
                "old_status": old_status,
                "new_status": status_value,
                "reason": reason or "",
            },
        )
        db.commit()
        db.refresh(report)
    return report.to_dict()
