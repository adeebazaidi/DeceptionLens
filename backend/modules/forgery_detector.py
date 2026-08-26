"""
Forgery Risk Detector
=====================
A transparent, multi-indicator heuristic system for preliminary risk assessment.

Risk levels: LOW | MEDIUM | HIGH

This is NOT a definitive forgery detector. It combines multiple
analytical indicators to produce a preliminary screening result.

All thresholds are configurable via environment variables.
Language uses "potentially suspicious" — never "forged" or "manipulated".
"""

import os
from typing import Dict, List, Tuple

# ── Configurable thresholds ───────────────────────────────────────────────────
# These can be overridden via environment variables.

def _thresh(env_key: str, default: float) -> float:
    return float(os.getenv(env_key, str(default)))


# Entropy thresholds
ENTROPY_ANOMALY_MEDIUM = _thresh("THRESH_ENTROPY_ANOMALY_MEDIUM", 0.12)
ENTROPY_ANOMALY_HIGH   = _thresh("THRESH_ENTROPY_ANOMALY_HIGH",   0.25)
ENTROPY_STD_MEDIUM     = _thresh("THRESH_ENTROPY_STD_MEDIUM",     0.5)
ENTROPY_STD_HIGH       = _thresh("THRESH_ENTROPY_STD_HIGH",       1.0)

# ELA thresholds
ELA_MEAN_MEDIUM = _thresh("THRESH_ELA_MEAN_MEDIUM", 8.0)
ELA_MEAN_HIGH   = _thresh("THRESH_ELA_MEAN_HIGH",   20.0)
ELA_STD_MEDIUM  = _thresh("THRESH_ELA_STD_MEDIUM",  6.0)
ELA_STD_HIGH    = _thresh("THRESH_ELA_STD_HIGH",    15.0)

# Noise thresholds
NOISE_STD_MEDIUM = _thresh("THRESH_NOISE_STD_MEDIUM", 3.0)
NOISE_STD_HIGH   = _thresh("THRESH_NOISE_STD_HIGH",   8.0)

# Texture thresholds (high contrast may indicate inconsistency)
TEXTURE_CONTRAST_MEDIUM = _thresh("THRESH_TEXTURE_CONTRAST_MEDIUM", 2.0)
TEXTURE_CONTRAST_HIGH   = _thresh("THRESH_TEXTURE_CONTRAST_HIGH",   5.0)


def _score_indicator(value: float, medium_thresh: float, high_thresh: float) -> int:
    """
    Map a single metric to a score:  0 = low, 1 = medium, 2 = high.
    """
    if value >= high_thresh:
        return 2
    if value >= medium_thresh:
        return 1
    return 0


def assess_risk(
    entropy_stats: Dict,
    ela_stats: Dict,
    noise_stats: Dict,
    texture_stats: Dict,
) -> Dict:
    """
    Combine multiple forensic indicators into a preliminary risk assessment.

    Returns:
        risk_level: "LOW", "MEDIUM", or "HIGH"
        reason:     List of human-readable indicator descriptions.

    This is a heuristic screening tool — results are preliminary and
    should not be interpreted as definitive evidence of manipulation.
    """
    reasons: List[str] = []
    scores: List[int] = []

    # ── Entropy indicators ────────────────────────────────────────────────────
    anomaly = entropy_stats.get("anomaly_score", 0.0)
    std_local = entropy_stats.get("std_local", 0.0)

    s = max(
        _score_indicator(anomaly, ENTROPY_ANOMALY_MEDIUM, ENTROPY_ANOMALY_HIGH),
        _score_indicator(std_local, ENTROPY_STD_MEDIUM, ENTROPY_STD_HIGH),
    )
    scores.append(s)
    if s == 2:
        reasons.append("High local entropy variation detected across image blocks")
    elif s == 1:
        reasons.append("Moderate local entropy variation detected")

    # ── ELA indicators ────────────────────────────────────────────────────────
    ela_mean = ela_stats.get("mean", 0.0)
    ela_std  = ela_stats.get("std",  0.0)

    s = max(
        _score_indicator(ela_mean, ELA_MEAN_MEDIUM, ELA_MEAN_HIGH),
        _score_indicator(ela_std,  ELA_STD_MEDIUM,  ELA_STD_HIGH),
    )
    scores.append(s)
    if s == 2:
        reasons.append("High ELA anomaly indicator — elevated error level response")
    elif s == 1:
        reasons.append("Moderate ELA response noted")

    # ── Noise indicators ──────────────────────────────────────────────────────
    noise_std = noise_stats.get("std", 0.0)

    s = _score_indicator(noise_std, NOISE_STD_MEDIUM, NOISE_STD_HIGH)
    scores.append(s)
    if s == 2:
        reasons.append("High spatial noise variation detected")
    elif s == 1:
        reasons.append("Moderate noise variation detected")

    # ── Texture indicators ────────────────────────────────────────────────────
    contrast = texture_stats.get("contrast", 0.0)

    s = _score_indicator(contrast, TEXTURE_CONTRAST_MEDIUM, TEXTURE_CONTRAST_HIGH)
    scores.append(s)
    if s == 2:
        reasons.append("High texture contrast — possible inconsistency in texture regions")
    elif s == 1:
        reasons.append("Elevated texture contrast noted")

    # ── Aggregate risk ────────────────────────────────────────────────────────
    max_score = max(scores) if scores else 0
    high_count = scores.count(2)
    medium_count = scores.count(1)

    if max_score == 2 and high_count >= 2:
        risk_level = "HIGH"
    elif max_score == 2 or medium_count >= 2:
        risk_level = "MEDIUM"
    elif medium_count == 1:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    if not reasons:
        reasons.append("No significant anomalies detected in forensic indicators")

    return {
        "risk_level": risk_level,
        "reason": reasons,
    }
