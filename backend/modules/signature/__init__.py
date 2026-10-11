"""
DeceptionLens — Handwritten Signature Analysis Module
=====================================================
Provides forensic evaluation of handwritten signatures:
  - Standalone Signature Screening (Otsu binarization, skeletonization, tremor heatmaps)
  - Reference Signature Comparison (SSIM, projection profile cosine similarity,
    centroid alignment, and difference overlay map)
"""

from modules.signature.signature_analysis import (
    load_grayscale_image,
    binarize_and_crop_signature,
    normalize_signature_size,
    compute_skeleton,
    detect_stroke_tremor,
    compute_signature_features,
    compare_signatures,
    analyze_signature_pipeline,
)

__all__ = [
    "load_grayscale_image",
    "binarize_and_crop_signature",
    "normalize_signature_size",
    "compute_skeleton",
    "detect_stroke_tremor",
    "compute_signature_features",
    "compare_signatures",
    "analyze_signature_pipeline",
]
