"""
DeceptionLens — Fingerprint Minutiae & Comparison Visualization Module
======================================================================
Generates professional forensic evidence artifacts:
1. Minutiae overlay maps (ridge endings vs bifurcations).
2. Skeleton visualization.
3. Ultra-clean side-by-side comparison map with typography, match verdict pill badges,
   and minutiae correspondence lines.
"""

from typing import List, Dict, Any
import math
import os
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def get_font(size: int, bold: bool = False):
    """Safely loads a crisp TrueType font on Windows/Linux with default fallbacks."""
    font_paths = [
        "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def render_minutiae_overlay(
    gray_image: np.ndarray,
    minutiae: List[Dict[str, Any]],
    skeleton: np.ndarray = None,
) -> np.ndarray:
    """
    Renders detected minutiae points over the grayscale fingerprint impression or skeleton.
    - Ridge endings: Coral Red circles with orientation vectors.
    - Bifurcations: Sky Blue / Cyan squares with orientation vectors.
    """
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
        tail_len = 8
        tx = int(x + tail_len * math.cos(ori))
        ty = int(y + tail_len * math.sin(ori))

        if m_type == "bifurcation":
            # Bifurcation: Cyan / Sky Blue square (BGR: 199, 132, 2)
            sz = 3.5
            cv2.rectangle(canvas, (int(x - sz), int(y - sz)), (int(x + sz), int(y + sz)), (199, 132, 2), 1, cv2.LINE_AA)
            cv2.line(canvas, (x, y), (tx, ty), (199, 132, 2), 1, cv2.LINE_AA)
        else:
            # Ridge Ending: Coral Red circle (BGR: 40, 70, 230)
            cv2.circle(canvas, (x, y), 3, (40, 70, 230), 1, cv2.LINE_AA)
            cv2.line(canvas, (x, y), (tx, ty), (40, 70, 230), 1, cv2.LINE_AA)

    return canvas


def render_skeleton_image(skeleton: np.ndarray) -> np.ndarray:
    """
    Renders skeleton (1=ridge, 0=background) as a high-contrast dark-on-white
    image suitable for forensic reporting.
    """
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
    Builds a high-end, clean side-by-side forensic comparison canvas:
    - Left panel: Reference fingerprint with minutiae.
    - Right panel: Questioned fingerprint with minutiae.
    - Vector lines: Correspondences connecting matched minutiae pairs across impressions.
    - Header: Modern typography, match verdict pill badge, and count chips.
    """
    ref_bgr = cv2.cvtColor(ref_image, cv2.COLOR_GRAY2BGR) if len(ref_image.shape) == 2 else ref_image.copy()
    quest_bgr = cv2.cvtColor(quest_image, cv2.COLOR_GRAY2BGR) if len(quest_image.shape) == 2 else quest_image.copy()

    ref_annotated = render_minutiae_overlay(ref_bgr, ref_minutiae)
    quest_annotated = render_minutiae_overlay(quest_bgr, quest_minutiae)

    h1, w1 = ref_annotated.shape[:2]
    h2, w2 = quest_annotated.shape[:2]
    target_h = max(h1, h2)

    # Pad images to uniform height
    pad_ref = np.full((target_h, w1, 3), 255, dtype=np.uint8)
    pad_ref[:h1, :w1] = ref_annotated

    pad_quest = np.full((target_h, w2, 3), 255, dtype=np.uint8)
    pad_quest[:h2, :w2] = quest_annotated

    gap = 90
    total_w = w1 + gap + w2
    header_h = 88
    footer_h = 36
    total_h = header_h + target_h + footer_h

    # Create canvas with soft slate background (BGR: 248, 250, 252)
    canvas = np.full((total_h, total_w, 3), 248, dtype=np.uint8)

    # Header Background: Dark Slate #0f172a (BGR: 42, 23, 15)
    canvas[:header_h, :] = (42, 23, 15)

    # Place reference and questioned images
    canvas[header_h:header_h + target_h, :w1] = pad_ref
    canvas[header_h:header_h + target_h, w1 + gap:w1 + gap + w2] = pad_quest

    # Central divider zone in background gap
    mid_x = w1 + gap // 2
    cv2.line(canvas, (mid_x, header_h + 10), (mid_x, header_h + target_h - 10), (220, 226, 235), 1, cv2.LINE_AA)

    # Draw matched correspondence lines with semi-transparent blending
    line_layer = canvas.copy()
    offset_x2 = w1 + gap

    for pair in matched_pairs:
        rx, ry = pair["ref_point"]
        qx, qy = pair["quest_point"]

        pt1 = (int(rx), int(ry + header_h))
        pt2 = (int(qx + offset_x2), int(qy + header_h))

        # Highlight endpoints with small halo circles
        cv2.circle(line_layer, pt1, 4, (16, 185, 129), -1, cv2.LINE_AA)
        cv2.circle(line_layer, pt1, 6, (255, 255, 255), 1, cv2.LINE_AA)

        cv2.circle(line_layer, pt2, 4, (16, 185, 129), -1, cv2.LINE_AA)
        cv2.circle(line_layer, pt2, 6, (255, 255, 255), 1, cv2.LINE_AA)

        # Connection line
        cv2.line(line_layer, pt1, pt2, (16, 185, 129), 1, cv2.LINE_AA)

    # Blend lines with 75% opacity
    cv2.addWeighted(line_layer, 0.75, canvas, 0.25, 0, canvas)

    # Convert canvas to PIL for ultra-crisp typography header & footer rendering
    pil_img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)

    font_title = get_font(13, bold=True)
    font_sub = get_font(11, bold=False)
    font_pill = get_font(12, bold=True)
    font_footer = get_font(11, bold=False)

    # ── Pill Badge Verdict in Header ──────────────────────────────────────────
    is_match = "Likely Match" in result_decision
    match_str = "LIKELY MATCH" if is_match else "LIKELY NON-MATCH"
    badge_text = f"{match_str}   •   {similarity_score:.1f}%   ({len(matched_pairs)} matched pairs)"

    # Pill dimensions
    bbox = font_pill.getbbox(badge_text)
    tw = bbox[2] - bbox[0]
    bbox[3] - bbox[1]

    pill_w = tw + 36
    pill_h = 30
    pill_x = (total_w - pill_w) // 2
    pill_y = 12

    pill_bg_color = (6, 78, 59) if is_match else (127, 29, 29)        # Dark Emerald vs Dark Red
    pill_border_color = (16, 185, 129) if is_match else (239, 68, 68)  # Bright Emerald vs Bright Red
    pill_text_color = (209, 250, 229) if is_match else (254, 202, 202)  # Mint Green vs Soft Pink

    # Draw rounded pill
    draw.rounded_rectangle(
        [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
        radius=15,
        fill=pill_bg_color,
        outline=pill_border_color,
        width=1,
    )

    # Draw status pulse dot inside pill
    dot_color = (16, 185, 129) if is_match else (239, 68, 68)
    draw.ellipse([pill_x + 12, pill_y + 11, pill_x + 19, pill_y + 18], fill=dot_color)

    # Draw Pill Text
    draw.text((pill_x + 26, pill_y + 7), badge_text, fill=pill_text_color, font=font_pill)

    # ── Header Sub-Titles ─────────────────────────────────────────────────────
    ref_title = "REFERENCE IMPRESSION"
    ref_count = f"{len(ref_minutiae)} minutiae points"
    draw.text((20, header_h - 36), ref_title, fill=(241, 245, 249), font=font_title)
    draw.text((20, header_h - 18), ref_count, fill=(148, 163, 184), font=font_sub)

    quest_title = "QUESTIONED IMPRESSION"
    quest_count = f"{len(quest_minutiae)} minutiae points"
    draw.text((offset_x2 + 20, header_h - 36), quest_title, fill=(241, 245, 249), font=font_title)
    draw.text((offset_x2 + 20, header_h - 18), quest_count, fill=(148, 163, 184), font=font_sub)

    # Footer
    footer_text = "DeceptionLens Forensic Minutiae Verification System — Research & Educational Purpose Only"
    draw.text((20, total_h - 24), footer_text, fill=(100, 116, 139), font=font_footer)

    # Convert back to BGR numpy array for OpenCV compatibility
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def save_image_artifact(image: np.ndarray, destination_path: str) -> str:
    """
    Safely saves an OpenCV image to the specified path, ensuring parent directory exists.
    """
    Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(destination_path, image)
    return destination_path
