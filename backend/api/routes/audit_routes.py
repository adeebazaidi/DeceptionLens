"""
Audit Trail REST API Routes
===========================
Provides read access to the forensic audit log for case chain-of-custody,
evidence acquisitions, integrity checks, and investigative decisions.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import AuditLog, Case, Evidence
from api.schemas.case_schemas import AuditLogListResponse, AuditLogResponse

router = APIRouter()


@router.get("/audit-logs", response_model=AuditLogListResponse)
def list_audit_logs(
    case_id: Optional[str] = Query(None, description="Filter by case ID"),
    evidence_id: Optional[str] = Query(None, description="Filter by evidence ID"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    limit: int = Query(50, ge=1, le=200, description="Max logs to return"),
    page: int = Query(1, ge=1, description="Page number"),
    db: Session = Depends(get_db),
):
    """
    List forensic audit events across all cases and evidence.
    """
    query = db.query(AuditLog)

    if case_id and case_id.strip():
        query = query.filter(AuditLog.case_id == case_id.strip())

    if evidence_id and evidence_id.strip():
        query = query.filter(AuditLog.evidence_id == evidence_id.strip())

    if action_type and action_type.strip():
        query = query.filter(AuditLog.action_type == action_type.strip())

    total = query.count()
    offset = (page - 1) * limit
    logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()

    return {
        "audit_logs": [log.to_dict() for log in logs],
        "total": total,
    }


@router.get("/cases/{case_id}/audit-logs")
def get_case_audit_logs(case_id: str, db: Session = Depends(get_db)):
    """
    Retrieve chronological audit trail for a specific case.
    """
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    logs = (
        db.query(AuditLog)
        .filter(AuditLog.case_id == case_id)
        .order_by(desc(AuditLog.created_at))
        .all()
    )
    return {"audit_logs": [log.to_dict() for log in logs], "total": len(logs)}


@router.get("/evidence/{evidence_id}/audit-logs")
def get_evidence_audit_logs(evidence_id: str, db: Session = Depends(get_db)):
    """
    Retrieve chronological audit trail for a specific evidence item.
    """
    evidence = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail=f"Evidence '{evidence_id}' not found.")

    logs = (
        db.query(AuditLog)
        .filter(AuditLog.evidence_id == evidence_id)
        .order_by(desc(AuditLog.created_at))
        .all()
    )
    return {"audit_logs": [log.to_dict() for log in logs], "total": len(logs)}
