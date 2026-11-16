"""
DeceptionLens — Dashboard & Report Management Module
====================================================
  dashboard.py — system-wide forensic overview for the Dashboard page
  reports.py   — saved, SHA-256-sealed case reports (generate, list, view,
                 download, verify, archive)
"""

from modules.reports.dashboard import get_dashboard_overview
from modules.reports.reports import (
    create_report,
    download_report,
    get_report,
    list_reports,
    update_report_status,
    verify_report,
)

__all__ = [
    "get_dashboard_overview",
    "create_report",
    "list_reports",
    "get_report",
    "download_report",
    "verify_report",
    "update_report_status",
]
