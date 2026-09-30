"""
DeceptionLens — Fingerprint Minutiae Matching Module
====================================================
Performs geometric alignment (translation and rotation invariance),
spatial and angular tolerance pairing, similarity score computation,
and forensic verification decision.
"""

from typing import List, Dict, Any, Tuple, Optional
import math
import os
import numpy as np


# Configurable default decision threshold (percentage)
# Configurable via environment variable MATCH_THRESHOLD
DEFAULT_MATCH_THRESHOLD = float(os.getenv("FINGERPRINT_MATCH_THRESHOLD", "45.0"))

# Spatial and angular tolerances for minutiae pairing
DEFAULT_DISTANCE_TOLERANCE = 18.0  # pixels
DEFAULT_ANGLE_TOLERANCE = 0.65     # radians (~37 degrees)


def _angle_diff(a1: float, a2: float) -> float:
    """Computes minimal absolute difference between two angles in radians."""
    diff = (a1 - a2 + math.pi) % (2.0 * math.pi) - math.pi
    return abs(diff)


def match_minutiae_sets(
    ref_minutiae: List[Dict[str, Any]],
    quest_minutiae: List[Dict[str, Any]],
    dist_tol: float = DEFAULT_DISTANCE_TOLERANCE,
    angle_tol: float = DEFAULT_ANGLE_TOLERANCE,
    threshold: float = DEFAULT_MATCH_THRESHOLD,
) -> Dict[str, Any]:
    """
    Performs rotation and translation invariant minutiae matching using
    vectorized NumPy geometric transformation and spatial pairing.

    Returns:
        Structured dictionary with similarity score, decision, and matched pairs.
    """
    n_ref = len(ref_minutiae)
    n_quest = len(quest_minutiae)

    if n_ref == 0 or n_quest == 0:
        return {
            "result": "Likely Non-Match",
            "similarity_score": 0.0,
            "reference_minutiae": n_ref,
            "questioned_minutiae": n_quest,
            "matched_minutiae": 0,
            "threshold": threshold,
            "matched_pairs": [],
            "best_alignment": None,
        }

    # Extract NumPy coordinate and orientation arrays for fast vectorized operations
    r_pts = np.array([[m["x"], m["y"]] for m in ref_minutiae], dtype=np.float32)
    r_ori = np.array([m["orientation"] for m in ref_minutiae], dtype=np.float32)
    r_type = np.array([1 if m["type"] == "ending" else 2 for m in ref_minutiae], dtype=np.int32)

    q_pts = np.array([[m["x"], m["y"]] for m in quest_minutiae], dtype=np.float32)
    q_ori = np.array([m["orientation"] for m in quest_minutiae], dtype=np.float32)
    q_type = np.array([1 if m["type"] == "ending" else 2 for m in quest_minutiae], dtype=np.int32)

    best_matched_pairs: List[Dict[str, Any]] = []
    best_alignment: Optional[Dict[str, Any]] = None
    max_matches = 0

    # Limit candidate base pairs to compatible types from core impressions
    ref_candidates = list(range(min(n_ref, 35)))
    quest_candidates = list(range(min(n_quest, 35)))

    dist_tol_sq = dist_tol ** 2
    diff_type_tol_sq = (dist_tol * 0.7) ** 2

    for r_idx in ref_candidates:
        r_x0, r_y0 = r_pts[r_idx]
        r_o0 = r_ori[r_idx]
        r_t0 = r_type[r_idx]

        # Shift reference coordinates to origin at base point
        dx = r_pts[:, 0] - r_x0
        dy = r_pts[:, 1] - r_y0

        for q_idx in quest_candidates:
            # Candidate pairs must share the same minutia type (ending-ending or bifurcation-bifurcation)
            if r_t0 != q_type[q_idx]:
                continue

            q_x0, q_y0 = q_pts[q_idx]
            dtheta = q_ori[q_idx] - r_o0
            cos_t = math.cos(dtheta)
            sin_t = math.sin(dtheta)

            # Rigid rotation and translation of all reference points
            tx = q_x0 + (dx * cos_t - dy * sin_t)
            ty = q_y0 + (dx * sin_t + dy * cos_t)
            to = r_ori + dtheta

            # Vectorized pairwise spatial distances to questioned points: shape (N_ref, N_quest)
            spatial_dist_sq = (tx[:, None] - q_pts[None, :, 0]) ** 2 + (ty[:, None] - q_pts[None, :, 1]) ** 2

            # Vectorized angular difference
            ang_diff = np.abs((to[:, None] - q_ori[None, :] + math.pi) % (2.0 * math.pi) - math.pi)

            # Compatibility mask
            type_match_mat = (r_type[:, None] == q_type[None, :])
            valid_mask = (ang_diff <= angle_tol) & (
                (type_match_mat & (spatial_dist_sq <= dist_tol_sq))
                | (~type_match_mat & (spatial_dist_sq <= diff_type_tol_sq))
            )

            # Quick count check: max possible inliers
            possible_inliers = int(np.sum(np.any(valid_mask, axis=1)))
            if possible_inliers <= max_matches:
                continue

            # Greedy 1-to-1 bipartite pairing
            matched_this_trial: List[Dict[str, Any]] = []
            used_quest = set()

            # Process candidates sorted by spatial distance
            for i in range(n_ref):
                row_valid = valid_mask[i]
                if not np.any(row_valid):
                    continue

                best_j = -1
                best_d_sq = float("inf")

                for j in np.where(row_valid)[0]:
                    if j in used_quest:
                        continue
                    d_sq = spatial_dist_sq[i, j]
                    if d_sq < best_d_sq:
                        best_d_sq = d_sq
                        best_j = j

                if best_j != -1:
                    used_quest.add(best_j)
                    matched_this_trial.append({
                        "ref_index": int(i),
                        "quest_index": int(best_j),
                        "distance": round(float(math.sqrt(best_d_sq)), 2),
                        "ref_point": (int(ref_minutiae[i]["x"]), int(ref_minutiae[i]["y"])),
                        "quest_point": (int(quest_minutiae[best_j]["x"]), int(quest_minutiae[best_j]["y"])),
                        "type": ref_minutiae[i]["type"],
                    })

            if len(matched_this_trial) > max_matches:
                max_matches = len(matched_this_trial)
                best_matched_pairs = matched_this_trial
                best_alignment = {
                    "base_ref_idx": int(r_idx),
                    "base_quest_idx": int(q_idx),
                    "rotation_degrees": round(math.degrees(dtheta), 2),
                    "translation_x": round(float(q_x0 - r_x0), 2),
                    "translation_y": round(float(q_y0 - r_y0), 2),
                }

    # Similarity score calculation:
    # 1. Sørensen-Dice coefficient: (2 * matches) / (N_ref + N_quest)
    # 2. Overlap coefficient: matches / min(N_ref, N_quest)
    dice_score = (2.0 * max_matches) / float(n_ref + n_quest)
    overlap_score = max_matches / float(min(n_ref, n_quest))

    # Balanced combined score: 70% Dice + 30% Overlap
    combined_score = (0.70 * dice_score + 0.30 * overlap_score) * 100.0
    combined_score = round(min(100.0, max(0.0, combined_score)), 2)

    decision = "Likely Match" if combined_score >= threshold else "Likely Non-Match"

    return {
        "result": decision,
        "similarity_score": combined_score,
        "reference_minutiae": n_ref,
        "questioned_minutiae": n_quest,
        "matched_minutiae": max_matches,
        "threshold": threshold,
        "matched_pairs": best_matched_pairs,
        "best_alignment": best_alignment,
    }
