"""
DeceptionLens — Fingerprint Minutiae Extraction Module
======================================================
Implements binarization, skeletonization, Crossing Number (CN) feature extraction,
orientation computation, and false minutiae pruning.
"""

from typing import List, Dict, Any, Tuple
import math
import numpy as np
import cv2
from skimage.morphology import skeletonize


# Minutiae class types
TYPE_ENDING = "ending"
TYPE_BIFURCATION = "bifurcation"


def binarize_fingerprint(
    enhanced: np.ndarray,
    foreground_mask: np.ndarray = None,
    block_size: int = 15,
    c_offset: int = 2,
) -> np.ndarray:
    """
    Converts enhanced grayscale image into a binary ridge image where
    fingerprint ridges are 1 (white) and background/valleys are 0 (black).

    Uses adaptive Gaussian thresholding with inverse output to map dark ridges to 1.
    """
    if len(enhanced.shape) == 3:
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)

    # Adaptive Gaussian thresholding: handles varying illumination across fingerprint
    # Since fingerprint ridges are typically darker than valleys, cv2.THRESH_BINARY_INV
    # makes ridges foreground (255) and valleys background (0).
    binary = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=block_size,
        C=c_offset,
    )

    if foreground_mask is not None:
        binary = cv2.bitwise_and(binary, binary, mask=foreground_mask)

    # Slight morphological opening to remove isolated single-pixel noise specs
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    return binary


def skeletonize_fingerprint(binary: np.ndarray) -> np.ndarray:
    """
    Converts binary ridge image (255=ridge, 0=valley) into a 1-pixel-wide skeleton
    using scikit-image's morphology skeletonize (Zhang-Suen thinning).

    Returns:
        Boolean or uint8 skeleton array (1 where ridge skeleton is present, 0 elsewhere).
    """
    bool_binary = binary > 127
    skeleton = skeletonize(bool_binary)
    return skeleton.astype(np.uint8)


def _get_neighbors_clockwise(skeleton: np.ndarray, y: int, x: int) -> List[int]:
    """
    Returns the 8 1-pixel neighbors of (x, y) in clockwise order starting from top-left:
    P1 P2 P3
    P8  P P4
    P7 P6 P5
    """
    p1 = int(skeleton[y - 1, x - 1] > 0)
    p2 = int(skeleton[y - 1, x] > 0)
    p3 = int(skeleton[y - 1, x + 1] > 0)
    p4 = int(skeleton[y, x + 1] > 0)
    p5 = int(skeleton[y + 1, x + 1] > 0)
    p6 = int(skeleton[y + 1, x] > 0)
    p7 = int(skeleton[y + 1, x - 1] > 0)
    p8 = int(skeleton[y, x - 1] > 0)
    return [p1, p2, p3, p4, p5, p6, p7, p8]


def compute_crossing_number(neighbors: List[int]) -> int:
    """
    Rutovitz Crossing Number:
    CN = 0.5 * sum(|P_{i+1} - P_i|) for i=1..8 with P9 = P1.

    CN = 1: Ridge Ending
    CN = 2: Continuous Ridge
    CN = 3: Bifurcation
    CN > 3: Complex crossover
    """
    n = neighbors + [neighbors[0]]
    cn_sum = sum(abs(n[i + 1] - n[i]) for i in range(8))
    return cn_sum // 2


def _compute_ridge_ending_orientation(skeleton: np.ndarray, y: int, x: int, trace_len: int = 8) -> float:
    """
    Estimates the orientation angle (in radians) of a ridge ending by tracing
    along the skeleton ridge for up to trace_len pixels.
    """
    h, w = skeleton.shape
    visited = {(y, x)}
    curr_y, curr_x = y, x

    for _ in range(trace_len):
        next_point = None
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                ny, nx = curr_y + dy, curr_x + dx
                if 0 <= ny < h and 0 <= nx < w and skeleton[ny, nx] > 0:
                    if (ny, nx) not in visited:
                        next_point = (ny, nx)
                        break
            if next_point:
                break

        if next_point is None:
            break

        visited.add(next_point)
        curr_y, curr_x = next_point

    # Vector pointing outward from ridge ending along the ridge
    angle = math.atan2(curr_y - y, curr_x - x)
    return round(angle, 4)


def _compute_bifurcation_orientation(skeleton: np.ndarray, y: int, x: int, trace_len: int = 6) -> float:
    """
    Estimates the orientation angle for a bifurcation by averaging the initial direction
    of the 3 diverging branches.
    """
    h, w = skeleton.shape
    angles = []

    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and skeleton[ny, nx] > 0:
                angles.append(math.atan2(dy, dx))

    if not angles:
        return 0.0

    # Mean angle via circular statistics
    mean_sin = sum(math.sin(a) for a in angles) / len(angles)
    mean_cos = sum(math.cos(a) for a in angles) / len(angles)
    return round(math.atan2(mean_sin, mean_cos), 4)


def extract_raw_minutiae(skeleton: np.ndarray) -> List[Dict[str, Any]]:
    """
    Extracts candidate minutiae points (ridge endings & bifurcations)
    using the Crossing Number algorithm on the 1-pixel skeleton.
    """
    h, w = skeleton.shape
    minutiae = []

    # Exclude outermost 1-pixel boundary for 3x3 neighbor safety
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if skeleton[y, x] == 0:
                continue

            neighbors = _get_neighbors_clockwise(skeleton, y, x)
            cn = compute_crossing_number(neighbors)

            if cn == 1:
                # Ridge Ending
                orientation = _compute_ridge_ending_orientation(skeleton, y, x)
                minutiae.append({
                    "x": int(x),
                    "y": int(y),
                    "type": TYPE_ENDING,
                    "orientation": orientation,
                })
            elif cn == 3:
                # Bifurcation
                orientation = _compute_bifurcation_orientation(skeleton, y, x)
                minutiae.append({
                    "x": int(x),
                    "y": int(y),
                    "type": TYPE_BIFURCATION,
                    "orientation": orientation,
                })

    return minutiae


def filter_false_minutiae(
    minutiae: List[Dict[str, Any]],
    image_shape: Tuple[int, int],
    foreground_mask: np.ndarray = None,
    border_margin: int = 10,
    min_distance: float = 6.0,
) -> List[Dict[str, Any]]:
    """
    Conservative post-processing to eliminate false minutiae caused by:
    1. Image frame borders (spurious endings where ridges touch image boundary)
    2. Boundary of the foreground segmentation mask
    3. Minutiae clusters too close to each other (e.g. broken skeleton segments or spurs)

    Args:
        minutiae: List of detected candidate minutiae dicts.
        image_shape: (height, width) of the processed image.
        foreground_mask: Binary mask of active fingerprint area.
        border_margin: Pixel distance from image boundary to discard.
        min_distance: Minimum allowable Euclidean distance between two minutiae.

    Returns:
        Filtered list of reliable minutiae.
    """
    h, w = image_shape
    if not minutiae:
        return []

    # 1. Filter boundary minutiae
    valid_after_border = []
    eroded_mask = None
    if foreground_mask is not None:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        eroded_mask = cv2.erode(foreground_mask, kernel)

    for m in minutiae:
        x, y = m["x"], m["y"]
        # Check image margins
        if x < border_margin or x >= w - border_margin or y < border_margin or y >= h - border_margin:
            continue

        # Check foreground mask boundary
        if eroded_mask is not None and eroded_mask[y, x] == 0:
            continue

        valid_after_border.append(m)

    if not valid_after_border:
        return []

    # 2. Filter minutiae that are excessively close to each other (broken ridges or spurs)
    keep = []
    discard = set()
    n = len(valid_after_border)

    for i in range(n):
        if i in discard:
            continue
        m1 = valid_after_border[i]

        for j in range(i + 1, n):
            if j in discard:
                continue
            m2 = valid_after_border[j]
            dist = math.hypot(m1["x"] - m2["x"], m1["y"] - m2["y"])

            if dist < min_distance:
                dtheta = abs((m1["orientation"] - m2["orientation"] + math.pi) % (2.0 * math.pi) - math.pi)
                # If two endings face roughly opposite directions (~pi rad), it's a broken ridge -> discard both
                if m1["type"] == TYPE_ENDING and m2["type"] == TYPE_ENDING and abs(dtheta - math.pi) < 0.65:
                    discard.add(i)
                    discard.add(j)
                    break
                else:
                    # Otherwise keep the first and drop the redundant neighbor
                    discard.add(j)

        if i not in discard:
            keep.append(m1)

    return keep


def extract_fingerprint_minutiae(
    enhanced: np.ndarray,
    foreground_mask: np.ndarray = None,
) -> Tuple[np.ndarray, np.ndarray, List[Dict[str, Any]]]:
    """
    Complete extraction pipeline:
    1. Binarize enhanced fingerprint
    2. Skeletonize to 1-pixel width
    3. Extract Crossing Number minutiae
    4. Filter false minutiae

    Returns:
        (binary_ridge_image, skeleton_image, filtered_minutiae_list)
    """
    binary = binarize_fingerprint(enhanced, foreground_mask=foreground_mask)
    skeleton = skeletonize_fingerprint(binary)
    raw_minutiae = extract_raw_minutiae(skeleton)
    filtered = filter_false_minutiae(
        raw_minutiae,
        image_shape=skeleton.shape,
        foreground_mask=foreground_mask,
    )

    return binary, skeleton, filtered
