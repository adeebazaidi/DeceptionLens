"""
Texture Analysis Module
=======================
Extracts GLCM (Gray-Level Co-occurrence Matrix) features using scikit-image.

Features extracted:
  - contrast      : Measures local intensity variation.
  - dissimilarity : Similar to contrast but grows linearly.
  - homogeneity   : Closeness of element distribution to diagonal.
  - energy        : Uniformity of the texture (sum of squared elements).
  - correlation   : Linear dependency of grey levels on those of neighbours.
"""

from typing import Dict

import numpy as np
from skimage.feature import graycomatrix, graycoprops


def compute_glcm_features(gray: np.ndarray) -> Dict[str, float]:
    """
    Compute GLCM texture features from a grayscale image.

    Uses distances=[1], angles=[0°, 45°, 90°, 135°] and averages
    across all angles for a rotation-invariant result.

    Args:
        gray: Grayscale image as uint8 ndarray.

    Returns:
        Dictionary of five texture features.
    """
    # Quantize to 64 levels for efficiency (common in forensics)
    gray_q = (gray // 4).astype(np.uint8)

    glcm = graycomatrix(
        gray_q,
        distances=[1],
        angles=[0, np.pi / 4, np.pi / 2, 3 * np.pi / 4],
        levels=64,
        symmetric=True,
        normed=True,
    )

    def _mean_prop(prop: str) -> float:
        return float(np.mean(graycoprops(glcm, prop)))

    return {
        "contrast": round(_mean_prop("contrast"), 6),
        "dissimilarity": round(_mean_prop("dissimilarity"), 6),
        "homogeneity": round(_mean_prop("homogeneity"), 6),
        "energy": round(_mean_prop("energy"), 6),
        "correlation": round(_mean_prop("correlation"), 6),
    }
