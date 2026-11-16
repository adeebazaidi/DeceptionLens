"""
Dashboard & Report Management REST API Routes
=============================================
Thin FastAPI route handlers. All logic lives in modules.reports.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from modules.reports import (
    create_report,
    download_report,
    get_dashboard_overview,
    get_report,
    list_reports,
    update_report_status,
    verify_report,
)

router = APIRouter()


class ReportCreate(BaseModel):
    case_id: str = Field(..., min_length=1, description="Case to report on")
    generated_by: str = Field(..., min_length=2, max_length=128, description="Examiner generating the report")
    title: Optional[str] = Field(None, max_length=255, description="Optional report title")
    notes: Optional[str] = Field(None, max_length=5000, description="Examiner notes / conclusions")


class ReportStatusUpdate(BaseModel):
    status: str = Field(..., description="'Final' or 'Archived'")
    reason: Optional[str] = None


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard/overview", tags=["Dashboard"])
def dashboard_overview_route(db: Session = Depends(get_db)):
    """System-wide overview: cases, evidence, verdicts, integrity, reports, activity."""
    return get_dashboard_overview(db=db)


# ── Reports ───────────────────────────────────────────────────────────────────

@router.post("/reports", status_code=status.HTTP_201_CREATED, tags=["Report Management"])
def create_report_route(report_in: ReportCreate, db: Session = Depends(get_db)):
    """Generate and save a SHA-256-sealed snapshot report for a case."""
    return create_report(
        db=db,
        case_id=report_in.case_id,
        generated_by=report_in.generated_by,
        title=report_in.title,
        notes=report_in.notes,
    )


@router.get("/reports", tags=["Report Management"])
def list_reports_route(
    case_id: Optional[str] = Query(None, description="Filter by case ID"),
    search: Optional[str] = Query(None, description="Search report ID, title, case ID, or examiner"),
    status_filter: Optional[str] = Query(None, alias="status", description="Final (default), Archived, or all"),
    db: Session = Depends(get_db),
):
    """List saved reports, newest first."""
    return list_reports(db=db, case_id=case_id, search=search, status_filter=status_filter)


@router.get("/reports/{report_id}", tags=["Report Management"])
def get_report_route(report_id: str, db: Session = Depends(get_db)):
    """Retrieve a saved report including its full content."""
    return get_report(db=db, report_id=report_id)


@router.get("/reports/{report_id}/download", tags=["Report Management"])
def download_report_route(report_id: str, db: Session = Depends(get_db)):
    """Download a saved report as JSON (logged in the audit trail)."""
    return download_report(db=db, report_id=report_id)


@router.post("/reports/{report_id}/verify", tags=["Report Management"])
def verify_report_route(report_id: str, db: Session = Depends(get_db)):
    """Re-hash the saved report content and compare it with its seal."""
    return verify_report(db=db, report_id=report_id)


@router.patch("/reports/{report_id}/status", tags=["Report Management"])
def update_report_status_route(report_id: str, status_in: ReportStatusUpdate, db: Session = Depends(get_db)):
    """Archive or restore a saved report (reports are never deleted)."""
    return update_report_status(db=db, report_id=report_id, status_value=status_in.status, reason=status_in.reason)
