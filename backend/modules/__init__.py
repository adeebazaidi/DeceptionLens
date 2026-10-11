"""
DeceptionLens — Forensic Analysis Modules
==========================================
The core forensic inspection suite powering DeceptionLens.
Contains 4 dedicated forensic domain packages:

  - `modules.image`:
      Image forgery detection algorithms (ELA, Shannon entropy,
      noise residuals, GLCM texture, metadata, ML feature extraction).
  - `modules.signature`:
      Handwritten signature forgery evaluation (stroke tremor,
      hesitation analysis, skeletonization, 1-vs-1 comparison).
  - `modules.fingerprint`:
      Biometric fingerprint verification pipeline (ridge enhancement,
      minutiae crossing number extraction, bipartite rigid matching).
  - `modules.document_analysis`:
      Forensic document analysis (PyMuPDF rendering, EasyOCR text
      extraction, spaCy NER, normalization, cross-field contradiction detection).
"""

import sys

# Subpackages
from modules import image
from modules import signature
from modules import fingerprint
from modules import document_analysis

# Image Forensics Exports
from modules.image import (
    load_image,
    validate_image,
    get_image_info,
    calculate_global_entropy,
    calculate_local_entropy,
    compute_entropy_stats,
    generate_entropy_heatmap,
    perform_ela,
    compute_ela_stats,
    save_ela_image,
    estimate_noise_map,
    compute_noise_stats,
    save_noise_map,
    compute_glcm_features,
    extract_metadata,
    FEATURE_NAMES,
    extract_all_features,
    features_to_vector,
    stats_to_features,
    assess_risk,
    detect_blur,
    detect_copy_move,
    assess_noise_consistency,
    compute_forgery_probability,
    ela_verdict,
)

# Signature Forensics Exports
from modules.signature import (
    analyze_signature_pipeline,
    binarize_and_crop_signature,
    compute_skeleton,
    detect_stroke_tremor,
    compute_signature_features,
    compare_signatures,
)

# Fingerprint Verification Exports
from modules.fingerprint import (
    compare_fingerprints,
    preprocess_fingerprint,
    enhance_ridges,
    extract_fingerprint_minutiae,
    match_minutiae_sets,
    DEFAULT_MATCH_THRESHOLD,
)

# Document Analysis Exports
from modules.document_analysis import (
    analyze_document,
    load_document,
    perform_ocr,
    clean_text,
    extract_entities_and_info,
    check_consistency,
)

# ── Backward Compatibility Module Aliases ─────────────────────────────────────
# Allows legacy flat imports (e.g. `from modules.entropy_analysis import ...`
# or `from fingerprint.service import ...`) to continue resolving seamlessly.
_aliases = {
    "modules.preprocessing": "modules.image.preprocessing",
    "modules.entropy_analysis": "modules.image.entropy_analysis",
    "modules.ela_analysis": "modules.image.ela_analysis",
    "modules.noise_analysis": "modules.image.noise_analysis",
    "modules.texture_analysis": "modules.image.texture_analysis",
    "modules.metadata_analysis": "modules.image.metadata_analysis",
    "modules.feature_extraction": "modules.image.feature_extraction",
    "modules.forgery_detector": "modules.image.forgery_detector",
    "modules.advanced_analysis": "modules.image.advanced_analysis",
    "modules.signature_analysis": "modules.signature.signature_analysis",
    "fingerprint": "modules.fingerprint",
    "fingerprint.preprocessing": "modules.fingerprint.preprocessing",
    "fingerprint.enhancement": "modules.fingerprint.enhancement",
    "fingerprint.minutiae": "modules.fingerprint.minutiae",
    "fingerprint.matching": "modules.fingerprint.matching",
    "fingerprint.visualization": "modules.fingerprint.visualization",
    "fingerprint.service": "modules.fingerprint.service",
}

for _alias, _target in _aliases.items():
    if _alias not in sys.modules:
        __import__(_target)
        sys.modules[_alias] = sys.modules[_target]

__all__ = [
    # Subpackages
    "image",
    "signature",
    "fingerprint",
    "document_analysis",
    # Image Forensics
    "load_image",
    "validate_image",
    "get_image_info",
    "calculate_global_entropy",
    "calculate_local_entropy",
    "compute_entropy_stats",
    "generate_entropy_heatmap",
    "perform_ela",
    "compute_ela_stats",
    "save_ela_image",
    "estimate_noise_map",
    "compute_noise_stats",
    "save_noise_map",
    "compute_glcm_features",
    "extract_metadata",
    "FEATURE_NAMES",
    "extract_all_features",
    "features_to_vector",
    "stats_to_features",
    "assess_risk",
    "detect_blur",
    "detect_copy_move",
    "assess_noise_consistency",
    "compute_forgery_probability",
    "ela_verdict",
    # Signature Forensics
    "analyze_signature_pipeline",
    "binarize_and_crop_signature",
    "compute_skeleton",
    "detect_stroke_tremor",
    "compute_signature_features",
    "compare_signatures",
    # Fingerprint Verification
    "compare_fingerprints",
    "preprocess_fingerprint",
    "enhance_ridges",
    "extract_fingerprint_minutiae",
    "match_minutiae_sets",
    "DEFAULT_MATCH_THRESHOLD",
    # Document Forensics
    "analyze_document",
    "load_document",
    "perform_ocr",
    "clean_text",
    "extract_entities_and_info",
    "check_consistency",
]
