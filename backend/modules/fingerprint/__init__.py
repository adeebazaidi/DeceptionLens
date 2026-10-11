"""
DeceptionLens — Fingerprint Forensic Comparison Package
"""

from modules.fingerprint.preprocessing import preprocess_fingerprint
from modules.fingerprint.enhancement import enhance_ridges
from modules.fingerprint.minutiae import extract_fingerprint_minutiae
from modules.fingerprint.matching import match_minutiae_sets, DEFAULT_MATCH_THRESHOLD
from modules.fingerprint.service import compare_fingerprints

__all__ = [
    "preprocess_fingerprint",
    "enhance_ridges",
    "extract_fingerprint_minutiae",
    "match_minutiae_sets",
    "DEFAULT_MATCH_THRESHOLD",
    "compare_fingerprints",
]
