"""
DeceptionLens — ORM Models
==========================
Case          — a forensic investigation
Evidence      — a digital file attached to a case, with its SHA-256 baseline
AnalysisRecord— the stored result of running a forensic module on evidence
AuditLog      — an immutable chain-of-custody event

Each model exposes to_dict() returning a JSON-serializable dict matching the
response schemas in api/schemas/case_schemas.py.
"""

import json
from datetime import datetime, timezone
from typing import Any, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


def _load_json(value: Optional[str]) -> Any:
    if not value:
        return {}
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return {"raw": value}


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    case_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, default="")
    case_type: Mapped[str] = mapped_column(String(64), default="Other")
    investigator: Mapped[str] = mapped_column(String(128))
    priority: Mapped[str] = mapped_column(String(32), default="Medium")
    status: Mapped[str] = mapped_column(String(32), default="Open")
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=_utcnow)

    evidence: Mapped[List["Evidence"]] = relationship(
        back_populates="case", order_by="Evidence.uploaded_at"
    )
    analysis_records: Mapped[List["AnalysisRecord"]] = relationship(
        back_populates="case", order_by="AnalysisRecord.created_at"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "case_id": self.case_id,
            "title": self.title,
            "description": self.description or "",
            "case_type": self.case_type,
            "investigator": self.investigator,
            "priority": self.priority,
            "status": self.status,
            "is_archived": bool(self.is_archived),
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
            "evidence_count": sum(1 for e in self.evidence if e.status != "Archived"),
            "analysis_count": len(self.analysis_records),
        }


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    evidence_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), index=True)
    evidence_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, default="")
    evidence_type: Mapped[str] = mapped_column(String(64), default="Image")
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_filename: Mapped[str] = mapped_column(String(255), unique=True)
    storage_path: Mapped[str] = mapped_column(String(1024))
    file_size: Mapped[int] = mapped_column(Integer)
    mime_type: Mapped[str] = mapped_column(String(128), default="application/octet-stream")
    sha256_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="Active")
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=_utcnow)

    case: Mapped["Case"] = relationship(back_populates="evidence")
    analysis_records: Mapped[List["AnalysisRecord"]] = relationship(
        back_populates="evidence", order_by="AnalysisRecord.created_at"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "evidence_id": self.evidence_id,
            "case_id": self.case_id,
            "evidence_name": self.evidence_name,
            "description": self.description or "",
            "evidence_type": self.evidence_type,
            "original_filename": self.original_filename,
            "storage_filename": self.storage_filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "sha256_hash": self.sha256_hash,
            "status": self.status,
            "uploaded_at": _iso(self.uploaded_at),
            "download_url": f"/api/evidence/{self.evidence_id}/download",
            "preview_url": f"/api/evidence/{self.evidence_id}/preview",
            "has_analysis": len(self.analysis_records) > 0,
        }


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    record_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), index=True)
    evidence_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("evidence.evidence_id"), index=True
    )
    module_type: Mapped[str] = mapped_column(String(64))
    result_summary: Mapped[Optional[str]] = mapped_column(Text, default="")
    verdict: Mapped[Optional[str]] = mapped_column(String(64))
    result_data: Mapped[Optional[str]] = mapped_column(Text, default="{}")  # JSON-encoded
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=_utcnow)

    case: Mapped["Case"] = relationship(back_populates="analysis_records")
    evidence: Mapped[Optional["Evidence"]] = relationship(back_populates="analysis_records")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "record_id": self.record_id,
            "case_id": self.case_id,
            "evidence_id": self.evidence_id,
            "module_type": self.module_type,
            "result_summary": self.result_summary,
            "verdict": self.verdict,
            "result_data": _load_json(self.result_data),
            "created_at": _iso(self.created_at),
        }


class AuditLog(Base):
    """
    Immutable audit event. case_id / evidence_id are plain indexed columns
    (not foreign keys) so the trail survives independently of the records
    it describes.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    case_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    evidence_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    action_type: Mapped[str] = mapped_column(String(64), index=True)
    actor: Mapped[str] = mapped_column(String(128), default="Forensic Examiner")
    details: Mapped[Optional[str]] = mapped_column(Text, default="{}")  # JSON-encoded
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_id": self.event_id,
            "case_id": self.case_id,
            "evidence_id": self.evidence_id,
            "action_type": self.action_type,
            "actor": self.actor,
            "details": _load_json(self.details),
            "created_at": _iso(self.created_at),
        }


class ForensicReport(Base):
    """
    A saved, immutable snapshot of a case report. `content` holds the full
    report JSON and `sha256_hash` seals it, so later tampering is detectable.
    """

    __tablename__ = "forensic_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    generated_by: Mapped[str] = mapped_column(String(128))
    notes: Mapped[Optional[str]] = mapped_column(Text, default="")
    content: Mapped[str] = mapped_column(Text)  # canonical JSON of the report
    sha256_hash: Mapped[str] = mapped_column(String(64))
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    analysis_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="Final")
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )

    case: Mapped["Case"] = relationship()

    def to_dict(self, include_content: bool = False) -> dict:
        data = {
            "id": self.id,
            "report_id": self.report_id,
            "case_id": self.case_id,
            "case_title": self.case.title if self.case else None,
            "title": self.title,
            "generated_by": self.generated_by,
            "notes": self.notes or "",
            "sha256_hash": self.sha256_hash,
            "evidence_count": self.evidence_count,
            "analysis_count": self.analysis_count,
            "status": self.status,
            "created_at": _iso(self.created_at),
            "download_url": f"/api/reports/{self.report_id}/download",
        }
        if include_content:
            data["content"] = _load_json(self.content)
        return data
