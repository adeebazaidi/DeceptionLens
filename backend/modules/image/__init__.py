"""
DeceptionLens — Image Forgery Detection Module
==============================================
Provides forensic algorithms for detecting image manipulation:
  - Error Level Analysis (ELA)
  - Shannon Entropy & Local Block Variation Heatmaps
  - High-Frequency Sensor Noise Residuals
  - GLCM Texture Feature Descriptors
  - EXIF / TIFF Metadata Extraction
  - 17-Dimensional Canonical Forensic Feature Vector for ML
  - Rule-Based Multi-Factor Forgery Risk Assessment
  - Laplacian Blur Detection & Copy-Move Heuristics
"""

from modules.image.preprocessing import (
    load_image,
    validate_image,
    get_image_info,
)
from modules.image.entropy_analysis import (
    calculate_global_entropy,
    calculate_local_entropy,
    compute_entropy_stats,
    generate_entropy_heatmap,
)
from modules.image.ela_analysis import (
    perform_ela,
    compute_ela_stats,
    save_ela_image,
)
from modules.image.noise_analysis import (
    estimate_noise_map,
    compute_noise_stats,
    save_noise_map,
)
from modules.image.texture_analysis import compute_glcm_features
from modules.image.metadata_analysis import extract_metadata
from modules.image.feature_extraction import (
    FEATURE_NAMES,
    extract_all_features,
    features_to_vector,
    stats_to_features,
)
from modules.image.forgery_detector import assess_risk
from modules.image.advanced_analysis import (
    detect_blur,
    detect_copy_move,
    assess_noise_consistency,
    compute_forgery_probability,
    ela_verdict,
)

__all__ = [
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
]
