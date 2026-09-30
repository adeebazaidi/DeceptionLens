"""
DeceptionLens — Fingerprint Forensic Comparison Package
"""

from fingerprint.preprocessing import preprocess_fingerprint
from fingerprint.enhancement import enhance_ridges
from fingerprint.minutiae import extract_fingerprint_minutiae
from fingerprint.matching import match_minutiae_sets
from fingerprint.service import compare_fingerprints

__all__ = [
    "preprocess_fingerprint",
    "enhance_ridges",
    "extract_fingerprint_minutiae",
    "match_minutiae_sets",
    "compare_fingerprints",
]
