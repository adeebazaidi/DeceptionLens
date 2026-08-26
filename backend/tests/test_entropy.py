"""
Tests — Entropy Analysis
"""

import sys
from pathlib import Path
import numpy as np
import pytest

# Allow imports from backend root
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.entropy_analysis import (
    calculate_global_entropy,
    calculate_local_entropy,
    compute_entropy_stats,
)


class TestGlobalEntropy:
    def test_constant_image_has_zero_entropy(self):
        """A constant (uniform) image has entropy = 0."""
        gray = np.full((64, 64), 128, dtype=np.uint8)
        result = calculate_global_entropy(gray)
        assert result == pytest.approx(0.0, abs=1e-6)

    def test_normal_image_has_positive_entropy(self):
        """A natural-looking random image should have entropy > 0."""
        rng = np.random.default_rng(42)
        gray = rng.integers(0, 256, size=(128, 128), dtype=np.uint8)
        result = calculate_global_entropy(gray)
        assert result > 5.0, f"Expected high entropy, got {result}"

    def test_entropy_bounded(self):
        """Entropy of a uint8 image must be in [0, 8]."""
        rng = np.random.default_rng(0)
        gray = rng.integers(0, 256, size=(256, 256), dtype=np.uint8)
        result = calculate_global_entropy(gray)
        assert 0.0 <= result <= 8.0

    def test_tiny_2x2_image(self):
        """Entropy should not crash on a tiny image."""
        gray = np.array([[0, 255], [128, 64]], dtype=np.uint8)
        result = calculate_global_entropy(gray)
        assert result >= 0.0


class TestLocalEntropy:
    def test_returns_correct_shape(self):
        """Local entropy map should have shape (rows, cols) matching grid."""
        gray = np.random.randint(0, 256, (64, 64), dtype=np.uint8)
        result = calculate_local_entropy(gray, grid_size=8)
        assert result.shape == (8, 8)

    def test_constant_image_local_zero(self):
        """All local blocks of a constant image should have ~0 entropy."""
        gray = np.full((64, 64), 200, dtype=np.uint8)
        result = calculate_local_entropy(gray, grid_size=4)
        assert np.allclose(result, 0.0, atol=1e-6)


class TestEntropyStats:
    def test_stats_keys_present(self):
        """All expected keys must be in the output dict."""
        gray = np.random.randint(0, 256, (64, 64), dtype=np.uint8)
        stats = compute_entropy_stats(gray, grid_size=8)
        for key in ("global", "mean_local", "std_local", "min_local", "max_local", "anomaly_score"):
            assert key in stats

    def test_no_nan_or_inf(self):
        """Stats must not contain NaN or Inf."""
        gray = np.random.randint(0, 256, (128, 128), dtype=np.uint8)
        stats = compute_entropy_stats(gray)
        for key, val in stats.items():
            assert np.isfinite(val), f"Key '{key}' is not finite: {val}"

    def test_anomaly_score_in_range(self):
        """Anomaly score must be in [0, 1]."""
        gray = np.random.randint(0, 256, (128, 128), dtype=np.uint8)
        stats = compute_entropy_stats(gray)
        assert 0.0 <= stats["anomaly_score"] <= 1.0
