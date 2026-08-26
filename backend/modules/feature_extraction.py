"""
Feature Extraction Module
=========================
Combines all forensic features into a flat, consistently-ordered dictionary
suitable for ML training and inference.

The feature order is fixed and must match between training and prediction.
Feature names are saved alongside the model to guarantee consistency.
"""

from typing import Dict, List

import numpy as np

from modules.entropy_analysis import compute_entropy_stats
from modules.ela_analysis import perform_ela, compute_ela_stats
from modules.noise_analysis import estimate_noise_map, compute_noise_stats
from modules.texture_analysis import compute_glcm_features
from modules.preprocessing import load_image

# Canonical feature order — must not change after model training
FEATURE_NAMES: List[str] = [
    # Entropy features
    "entropy_global",
    "entropy_mean_local",
    "entropy_std_local",
    "entropy_min_local",
    "entropy_max_local",
    "entropy_anomaly_score",
    # ELA features
    "ela_mean",
    "ela_std",
    "ela_max",
    # Noise features
    "noise_mean",
    "noise_std",
    "noise_max",
    # Texture features
    "texture_contrast",
    "texture_dissimilarity",
    "texture_homogeneity",
    "texture_energy",
    "texture_correlation",
]


def extract_all_features(image_path: str) -> Dict[str, float]:
    """
    Extract all forensic features from an image file.

    Returns a flat dict with keys matching FEATURE_NAMES.
    Values are Python floats. No NaN or Inf values are returned —
    they are replaced with 0.0 to ensure safe ML consumption.
    """
    pil_img, cv_img, gray = load_image(image_path)

    entropy = compute_entropy_stats(gray)
    ela_image = perform_ela(image_path)
    ela = compute_ela_stats(ela_image)
    noise_map = estimate_noise_map(gray)
    noise = compute_noise_stats(noise_map)
    texture = compute_glcm_features(gray)

    raw = {
        "entropy_global": entropy["global"],
        "entropy_mean_local": entropy["mean_local"],
        "entropy_std_local": entropy["std_local"],
        "entropy_min_local": entropy["min_local"],
        "entropy_max_local": entropy["max_local"],
        "entropy_anomaly_score": entropy["anomaly_score"],
        "ela_mean": ela["mean"],
        "ela_std": ela["std"],
        "ela_max": ela["max"],
        "noise_mean": noise["mean"],
        "noise_std": noise["std"],
        "noise_max": noise["max"],
        "texture_contrast": texture["contrast"],
        "texture_dissimilarity": texture["dissimilarity"],
        "texture_homogeneity": texture["homogeneity"],
        "texture_energy": texture["energy"],
        "texture_correlation": texture["correlation"],
    }

    # Sanitize: replace any NaN / Inf with 0.0
    return {
        k: float(v) if np.isfinite(v) else 0.0
        for k, v in raw.items()
    }


def features_to_vector(features: Dict[str, float]) -> List[float]:
    """
    Convert a feature dict to an ordered list matching FEATURE_NAMES.
    This ensures the prediction vector aligns with the trained model.
    """
    return [features.get(name, 0.0) for name in FEATURE_NAMES]


def stats_to_features(
    entropy_stats: dict,
    ela_stats: dict,
    noise_stats: dict,
    texture_stats: dict,
) -> Dict[str, float]:
    """
    Build the feature dict directly from already-computed stat dicts.
    Used during inference to avoid re-computing features.
    """
    raw = {
        "entropy_global": entropy_stats.get("global", 0.0),
        "entropy_mean_local": entropy_stats.get("mean_local", 0.0),
        "entropy_std_local": entropy_stats.get("std_local", 0.0),
        "entropy_min_local": entropy_stats.get("min_local", 0.0),
        "entropy_max_local": entropy_stats.get("max_local", 0.0),
        "entropy_anomaly_score": entropy_stats.get("anomaly_score", 0.0),
        "ela_mean": ela_stats.get("mean", 0.0),
        "ela_std": ela_stats.get("std", 0.0),
        "ela_max": ela_stats.get("max", 0.0),
        "noise_mean": noise_stats.get("mean", 0.0),
        "noise_std": noise_stats.get("std", 0.0),
        "noise_max": noise_stats.get("max", 0.0),
        "texture_contrast": texture_stats.get("contrast", 0.0),
        "texture_dissimilarity": texture_stats.get("dissimilarity", 0.0),
        "texture_homogeneity": texture_stats.get("homogeneity", 0.0),
        "texture_energy": texture_stats.get("energy", 0.0),
        "texture_correlation": texture_stats.get("correlation", 0.0),
    }
    return {k: float(v) if np.isfinite(v) else 0.0 for k, v in raw.items()}
