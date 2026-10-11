"""
Unit tests for Document Analysis Consistency Checker.
======================================================
Tests rule-based cross-field inconsistency detection across
dates, locations, monetary amounts, person names, and case numbers.
"""

import pytest
from modules.document_analysis.consistency_checker import check_consistency


class TestDocumentConsistencyChecker:
    """Test suite for check_consistency function."""

    def test_empty_entities(self):
        """Empty entity dictionary should report no inconsistency."""
        res = check_consistency({})
        assert res["status"] == "No inconsistency detected"
        assert len(res["issues"]) == 0

    def test_genuine_date_difference(self):
        """Different dates with different roles (incident vs report) are legitimate."""
        entities = {
            "dates": [
                {"value": "12/08/2026", "source_text": "Incident Date: 12/08/2026"},
                {"value": "15/08/2026", "source_text": "Report Filed: 15/08/2026"},
            ]
        }
        res = check_consistency(entities)
        assert len(res["issues"]) == 0
        assert res["status"] == "No inconsistency detected"

    def test_actual_date_conflict(self):
        """Conflicting dates claiming the same role (incident date) should be flagged."""
        entities = {
            "dates": [
                {"value": "12/08/2026", "source_text": "Incident Date: 12/08/2026"},
                {"value": "15/08/2026", "source_text": "Incident occurred on 15/08/2026"},
            ]
        }
        res = check_consistency(entities)
        assert len(res["issues"]) == 1
        assert res["issues"][0]["type"] == "DATE_INCONSISTENCY"
        assert res["issues"][0]["field"] == "incident_date"
        assert res["status"] == "Potential inconsistency"

    def test_multiple_legitimate_locations(self):
        """Distinct locations under different semantic roles (crime scene vs residence)."""
        entities = {
            "locations": [
                {"value": "Moradabad", "source_text": "Incident Location: Moradabad"},
                {"value": "Bijnor", "source_text": "Police Station: Bijnor"},
                {"value": "Delhi", "source_text": "Residence: Delhi"},
            ]
        }
        res = check_consistency(entities)
        assert len(res["issues"]) == 0
        assert res["status"] == "No inconsistency detected"

    def test_actual_location_conflict(self):
        """Conflicting locations for the same role (incident location) should be flagged."""
        entities = {
            "locations": [
                {"value": "Moradabad", "source_text": "Incident Location: Moradabad"},
                {"value": "Bijnor", "source_text": "Place of Incident: Bijnor"},
            ]
        }
        res = check_consistency(entities)
        assert len(res["issues"]) == 1
        assert res["issues"][0]["type"] == "LOCATION_INCONSISTENCY"
        assert res["issues"][0]["field"] == "incident_location"

    def test_multiple_legitimate_amounts(self):
        """Different monetary amounts under distinct roles (loss vs fine vs compensation)."""
        entities = {
            "money": [
                {"value": "50,000", "source_text": "Total Loss: 50,000"},
                {"value": "75,000", "source_text": "Compensation: 75,000"},
                {"value": "10,000", "source_text": "Fine: 10,000"},
            ]
        }
        res = check_consistency(entities)
        assert len(res["issues"]) == 0
        assert res["status"] == "No inconsistency detected"

    def test_actual_amount_conflict(self):
        """Conflicting amounts under the same role (total loss) should trigger an issue."""
        entities = {
            "money": [
                {"value": "50,000", "source_text": "Total Loss: 50,000"},
                {"value": "75,000", "source_text": "total loss: 75,000"},
            ]
        }
        res = check_consistency(entities)
        assert len(res["issues"]) == 1
        assert res["issues"][0]["type"] == "AMOUNT_INCONSISTENCY"
        assert res["issues"][0]["field"] == "total_loss"

    def test_different_people_different_roles(self):
        """Different people with distinct roles (accused vs witness) are legitimate."""
        entities = {
            "persons": [
                {"value": "Rahul Sharma", "source_text": "Accused: Rahul Sharma"},
                {"value": "Rahul Verma", "source_text": "Witness: Rahul Verma"},
            ]
        }
        res = check_consistency(entities)
        assert len(res["issues"]) == 0
        assert res["status"] == "No inconsistency detected"

    def test_same_role_conflicting_person(self):
        """Multiple distinct people associated with the same role (accused vs defendant)."""
        entities = {
            "persons": [
                {"value": "Rahul Sharma", "source_text": "Accused: Rahul Sharma"},
                {"value": "Rahul Verma", "source_text": "Defendant: Rahul Verma"},
            ]
        }
        res = check_consistency(entities)
        assert len(res["issues"]) == 1
        assert res["issues"][0]["type"] == "NAME_INCONSISTENCY"
        assert res["issues"][0]["field"] == "accused"

    def test_conflicting_case_numbers(self):
        """Conflicting FIR identifiers should trigger case ID inconsistency."""
        case_info = {
            "case_numbers": [
                {"value": "FIR-101", "source_text": "FIR No: FIR-101"},
                {"value": "FIR-999", "source_text": "fir number: FIR-999"},
            ]
        }
        res = check_consistency({}, case_info)
        assert len(res["issues"]) == 1
        assert res["issues"][0]["type"] == "CASE_ID_INCONSISTENCY"
        assert res["issues"][0]["field"] == "fir_number"

    def test_multiple_inconsistencies_status(self):
        """Multiple issues should produce 'Multiple potential inconsistencies' status."""
        entities = {
            "dates": [
                {"value": "12/08/2026", "source_text": "Incident Date: 12/08/2026"},
                {"value": "15/08/2026", "source_text": "Incident occurred on 15/08/2026"},
            ],
            "money": [
                {"value": "50,000", "source_text": "Total Loss: 50,000"},
                {"value": "75,000", "source_text": "total loss: 75,000"},
            ],
        }
        res = check_consistency(entities)
        assert len(res["issues"]) == 2
        assert res["status"] == "Multiple potential inconsistencies"
