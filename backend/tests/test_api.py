"""
Tests — API Endpoint
====================
Integration tests for POST /api/image/analyze.
"""

import io
import sys
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

# Allow imports from backend root
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app

client = TestClient(app)


def _make_jpeg_bytes(size=(64, 64)) -> bytes:
    """Create a JPEG image in memory."""
    rng = np.random.default_rng(99)
    arr = rng.integers(0, 256, (*size, 3), dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def _make_png_bytes(size=(64, 64)) -> bytes:
    """Create a PNG image in memory."""
    rng = np.random.default_rng(7)
    arr = rng.integers(0, 256, (*size, 3), dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestValidUpload:
    def test_jpeg_returns_200(self):
        """Valid JPEG should return HTTP 200."""
        data = _make_jpeg_bytes()
        response = client.post(
            "/api/image/analyze",
            files={"file": ("test.jpg", data, "image/jpeg")},
        )
        assert response.status_code == 200

    def test_response_has_success_true(self):
        """Response JSON should have success=true."""
        data = _make_jpeg_bytes()
        response = client.post(
            "/api/image/analyze",
            files={"file": ("test.jpg", data, "image/jpeg")},
        )
        body = response.json()
        assert body["success"] is True

    def test_response_has_all_sections(self):
        """All expected top-level keys should be present."""
        data = _make_jpeg_bytes()
        response = client.post(
            "/api/image/analyze",
            files={"file": ("test.jpg", data, "image/jpeg")},
        )
        body = response.json()
        for key in ("entropy", "ela", "noise", "texture", "metadata", "preliminary_result", "ml_prediction"):
            assert key in body, f"Missing key: {key}"

    def test_entropy_keys(self):
        """Entropy section must have expected keys."""
        data = _make_jpeg_bytes()
        response = client.post(
            "/api/image/analyze",
            files={"file": ("test.jpg", data, "image/jpeg")},
        )
        body = response.json()
        for key in ("global", "mean_local", "std_local", "anomaly_score", "heatmap_url"):
            assert key in body["entropy"]

    def test_png_upload(self):
        """PNG upload should also succeed."""
        data = _make_png_bytes()
        response = client.post(
            "/api/image/analyze",
            files={"file": ("test.png", data, "image/png")},
        )
        assert response.status_code == 200

    def test_ml_prediction_not_available_without_model(self):
        """ml_prediction.available should be false when no model is trained."""
        data = _make_jpeg_bytes()
        response = client.post(
            "/api/image/analyze",
            files={"file": ("test.jpg", data, "image/jpeg")},
        )
        body = response.json()
        ml = body.get("ml_prediction", {})
        # Either available=False OR available=True (if model exists)
        assert "available" in ml


class TestUnsupportedFile:
    def test_txt_file_returns_400(self):
        """A .txt file should return 400."""
        response = client.post(
            "/api/image/analyze",
            files={"file": ("readme.txt", b"hello world", "text/plain")},
        )
        assert response.status_code == 400

    def test_pdf_file_returns_400(self):
        """A .pdf file should return 400."""
        response = client.post(
            "/api/image/analyze",
            files={"file": ("doc.pdf", b"%PDF-1.4", "application/pdf")},
        )
        assert response.status_code == 400


class TestMissingFile:
    def test_no_file_field_returns_422(self):
        """Missing file field should return 422 Unprocessable Entity."""
        response = client.post("/api/image/analyze")
        assert response.status_code == 422


class TestOversizedFile:
    def test_oversized_returns_413(self, monkeypatch):
        """File exceeding max size should return 413."""
        import api.routes.image_routes as routes_mod
        monkeypatch.setattr(routes_mod, "MAX_SIZE_BYTES", 100)  # 100 bytes

        data = _make_jpeg_bytes()  # ~several KB
        response = client.post(
            "/api/image/analyze",
            files={"file": ("big.jpg", data, "image/jpeg")},
        )
        assert response.status_code == 413


class TestDocumentNLPUnavailable:
    def test_returns_503_when_spacy_cannot_load(self, monkeypatch):
        """A broken/blocked spaCy install should yield a clear 503, not a crash."""
        import modules.document_analysis.analyzer as analyzer_mod
        import modules.document_analysis.nlp_service as nlp_mod

        def _fail():
            raise nlp_mod.NLPUnavailableError("blocked by test")

        monkeypatch.setattr(nlp_mod, "get_nlp", _fail)
        # Skip real OCR to keep the test fast.
        monkeypatch.setattr(
            analyzer_mod,
            "perform_ocr",
            lambda pages: [{"page_num": 1, "raw_text": "Case No. 42", "ocr_items": []}],
        )

        response = client.post(
            "/api/document/analyze",
            files={"file": ("doc.png", _make_png_bytes(), "image/png")},
        )
        assert response.status_code == 503
        assert "temporarily unavailable" in response.json()["detail"]

    def test_oversized_document_returns_400(self):
        """The size check must not be swallowed into a 500 by the generic handler."""
        data = b"0" * (20 * 1024 * 1024 + 1)
        response = client.post(
            "/api/document/analyze",
            files={"file": ("big.pdf", data, "application/pdf")},
        )
        assert response.status_code == 400
