"""
DeceptionLens — Case Management: Unique ID Generators
=====================================================
Generates forensic-grade unique identifiers for Cases and Evidence items.
Both functions follow the DL-<TYPE>-YYYYMMDD-XXXXXX pattern to make
IDs human-readable, sortable by creation date, and collision-resistant.
"""

import uuid
from datetime import datetime, timezone


def generate_case_id() -> str:
    """Generate a unique forensic Case ID: DL-CASE-YYYYMMDD-XXXXXX."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:6].upper()
    return f"DL-CASE-{date_str}-{unique_suffix}"


def generate_evidence_id() -> str:
    """Generate a unique forensic Evidence ID: DL-EVD-YYYYMMDD-XXXXXX."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:6].upper()
    return f"DL-EVD-{date_str}-{unique_suffix}"
