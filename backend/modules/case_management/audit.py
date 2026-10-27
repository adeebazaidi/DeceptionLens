"""
DeceptionLens — Case Management: Audit Log Service
==================================================
Handles writing and reading forensic audit events.
All write operations produce immutable AuditLog rows to support
chain-of-custody requirements. Read helpers are thin query wrappers
consumed directly by audit_routes.py.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from database.models import AuditLog


def log_audit_event(
    db: Session,
    action_type: str,
    actor: str,
    case_id: Optional[str] = None,
    evidence_id: Optional[str] = None,
    details: Optional[dict] = None,
) -> AuditLog:
    """
    Records an immutable forensic audit event.

    Creates an AuditLog row with a unique EVT-YYYYMMDD-XXXXXX event_id,
    flushes it to the session (caller is responsible for commit), and returns
    the newly-created ORM object.
    """
    event_id = (
        f"EVT-{datetime.now(timezone.utc).strftime('%Y%m%d')}-"
        f"{uuid.uuid4().hex[:6].upper()}"
    )
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
