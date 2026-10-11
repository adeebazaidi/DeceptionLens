"""
Tests — ELA Analysis
"""

import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.image.ela_analysis import compute_ela_stats, perform_ela, save_ela_image


def _make_temp_jpeg(size=(64, 64)) -> str:
    """Create a temporary JPEG file and return its path."""
    rng = np.random.default_rng(1)
    arr = rng.integers(0, 256, (*size, 3), dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    img.save(tmp.name, format="JPEG", quality=95)
    tmp.close()
    return tmp.name


class TestPerformELA:
    def test_returns_pil_image(self):
        """perform_ela should return a PIL Image."""
        tmp = _make_temp_jpeg()
        try:
            result = perform_ela(tmp)
            assert isinstance(result, Image.Image)
        finally:
            os.unlink(tmp)

    def test_output_size_matches_input(self):
        """ELA image should be the same size as the original.
        PIL Image.size returns (width, height).
        numpy array shape (80, 60, 3) → height=80, width=60 → PIL size=(60, 80).
        """
        tmp = _make_temp_jpeg((80, 60))  # numpy shape: (height=80, width=60, 3)
        try:
            result = perform_ela(tmp)
            # PIL size is (width, height) = (60, 80)
            assert result.size == (60, 80)
        finally:
            os.unlink(tmp)

    def test_invalid_path_raises(self):
        """perform_ela should raise an exception for a non-existent file."""
        with pytest.raises(Exception):
            perform_ela("/nonexistent/path/fake.jpg")

    def test_ela_values_in_range(self):
        """ELA pixel values should be in [0, 255]."""
        tmp = _make_temp_jpeg()
        try:
            ela = perform_ela(tmp)
            arr = np.array(ela)
            assert arr.min() >= 0
            assert arr.max() <= 255
        finally:
            os.unlink(tmp)


class TestELAStats:
    def test_stats_keys_present(self):
        """All expected keys must be present."""
        tmp = _make_temp_jpeg()
        try:
            ela = perform_ela(tmp)
            stats = compute_ela_stats(ela)
            for key in ("mean", "std", "max"):
                assert key in stats
        finally:
            os.unlink(tmp)

    def test_no_nan_or_inf(self):
        """Stats must be finite."""
        tmp = _make_temp_jpeg()
        try:
            ela = perform_ela(tmp)
            stats = compute_ela_stats(ela)
            for key, val in stats.items():
                assert np.isfinite(val), f"'{key}' is not finite: {val}"
        finally:
            os.unlink(tmp)


class TestSaveELAImage:
    def test_saves_png(self):
        """save_ela_image should write a PNG file."""
        tmp_in = _make_temp_jpeg()
        tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp_out.close()
        try:
            ela = perform_ela(tmp_in)
            save_ela_image(ela, tmp_out.name)
            assert os.path.exists(tmp_out.name)
            assert os.path.getsize(tmp_out.name) > 0
        finally:
            os.unlink(tmp_in)
            if os.path.exists(tmp_out.name):
                os.unlink(tmp_out.name)
