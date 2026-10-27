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
from typing import Any, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

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

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    case_type = Column(String(64), nullable=False, default="Other")
    investigator = Column(String(128), nullable=False)
    priority = Column(String(32), nullable=False, default="Medium")
    status = Column(String(32), nullable=False, default="Open")
    is_archived = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow)

    evidence = relationship(
        "Evidence", back_populates="case", order_by="Evidence.uploaded_at"
    )
    analysis_records = relationship(
        "AnalysisRecord", back_populates="case", order_by="AnalysisRecord.created_at"
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

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(String(64), unique=True, index=True, nullable=False)
    case_id = Column(String(64), ForeignKey("cases.case_id"), index=True, nullable=False)
    evidence_name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    evidence_type = Column(String(64), nullable=False, default="Image")
    original_filename = Column(String(255), nullable=False)
    storage_filename = Column(String(255), unique=True, nullable=False)
    storage_path = Column(String(1024), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(128), nullable=False, default="application/octet-stream")
    sha256_hash = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="Active")
    uploaded_at = Column(DateTime(timezone=True), default=_utcnow)

    case = relationship("Case", back_populates="evidence")
    analysis_records = relationship(
        "AnalysisRecord", back_populates="evidence", order_by="AnalysisRecord.created_at"
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

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(String(64), unique=True, index=True, nullable=False)
    case_id = Column(String(64), ForeignKey("cases.case_id"), index=True, nullable=False)
    evidence_id = Column(String(64), ForeignKey("evidence.evidence_id"), index=True, nullable=True)
    module_type = Column(String(64), nullable=False)
    result_summary = Column(Text, default="")
    verdict = Column(String(64), nullable=True)
    result_data = Column(Text, default="{}")  # JSON-encoded
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    case = relationship("Case", back_populates="analysis_records")
    evidence = relationship("Evidence", back_populates="analysis_records")

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

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(64), unique=True, index=True, nullable=False)
    case_id = Column(String(64), index=True, nullable=True)
    evidence_id = Column(String(64), index=True, nullable=True)
    action_type = Column(String(64), index=True, nullable=False)
    actor = Column(String(128), nullable=False, default="Forensic Examiner")
    details = Column(Text, default="{}")  # JSON-encoded
    created_at = Column(DateTime(timezone=True), default=_utcnow, index=True)

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
