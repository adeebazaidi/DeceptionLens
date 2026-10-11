"""
Unit Tests for Signature Analysis Module & API Route
==================================================
"""

import io
import numpy as np
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from main import app
from modules.signature.signature_analysis import (
    binarize_and_crop_signature,
    compute_skeleton,
    detect_stroke_tremor,
    compute_signature_features,
    compare_signatures,
)

client = TestClient(app)


def create_synthetic_signature_image(smooth: bool = True) -> bytes:
    """Create a synthetic signature image in memory."""
    img = Image.new("RGB", (400, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    if smooth:
        # Smooth fluid curved stroke
        points = [(50, 100), (100, 40), (180, 160), (250, 60), (350, 120)]
        draw.line(points, fill=(0, 0, 0), width=4, joint="curve")
        draw.ellipse([200, 70, 240, 110], outline=(0, 0, 0), width=3)
    else:
        # Jagged/tremorous stroke
        points = []
        for x in range(50, 350, 10):
            y = 100 + int(np.random.randint(-15, 15))
            points.append((x, y))
        draw.line(points, fill=(0, 0, 0), width=4)
        
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_binarize_and_crop():
    img_bytes = create_synthetic_signature_image(smooth=True)
    pil_img = Image.open(io.BytesIO(img_bytes)).convert("L")
    gray = np.array(pil_img, dtype=np.uint8)
    
    binary_mask, bbox = binarize_and_crop_signature(gray)
    assert binary_mask is not None
    assert np.sum(binary_mask) > 0
    assert bbox[2] > 0 and bbox[3] > 0


def test_skeletonization_and_tremor():
    img_bytes = create_synthetic_signature_image(smooth=True)
    pil_img = Image.open(io.BytesIO(img_bytes)).convert("L")
    gray = np.array(pil_img, dtype=np.uint8)
    binary_mask, _ = binarize_and_crop_signature(gray)
    
    skel = compute_skeleton(binary_mask)
    assert skel.shape == binary_mask.shape
    assert np.sum(skel) > 0
    
    tremor_score, heatmap = detect_stroke_tremor(binary_mask, skel)
    assert 0.0 <= tremor_score <= 1.0
    assert heatmap.shape == (binary_mask.shape[0], binary_mask.shape[1], 3)


def test_signature_features():
    img_bytes = create_synthetic_signature_image(smooth=True)
    pil_img = Image.open(io.BytesIO(img_bytes)).convert("L")
    gray = np.array(pil_img, dtype=np.uint8)
    binary_mask, _ = binarize_and_crop_signature(gray)
    skel = compute_skeleton(binary_mask)
    
    feats = compute_signature_features(binary_mask, skel)
    assert "aspect_ratio" in feats
    assert "density" in feats
    assert "centroid_x" in feats
    assert "centroid_y" in feats
    assert "tremor_score" in feats


def test_signature_comparison():
    img_bytes1 = create_synthetic_signature_image(smooth=True)
    img_bytes2 = create_synthetic_signature_image(smooth=True)
    
    gray1 = np.array(Image.open(io.BytesIO(img_bytes1)).convert("L"), dtype=np.uint8)
    gray2 = np.array(Image.open(io.BytesIO(img_bytes2)).convert("L"), dtype=np.uint8)
    
    bin1, _ = binarize_and_crop_signature(gray1)
    bin2, _ = binarize_and_crop_signature(gray2)
    skel1 = compute_skeleton(bin1)
    skel2 = compute_skeleton(bin2)
    
    f1 = compute_signature_features(bin1, skel1)
    f2 = compute_signature_features(bin2, skel2)
    
    metrics, overlay = compare_signatures(bin1, bin2, f1, f2)
    assert "ssim" in metrics
    assert "match_percentage" in metrics
    assert "verdict" in metrics
    assert overlay.shape == (bin1.shape[0], bin1.shape[1], 3)


def test_signature_api_standalone():
    query_bytes = create_synthetic_signature_image(smooth=True)
    response = client.post(
        "/api/signature/analyze",
        files={"file": ("query.png", query_bytes, "image/png")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["analysis"]["mode"] == "STANDALONE"
    assert "query_features" in data["analysis"]
    assert "visual_urls" in data["analysis"]


def test_signature_api_comparison():
    query_bytes = create_synthetic_signature_image(smooth=True)
    ref_bytes = create_synthetic_signature_image(smooth=True)
    
    response = client.post(
        "/api/signature/analyze",
        files={
            "file": ("query.png", query_bytes, "image/png"),
            "reference_file": ("ref.png", ref_bytes, "image/png"),
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["analysis"]["mode"] == "COMPARISON"
    assert "comparison" in data["analysis"]
    assert "comparison_overlay_url" in data["analysis"]["visual_urls"]
