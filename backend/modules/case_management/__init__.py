"""
DeceptionLens — Case Management Module
======================================
Provides business logic for forensic case lifecycle management:

  ids.py      — Unique ID generators (DL-CASE-* and DL-EVD-*)
  audit.py    — Immutable audit event writing (log_audit_event)
  cases.py    — Case CRUD, status transitions, archiving, reporting, dashboard
  evidence.py — Evidence upload, listing, download, integrity, analysis dispatch

Usage from route handlers:
    from modules.case_management import (
        generate_case_id, generate_evidence_id,
        log_audit_event,
        create_case, list_cases, get_case_details, update_case,
        update_case_status, archive_case,
        get_dashboard_summary, generate_case_report,
        upload_evidence, list_case_evidence, list_all_evidence,
        get_evidence_details, download_evidence, preview_evidence,
        verify_integrity, update_evidence_status, run_evidence_analysis,
    )
"""

from modules.case_management.ids import (
    generate_case_id,
    generate_evidence_id,
)
from modules.case_management.audit import log_audit_event
from modules.case_management.cases import (
    list_cases,
    create_case,
    get_case_details,
    update_case,
    update_case_status,
    archive_case,
    get_dashboard_summary,
    generate_case_report,
)
from modules.case_management.evidence import (
    upload_evidence,
    list_case_evidence,
    list_all_evidence,
    get_evidence_details,
    download_evidence,
    preview_evidence,
    verify_integrity,
    update_evidence_status,
    run_evidence_analysis,
)

__all__ = [
    # IDs
    "generate_case_id",
    "generate_evidence_id",
    # Audit
    "log_audit_event",
    # Cases
    "list_cases",
    "create_case",
    "get_case_details",
    "update_case",
    "update_case_status",
    "archive_case",
    "get_dashboard_summary",
    "generate_case_report",
    # Evidence
    "upload_evidence",
    "list_case_evidence",
    "list_all_evidence",
    "get_evidence_details",
    "download_evidence",
    "preview_evidence",
    "verify_integrity",
    "update_evidence_status",
    "run_evidence_analysis",
]
