"""
DeceptionLens — Fingerprint Algorithm Evaluation Benchmark
==========================================================
Evaluates verification performance on FVC2002 dataset impressions.
Calculates Genuine/Impostor score distributions, False Acceptance Rate (FAR),
False Rejection Rate (FRR), and verification accuracy at a chosen threshold.

Usage:
    python -m evaluation.evaluate_fingerprint [--dataset-dir PATH] [--threshold 45.0]
"""

import argparse
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Add backend directory to sys.path so imports work seamlessly
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fingerprint.service import compare_fingerprints
from fingerprint.matching import DEFAULT_MATCH_THRESHOLD


def discover_fingerprint_images(dataset_path: Path) -> Dict[str, List[Path]]:
    """
    Scans dataset directory and groups impressions by finger identifier.
    Supports FVC naming conventions (e.g. 101_1.tif, 101_2.png, finger1_imp1.bmp).
    """
    valid_exts = {".tif", ".tiff", ".png", ".bmp", ".jpg", ".jpeg"}
    finger_groups: Dict[str, List[Path]] = defaultdict(list)

    if not dataset_path.exists():
        return finger_groups

    # Walk recursively
    for file_path in dataset_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in valid_exts:
            stem = file_path.stem

            # 1. SOCOFing convention: <ID>__<Gender>_<Hand>_<Finger>_finger[_<Alteration>]
            socofing_match = re.match(
                r"^(\d+__[MF]_(?:Left|Right)_[a-zA-Z]+_finger)(?:.*)?$",
                stem,
                re.IGNORECASE,
            )
            if socofing_match:
                finger_id = socofing_match.group(1).lower()
            else:
                # 2. FVC convention: 101_1, finger1_imp2
                match = re.match(r"^(\d+|[a-zA-Z]+_\d+)[_-](\d+)$", stem)
                if match:
                    finger_id = match.group(1)
                else:
                    # Default grouping by filename prefix
                    parts = stem.split("_")
                    finger_id = parts[0] if len(parts) > 1 else stem

            finger_groups[finger_id].append(file_path)

    # Sort files within each finger group
    for k in finger_groups:
        finger_groups[k].sort()

    return finger_groups


def run_evaluation(
    dataset_dir: str,
    threshold: float = DEFAULT_MATCH_THRESHOLD,
    max_genuine_pairs: int = 50,
    max_impostor_pairs: int = 50,
) -> Dict[str, Any]:
    """
    Executes automated benchmark evaluation.
    """
    target_path = Path(dataset_dir)
    if not target_path.exists():
        # Fallback to bundled sample pairs
        socofing_sample = BACKEND_DIR / "datasets" / "fingerprints" / "socofing" / "sample_pairs"
        fvc_sample = BACKEND_DIR / "datasets" / "fingerprints" / "fvc2002" / "sample_pairs"
        if "socofing" in str(dataset_dir).lower() and socofing_sample.exists():
            print(f"Target path '{dataset_dir}' not found. Falling back to '{socofing_sample}'.")
            target_path = socofing_sample
        elif fvc_sample.exists():
            print(f"Target path '{dataset_dir}' not found. Falling back to '{fvc_sample}'.")
            target_path = fvc_sample
        elif socofing_sample.exists():
            print(f"Target path '{dataset_dir}' not found. Falling back to '{socofing_sample}'.")
            target_path = socofing_sample
        else:
            raise FileNotFoundError(f"Dataset directory '{dataset_dir}' not found.")

    finger_groups = discover_fingerprint_images(target_path)
    if not finger_groups:
        raise ValueError(f"No valid fingerprint images found in '{target_path}'.")

    print(f"Discovered {len(finger_groups)} distinct fingers with total {sum(len(v) for v in finger_groups.values())} impressions.")

    # 1. Generate Genuine Pairs (same finger, different impressions)
    genuine_pairs: List[Tuple[Path, Path]] = []
    for finger_id, impressions in finger_groups.items():
        if len(impressions) >= 2:
            for i in range(len(impressions)):
                for j in range(i + 1, len(impressions)):
                    genuine_pairs.append((impressions[i], impressions[j]))
                    if len(genuine_pairs) >= max_genuine_pairs:
                        break
            if len(genuine_pairs) >= max_genuine_pairs:
                break

    # 2. Generate Impostor Pairs (different fingers)
    impostor_pairs: List[Tuple[Path, Path]] = []
    finger_ids = list(finger_groups.keys())
    for i in range(len(finger_ids)):
        for j in range(i + 1, len(finger_ids)):
            f1, f2 = finger_ids[i], finger_ids[j]
            # Pair first impression of f1 with first impression of f2
            impostor_pairs.append((finger_groups[f1][0], finger_groups[f2][0]))
            if len(impostor_pairs) >= max_impostor_pairs:
                break
        if len(impostor_pairs) >= max_impostor_pairs:
            break

    print(f"\nEvaluating {len(genuine_pairs)} Genuine pairs and {len(impostor_pairs)} Impostor pairs...")
    print(f"Decision Threshold: {threshold:.1f}%\n" + "-" * 60)

    # 3. Evaluate Genuine Pairs
    genuine_scores = []
    false_rejections = 0
    for idx, (p1, p2) in enumerate(genuine_pairs, 1):
        try:
            res = compare_fingerprints(str(p1), str(p2), threshold=threshold, generate_visualizations=False)
            score = res["similarity_score"]
            genuine_scores.append(score)
            if score < threshold:
                false_rejections += 1
            print(f" [GENUINE  {idx:02d}] {p1.name} vs {p2.name} -> Score: {score:5.2f}% ({res['result']})")
        except Exception as e:
            print(f" [GENUINE  {idx:02d}] {p1.name} vs {p2.name} -> ERROR: {e}")

    # 4. Evaluate Impostor Pairs
    impostor_scores = []
    false_acceptances = 0
    for idx, (p1, p2) in enumerate(impostor_pairs, 1):
        try:
            res = compare_fingerprints(str(p1), str(p2), threshold=threshold, generate_visualizations=False)
            score = res["similarity_score"]
            impostor_scores.append(score)
            if score >= threshold:
                false_acceptances += 1
            print(f" [IMPOSTOR {idx:02d}] {p1.name} vs {p2.name} -> Score: {score:5.2f}% ({res['result']})")
        except Exception as e:
            print(f" [IMPOSTOR {idx:02d}] {p1.name} vs {p2.name} -> ERROR: {e}")

    n_gen = len(genuine_scores)
    n_imp = len(impostor_scores)

    avg_gen = sum(genuine_scores) / n_gen if n_gen > 0 else 0.0
    avg_imp = sum(impostor_scores) / n_imp if n_imp > 0 else 0.0

    frr = (false_rejections / n_gen * 100.0) if n_gen > 0 else 0.0
    far = (false_acceptances / n_imp * 100.0) if n_imp > 0 else 0.0

    correct_decisions = (n_gen - false_rejections) + (n_imp - false_acceptances)
    total_comparisons = n_gen + n_imp
    accuracy = (correct_decisions / total_comparisons * 100.0) if total_comparisons > 0 else 0.0

    print("\n" + "=" * 60)
    print("           DECEPTIONLENS FINGERPRINT BENCHMARK REPORT")
    print("=" * 60)
    print(f"Dataset Location            : {target_path}")
    print(f"Genuine Comparisons         : {n_gen}")
    print(f"Impostor Comparisons        : {n_imp}")
    print(f"Decision Threshold          : {threshold:.1f}%")
    print("-" * 60)
    print(f"Average Genuine Similarity  : {avg_gen:.2f}%")
    print(f"Average Impostor Similarity : {avg_imp:.2f}%")
    print(f"Separation Margin           : {(avg_gen - avg_imp):.2f}%")
    print("-" * 60)
    print(f"False Acceptance Rate (FAR) : {far:.2f}% ({false_acceptances}/{n_imp})")
    print(f"False Rejection Rate (FRR)  : {frr:.2f}% ({false_rejections}/{n_gen})")
    print(f"Overall Accuracy            : {accuracy:.2f}%")
    print("=" * 60)
    print("Forensic Interpretation Note:")
    print("Results are indicative algorithmic comparisons for academic evaluation.")
    print("In legal and forensic jurisprudence, minutiae matching is used as an expert aid")
    print("and not as automated conclusive proof of identity.")
    print("=" * 60 + "\n")

    return {
        "genuine_count": n_gen,
        "impostor_count": n_imp,
        "avg_genuine_similarity": round(avg_gen, 2),
        "avg_impostor_similarity": round(avg_imp, 2),
        "threshold": threshold,
        "far": round(far, 2),
        "frr": round(frr, 2),
        "accuracy": round(accuracy, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="DeceptionLens Fingerprint Verification Benchmark (FVC2002 & SOCOfing)")
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default=str(BACKEND_DIR / "datasets" / "fingerprints" / "socofing"),
        help="Path to directory containing SOCOfing or FVC2002 images or sample pairs",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_MATCH_THRESHOLD,
        help="Decision threshold percentage (default: 45.0)",
    )
    parser.add_argument(
        "--max-pairs",
        type=int,
        default=25,
        help="Maximum genuine and impostor pairs to test (default: 25)",
    )
    args = parser.parse_args()
    run_evaluation(
        dataset_dir=args.dataset_dir,
        threshold=args.threshold,
        max_genuine_pairs=args.max_pairs,
        max_impostor_pairs=args.max_pairs,
    )


if __name__ == "__main__":
    main()
