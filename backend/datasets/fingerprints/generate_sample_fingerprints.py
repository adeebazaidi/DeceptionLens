"""
DeceptionLens — Synthetic Demonstration Fingerprint Generator
=============================================================
Generates authentic-looking benchmark fingerprint impression pairs
for automated testing, demo verification, and offline college viva demonstrations.
"""

import math
from pathlib import Path
import cv2
import numpy as np


def generate_fingerprint_impression(
    finger_id: int = 101,
    impression_id: int = 1,
    size: tuple = (380, 300),
    rotation_deg: float = 0.0,
    shift_xy: tuple = (0, 0),
    noise_level: float = 8.0,
) -> np.ndarray:
    """
    Synthesizes a realistic fingerprint impression with core loop pattern,
    natural ridge flow frequencies, ridge endings, and bifurcations.
    """
    h, w = size
    canvas = np.full((h, w), 245.0, dtype=np.float32)

    cx = w / 2.0 + (finger_id % 7 - 3) * 6 + shift_xy[0]
    cy = h / 2.0 + (finger_id % 5 - 2) * 8 + shift_xy[1]

    rad = math.radians(rotation_deg)
    cos_r = math.cos(rad)
    sin_r = math.sin(rad)

    # Ridge frequency (~8 pixels per ridge-valley cycle)
    wavelength = 8.5
    k = 2.0 * math.pi / wavelength

    # Elliptical mask defining finger outline
    y_grid, x_grid = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = x_grid - cx
    dy = y_grid - cy

    # Rotate coordinates
    rx = dx * cos_r - dy * sin_r
    ry = dx * sin_r + dy * cos_r

    # Radial distance from core loop
    r = np.sqrt(rx ** 2 + (ry * 0.85) ** 2)

    # Angular component for loop/whorl ridge flow
    theta = np.arctan2(ry, rx)

    # Phase function: combines concentric rings + spiral core flow
    phase = r * (2.0 * math.pi / wavelength) + 1.2 * np.sin(theta * 2.0)

    # Ridge modulation: cosine wave creating ridges and valleys
    ridges = np.cos(phase)

    # Introduce pseudo-random minutiae perturbations seeded deterministically by finger_id
    rng = np.random.RandomState(finger_id * 100)
    num_perturbations = 18
    for _ in range(num_perturbations):
        px = rng.uniform(-w * 0.35, w * 0.35)
        py = rng.uniform(-h * 0.35, h * 0.35)
        pr = np.hypot(rx - px, ry - py)
        # Ridge break / bifurcation phase dislocation
        ridges += 0.8 * np.exp(-(pr ** 2) / (2.0 * (12.0 ** 2))) * np.sin(phase)

    # Map cosine [-1, 1] to grayscale [30, 230] (dark ridges, light valleys)
    img = 135.0 - 95.0 * ridges

    # Finger boundary mask
    finger_mask = ((rx / (w * 0.42)) ** 2 + (ry / (h * 0.45)) ** 2) <= 1.0
    img[~finger_mask] = 250.0

    # Impression-specific sensor noise
    imp_rng = np.random.RandomState(finger_id * 1000 + impression_id)
    noise = imp_rng.normal(0, noise_level, (h, w))
    img += noise

    # Subtle pressure variation
    pressure_gradient = np.exp(-((rx / (w * 0.5)) ** 2 + (ry / (h * 0.5)) ** 2) * 0.6)
    img = img * pressure_gradient + 245.0 * (1.0 - pressure_gradient)

    img = np.clip(img, 0, 255).astype(np.uint8)
    return img


def generate_benchmark_samples(output_dir: str = None) -> list:
    """
    Generates genuine and impostor demonstration pairs and writes them to disk.
    """
    if output_dir is None:
        output_dir = str(Path(__file__).parent / "fvc2002" / "sample_pairs")

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    generated_files = []

    # Finger 101: Impressions 1 and 2 (Genuine Pair)
    img_101_1 = generate_fingerprint_impression(101, 1, rotation_deg=0.0, shift_xy=(0, 0))
    p1 = str(out_path / "101_1.png")
    cv2.imwrite(p1, img_101_1)
    generated_files.append(p1)

    img_101_2 = generate_fingerprint_impression(101, 2, rotation_deg=3.5, shift_xy=(4, -3))
    p2 = str(out_path / "101_2.png")
    cv2.imwrite(p2, img_101_2)
    generated_files.append(p2)

    # Finger 102: Impressions 1 and 2 (Impostor to 101, Genuine to each other)
    img_102_1 = generate_fingerprint_impression(102, 1, rotation_deg=0.0, shift_xy=(0, 0))
    p3 = str(out_path / "102_1.png")
    cv2.imwrite(p3, img_102_1)
    generated_files.append(p3)

    img_102_2 = generate_fingerprint_impression(102, 2, rotation_deg=-2.5, shift_xy=(-3, 4))
    p4 = str(out_path / "102_2.png")
    cv2.imwrite(p4, img_102_2)
    generated_files.append(p4)

    return generated_files


if __name__ == "__main__":
    files = generate_benchmark_samples()
    print(f"Successfully generated {len(files)} benchmark fingerprint samples in {Path(files[0]).parent}")
