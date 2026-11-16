"""
Unit tests for Document Analysis Consistency Checker.
======================================================
Tests rule-based cross-field inconsistency detection across
dates, locations, monetary amounts, person names, and case numbers.
"""

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


class TestIdentifierPatterns:
    """Regex patterns used to extract case / FIR numbers from document text."""

    @staticmethod
    def _ids(pattern, text):
        import re
        return [m.group(1) for m in re.finditer(pattern, text)]

    def test_fir_number_extracted(self):
        from modules.document_analysis.nlp_service import FIR_NUMBER_PATTERN
        assert self._ids(FIR_NUMBER_PATTERN, "FIR No. 221/2024 registered") == ["221/2024"]

    def test_fir_not_matched_inside_words(self):
        """'fir' inside 'confirmed' must not yield a bogus FIR number."""
        from modules.document_analysis.nlp_service import FIR_NUMBER_PATTERN
        assert self._ids(FIR_NUMBER_PATTERN, "The witness confirmed the statement.") == []

    def test_case_number_extracted(self):
        from modules.document_analysis.nlp_service import CASE_NUMBER_PATTERN
        assert self._ids(CASE_NUMBER_PATTERN, "Case No. CR-42/2023 and case number: 77") == ["CR-42/2023", "77"]

    def test_plain_words_after_case_not_ids(self):
        """'the case was closed' must not produce case number 'was'."""
        from modules.document_analysis.nlp_service import CASE_NUMBER_PATTERN
        assert self._ids(CASE_NUMBER_PATTERN, "In this case the matter was closed. Showcase 5 items.") == []


class TestMoneyHandling:
    """Rupee amounts: extraction pattern, normalization, and inconsistency detection."""

    def test_normalize_money_values(self):
        from modules.document_analysis.normalization import normalize_money
        assert normalize_money("Rs. 5,000") == 5000.0  # previously 0.5 ("." from "Rs.")
        assert normalize_money("Rs.7,500") == 7500.0
        assert normalize_money("₹1,20,000.50") == 120000.5
        assert normalize_money("$5,000") == 5000.0
        assert normalize_money("3 lakh") == 300000.0
        assert normalize_money("2.5 crore") == 25000000.0
        assert normalize_money("no amount") is None

    def test_money_pattern_finds_rupee_amounts(self):
        import re
        from modules.document_analysis.nlp_service import MONEY_PATTERN
        text = "Paid Rs. 5,000 and ₹7,500, INR 200, then 3 lakh and 900 rupees. Room 42 is not money."
        found = [m.group(0) for m in re.finditer(MONEY_PATTERN, text)]
        assert found == ["Rs. 5,000", "₹7,500", "INR 200", "3 lakh", "900 rupees"]

    def test_money_pattern_ignores_words_containing_rs(self):
        import re
        from modules.document_analysis.nlp_service import MONEY_PATTERN
        assert [m.group(0) for m in re.finditer(MONEY_PATTERN, "Officers 12 and users 30")] == []

    def test_money_pattern_tolerates_ocr_colon(self):
        """OCR frequently reads 'Rs. 5,000' as 'Rs: 5,000'."""
        import re
        from modules.document_analysis.nlp_service import MONEY_PATTERN
        from modules.document_analysis.normalization import normalize_money
        found = [m.group(0) for m in re.finditer(MONEY_PATTERN, "the total amount Rs: 5,000 from")]
        assert found == ["Rs: 5,000"]
        assert normalize_money(found[0]) == 5000.0

    def test_conflicting_rupee_totals_flagged(self):
        entities = {"money": [
            {"value": "Rs. 5,000", "source_text": "transferred the total amount Rs. 5,000 from"},
            {"value": "Rs. 7,500", "source_text": "the total amount Rs. 7,500 is recorded"},
        ]}
        res = check_consistency(entities)
        assert [i["type"] for i in res["issues"]] == ["AMOUNT_INCONSISTENCY"]

    def test_same_amount_different_format_not_flagged(self):
        entities = {"money": [
            {"value": "Rs. 5,000", "source_text": "the total amount Rs. 5,000 was"},
            {"value": "5,000 rupees", "source_text": "total amount of 5,000 rupees"},
        ]}
        assert check_consistency(entities)["issues"] == []
