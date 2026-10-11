"""
DeceptionLens — Fingerprint Comparison Service
==============================================
Orchestrates end-to-end forensic comparison pipeline:
loading, preprocessing, ridge enhancement, skeletonization,
minutiae extraction, geometric matching, and visualization rendering.
"""

from typing import Dict, Any
import time
import uuid
from pathlib import Path

from modules.fingerprint.preprocessing import preprocess_fingerprint
from modules.fingerprint.enhancement import enhance_ridges
from modules.fingerprint.minutiae import extract_fingerprint_minutiae, TYPE_ENDING, TYPE_BIFURCATION
from modules.fingerprint.matching import match_minutiae_sets, DEFAULT_MATCH_THRESHOLD
from modules.fingerprint.visualization import (
    render_minutiae_overlay,
    render_skeleton_image,
    render_comparison_canvas,
    save_image_artifact,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
OUTPUTS_DIR = BASE_DIR / "outputs" / "fingerprint"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

MIN_REQUIRED_MINUTIAE = 5


def _unique_id() -> str:
    return uuid.uuid4().hex[:12]


def process_single_fingerprint(source: Any) -> Dict[str, Any]:
    """
    Runs preprocessing, enhancement, skeletonization, and minutiae extraction
    for an individual fingerprint impression.

    Returns:
        Dictionary containing all processed artifacts and minutiae points.
    """
    raw_img, preprocessed_gray, meta = preprocess_fingerprint(source)
    enhanced, mask = enhance_ridges(preprocessed_gray)
    binary, skeleton, minutiae = extract_fingerprint_minutiae(enhanced, foreground_mask=mask)

    endings_count = sum(1 for m in minutiae if m["type"] == TYPE_ENDING)
    bifurcations_count = sum(1 for m in minutiae if m["type"] == TYPE_BIFURCATION)

    return {
        "raw_image": raw_img,
        "preprocessed": preprocessed_gray,
        "enhanced": enhanced,
        "mask": mask,
        "binary": binary,
        "skeleton": skeleton,
        "minutiae": minutiae,
        "meta": meta,
        "endings_count": endings_count,
        "bifurcations_count": bifurcations_count,
        "total_minutiae": len(minutiae),
    }


def compare_fingerprints(
    ref_source: Any,
    quest_source: Any,
    threshold: float = DEFAULT_MATCH_THRESHOLD,
    generate_visualizations: bool = True,
) -> Dict[str, Any]:
    """
    End-to-end fingerprint verification comparison:
    1. Preprocesses and extracts minutiae from reference fingerprint
    2. Preprocesses and extracts minutiae from questioned fingerprint
    3. Validates minimum feature thresholds
    4. Computes geometric alignment and minutiae pairing
    5. Saves visual forensic artifacts
    6. Returns structured response with similarity score and decision

    Args:
        ref_source: File path, bytes, or numpy array for reference fingerprint.
        quest_source: File path, bytes, or numpy array for questioned fingerprint.
        threshold: Decision threshold percentage (default 45.0%).
        generate_visualizations: Whether to render and save image artifacts.

    Raises:
        ValueError: If images cannot be decoded or insufficient features are detected.
    """
    start_time = time.perf_counter()
    uid = _unique_id()

    # Step 1: Process reference fingerprint
    ref_data = process_single_fingerprint(ref_source)
    if ref_data["total_minutiae"] < MIN_REQUIRED_MINUTIAE:
        raise ValueError(
            f"Reference fingerprint has insufficient distinguishable features "
            f"({ref_data['total_minutiae']} detected, minimum required is {MIN_REQUIRED_MINUTIAE}). "
            f"Please provide a clearer reference impression."
        )

    # Step 2: Process questioned fingerprint
    quest_data = process_single_fingerprint(quest_source)
    if quest_data["total_minutiae"] < MIN_REQUIRED_MINUTIAE:
        raise ValueError(
            f"Questioned fingerprint has insufficient distinguishable features "
            f"({quest_data['total_minutiae']} detected, minimum required is {MIN_REQUIRED_MINUTIAE}). "
            f"Please provide a clearer questioned impression."
        )

    # Step 3: Minutiae matching
    match_result = match_minutiae_sets(
        ref_data["minutiae"],
        quest_data["minutiae"],
        threshold=threshold,
    )

    elapsed_time = round(time.perf_counter() - start_time, 3)

    # Step 4: Render and persist visual artifacts
    viz_urls: Dict[str, str] = {}
    if generate_visualizations:
        # Reference visualizations
        ref_enh_path = str(OUTPUTS_DIR / f"{uid}_ref_enhanced.png")
        save_image_artifact(ref_data["enhanced"], ref_enh_path)
        viz_urls["reference_enhanced"] = f"/outputs/fingerprint/{uid}_ref_enhanced.png"

        ref_skel_path = str(OUTPUTS_DIR / f"{uid}_ref_skeleton.png")
        save_image_artifact(render_skeleton_image(ref_data["skeleton"]), ref_skel_path)
        viz_urls["reference_skeleton"] = f"/outputs/fingerprint/{uid}_ref_skeleton.png"

        ref_min_path = str(OUTPUTS_DIR / f"{uid}_ref_minutiae.png")
        ref_min_img = render_minutiae_overlay(ref_data["preprocessed"], ref_data["minutiae"], ref_data["skeleton"])
        save_image_artifact(ref_min_img, ref_min_path)
        viz_urls["reference_minutiae"] = f"/outputs/fingerprint/{uid}_ref_minutiae.png"

        # Questioned visualizations
        quest_enh_path = str(OUTPUTS_DIR / f"{uid}_quest_enhanced.png")
        save_image_artifact(quest_data["enhanced"], quest_enh_path)
        viz_urls["questioned_enhanced"] = f"/outputs/fingerprint/{uid}_quest_enhanced.png"

        quest_skel_path = str(OUTPUTS_DIR / f"{uid}_quest_skeleton.png")
        save_image_artifact(render_skeleton_image(quest_data["skeleton"]), quest_skel_path)
        viz_urls["questioned_skeleton"] = f"/outputs/fingerprint/{uid}_quest_skeleton.png"

        quest_min_path = str(OUTPUTS_DIR / f"{uid}_quest_minutiae.png")
        quest_min_img = render_minutiae_overlay(quest_data["preprocessed"], quest_data["minutiae"], quest_data["skeleton"])
        save_image_artifact(quest_min_img, quest_min_path)
        viz_urls["questioned_minutiae"] = f"/outputs/fingerprint/{uid}_quest_minutiae.png"

        # Side-by-side comparison map
        comp_path = str(OUTPUTS_DIR / f"{uid}_comparison.png")
        comp_img = render_comparison_canvas(
            ref_data["preprocessed"],
            ref_data["minutiae"],
            quest_data["preprocessed"],
            quest_data["minutiae"],
            match_result["matched_pairs"],
            match_result["similarity_score"],
            match_result["result"],
        )
        save_image_artifact(comp_img, comp_path)
        viz_urls["comparison"] = f"/outputs/fingerprint/{uid}_comparison.png"

    return {
        "success": True,
        "result": match_result["result"],
        "similarity_score": match_result["similarity_score"],
        "reference_minutiae": match_result["reference_minutiae"],
        "questioned_minutiae": match_result["questioned_minutiae"],
        "matched_minutiae": match_result["matched_minutiae"],
        "threshold": threshold,
        "processing_time": elapsed_time,
        "details": {
            "reference_endings": ref_data["endings_count"],
            "reference_bifurcations": ref_data["bifurcations_count"],
            "questioned_endings": quest_data["endings_count"],
            "questioned_bifurcations": quest_data["bifurcations_count"],
            "alignment": match_result.get("best_alignment"),
            "matched_count": len(match_result["matched_pairs"]),
        },
        "visualizations": viz_urls,
    }
