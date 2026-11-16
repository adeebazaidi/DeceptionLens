"""
DeceptionLens — Dashboard: System-wide Forensic Overview
========================================================
Aggregates cases, evidence, analysis verdicts, integrity checks, reports,
and recent activity into a single payload for the Dashboard page.
"""

import json
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from api.schemas.case_schemas import VALID_CASE_TYPES, VALID_PRIORITIES, VALID_STATUSES
from database.models import AnalysisRecord, AuditLog, Case, Evidence, ForensicReport

ACTIVITY_DAYS = 14

# Display order for the workflow-ordered categories.
STATUS_ORDER = ["Open", "In Progress", "Under Review", "Closed"]
PRIORITY_ORDER = ["Critical", "High", "Medium", "Low"]


def _count_by(db: Session, column, *filters) -> dict:
    rows = db.query(column, func.count()).filter(*filters).group_by(column).all()
    return {key: count for key, count in rows if key is not None}


def _as_utc(value: datetime) -> datetime:
    # SQLite returns naive datetimes; values are stored in UTC.
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def get_dashboard_overview(db: Session) -> dict:
    active_case = Case.is_archived == False  # noqa: E712

    cases_by_status = _count_by(db, Case.status, active_case)
    cases_by_type = _count_by(db, Case.case_type, active_case)
    cases_by_priority = _count_by(db, Case.priority, active_case)

    # Integrity checks: details is JSON text holding {"matches": bool, ...}
    integrity_rows = db.query(AuditLog.details).filter(AuditLog.action_type == "INTEGRITY_CHECKED").all()
    mismatches = 0
    for (details,) in integrity_rows:
        try:
            if json.loads(details or "{}").get("matches") is False:
                mismatches += 1
        except (TypeError, ValueError):
            continue

    # Activity: audit events per day for the last ACTIVITY_DAYS days (UTC).
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=ACTIVITY_DAYS - 1)
    since = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
    recent_times = db.query(AuditLog.created_at).filter(AuditLog.created_at >= since).all()
    per_day = Counter(_as_utc(ts).date() for (ts,) in recent_times if ts)
    activity = [
        {"date": (start + timedelta(days=i)).isoformat(), "events": per_day.get(start + timedelta(days=i), 0)}
        for i in range(ACTIVITY_DAYS)
    ]

    recent_analyses = db.query(AnalysisRecord).order_by(desc(AnalysisRecord.created_at)).limit(6).all()
    recent_reports = (
        db.query(ForensicReport)
        .filter(ForensicReport.status == "Final")
        .order_by(desc(ForensicReport.created_at))
        .limit(6)
        .all()
    )

    return {
        "totals": {
            "active_cases": db.query(Case).filter(active_case).count(),
            "archived_cases": db.query(Case).filter(Case.is_archived == True).count(),  # noqa: E712
            "active_evidence": db.query(Evidence).filter(Evidence.status == "Active").count(),
            "analyses": db.query(AnalysisRecord).count(),
            "reports": db.query(ForensicReport).filter(ForensicReport.status == "Final").count(),
            "integrity_checks": len(integrity_rows),
            "integrity_mismatches": mismatches,
        },
        "cases_by_status": [{"label": s, "count": cases_by_status.get(s, 0)} for s in STATUS_ORDER if s in VALID_STATUSES],
        "cases_by_priority": [{"label": p, "count": cases_by_priority.get(p, 0)} for p in PRIORITY_ORDER if p in VALID_PRIORITIES],
        "cases_by_type": sorted(
            ({"label": t, "count": cases_by_type.get(t, 0)} for t in VALID_CASE_TYPES),
            key=lambda row: (-row["count"], row["label"]),
        ),
        "evidence_by_type": sorted(
            ({"label": k, "count": v} for k, v in _count_by(db, Evidence.evidence_type, Evidence.status == "Active").items()),
            key=lambda row: (-row["count"], row["label"]),
        ),
        "analyses_by_module": sorted(
            ({"label": k, "count": v} for k, v in _count_by(db, AnalysisRecord.module_type).items()),
            key=lambda row: (-row["count"], row["label"]),
        ),
        "analysis_verdicts": sorted(
            ({"label": k, "count": v} for k, v in _count_by(db, AnalysisRecord.verdict).items()),
            key=lambda row: (-row["count"], row["label"]),
        ),
        "activity": activity,
        "recent_analyses": [a.to_dict() | {"result_data": None} for a in recent_analyses],
        "recent_reports": [r.to_dict() for r in recent_reports],
    }
