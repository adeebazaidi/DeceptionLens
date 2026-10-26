"""
Tests — Case and Evidence Management Module
===========================================
Comprehensive unit and integration test suite covering:
- Case creation, validation, unique ID generation, and editing
- Status transitions and safe archiving
- Evidence uploading, format validation, and safe storage
- Secure controlled download and path traversal prevention
- SHA-256 cryptographic integrity recalculation & mismatch detection
- Audit logging of all forensic events
- Dashboard statistics calculation
"""

import io
import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Allow imports from backend root
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from database.connection import init_db, get_db, SessionLocal
from database.models import Case, Evidence, AuditLog
from storage.evidence_storage import STORAGE_DIR

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure database schema is ready before tests."""
    init_db()
    yield


class TestCaseManagement:
    def test_create_case_success(self):
        """Test creating a valid forensic case."""
        payload = {
            "title": "Suspected Financial Document Forgery",
            "description": "Investigation into manipulated invoice headers and signatures.",
            "case_type": "Document Analysis",
            "investigator": "Inspector Sarah Connor",
            "priority": "High",
            "status": "Open",
        }
        res = client.post("/api/cases", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["case_id"].startswith("DL-CASE-")
        assert data["title"] == payload["title"]
        assert data["investigator"] == payload["investigator"]
        assert data["status"] == "Open"
        assert data["priority"] == "High"
        assert data["case_type"] == "Document Analysis"

    def test_create_case_validation_errors(self):
        """Test validation rules when creating cases."""
        # Missing title
        res = client.post("/api/cases", json={
            "description": "No title",
            "case_type": "Image Forgery",
            "investigator": "John Doe",
        })
        assert res.status_code == 422

        # Invalid case type
        res = client.post("/api/cases", json={
            "title": "Bad Type Case",
            "case_type": "InvalidType123",
            "investigator": "John Doe",
        })
        assert res.status_code == 400

        # Invalid priority
        res = client.post("/api/cases", json={
            "title": "Bad Priority Case",
            "case_type": "Image Forgery",
            "investigator": "John Doe",
            "priority": "ExtremeUrgent",
        })
        assert res.status_code == 400

    def test_list_and_search_cases(self):
        """Test listing, searching, and filtering cases."""
        # Create distinct case
        c_res = client.post("/api/cases", json={
            "title": "Homicide Fingerprint Latent Match",
            "description": "Crime scene latent print extraction.",
            "case_type": "Fingerprint Verification",
            "investigator": "Officer Davis",
            "priority": "Critical",
            "status": "In Progress",
        })
        case_id = c_res.json()["case_id"]

        # Search by Title
        search_res = client.get("/api/cases?search=Homicide")
        assert search_res.status_code == 200
        found = [c for c in search_res.json()["cases"] if c["case_id"] == case_id]
        assert len(found) == 1

        # Search by Case ID
        id_search_res = client.get(f"/api/cases?search={case_id}")
        assert id_search_res.status_code == 200
        assert len(id_search_res.json()["cases"]) >= 1

        # Filter by Case Type
        filter_type_res = client.get("/api/cases?case_type=Fingerprint Verification")
        assert filter_type_res.status_code == 200
        assert all(c["case_type"] == "Fingerprint Verification" for c in filter_type_res.json()["cases"])

        # Filter by Priority
        filter_pri_res = client.get("/api/cases?priority=Critical")
        assert filter_pri_res.status_code == 200
        assert all(c["priority"] == "Critical" for c in filter_pri_res.json()["cases"])

    def test_update_case_preserves_id(self):
        """Test editing a case updates fields, updates timestamp, and preserves case_id."""
        c_res = client.post("/api/cases", json={
            "title": "Original Title",
            "description": "Original Description",
            "case_type": "Other",
            "investigator": "Initial Agent",
            "priority": "Low",
            "status": "Open",
        })
        orig_data = c_res.json()
        case_id = orig_data["case_id"]

        # Update
        up_res = client.put(f"/api/cases/{case_id}", json={
            "title": "Updated Title After Evidence Review",
            "priority": "High",
            "investigator": "Senior Examiner Jones",
        })
        assert up_res.status_code == 200
        up_data = up_res.json()
        assert up_data["case_id"] == case_id  # Preserved!
        assert up_data["title"] == "Updated Title After Evidence Review"
        assert up_data["priority"] == "High"
        assert up_data["investigator"] == "Senior Examiner Jones"

    def test_update_case_status(self):
        """Test dedicated status update endpoint."""
        c_res = client.post("/api/cases", json={
            "title": "Status Transition Case",
            "case_type": "Image Forgery",
            "investigator": "Examiner",
            "status": "Open",
        })
        case_id = c_res.json()["case_id"]

        patch_res = client.patch(
            f"/api/cases/{case_id}/status",
            json={"status": "In Progress", "notes": "Initiated preliminary forensic scan."},
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "In Progress"

    def test_archive_case(self):
        """Test safe soft-archive of a case."""
        c_res = client.post("/api/cases", json={
            "title": "Case to be Archived",
            "case_type": "Other",
            "investigator": "Examiner",
        })
        case_id = c_res.json()["case_id"]

        del_res = client.delete(f"/api/cases/{case_id}")
        assert del_res.status_code == 200

        # Should not appear in standard list
        list_res = client.get("/api/cases")
        assert all(c["case_id"] != case_id for c in list_res.json()["cases"])

        # Should appear when include_archived=true
        arch_res = client.get("/api/cases?include_archived=true")
        assert any(c["case_id"] == case_id for c in arch_res.json()["cases"])


class TestEvidenceManagement:
    def test_upload_evidence_success(self):
        """Test uploading digital evidence to an existing case."""
        # 1. Create case
        c_res = client.post("/api/cases", json={
            "title": "Evidence Upload Test Case",
            "case_type": "Image Forgery",
            "investigator": "Agent Fox",
        })
        case_id = c_res.json()["case_id"]

        # 2. Upload image evidence
        sample_img_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        files = {
            "file": ("suspect_photo.png", sample_img_bytes, "image/png"),
        }
        data = {
            "evidence_name": "Tampered License Plate",
            "description": "High-res photograph of rear license plate.",
            "evidence_type": "Image",
        }

        res = client.post(f"/api/cases/{case_id}/evidence", files=files, data=data)
        assert res.status_code == 201
        ev_data = res.json()

        assert ev_data["evidence_id"].startswith("DL-EVD-")
        assert ev_data["case_id"] == case_id
        assert ev_data["evidence_name"] == "Tampered License Plate"
        assert ev_data["original_filename"] == "suspect_photo.png"
        assert len(ev_data["sha256_hash"]) == 64
        assert ev_data["status"] == "Active"

    def test_upload_evidence_rejects_unsupported_type(self):
        """Test rejecting unsupported executable or script files."""
        c_res = client.post("/api/cases", json={
            "title": "Security Rejection Case",
            "case_type": "Other",
            "investigator": "Security Officer",
        })
        case_id = c_res.json()["case_id"]

        files = {
            "file": ("malicious.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/x-dosexec"),
        }
        data = {"evidence_name": "Suspicious Executable", "evidence_type": "Other"}
        res = client.post(f"/api/cases/{case_id}/evidence", files=files, data=data)
        assert res.status_code == 400
        assert "Unsupported file format" in res.json()["detail"]

    def test_secure_evidence_download(self):
        """Test downloading original evidence through the controlled endpoint."""
        c_res = client.post("/api/cases", json={
            "title": "Download Test Case",
            "case_type": "Image Forgery",
            "investigator": "Officer Download",
        })
        case_id = c_res.json()["case_id"]

        test_content = b"GENUINE_EVIDENCE_PAYLOAD_TEST_12345"
        files = {"file": ("contract_scan.pdf", test_content, "application/pdf")}
        data = {"evidence_name": "Original Contract", "evidence_type": "Document"}
        ev_res = client.post(f"/api/cases/{case_id}/evidence", files=files, data=data)
        evidence_id = ev_res.json()["evidence_id"]

        # Download
        dl_res = client.get(f"/api/evidence/{evidence_id}/download")
        assert dl_res.status_code == 200
        assert dl_res.content == test_content
        assert "contract_scan.pdf" in dl_res.headers.get("content-disposition", "")


class TestIntegrityAndAudit:
    def test_sha256_integrity_match(self):
        """Test that recalculating hash on an untampered file yields 'Hash Matches'."""
        c_res = client.post("/api/cases", json={
            "title": "Integrity Check Case",
            "case_type": "Signature Verification",
            "investigator": "Examiner Audit",
        })
        case_id = c_res.json()["case_id"]

        sample_bytes = b"SAMPLE_SIGNATURE_VECTOR_DATA_ABC"
        files = {"file": ("sig.png", sample_bytes, "image/png")}
        ev_res = client.post(f"/api/cases/{case_id}/evidence", files=files, data={"evidence_name": "Sig 1"})
        evidence_id = ev_res.json()["evidence_id"]
        original_hash = ev_res.json()["sha256_hash"]

        # Verify Integrity
        check_res = client.post(f"/api/evidence/{evidence_id}/verify-integrity")
        assert check_res.status_code == 200
        result = check_res.json()
        assert result["status"] == "Hash Matches"
        assert result["matches"] is True
        assert result["recorded_hash"] == original_hash
        assert result["calculated_hash"] == original_hash
        assert "matches the recorded baseline" in result["explanation"]

    def test_sha256_integrity_detects_disk_modification(self):
        """Test that physical file modification on disk results in 'Hash Mismatch'."""
        c_res = client.post("/api/cases", json={
            "title": "Tamper Test Case",
            "case_type": "Image Forgery",
            "investigator": "Integrity Tester",
        })
        case_id = c_res.json()["case_id"]

        original_bytes = b"ORIGINAL_AUTHENTIC_STREAM"
        files = {"file": ("sample.jpg", original_bytes, "image/jpeg")}
        ev_res = client.post(f"/api/cases/{case_id}/evidence", files=files, data={"evidence_name": "Audit Sample"})
        evidence_id = ev_res.json()["evidence_id"]
        storage_filename = ev_res.json()["storage_filename"]
        original_hash = ev_res.json()["sha256_hash"]

        # Simulate external file tampering
        file_path = STORAGE_DIR / storage_filename
        with open(file_path, "wb") as f:
            f.write(b"CORRUPTED_MODIFIED_STREAM_TAMPERED!")

        # Verify Integrity
        check_res = client.post(f"/api/evidence/{evidence_id}/verify-integrity")
        assert check_res.status_code == 200
        result = check_res.json()
        assert result["status"] == "Hash Mismatch"
        assert result["matches"] is False
        assert result["recorded_hash"] == original_hash
        assert result["calculated_hash"] != original_hash
        assert "differs from the recorded baseline" in result["explanation"]

    def test_audit_logs_recorded(self):
        """Test that actions generate audit trail records."""
        # 1. Create case
        c_res = client.post("/api/cases", json={
            "title": "Audit Trail Verification Case",
            "case_type": "Document Analysis",
            "investigator": "Auditor Dave",
        })
        case_id = c_res.json()["case_id"]

        # Check case audit logs
        logs_res = client.get(f"/api/cases/{case_id}/audit-logs")
        assert logs_res.status_code == 200
        logs = logs_res.json()["audit_logs"]
        assert any(log["action_type"] == "CASE_CREATED" for log in logs)

        # 2. Upload evidence
        files = {"file": ("doc.pdf", b"%PDF-1.4 sample content", "application/pdf")}
        ev_res = client.post(f"/api/cases/{case_id}/evidence", files=files, data={"evidence_name": "Audit Doc"})
        evidence_id = ev_res.json()["evidence_id"]

        # Check evidence audit logs
        ev_logs_res = client.get(f"/api/evidence/{evidence_id}/audit-logs")
        assert ev_logs_res.status_code == 200
        ev_logs = ev_logs_res.json()["audit_logs"]
        assert any(log["action_type"] == "EVIDENCE_UPLOADED" for log in ev_logs)

    def test_case_report_generation(self):
        """Test comprehensive forensic report generation."""
        c_res = client.post("/api/cases", json={
            "title": "Full Report Case",
            "case_type": "Image Forgery",
            "investigator": "Dr. Watson",
            "priority": "Medium",
        })
        case_id = c_res.json()["case_id"]

        # Upload evidence
        client.post(f"/api/cases/{case_id}/evidence", files={
            "file": ("evidence_item.jpg", b"SOME_IMAGE_DATA_123", "image/jpeg")
        }, data={"evidence_name": "Photo 1"})

        report_res = client.get(f"/api/cases/{case_id}/report")
        assert report_res.status_code == 200
        rep = report_res.json()
        assert rep["case_overview"]["case_id"] == case_id
        assert rep["evidence_summary"]["total_items"] == 1
        assert "audit_trail" in rep
        assert "forensic_disclaimer" in rep

    def test_dashboard_summary_endpoint(self):
        """Test dashboard statistics aggregation."""
        stats_res = client.get("/api/cases/stats/summary")
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert "total_cases" in stats
        assert "cases_by_type" in stats
        assert "cases_by_priority" in stats
        assert "recent_cases" in stats
        assert "recent_audit_logs" in stats
