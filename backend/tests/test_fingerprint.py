"""
DeceptionLens — Fingerprint Verification Unit & Integration Tests
=================================================================
Tests preprocessing, enhancement, minutiae extraction, matching,
and the FastAPI /api/fingerprint/compare endpoint.
"""

import io
from pathlib import Path
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from main import app
from fingerprint.preprocessing import (
    decode_image_bytes,
    to_grayscale,
    resize_preserve_aspect,
    preprocess_fingerprint,
)
from fingerprint.enhancement import compute_foreground_mask, enhance_ridges
from fingerprint.minutiae import (
    binarize_fingerprint,
    skeletonize_fingerprint,
    compute_crossing_number,
    extract_fingerprint_minutiae,
    TYPE_ENDING,
    TYPE_BIFURCATION,
)
from fingerprint.matching import match_minutiae_sets
from fingerprint.service import compare_fingerprints

client = TestClient(app)

SAMPLE_DIR = Path(__file__).parent.parent / "datasets" / "fingerprints" / "fvc2002" / "sample_pairs"
SAMPLE_101_1 = str(SAMPLE_DIR / "101_1.png")
SAMPLE_101_2 = str(SAMPLE_DIR / "101_2.png")
SAMPLE_102_1 = str(SAMPLE_DIR / "102_1.png")


def _encode_png(img: np.ndarray) -> bytes:
    _, buf = cv2.imencode(".png", img)
    return buf.tobytes()


class TestFingerprintPreprocessing:
    def test_decode_image_bytes(self):
        sample = np.full((120, 120, 3), 128, dtype=np.uint8)
        raw_bytes = _encode_png(sample)
        decoded = decode_image_bytes(raw_bytes)
        assert decoded is not None
        assert decoded.shape[0] == 120 and decoded.shape[1] == 120

    def test_decode_empty_bytes_raises(self):
        with pytest.raises(ValueError, match="empty"):
            decode_image_bytes(b"")

    def test_decode_corrupt_bytes_raises(self):
        with pytest.raises(ValueError, match="corrupted or unsupported"):
            decode_image_bytes(b"not_an_image_at_all_junk_bytes")

    def test_to_grayscale(self):
        rgb = np.zeros((100, 100, 3), dtype=np.uint8)
        gray = to_grayscale(rgb)
        assert len(gray.shape) == 2
        # Idempotent for already gray
        assert len(to_grayscale(gray).shape) == 2

    def test_resize_preserve_aspect(self):
        large = np.zeros((1000, 500), dtype=np.uint8)
        resized, scale = resize_preserve_aspect(large, max_dim=640)
        assert resized.shape[0] == 640
        assert resized.shape[1] == 320
        assert scale == 0.64

    def test_resize_too_small_raises(self):
        tiny = np.zeros((40, 40), dtype=np.uint8)
        with pytest.raises(ValueError, match="too small"):
            resize_preserve_aspect(tiny)


class TestFingerprintMinutiae:
    def test_crossing_number_ending(self):
        # A single neighbor in 8-neighborhood -> ending
        neighbors = [1, 0, 0, 0, 0, 0, 0, 0]
        cn = compute_crossing_number(neighbors)
        assert cn == 1

    def test_crossing_number_continuous(self):
        # Two opposite neighbors -> continuous line
        neighbors = [0, 1, 0, 0, 0, 1, 0, 0]
        cn = compute_crossing_number(neighbors)
        assert cn == 2

    def test_crossing_number_bifurcation(self):
        # Three diverging branches -> bifurcation
        neighbors = [1, 0, 1, 0, 1, 0, 0, 0]
        cn = compute_crossing_number(neighbors)
        assert cn == 3

    def test_extract_minutiae_on_sample(self):
        raw, pre, meta = preprocess_fingerprint(SAMPLE_101_1)
        enhanced, mask = enhance_ridges(pre)
        binary, skeleton, minutiae = extract_fingerprint_minutiae(enhanced, foreground_mask=mask)
        assert len(minutiae) >= 5
        for m in minutiae:
            assert "x" in m and "y" in m
            assert m["type"] in (TYPE_ENDING, TYPE_BIFURCATION)
            assert "orientation" in m


class TestFingerprintMatching:
    def test_identical_minutiae_yields_high_match(self):
        minutiae = [
            {"x": 100, "y": 100, "type": TYPE_ENDING, "orientation": 0.5},
            {"x": 120, "y": 110, "type": TYPE_BIFURCATION, "orientation": 1.2},
            {"x": 140, "y": 130, "type": TYPE_ENDING, "orientation": -0.4},
            {"x": 160, "y": 150, "type": TYPE_BIFURCATION, "orientation": 0.8},
            {"x": 180, "y": 170, "type": TYPE_ENDING, "orientation": 1.5},
            {"x": 200, "y": 190, "type": TYPE_ENDING, "orientation": -1.1},
        ]
        res = match_minutiae_sets(minutiae, minutiae, threshold=45.0)
        assert res["result"] == "Likely Match"
        assert res["similarity_score"] == 100.0
        assert res["matched_minutiae"] == 6

    def test_empty_minutiae_yields_non_match(self):
        res = match_minutiae_sets([], [])
        assert res["result"] == "Likely Non-Match"
        assert res["similarity_score"] == 0.0

    def test_genuine_vs_impostor_pairs(self):
        res_genuine = compare_fingerprints(SAMPLE_101_1, SAMPLE_101_2)
        assert res_genuine["success"] is True
        assert res_genuine["result"] == "Likely Match"
        assert res_genuine["similarity_score"] >= 45.0

        res_impostor = compare_fingerprints(SAMPLE_101_1, SAMPLE_102_1)
        assert res_impostor["success"] is True
        assert res_impostor["similarity_score"] < res_genuine["similarity_score"]


class TestFingerprintAPI:
    def test_api_missing_file_returns_400(self):
        resp = client.post("/api/fingerprint/compare")
        assert resp.status_code == 400

    def test_api_unsupported_format_returns_400(self):
        files = {
            "reference": ("ref.txt", b"hello text", "text/plain"),
            "questioned": ("quest.png", b"fake", "image/png"),
        }
        resp = client.post("/api/fingerprint/compare", files=files)
        assert resp.status_code == 400
        assert "Unsupported file format" in resp.json()["detail"]

    def test_api_corrupt_file_returns_422(self):
        files = {
            "reference": ("ref.png", b"not_a_valid_image", "image/png"),
            "questioned": ("quest.png", b"not_a_valid_image", "image/png"),
        }
        resp = client.post("/api/fingerprint/compare", files=files)
        assert resp.status_code == 422

    def test_api_successful_comparison(self):
        with open(SAMPLE_101_1, "rb") as f1, open(SAMPLE_101_2, "rb") as f2:
            files = {
                "reference": ("101_1.png", f1.read(), "image/png"),
                "questioned": ("101_2.png", f2.read(), "image/png"),
            }

        resp = client.post("/api/fingerprint/compare", files=files)
        assert resp.status_code == 200
        data = resp.json()

        assert data["success"] is True
        assert data["result"] in ("Likely Match", "Likely Non-Match")
        assert "similarity_score" in data
        assert "reference_minutiae" in data
        assert "questioned_minutiae" in data
        assert "matched_minutiae" in data
        assert "threshold" in data
        assert "processing_time" in data
        assert "visualizations" in data
        assert "comparison" in data["visualizations"]
        assert "reference_minutiae" in data["visualizations"]
        assert "questioned_minutiae" in data["visualizations"]

    def test_api_successful_socofing_comparison(self):
        socofing_dir = Path(__file__).parent.parent / "datasets" / "fingerprints" / "socofing" / "sample_pairs"
        ref_path = socofing_dir / "1__M_Left_index_finger.BMP"
        quest_path = socofing_dir / "1__M_Left_index_finger_CR.BMP"

        if not ref_path.exists() or not quest_path.exists():
            pytest.skip("SOCOfing sample pairs not found.")

        with open(ref_path, "rb") as f1, open(quest_path, "rb") as f2:
            files = {
                "reference": ("1__M_Left_index_finger.BMP", f1.read(), "image/bmp"),
                "questioned": ("1__M_Left_index_finger_CR.BMP", f2.read(), "image/bmp"),
            }

        resp = client.post("/api/fingerprint/compare", files=files)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["result"] == "Likely Match"
        assert data["similarity_score"] > 40.0
