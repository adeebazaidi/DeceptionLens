"""
DeceptionLens — Forensic Document Analysis Subpackage
=====================================================
Provides an end-to-end NLP and OCR analysis pipeline for forensic documents
(PDF reports, incident statements, legal filings, and scanned evidence):

Pipeline stages:
  1. Document Loading: PyMuPDF (fitz) rendering & Pillow image decoding
  2. Optical Character Recognition: EasyOCR high-confidence text and bounding-box extraction
  3. Text Preprocessing: Normalization and whitespace cleaning
  4. Entity & Context Extraction: spaCy NER (PERSON, DATE, LOC, GPE, ORG, MONEY) & regex identifiers
  5. Semantic Normalization: Unified date (YYYY-MM-DD), name, location, and monetary parsing
  6. Consistency Verification: Rule-based cross-field conflict and contradiction detection
  7. Forensic Reporting: Structured JSON report for courtroom/investigative review
"""

from modules.document_analysis.analyzer import analyze_document
from modules.document_analysis.ocr_service import (
    load_document,
    perform_ocr,
    clean_text,
)
from modules.document_analysis.nlp_service import (
    extract_entities_and_info,
    find_source_context,
    FORENSIC_KEYWORDS,
)
from modules.document_analysis.normalization import (
    normalize_date,
    normalize_name,
    normalize_location,
    normalize_money,
)
from modules.document_analysis.consistency_checker import (
    check_consistency,
    extract_role,
)

__all__ = [
    # Main Pipeline Orchestrator
    "analyze_document",
    # OCR & Document Loading
    "load_document",
    "perform_ocr",
    "clean_text",
    # NLP & Entity Extraction
    "extract_entities_and_info",
    "find_source_context",
    "FORENSIC_KEYWORDS",
    # Normalization Utilities
    "normalize_date",
    "normalize_name",
    "normalize_location",
    "normalize_money",
    # Consistency Verification
    "check_consistency",
    "extract_role",
]
