"""
Tests — Dashboard & Report Management Module
============================================
- Saved report generation, SHA-256 sealing, and snapshot immutability
- Listing, search, retrieval, download, archiving
- Report integrity verification (including tamper detection)
- Audit trail events for report actions
- Dashboard overview aggregation
"""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

# Allow imports from backend root
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from database.connection import SessionLocal
from database.models import ForensicReport

client = TestClient(app)


def _new_case(title="Report Module Case", **extra):
    payload = {"title": title, "case_type": "Document Analysis", "investigator": "Examiner R", **extra}
    res = client.post("/api/cases", json=payload)
    assert res.status_code == 201
    return res.json()["case_id"]


def _upload(case_id, name="doc.pdf", data=b"%PDF-1.4 report test", evidence_type="Document"):
    res = client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": (name, data, "application/pdf")},
        data={"evidence_name": name, "evidence_type": evidence_type},
    )
    assert res.status_code == 201
    return res.json()


def _new_report(case_id, **extra):
    res = client.post("/api/reports", json={"case_id": case_id, "generated_by": "Examiner R", **extra})
    assert res.status_code == 201, res.text
    return res.json()


class TestReportGeneration:
    def test_create_report_is_sealed_snapshot(self):
        case_id = _new_case()
        _upload(case_id)
        rep = _new_report(case_id, notes="Initial findings")

        assert rep["report_id"].startswith("DL-REP-")
        assert rep["case_id"] == case_id
        assert rep["status"] == "Final"
        assert rep["evidence_count"] == 1
        assert len(rep["sha256_hash"]) == 64
        assert rep["title"] == "Forensic Report — Report Module Case"
        assert rep["notes"] == "Initial findings"

    def test_snapshot_does_not_change_when_case_changes(self):
        case_id = _new_case()
        rep = _new_report(case_id)
        _upload(case_id)  # added after the report was generated

        saved = client.get(f"/api/reports/{rep['report_id']}").json()
        assert saved["content"]["evidence_summary"]["total_items"] == 0
        assert saved["content"]["report_id"] == rep["report_id"]
        assert saved["content"]["case_overview"]["case_id"] == case_id

    def test_missing_case_404(self):
        res = client.post("/api/reports", json={"case_id": "DL-CASE-NOPE", "generated_by": "Examiner R"})
        assert res.status_code == 404

    def test_archived_case_400(self):
        case_id = _new_case()
        client.delete(f"/api/cases/{case_id}")
        res = client.post("/api/reports", json={"case_id": case_id, "generated_by": "Examiner R"})
        assert res.status_code == 400

    def test_validation_422(self):
        assert client.post("/api/reports", json={"case_id": "X"}).status_code == 422


class TestReportManagement:
    def test_list_search_and_filter(self):
        case_id = _new_case(title="Searchable Ledger Case")
        rep = _new_report(case_id, title="Ledger Forgery Findings")

        listed = client.get("/api/reports", params={"case_id": case_id}).json()
        assert [r["report_id"] for r in listed["reports"]] == [rep["report_id"]]
        assert listed["reports"][0]["case_title"] == "Searchable Ledger Case"

        found = client.get("/api/reports", params={"search": "Ledger Forgery"}).json()
        assert any(r["report_id"] == rep["report_id"] for r in found["reports"])

    def test_download_is_attachment_and_logged(self):
        case_id = _new_case()
        rep = _new_report(case_id)

        res = client.get(f"/api/reports/{rep['report_id']}/download")
        assert res.status_code == 200
        assert f"{rep['report_id']}.json" in res.headers["content-disposition"]
        body = res.json()
        assert body["report"]["sha256_hash"] == rep["sha256_hash"]
        assert body["content"]["case_overview"]["case_id"] == case_id

        logs = client.get(f"/api/cases/{case_id}/audit-logs").json()["audit_logs"]
        actions = {log["action_type"] for log in logs}
        assert {"REPORT_GENERATED", "REPORT_DOWNLOADED"} <= actions

    def test_archive_and_restore(self):
        case_id = _new_case()
        rep = _new_report(case_id)
        rid = rep["report_id"]

        res = client.patch(f"/api/reports/{rid}/status", json={"status": "Archived", "reason": "superseded"})
        assert res.status_code == 200 and res.json()["status"] == "Archived"
        assert all(r["report_id"] != rid for r in client.get("/api/reports").json()["reports"])
        archived = client.get("/api/reports", params={"status": "Archived"}).json()["reports"]
        assert any(r["report_id"] == rid for r in archived)

        assert client.patch(f"/api/reports/{rid}/status", json={"status": "Final"}).json()["status"] == "Final"
        assert client.patch(f"/api/reports/{rid}/status", json={"status": "Deleted"}).status_code == 400

    def test_unknown_report_404(self):
        assert client.get("/api/reports/DL-REP-NOPE").status_code == 404
        assert client.post("/api/reports/DL-REP-NOPE/verify").status_code == 404


class TestReportIntegrity:
    def test_verify_untouched_report_matches(self):
        rep = _new_report(_new_case())
        res = client.post(f"/api/reports/{rep['report_id']}/verify").json()
        assert res["status"] == "Hash Matches"
        assert res["matches"] is True
        assert res["calculated_hash"] == rep["sha256_hash"]

    def test_verify_detects_tampered_content(self):
        rep = _new_report(_new_case())

        db = SessionLocal()
        try:
            row = db.query(ForensicReport).filter(ForensicReport.report_id == rep["report_id"]).one()
            row.content = row.content.replace("Examiner R", "Someone Else")
            db.commit()
        finally:
            db.close()

        res = client.post(f"/api/reports/{rep['report_id']}/verify").json()
        assert res["status"] == "Hash Mismatch"
        assert res["matches"] is False
        assert res["recorded_hash"] == rep["sha256_hash"]


class TestDashboardOverview:
    def test_overview_structure_and_counts(self):
        before = client.get("/api/dashboard/overview").json()

        case_id = _new_case(priority="Critical")
        ev = _upload(case_id)
        client.post(f"/api/evidence/{ev['evidence_id']}/verify-integrity")
        _new_report(case_id)

        after = client.get("/api/dashboard/overview").json()
        t0, t1 = before["totals"], after["totals"]
        assert t1["active_cases"] == t0["active_cases"] + 1
        assert t1["active_evidence"] == t0["active_evidence"] + 1
        assert t1["reports"] == t0["reports"] + 1
        assert t1["integrity_checks"] == t0["integrity_checks"] + 1

        assert [row["label"] for row in after["cases_by_status"]] == ["Open", "In Progress", "Under Review", "Closed"]
        assert [row["label"] for row in after["cases_by_priority"]] == ["Critical", "High", "Medium", "Low"]
        critical = next(row for row in after["cases_by_priority"] if row["label"] == "Critical")
        assert critical["count"] >= 1

        assert len(after["activity"]) == 14
        assert after["activity"][-1]["events"] >= 4  # case + upload + integrity + report today
        assert after["recent_reports"][0]["case_id"] == case_id
