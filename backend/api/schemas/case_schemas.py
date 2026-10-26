"""
Pydantic Schemas for Case and Evidence Management
================================================
Validates request payloads and formats serialized API responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Case Schemas ─────────────────────────────────────────────────────────────

VALID_CASE_TYPES = {
    "Image Forgery",
    "Fingerprint Verification",
    "Signature Verification",
    "Document Analysis",
    "Other",
}

VALID_PRIORITIES = {"Low", "Medium", "High", "Critical"}

VALID_STATUSES = {"Open", "In Progress", "Under Review", "Closed"}


class CaseCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255, description="Case title")
    description: Optional[str] = Field(None, max_length=5000, description="Investigation synopsis")
    case_type: str = Field("Other", description="Category of forensic investigation")
    investigator: str = Field(..., min_length=2, max_length=128, description="Investigator / examiner name")
    priority: str = Field("Medium", description="Low, Medium, High, or Critical")
    status: str = Field("Open", description="Open, In Progress, Under Review, or Closed")


class CaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    case_type: Optional[str] = None
    investigator: Optional[str] = Field(None, min_length=2, max_length=128)
    priority: Optional[str] = None
    status: Optional[str] = None


class CaseStatusUpdate(BaseModel):
    status: str = Field(..., description="New status")
    notes: Optional[str] = Field(None, description="Optional justification or status transition notes")


class CaseResponse(BaseModel):
    id: int
    case_id: str
    title: str
    description: Optional[str] = ""
    case_type: str
    investigator: str
    priority: str
    status: str
    is_archived: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    evidence_count: int = 0
    analysis_count: int = 0


class CaseListResponse(BaseModel):
    cases: List[CaseResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# ── Evidence Schemas ─────────────────────────────────────────────────────────

class EvidenceResponse(BaseModel):
    id: int
    evidence_id: str
    case_id: str
    evidence_name: str
    description: Optional[str] = ""
    evidence_type: str
    original_filename: str
    storage_filename: str
    file_size: int
    mime_type: str
    sha256_hash: str
    status: str
    uploaded_at: Optional[str] = None
    download_url: str
    preview_url: str
    has_analysis: bool = False


class EvidenceListResponse(BaseModel):
    evidence: List[EvidenceResponse]
    total: int


class EvidenceStatusUpdate(BaseModel):
    status: str = Field(..., description="'Active' or 'Archived'")
    reason: Optional[str] = None


# ── Integrity Check Schemas ──────────────────────────────────────────────────

class IntegrityCheckResponse(BaseModel):
    status: str  # "Hash Matches", "Hash Mismatch", "File Unavailable"
    matches: bool
    recorded_hash: str
    calculated_hash: Optional[str] = None
    explanation: str
    verified_at: str


# ── Audit Log Schemas ────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: int
    event_id: str
    case_id: Optional[str] = None
    evidence_id: Optional[str] = None
    action_type: str
    actor: str
    details: Dict[str, Any] = {}
    created_at: Optional[str] = None


class AuditLogListResponse(BaseModel):
    audit_logs: List[AuditLogResponse]
    total: int


# ── Analysis Record Schemas ──────────────────────────────────────────────────

class AnalysisRecordResponse(BaseModel):
    id: int
    record_id: str
    case_id: str
    evidence_id: Optional[str] = None
    module_type: str
    result_summary: Optional[str] = None
    verdict: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


# ── Dashboard & Stats Schemas ────────────────────────────────────────────────

class DashboardStatsResponse(BaseModel):
    total_cases: int
    open_cases: int
    in_progress_cases: int
    under_review_cases: int
    closed_cases: int
    total_evidence: int
    cases_by_type: Dict[str, int]
    cases_by_priority: Dict[str, int]
    recent_cases: List[CaseResponse]
    recent_audit_logs: List[AuditLogResponse]
