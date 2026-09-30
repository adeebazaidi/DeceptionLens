"""
Signature Analysis Module
=========================
Provides forensic evaluation of handwritten signatures:
  1. Standalone Signature Screening:
     - Otsu Binarization & Bounding Box Normalization
     - Skeletonization & Stroke Topology Analysis
     - Pen Tremor & Hesitation Detection (micro-curvature analysis along strokes)
     - Geometrical Centroid & Aspect Ratio Metrics
  2. Reference Signature Comparison (1-vs-1 Verification):
     - Structural Similarity Index (SSIM)
     - Projection Profile Cosine Distance
     - Aspect Ratio & Centroid Shift Deltas
     - Color-Coded Difference Overlay Heatmap
"""

import os
from pathlib import Path
from typing import Dict, Optional, Tuple, List

import cv2
import numpy as np
from PIL import Image
from skimage.morphology import skeletonize
from skimage.metrics import structural_similarity as ssim


def load_grayscale_image(img_input: str) -> np.ndarray:
    """Load image path as grayscale uint8 numpy array."""
    cv_img = cv2.imread(img_input)
    if cv_img is None:
        pil_img = Image.open(img_input).convert("L")
        return np.array(pil_img, dtype=np.uint8)
    return cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)


def binarize_and_crop_signature(gray: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
    """
    Binarize grayscale image using Otsu's thresholding and crop to signature bounding box.
    Returns:
      binary_mask: uint8 array where ink = 255 and background = 0
      bbox: (x, y, w, h)
    """
    # Gaussian blur to smooth paper grain
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Otsu thresholding (ink becomes 255, background 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Find bounding box of non-zero ink pixels
    coords = cv2.findNonZero(thresh)
    if coords is None:
        # Blank image fallback
        h, w = gray.shape
        return thresh, (0, 0, w, h)
    
    x, y, w, h = cv2.boundingRect(coords)
    
    # Add a small 10px margin around bounding box
    margin = 10
    h_img, w_img = gray.shape
    x1 = max(0, x - margin)
    y1 = max(0, y - margin)
    x2 = min(w_img, x + w + margin)
    y2 = min(h_img, y + h + margin)
    
    cropped_thresh = thresh[y1:y2, x1:x2]
    return cropped_thresh, (x1, y1, x2 - x1, y2 - y1)


def normalize_signature_size(binary_mask: np.ndarray, target_size: Tuple[int, int] = (256, 512)) -> np.ndarray:
    """Resize binary mask to target (height, width) maintaining aspect ratio with padding."""
    target_h, target_w = target_size
    h, w = binary_mask.shape
    if h == 0 or w == 0:
        return np.zeros((target_h, target_w), dtype=np.uint8)
    
    scale = min(target_h / h, target_w / w)
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    resized = cv2.resize(binary_mask, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    padded = np.zeros((target_h, target_w), dtype=np.uint8)
    pad_y = (target_h - new_h) // 2
    pad_x = (target_w - new_w) // 2
    padded[pad_y : pad_y + new_h, pad_x : pad_x + new_w] = resized
    return padded


def compute_skeleton(binary_mask: np.ndarray) -> np.ndarray:
    """Thin binary signature mask to 1-pixel wide skeleton."""
    bool_mask = binary_mask > 128
    skel_bool = skeletonize(bool_mask)
    return (skel_bool * 255).astype(np.uint8)


def detect_stroke_tremor(binary_mask: np.ndarray, skel: np.ndarray) -> Tuple[float, np.ndarray]:
    """
    Detect stroke hesitation and micro-tremors along signature edges.
    Genuine signatures have smooth, fast strokes. Forged / traced signatures
    show irregular micro-curvature and high edge gradient variance.
    
    Returns:
      tremor_score: float in range [0.0, 1.0]
      heatmap_bgr: uint8 BGR image displaying tremor regions in warm colors
    """
    if np.sum(binary_mask) == 0:
        h, w = binary_mask.shape
        return 0.0, np.zeros((h, w, 3), dtype=np.uint8)

    # Calculate distance transform from signature boundary
    dist = cv2.distanceTransform(binary_mask, cv2.DIST_L2, 5)
    
    # Calculate Laplacian of distance transform to capture stroke width jitter
    laplacian = cv2.Laplacian(dist.astype(np.float64), cv2.CV_64F)
    abs_lap = np.abs(laplacian)
    
    # Restrict analysis to stroke regions
    stroke_pixels = binary_mask > 0
    if not np.any(stroke_pixels):
        h, w = binary_mask.shape
        return 0.0, np.zeros((h, w, 3), dtype=np.uint8)

    tremor_map = np.zeros_like(abs_lap)
    tremor_map[stroke_pixels] = abs_lap[stroke_pixels]

    # Normalize map to [0, 255]
    max_val = np.percentile(tremor_map[stroke_pixels], 98) if np.any(stroke_pixels) else 1.0
    if max_val <= 0:
        max_val = 1.0
    
    norm_map = np.clip((tremor_map / max_val) * 255.0, 0, 255).astype(np.uint8)
    
    # Compute mean tremor metric on skeleton points
    skel_pixels = skel > 0
    if np.any(skel_pixels):
        skel_tremor_vals = norm_map[skel_pixels]
        # Standard deviation of local stroke gradient indicates hesitation jitter
        tremor_score = float(np.std(skel_tremor_vals) / 100.0)
    else:
        tremor_score = float(np.std(norm_map[stroke_pixels]) / 100.0)

    tremor_score = round(min(max(tremor_score, 0.0), 1.0), 4)

    # Colorize heatmap (COLORMAP_JET: Blue=Smooth, Red/Yellow=High Tremor)
    color_map = cv2.applyColorMap(norm_map, cv2.COLORMAP_JET)
    
    # Mask out background to keep background dark/transparent
    color_map[~stroke_pixels] = [15, 15, 20]  # dark background

    return tremor_score, color_map


def compute_signature_features(binary_mask: np.ndarray, skel: np.ndarray) -> Dict:
    """Extract morphological and geometric features from a normalized signature binary mask."""
    h, w = binary_mask.shape
    total_pixels = h * w
    ink_pixels = int(np.sum(binary_mask > 128))
    
    # 1. Bounding box & aspect ratio of actual ink
    coords = cv2.findNonZero(binary_mask)
    if coords is not None:
        bx, by, bw, bh = cv2.boundingRect(coords)
        aspect_ratio = float(bw / bh) if bh > 0 else 1.0
        ink_area = int(bw * bh)
        fill_factor = float(ink_pixels / ink_area) if ink_area > 0 else 0.0
    else:
        bx, by, bw, bh = 0, 0, w, h
        aspect_ratio = 1.0
        fill_factor = 0.0

    # 2. Pixel Density (Ink ratio relative to total container)
    density = float(ink_pixels / total_pixels)

    # 3. Center of Mass / Centroid (Normalized [0, 1])
    M = cv2.moments(binary_mask)
    if M["m00"] != 0:
        cx = float((M["m10"] / M["m00"]) / w)
        cy = float((M["m01"] / M["m00"]) / h)
    else:
        cx, cy = 0.5, 0.5

    # 4. Connected components count (pen lifts / dots / disconnected strokes)
    num_labels, _, _, _ = cv2.connectedComponentsWithStats(binary_mask)
    connected_components = max(0, num_labels - 1)  # subtract background label

    # 5. Projection Profiles (Horizontal & Vertical Ink Histograms)
    horiz_profile = np.sum(binary_mask > 128, axis=1, dtype=np.float32)
    vert_profile = np.sum(binary_mask > 128, axis=0, dtype=np.float32)
    
    # Normalize projection profiles
    h_sum = np.sum(horiz_profile)
    v_sum = np.sum(vert_profile)
    if h_sum > 0:
        horiz_profile /= h_sum
    if v_sum > 0:
        vert_profile /= v_sum

    # 6. Tremor analysis
    tremor_score, tremor_heatmap = detect_stroke_tremor(binary_mask, skel)

    return {
        "aspect_ratio": round(aspect_ratio, 4),
        "density": round(density, 4),
        "fill_factor": round(fill_factor, 4),
        "centroid_x": round(cx, 4),
        "centroid_y": round(cy, 4),
        "connected_components": connected_components,
        "tremor_score": tremor_score,
        "horiz_profile": horiz_profile.tolist(),
        "vert_profile": vert_profile.tolist(),
        "bbox": [bx, by, bw, bh],
        "tremor_heatmap": tremor_heatmap,
    }


def compare_signatures(
    query_binary: np.ndarray,
    ref_binary: np.ndarray,
    query_feats: Dict,
    ref_feats: Dict,
) -> Tuple[Dict, np.ndarray]:
    """
    Compare Query Signature against Reference Signature (1-vs-1 Verification).
    Returns metrics dict and overlay heatmap image.
    """
    # 1. Structural Similarity (SSIM)
    ssim_val, diff_map = ssim(query_binary, ref_binary, full=True)
    ssim_score = float(max(0.0, ssim_val))

    # 2. Aspect Ratio Delta
    ar_diff = float(abs(query_feats["aspect_ratio"] - ref_feats["aspect_ratio"]))

    # 3. Centroid Shift Distance
    dx = query_feats["centroid_x"] - ref_feats["centroid_x"]
    dy = query_feats["centroid_y"] - ref_feats["centroid_y"]
    centroid_shift = float(np.sqrt(dx * dx + dy * dy))

    # 4. Density Delta
    density_diff = float(abs(query_feats["density"] - ref_feats["density"]))

    # 5. Projection Profile Cosine Similarities
    q_hp = np.array(query_feats["horiz_profile"], dtype=np.float32)
    r_hp = np.array(ref_feats["horiz_profile"], dtype=np.float32)
    h_cos = float(np.dot(q_hp, r_hp) / (np.linalg.norm(q_hp) * np.linalg.norm(r_hp) + 1e-7))

    q_vp = np.array(query_feats["vert_profile"], dtype=np.float32)
    r_vp = np.array(ref_feats["vert_profile"], dtype=np.float32)
    v_cos = float(np.dot(q_vp, r_vp) / (np.linalg.norm(q_vp) * np.linalg.norm(r_vp) + 1e-7))

    profile_similarity = float((h_cos + v_cos) / 2.0)

    # 6. Composite Similarity Score (0 - 100%)
    weighted_sim = (
        ssim_score * 0.40 +
        profile_similarity * 0.30 +
        max(0.0, 1.0 - centroid_shift * 3.0) * 0.15 +
        max(0.0, 1.0 - ar_diff / 1.5) * 0.15
    )
    match_percentage = round(float(weighted_sim * 100.0), 1)

    # Determine risk verdict
    reasons = []
    if match_percentage >= 75.0:
        verdict = "GENUINE_MATCH"
        risk_level = "LOW"
    elif match_percentage >= 50.0:
        verdict = "SUSPICIOUS"
        risk_level = "MEDIUM"
        if ssim_score < 0.6:
            reasons.append("Low structural similarity to reference signature")
        if centroid_shift > 0.1:
            reasons.append("Notable center-of-mass shift compared to reference")
    else:
        verdict = "FORGERY_LIKELY"
        risk_level = "HIGH"
        reasons.append("Significant structural and geometric discrepancy from reference signature")

    if query_feats["tremor_score"] > 0.45:
        reasons.append("High stroke hesitation / micro-tremor detected in query signature")

    # 7. Generate Color-Coded Difference Overlay Heatmap
    # Green = Overlapping stroke
    # Red   = Discrepant stroke in query signature
    # Blue  = Missing stroke from reference signature
    h, w = query_binary.shape
    overlay = np.zeros((h, w, 3), dtype=np.uint8)

    q_mask = query_binary > 128
    r_mask = ref_binary > 128

    overlap = q_mask & r_mask
    extra_query = q_mask & (~r_mask)
    missing_ref = (~q_mask) & r_mask

    overlay[overlap] = [0, 220, 100]      # Green (Matching)
    overlay[extra_query] = [0, 50, 255]   # Red (Extra stroke in query)
    overlay[missing_ref] = [255, 120, 0]  # Blue (Missing stroke from ref)
    overlay[~ (q_mask | r_mask)] = [20, 20, 28]  # Dark background

    forgery_risk_percentage = round(float(max(0.1, min(99.9, 100.0 - match_percentage))), 1)

    metrics = {
        "ssim": round(ssim_score, 4),
        "aspect_ratio_diff": round(ar_diff, 4),
        "centroid_shift": round(centroid_shift, 4),
        "density_diff": round(density_diff, 4),
        "profile_similarity": round(profile_similarity, 4),
        "match_percentage": match_percentage,
        "forgery_risk_percentage": forgery_risk_percentage,
        "verdict": verdict,
        "risk_level": risk_level,
        "reasons": reasons if reasons else ["Signature closely matches reference proportions and strokes."],
    }

    return metrics, overlay


def analyze_signature_pipeline(
    query_path: str,
    ref_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    uid: str = "sig_test",
) -> Dict:
    """
    End-to-End Signature Forgery Pipeline.
    Processes query signature and optional reference signature, saving output preview images.
    """
    # 1. Load Query Signature
    query_gray = load_grayscale_image(query_path)
    q_bin_raw, q_bbox = binarize_and_crop_signature(query_gray)
    q_bin = normalize_signature_size(q_bin_raw)
    q_skel = compute_skeleton(q_bin)
    q_feats = compute_signature_features(q_bin, q_skel)

    # Prepare output URLs dictionary
    saved_images = {}
    if output_dir:
        out_p = Path(output_dir)
        out_p.mkdir(parents=True, exist_ok=True)

        # Save Binarized Query Image
        q_bin_file = out_p / f"{uid}_q_bin.png"
        cv2.imwrite(str(q_bin_file), q_bin)
        saved_images["binary_url"] = f"/outputs/signature/{uid}_q_bin.png"

        # Save Skeleton Query Image
        q_skel_file = out_p / f"{uid}_q_skel.png"
        cv2.imwrite(str(q_skel_file), q_skel)
        saved_images["skeleton_url"] = f"/outputs/signature/{uid}_q_skel.png"

        # Save Tremor Heatmap Query Image
        q_tremor_file = out_p / f"{uid}_q_tremor.png"
        cv2.imwrite(str(q_tremor_file), q_feats["tremor_heatmap"])
        saved_images["tremor_url"] = f"/outputs/signature/{uid}_q_tremor.png"

    # Evaluate standalone risk
    standalone_reasons = []
    if q_feats["tremor_score"] > 0.45:
        standalone_reasons.append("Elevated stroke tremor/hesitation detected along signature contours.")
    if q_feats["fill_factor"] < 0.05 or q_feats["fill_factor"] > 0.45:
        standalone_reasons.append("Unusual ink fill density ratio.")
    if q_feats["aspect_ratio"] > 4.5 or q_feats["aspect_ratio"] < 0.6:
        standalone_reasons.append("Extreme aspect ratio detected.")

    standalone_risk = "HIGH" if len(standalone_reasons) >= 2 else ("MEDIUM" if len(standalone_reasons) == 1 else "LOW")
    standalone_risk_pct = round(min(99.9, max(5.0, q_feats["tremor_score"] * 70.0 + len(standalone_reasons) * 15.0)), 1)

    response_data = {
        "mode": "COMPARISON" if ref_path else "STANDALONE",
        "query_features": {
            "aspect_ratio": q_feats["aspect_ratio"],
            "density": q_feats["density"],
            "fill_factor": q_feats["fill_factor"],
            "centroid": [q_feats["centroid_x"], q_feats["centroid_y"]],
            "connected_components": q_feats["connected_components"],
            "tremor_score": q_feats["tremor_score"],
        },
        "standalone_assessment": {
            "risk_level": standalone_risk,
            "forgery_risk_percentage": standalone_risk_pct,
            "reasons": standalone_reasons if standalone_reasons else ["Signature displays fluid stroke motion and normal geometry."],
        },
        "visual_urls": saved_images,
    }

    # 2. Reference Signature Comparison (if reference provided)
    if ref_path:
        ref_gray = load_grayscale_image(ref_path)
        r_bin_raw, _ = binarize_and_crop_signature(ref_gray)
        r_bin = normalize_signature_size(r_bin_raw)
        r_skel = compute_skeleton(r_bin)
        r_feats = compute_signature_features(r_bin, r_skel)

        comp_metrics, overlay_img = compare_signatures(q_bin, r_bin, q_feats, r_feats)

        if output_dir:
            out_p = Path(output_dir)
            # Save Reference Binarized Image
            r_bin_file = out_p / f"{uid}_r_bin.png"
            cv2.imwrite(str(r_bin_file), r_bin)
            saved_images["ref_binary_url"] = f"/outputs/signature/{uid}_r_bin.png"

            # Save Difference Overlay Image
            overlay_file = out_p / f"{uid}_overlay.png"
            cv2.imwrite(str(overlay_file), overlay_img)
            saved_images["comparison_overlay_url"] = f"/outputs/signature/{uid}_overlay.png"

        response_data["reference_features"] = {
            "aspect_ratio": r_feats["aspect_ratio"],
            "density": r_feats["density"],
            "fill_factor": r_feats["fill_factor"],
            "centroid": [r_feats["centroid_x"], r_feats["centroid_y"]],
            "connected_components": r_feats["connected_components"],
            "tremor_score": r_feats["tremor_score"],
        }
        response_data["comparison"] = comp_metrics

    return response_data
