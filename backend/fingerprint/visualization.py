"""
DeceptionLens — Fingerprint Minutiae & Comparison Visualization Module
======================================================================
Generates visual evidence artifacts:
1. Minutiae overlay maps (ridge endings vs bifurcations).
2. Skeleton visualization.
3. Side-by-side comparison map showing matched minutiae correspondence lines.
"""

from typing import List, Dict, Any, Tuple
import math
from pathlib import Path
import cv2
import numpy as np


# Visual styling colors (BGR format for OpenCV)
COLOR_ENDING = (40, 70, 230)       # Coral / Red-Orange for Ridge Endings
COLOR_BIFURCATION = (210, 160, 20) # Cyan / Teal for Bifurcations
COLOR_MATCH_LINE = (50, 210, 90)   # Vivid Emerald Green for valid matches
COLOR_DIVIDER = (200, 200, 200)    # Light gray divider
COLOR_TEXT = (30, 41, 59)          # Slate dark text
COLOR_BG_HEADER = (245, 248, 250)  # Off-white / light slate banner


def render_minutiae_overlay(
    gray_image: np.ndarray,
    minutiae: List[Dict[str, Any]],
    skeleton: np.ndarray = None,
) -> np.ndarray:
    """
    Renders detected minutiae points over the grayscale fingerprint impression or skeleton.
    - Ridge endings: Circles with direction vectors.
    - Bifurcations: Squares with direction indicators.
    """
    # Create 3-channel BGR image
    if len(gray_image.shape) == 2:
        canvas = cv2.cvtColor(gray_image, cv2.COLOR_GRAY2BGR)
    else:
        canvas = gray_image.copy()

    # Optionally blend skeleton in faint blue for anatomical reference
    if skeleton is not None:
        skel_mask = skeleton > 0
        canvas[skel_mask] = [180, 120, 40]  # Subtle blue-gray ridge centerline

    for m in minutiae:
        x, y = int(m["x"]), int(m["y"])
        m_type = m.get("type", "ending")
        ori = m.get("orientation", 0.0)

        # Direction vector endpoint
        tail_len = 9
        tx = int(x + tail_len * math.cos(ori))
        ty = int(y + tail_len * math.sin(ori))

        if m_type == "bifurcation":
            # Bifurcation: Teal square
            sz = 4
            cv2.rectangle(canvas, (x - sz, y - sz), (x + sz, y + sz), COLOR_BIFURCATION, 2)
            cv2.line(canvas, (x, y), (tx, ty), COLOR_BIFURCATION, 1, cv2.LINE_AA)
        else:
            # Ridge Ending: Coral circle
            cv2.circle(canvas, (x, y), 4, COLOR_ENDING, 2, cv2.LINE_AA)
            cv2.line(canvas, (x, y), (tx, ty), COLOR_ENDING, 1, cv2.LINE_AA)

    return canvas


def render_skeleton_image(skeleton: np.ndarray) -> np.ndarray:
    """
    Renders skeleton (1=ridge, 0=background) as a high-contrast dark-on-white
    or cyan-on-dark image suitable for forensic reporting.
    """
    # White background, dark ridges
    out = np.full((skeleton.shape[0], skeleton.shape[1], 3), 255, dtype=np.uint8)
    out[skeleton > 0] = [18, 30, 49]  # Dark slate ridges
    return out


def render_comparison_canvas(
    ref_image: np.ndarray,
    ref_minutiae: List[Dict[str, Any]],
    quest_image: np.ndarray,
    quest_minutiae: List[Dict[str, Any]],
    matched_pairs: List[Dict[str, Any]],
    similarity_score: float,
    result_decision: str,
) -> np.ndarray:
    """
    Builds a side-by-side forensic comparison canvas:
    - Left panel: Reference fingerprint with minutiae.
    - Right panel: Questioned fingerprint with minutiae.
    - Vector lines: Correspondences connecting matched minutiae pairs across impressions.
    - Banner: Match verdict, similarity percentage, and counts.
    """
    # Ensure 3-channel
    ref_bgr = cv2.cvtColor(ref_image, cv2.COLOR_GRAY2BGR) if len(ref_image.shape) == 2 else ref_image.copy()
    quest_bgr = cv2.cvtColor(quest_image, cv2.COLOR_GRAY2BGR) if len(quest_image.shape) == 2 else quest_image.copy()

    # Draw minutiae on both individual panels
    ref_annotated = render_minutiae_overlay(ref_bgr, ref_minutiae)
    quest_annotated = render_minutiae_overlay(quest_bgr, quest_minutiae)

    # Normalize panel heights
    h1, w1 = ref_annotated.shape[:2]
    h2, w2 = quest_annotated.shape[:2]
    target_h = max(h1, h2)

    # Pad images to uniform height
    pad_ref = np.full((target_h, w1, 3), 255, dtype=np.uint8)
    pad_ref[:h1, :w1] = ref_annotated

    pad_quest = np.full((target_h, w2, 3), 255, dtype=np.uint8)
    pad_quest[:h2, :w2] = quest_annotated

    # Side-by-side gap width
    gap = 80
    total_w = w1 + gap + w2
    header_h = 76
    footer_h = 36
    total_h = header_h + target_h + footer_h

    canvas = np.full((total_h, total_w, 3), 255, dtype=np.uint8)

    # Header background
    canvas[:header_h, :] = COLOR_BG_HEADER
    cv2.line(canvas, (0, header_h), (total_w, header_h), COLOR_DIVIDER, 1)

    # Place reference and questioned images
    canvas[header_h:header_h + target_h, :w1] = pad_ref
    canvas[header_h:header_h + target_h, w1 + gap:w1 + gap + w2] = pad_quest

    # Central divider zone
    mid_x = w1 + gap // 2
    cv2.line(canvas, (mid_x, header_h), (mid_x, header_h + target_h), (220, 220, 220), 1)

    # ── Tier 1: Centered Verdict & Score Badge ────────────────────────────────
    is_match = "Likely Match" in result_decision
    decision_color = (20, 140, 40) if is_match else (30, 30, 200)
    score_text = f"{result_decision}: {similarity_score:.1f}% ({len(matched_pairs)} matched)"
    text_size = cv2.getTextSize(score_text, cv2.FONT_HERSHEY_SIMPLEX, 0.60, 2)[0]
    center_x = (total_w - text_size[0]) // 2

    # Draw rounded-style pill behind the verdict
    pill_pad_x = 14
    pill_pad_y = 6
    pill_x1 = max(0, center_x - pill_pad_x)
    pill_y1 = 6
    pill_x2 = min(total_w - 1, center_x + text_size[0] + pill_pad_x)
    pill_y2 = 32
    pill_bg = (230, 245, 235) if is_match else (235, 235, 250)
    cv2.rectangle(canvas, (pill_x1, pill_y1), (pill_x2, pill_y2), pill_bg, -1)
    cv2.rectangle(canvas, (pill_x1, pill_y1), (pill_x2, pill_y2), decision_color, 1, cv2.LINE_AA)

    cv2.putText(
        canvas,
        score_text,
        (center_x, 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.60,
        decision_color,
        2,
        cv2.LINE_AA,
    )

    # Subtle horizontal line between tier 1 (verdict) and tier 2 (column titles)
    cv2.line(canvas, (16, 42), (total_w - 16, 42), (230, 234, 238), 1)

    # ── Tier 2: Column Headers ────────────────────────────────────────────────
    cv2.putText(
        canvas,
        f"Reference Impression ({len(ref_minutiae)} minutiae)",
        (20, 62),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        (45, 55, 72),
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        canvas,
        f"Questioned Impression ({len(quest_minutiae)} minutiae)",
        (w1 + gap + 20, 62),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        (45, 55, 72),
        2,
        cv2.LINE_AA,
    )

    # Draw matched correspondence lines
    offset_x2 = w1 + gap
    for pair in matched_pairs:
        rx, ry = pair["ref_point"]
        qx, qy = pair["quest_point"]

        pt1 = (int(rx), int(ry + header_h))
        pt2 = (int(qx + offset_x2), int(qy + header_h))

        # Highlight endpoints
        cv2.circle(canvas, pt1, 6, COLOR_MATCH_LINE, 2, cv2.LINE_AA)
        cv2.circle(canvas, pt2, 6, COLOR_MATCH_LINE, 2, cv2.LINE_AA)

        # Connection line with slight transparency via blend
        cv2.line(canvas, pt1, pt2, COLOR_MATCH_LINE, 1, cv2.LINE_AA)

    # Footer note
    footer_text = "DeceptionLens Minutiae Matching Aid — Research & Educational Use Only"
    cv2.putText(
        canvas,
        footer_text,
        (20, total_h - 12),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (120, 130, 140),
        1,
        cv2.LINE_AA,
    )

    return canvas


def save_image_artifact(image: np.ndarray, destination_path: str) -> str:
    """
    Safely saves an OpenCV image to the specified path, ensuring parent directory exists.
    """
    Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(destination_path, image)
    return destination_path
