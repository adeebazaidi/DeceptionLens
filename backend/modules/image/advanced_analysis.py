"""
Advanced Analysis Module
========================
Provides additional forensic metrics beyond the core ELA/entropy pipeline:

  - Blur Detection        : Laplacian variance method
  - Copy-Move Detection   : ORB keypoint matching on image blocks
  - Noise Consistency     : Spatial uniformity of noise residuals
  - Forgery Probability   : Weighted heuristic score (0–100%)

All results are preliminary indicators for research / educational use.
"""

from typing import Dict
import cv2
import numpy as np


# ── Blur Detection ──────────────────────────────────────────────────────────

BLUR_THRESHOLD = 100.0  # Laplacian variance below this → blurry


def detect_blur(gray: np.ndarray) -> Dict:
    """
    Detect overall image blur using the Laplacian variance method.

    A low variance means most pixels have similar intensity to their
    neighbours (smooth), which is characteristic of blur.

    Returns:
        is_blurred : bool
        variance   : float (Laplacian variance)
    """
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return {
        "is_blurred": lap_var < BLUR_THRESHOLD,
        "variance": round(lap_var, 4),
    }


# ── Copy-Move Detection ──────────────────────────────────────────────────────

COPY_MOVE_MIN_MATCHES = 20   # minimum ORB matches to flag as copy-move
COPY_MOVE_LOWE_RATIO  = 0.75  # Lowe's ratio test threshold


def detect_copy_move(gray: np.ndarray) -> Dict:
    """
    Detect copy-move forgery using ORB feature matching with ratio test.

    The image is split into two half-overlapping regions. Keypoints from
    each half are matched against the other. A high count of good matches
    between spatially distinct regions is a copy-move indicator.

    This is a heuristic — false positives can occur on repetitive textures.

    Returns:
        detected      : bool
        match_count   : int  (good matches found)
        confidence    : str  ("None" | "Low" | "Moderate" | "High")
    """
    h, w = gray.shape

    # Use ORB — no patent restrictions, fast, decent accuracy
    orb = cv2.ORB_create(nfeatures=500)

    # Split image into two quadrants and cross-match
    half_w = w // 2
    left  = gray[:, :half_w]
    right = gray[:, half_w:]

    kp1, des1 = orb.detectAndCompute(left,  None)
    kp2, des2 = orb.detectAndCompute(right, None)

    if des1 is None or des2 is None or len(des1) < 2 or len(des2) < 2:
        return {"detected": False, "match_count": 0, "confidence": "None"}

    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    try:
        raw_matches = bf.knnMatch(des1, des2, k=2)
    except cv2.error:
        return {"detected": False, "match_count": 0, "confidence": "None"}

    # Lowe's ratio test to filter ambiguous matches
    good = [m for m, n in raw_matches if m.distance < COPY_MOVE_LOWE_RATIO * n.distance]
    count = len(good)

    if count >= 60:
        confidence = "High"
    elif count >= 30:
        confidence = "Moderate"
    elif count >= COPY_MOVE_MIN_MATCHES:
        confidence = "Low"
    else:
        confidence = "None"

    return {
        "detected": count >= COPY_MOVE_MIN_MATCHES,
        "match_count": count,
        "confidence": confidence,
    }


# ── Noise Consistency ────────────────────────────────────────────────────────

NOISE_CONSISTENCY_HIGH_THRESH   = 3.0   # std < this → High consistency
NOISE_CONSISTENCY_MEDIUM_THRESH = 6.0   # std < this → Medium consistency


def assess_noise_consistency(noise_std: float) -> str:
    """
    Convert noise standard deviation into a consistency label.

    High consistency → spatially uniform noise (expected for authentic images).
    Low consistency  → spatially uneven noise (possible splicing indicator).

    Returns: "High" | "Medium" | "Low"
    """
    if noise_std < NOISE_CONSISTENCY_HIGH_THRESH:
        return "High"
    if noise_std < NOISE_CONSISTENCY_MEDIUM_THRESH:
        return "Medium"
    return "Low"


# ── Forgery Probability ──────────────────────────────────────────────────────

def compute_forgery_probability(
    entropy_stats: Dict,
    ela_stats: Dict,
    noise_stats: Dict,
    texture_stats: Dict,
    copy_move: Dict,
    blur: Dict,
) -> float:
    """
    Compute a weighted forgery probability score (0.0 – 100.0).

    This is a transparent heuristic — not a calibrated classifier.
    It combines normalized indicators from each forensic module.

    Weight breakdown:
      ELA mean         25%
      ELA std          15%
      Entropy anomaly  20%
      Entropy std      10%
      Noise std        10%
      Copy-move         15%
      Blur (inverse)    5%

    Each indicator is clipped to [0, 1] before weighting.
    """

    def clip(val: float, lo: float, hi: float) -> float:
        return max(0.0, min(1.0, (val - lo) / (hi - lo))) if hi > lo else 0.0

    ela_mean_score    = clip(ela_stats.get("mean", 0),          0,  30)
    ela_std_score     = clip(ela_stats.get("std",  0),          0,  20)
    entropy_an_score  = clip(entropy_stats.get("anomaly_score", 0), 0, 0.5)
    entropy_std_score = clip(entropy_stats.get("std_local",  0),    0, 1.5)
    noise_std_score   = clip(noise_stats.get("std",  0),           0,  10)

    # Copy-move contributes a fixed weight based on confidence
    cm_conf_map = {"None": 0.0, "Low": 0.4, "Moderate": 0.75, "High": 1.0}
    cm_score = cm_conf_map.get(copy_move.get("confidence", "None"), 0.0)

    # Blur: blurry images are less likely to show ELA artifacts → slight downweight
    blur_penalty = 0.1 if blur.get("is_blurred", False) else 0.0

    weighted = (
        ela_mean_score    * 0.25 +
        ela_std_score     * 0.15 +
        entropy_an_score  * 0.20 +
        entropy_std_score * 0.10 +
        noise_std_score   * 0.10 +
        cm_score          * 0.15 +
        (1 - blur_penalty) * 0.05
    )

    probability = round(float(weighted * 100), 1)
    return min(probability, 99.9)   # never claim 100% certainty


# ── ELA verdict ──────────────────────────────────────────────────────────────

def ela_verdict(ela_stats: Dict) -> str:
    """Return a human-readable ELA verdict based on mean error level."""
    mean = ela_stats.get("mean", 0)
    if mean >= 20:
        return "Suspicious"
    if mean >= 8:
        return "Elevated"
    return "Normal"
