"""
Case Management REST API Routes
================================
Thin FastAPI route handlers for Case operations.
All business logic lives in modules.case_management.cases.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from api.schemas.case_schemas import (
    CaseCreate,
    CaseUpdate,
    CaseStatusUpdate,
    CaseResponse,
    CaseListResponse,
)
from modules.case_management import (
    list_cases,
    create_case,
    get_case_details,
    update_case,
    update_case_status,
    archive_case,
    get_dashboard_summary,
    generate_case_report,
)

router = APIRouter()


@router.get("", response_model=CaseListResponse)
def list_cases_route(
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
    return list_cases(
        db=db,
        search=search,
        case_type=case_type,
        priority=priority,
        status_filter=status_filter,
        include_archived=include_archived,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit,
    )


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case_route(case_in: CaseCreate, db: Session = Depends(get_db)):
    """
    Create a new forensic investigation case with auto-generated unique Case ID
    and permanent database persistence.
    """
    return create_case(db=db, case_in=case_in)


@router.get("/stats/summary")
def get_dashboard_summary_route(db: Session = Depends(get_db)):
    """
    Provides aggregated forensic case metrics and activity overview for the Dashboard.
    """
    return get_dashboard_summary(db=db)


@router.get("/{case_id}")
def get_case_details_route(case_id: str, db: Session = Depends(get_db)):
    """
    Retrieve full case details, including associated evidence and analysis records.
    """
    return get_case_details(db=db, case_id=case_id)


@router.put("/{case_id}", response_model=CaseResponse)
def update_case_route(case_id: str, case_in: CaseUpdate, db: Session = Depends(get_db)):
    """
    Update case information while preserving case_id and recording updated timestamp.
    """
    return update_case(db=db, case_id=case_id, case_in=case_in)


@router.patch("/{case_id}/status", response_model=CaseResponse)
def update_case_status_route(
    case_id: str, status_in: CaseStatusUpdate, db: Session = Depends(get_db)
):
    """
    Dedicated endpoint for case status transitions
    (e.g. Open -> In Progress -> Under Review -> Closed).
    """
    return update_case_status(db=db, case_id=case_id, status_in=status_in)


@router.delete("/{case_id}")
def archive_case_route(case_id: str, db: Session = Depends(get_db)):
    """
    Safe soft-archive removal: preserves all evidence, analysis records,
    and audit trail without permanent loss of data.
    """
    return archive_case(db=db, case_id=case_id)


@router.get("/{case_id}/report")
def generate_case_report_route(case_id: str, db: Session = Depends(get_db)):
    """
    Generates a structured forensic report for the case, including metadata,
    evidence chain of custody with SHA-256 hashes, analysis findings, and audit events.
    """
    return generate_case_report(db=db, case_id=case_id)
