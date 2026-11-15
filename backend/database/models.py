"""
Database Models for DeceptionLens Forensic Case & Evidence Management
====================================================================
Defines persistent SQLAlchemy ORM models for:
- Cases
- Evidence
- Audit Logs
- Analysis Records
"""

from datetime import datetime, timezone
import json
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .connection import Base


def utc_now() -> datetime:
    """Returns current UTC timestamp."""
    return datetime.now(timezone.utc)


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    case_type = Column(String(64), nullable=False, default="Other")
    investigator = Column(String(128), nullable=False)
    priority = Column(String(32), nullable=False, default="Medium")
    status = Column(String(32), nullable=False, default="Open")
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    evidence = relationship(
        "Evidence",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="Evidence.uploaded_at.desc()",
    )
    audit_logs = relationship(
        "AuditLog",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="AuditLog.created_at.desc()",
    )
    analysis_records = relationship(
        "AnalysisRecord",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="AnalysisRecord.created_at.desc()",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "title": self.title,
            "description": self.description or "",
            "case_type": self.case_type,
            "investigator": self.investigator,
            "priority": self.priority,
            "status": self.status,
            "is_archived": self.is_archived,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "evidence_count": len([e for e in self.evidence if e.status != "Archived"]) if self.evidence else 0,
            "analysis_count": len(self.analysis_records) if self.analysis_records else 0,
        }


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    evidence_id = Column(String(64), unique=True, index=True, nullable=False)
    case_id = Column(String(64), ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    evidence_type = Column(String(64), nullable=False, default="Other")
    original_filename = Column(String(255), nullable=False)
    storage_filename = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    mime_type = Column(String(128), nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="Active")  # Active, Archived
    uploaded_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    case = relationship("Case", back_populates="evidence")
    audit_logs = relationship(
        "AuditLog",
        back_populates="evidence",
        order_by="AuditLog.created_at.desc()",
    )
    analysis_records = relationship(
        "AnalysisRecord",
        back_populates="evidence",
        order_by="AnalysisRecord.created_at.desc()",
    )

    def to_dict(self):
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
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "download_url": f"/api/evidence/{self.evidence_id}/download",
            "preview_url": f"/api/evidence/{self.evidence_id}/preview",
            "has_analysis": len(self.analysis_records) > 0 if self.analysis_records else False,
        }


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(String(64), unique=True, index=True, nullable=False)
    case_id = Column(String(64), ForeignKey("cases.case_id", ondelete="SET NULL"), nullable=True, index=True)
    evidence_id = Column(String(64), ForeignKey("evidence.evidence_id", ondelete="SET NULL"), nullable=True, index=True)
    action_type = Column(String(64), nullable=False, index=True)
    actor = Column(String(128), nullable=False, default="System Investigator")
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    # Relationships
    case = relationship("Case", back_populates="audit_logs")
    evidence = relationship("Evidence", back_populates="audit_logs")

    def to_dict(self):
        details_obj = None
        if self.details:
            try:
                details_obj = json.loads(self.details)
            except Exception:
                details_obj = {"message": self.details}
        return {
            "id": self.id,
            "event_id": self.event_id,
            "case_id": self.case_id,
            "evidence_id": self.evidence_id,
            "action_type": self.action_type,
            "actor": self.actor,
            "details": details_obj or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    record_id = Column(String(64), unique=True, index=True, nullable=False)
    case_id = Column(String(64), ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_id = Column(String(64), ForeignKey("evidence.evidence_id", ondelete="SET NULL"), nullable=True, index=True)
    module_type = Column(String(64), nullable=False)  # "Image Forgery", "Fingerprint Verification", "Signature Verification", "Document Analysis"
    result_summary = Column(Text, nullable=True)
    result_data = Column(Text, nullable=True)  # JSON payload
    verdict = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    case = relationship("Case", back_populates="analysis_records")
    evidence = relationship("Evidence", back_populates="analysis_records")

    def to_dict(self):
        data_obj = None
        if self.result_data:
            try:
                data_obj = json.loads(self.result_data)
            except Exception:
                data_obj = {"raw": self.result_data}
        return {
            "id": self.id,
            "record_id": self.record_id,
            "case_id": self.case_id,
            "evidence_id": self.evidence_id,
            "module_type": self.module_type,
            "result_summary": self.result_summary,
            "verdict": self.verdict,
            "result_data": data_obj,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
