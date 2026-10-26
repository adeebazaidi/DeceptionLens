"""
Case Management REST API Routes
===============================
Provides CRUD operations, search, filters, pagination, status transitions,
and forensic report generation for cases.
"""

from datetime import datetime, timezone
import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, asc, func
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Case, Evidence, AuditLog, AnalysisRecord
from api.schemas.case_schemas import (
    CaseCreate,
    CaseUpdate,
    CaseStatusUpdate,
    CaseResponse,
    CaseListResponse,
    VALID_CASE_TYPES,
    VALID_PRIORITIES,
    VALID_STATUSES,
)

router = APIRouter()


def generate_case_id() -> str:
    """Generate a unique forensic Case ID: DL-CASE-YYYYMMDD-XXXX."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:6].upper()
    return f"DL-CASE-{date_str}-{unique_suffix}"


def log_audit_event(
    db: Session,
    action_type: str,
    actor: str,
    case_id: Optional[str] = None,
    evidence_id: Optional[str] = None,
    details: Optional[dict] = None,
) -> AuditLog:
    """Records an immutable forensic audit event."""
    event_id = f"EVT-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    audit_entry = AuditLog(
        event_id=event_id,
        case_id=case_id,
        evidence_id=evidence_id,
        action_type=action_type,
        actor=actor or "Forensic Examiner",
        details=json.dumps(details or {}),
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit_entry)
    db.flush()
    return audit_entry


@router.get("", response_model=CaseListResponse)
def list_cases(
    search: Optional[str] = Query(None, description="Search by Case ID or Title"),
    case_type: Optional[str] = Query(None, description="Filter by case type"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    include_archived: bool = Query(False, description="Include archived cases"),
    sort_by: str = Query("created_at", description="created_at, title, priority, updated_at"),
    sort_order: str = Query("desc", description="asc or desc"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    List forensic cases with search, multi-criteria filtering, sorting, and pagination.
    """
    query = db.query(Case)

    if not include_archived:
        query = query.filter(Case.is_archived == False)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter((Case.case_id.ilike(term)) | (Case.title.ilike(term)))

    if case_type and case_type.strip():
        query = query.filter(Case.case_type == case_type.strip())

    if priority and priority.strip():
        query = query.filter(Case.priority == priority.strip())

    if status_filter and status_filter.strip():
        query = query.filter(Case.status == status_filter.strip())

    # Sorting
    sort_col = getattr(Case, sort_by, Case.created_at)
    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_col))
    else:
        query = query.order_by(desc(sort_col))

    total = query.count()
    offset = (page - 1) * limit
    cases = query.offset(offset).limit(limit).all()

    total_pages = (total + limit - 1) // limit if total > 0 else 1

    return {
        "cases": [c.to_dict() for c in cases],
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
    }


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(case_in: CaseCreate, db: Session = Depends(get_db)):
    """
    Create a new forensic investigation case with auto-generated unique Case ID
    and permanent database persistence.
    """
    # Validation
    if case_in.case_type not in VALID_CASE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid case_type '{case_in.case_type}'. Allowed: {', '.join(sorted(VALID_CASE_TYPES))}",
        )
    if case_in.priority not in VALID_PRIORITIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid priority '{case_in.priority}'. Allowed: {', '.join(sorted(VALID_PRIORITIES))}",
        )
    if case_in.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{case_in.status}'. Allowed: {', '.join(sorted(VALID_STATUSES))}",
        )

    # Ensure unique Case ID
    new_case_id = generate_case_id()
    while db.query(Case).filter(Case.case_id == new_case_id).first() is not None:
        new_case_id = generate_case_id()

    now = datetime.now(timezone.utc)
    new_case = Case(
        case_id=new_case_id,
        title=case_in.title.strip(),
        description=case_in.description.strip() if case_in.description else "",
        case_type=case_in.case_type,
        investigator=case_in.investigator.strip(),
        priority=case_in.priority,
        status=case_in.status,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )

    db.add(new_case)
    db.flush()

    # Audit Log
    log_audit_event(
        db=db,
        action_type="CASE_CREATED",
        actor=new_case.investigator,
        case_id=new_case.case_id,
        details={
            "title": new_case.title,
            "case_type": new_case.case_type,
            "priority": new_case.priority,
            "status": new_case.status,
        },
    )

    db.commit()
    db.refresh(new_case)
    return new_case.to_dict()


@router.get("/stats/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Provides aggregated forensic case metrics and activity overview for Dashboard.
    """
    total_cases = db.query(Case).filter(Case.is_archived == False).count()
    open_cases = db.query(Case).filter(Case.is_archived == False, Case.status == "Open").count()
    in_progress_cases = db.query(Case).filter(Case.is_archived == False, Case.status == "In Progress").count()
    under_review_cases = db.query(Case).filter(Case.is_archived == False, Case.status == "Under Review").count()
    closed_cases = db.query(Case).filter(Case.is_archived == False, Case.status == "Closed").count()
    total_evidence = db.query(Evidence).filter(Evidence.status == "Active").count()

    # By type
    types_count = {}
    for ct in VALID_CASE_TYPES:
        types_count[ct] = db.query(Case).filter(Case.is_archived == False, Case.case_type == ct).count()

    # By priority
    priority_count = {}
    for p in VALID_PRIORITIES:
        priority_count[p] = db.query(Case).filter(Case.is_archived == False, Case.priority == p).count()

    # Recent 5 cases
    recent_cases = (
        db.query(Case)
        .filter(Case.is_archived == False)
        .order_by(desc(Case.created_at))
        .limit(5)
        .all()
    )

    # Recent 10 audit logs
    recent_logs = (
        db.query(AuditLog)
        .order_by(desc(AuditLog.created_at))
        .limit(10)
        .all()
    )

    return {
        "total_cases": total_cases,
        "open_cases": open_cases,
        "in_progress_cases": in_progress_cases,
        "under_review_cases": under_review_cases,
        "closed_cases": closed_cases,
        "total_evidence": total_evidence,
        "cases_by_type": types_count,
        "cases_by_priority": priority_count,
        "recent_cases": [c.to_dict() for c in recent_cases],
        "recent_audit_logs": [l.to_dict() for l in recent_logs],
    }


@router.get("/{case_id}")
def get_case_details(case_id: str, db: Session = Depends(get_db)):
    """
    Retrieve full case details, including associated evidence and analysis records.
    """
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    case_data = case.to_dict()
    case_data["evidence"] = [e.to_dict() for e in case.evidence if e.status != "Archived"]
    case_data["analysis_records"] = [a.to_dict() for a in case.analysis_records]
    return case_data


@router.put("/{case_id}", response_model=CaseResponse)
def update_case(case_id: str, case_in: CaseUpdate, db: Session = Depends(get_db)):
    """
    Update case information while preserving case_id and recording updated timestamp.
    """
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    changes = {}

    if case_in.title is not None and case_in.title.strip() != case.title:
        changes["title"] = {"old": case.title, "new": case_in.title.strip()}
        case.title = case_in.title.strip()

    if case_in.description is not None and case_in.description.strip() != (case.description or ""):
        changes["description"] = "Updated synopsis"
        case.description = case_in.description.strip()

    if case_in.case_type is not None and case_in.case_type in VALID_CASE_TYPES and case_in.case_type != case.case_type:
        changes["case_type"] = {"old": case.case_type, "new": case_in.case_type}
        case.case_type = case_in.case_type

    if case_in.investigator is not None and case_in.investigator.strip() != case.investigator:
        changes["investigator"] = {"old": case.investigator, "new": case_in.investigator.strip()}
        case.investigator = case_in.investigator.strip()

    if case_in.priority is not None and case_in.priority in VALID_PRIORITIES and case_in.priority != case.priority:
        changes["priority"] = {"old": case.priority, "new": case_in.priority}
        case.priority = case_in.priority

    if case_in.status is not None and case_in.status in VALID_STATUSES and case_in.status != case.status:
        changes["status"] = {"old": case.status, "new": case_in.status}
        case.status = case_in.status

    if changes:
        case.updated_at = datetime.now(timezone.utc)
        log_audit_event(
            db=db,
            action_type="CASE_UPDATED",
            actor=case.investigator,
            case_id=case.case_id,
            details={"changes": changes},
        )
        db.commit()
        db.refresh(case)

    return case.to_dict()


@router.patch("/{case_id}/status", response_model=CaseResponse)
def update_case_status(case_id: str, status_in: CaseStatusUpdate, db: Session = Depends(get_db)):
    """
    Dedicated endpoint for case status transitions (e.g. Open -> In Progress -> Under Review -> Closed).
    """
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    if status_in.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{status_in.status}'. Allowed: {', '.join(sorted(VALID_STATUSES))}",
        )

    old_status = case.status
    if old_status != status_in.status:
        case.status = status_in.status
        case.updated_at = datetime.now(timezone.utc)

        log_audit_event(
            db=db,
            action_type="CASE_STATUS_CHANGED",
            actor=case.investigator,
            case_id=case.case_id,
            details={
                "old_status": old_status,
                "new_status": status_in.status,
                "notes": status_in.notes or "",
            },
        )
        db.commit()
        db.refresh(case)

    return case.to_dict()


@router.delete("/{case_id}")
def archive_case(case_id: str, db: Session = Depends(get_db)):
    """
    Safe soft-archive removal: preserves all evidence, analysis records,
    and audit trail without permanent loss of data.
    """
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    case.is_archived = True
    case.updated_at = datetime.now(timezone.utc)

    log_audit_event(
        db=db,
        action_type="CASE_ARCHIVED",
        actor=case.investigator,
        case_id=case.case_id,
        details={"message": "Case archived safely (soft delete). All evidence preserved."},
    )

    db.commit()
    return {"success": True, "message": f"Case '{case_id}' has been safely archived."}


@router.get("/{case_id}/report")
def generate_case_report(case_id: str, db: Session = Depends(get_db)):
    """
    Generates a structured forensic report for the case, including metadata,
    evidence chain of custody with SHA-256 hashes, analysis findings, and audit events.
    """
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    active_evidence = [e for e in case.evidence if e.status != "Archived"]
    analysis_records = list(case.analysis_records)
    audit_logs = (
        db.query(AuditLog)
        .filter(AuditLog.case_id == case_id)
        .order_by(asc(AuditLog.created_at))
        .all()
    )

    report = {
        "report_id": f"REP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system": "DeceptionLens Digital Forensics and Forgery Detection System",
        "case_overview": case.to_dict(),
        "evidence_summary": {
            "total_items": len(active_evidence),
            "items": [
                {
                    "evidence_id": e.evidence_id,
                    "evidence_name": e.evidence_name,
                    "evidence_type": e.evidence_type,
                    "original_filename": e.original_filename,
                    "file_size_bytes": e.file_size,
                    "mime_type": e.mime_type,
                    "sha256_hash": e.sha256_hash,
                    "uploaded_at": e.uploaded_at.isoformat() if e.uploaded_at else None,
                }
                for e in active_evidence
            ],
        },
        "forensic_analysis_records": [
            {
                "record_id": a.record_id,
                "evidence_id": a.evidence_id,
                "module_type": a.module_type,
                "verdict": a.verdict,
                "result_summary": a.result_summary,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in analysis_records
        ],
        "audit_trail": [
            {
                "event_id": log.event_id,
                "action_type": log.action_type,
                "actor": log.actor,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "details": json.loads(log.details) if log.details else {},
            }
            for log in audit_logs
        ],
        "forensic_disclaimer": (
            "This report is generated by DeceptionLens for research and educational purposes. "
            "Integrity checks confirm byte-level match against stored reference hashes. "
            "Analytical scores and verdicts are preliminary forensic indicators."
        ),
    }

    return report
