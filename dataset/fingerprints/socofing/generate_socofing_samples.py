"""
DeceptionLens — SOCOFing Synthetic Demonstration Sample Generator
==================================================================
Generates realistic SOCOFing benchmark impressions (Real and Altered: CR, Obl, Zcut)
matching SOCOFing 96x103 8-bit BMP standards for instant offline demonstration.
"""

import math
from pathlib import Path
import cv2
import numpy as np


def generate_socofing_impression(
    subject_id: int = 1,
    gender: str = "M",
    hand: str = "Left",
    finger: str = "index",
    alteration: str = None,  # None (Real), 'CR' (Central Rotation), 'Obl' (Obliteration), 'Zcut' (Z-Cut)
    size: tuple = (103, 96),  # (height, width)
) -> np.ndarray:
    """
    Generates a realistic 96x103 biometric impression adhering to SOCOFing standards.
    """
    h, w = size
    # Seed generator deterministically per subject/finger
    seed = (subject_id * 1000) + (10 if hand == "Left" else 20) + hash(finger) % 100
    rng = np.random.RandomState(abs(seed) % (2**31 - 1))

    cx = w / 2.0 + rng.uniform(-3, 3)
    cy = h / 2.0 + rng.uniform(-4, 4)

    y_grid, x_grid = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = x_grid - cx
    dy = y_grid - cy

    # Radial and angular components
    r = np.sqrt(dx**2 + (dy * 0.9)**2)
    theta = np.arctan2(dy, dx)

    # Ridge wavelength ~5-6 pixels for compact 96x103 sensor
    wavelength = 5.2
    phase = r * (2.0 * math.pi / wavelength) + 1.2 * np.sin(theta * 2.0)

    # Add pseudo-random minutiae dislocations (ridge breaks & bifurcations)
    ridges = np.cos(phase)
    for _ in range(12):
        px = rng.uniform(-w * 0.35, w * 0.35)
        py = rng.uniform(-h * 0.35, h * 0.35)
        pr = np.hypot(dx - px, dy - py)
        ridges += 0.7 * np.exp(-(pr**2) / (2.0 * (6.0**2))) * np.sin(phase)

    # Grayscale image [20, 235]
    img = 130.0 - 90.0 * ridges

    # Finger oval boundary mask
    finger_mask = ((dx / (w * 0.44))**2 + (dy / (h * 0.46))**2) <= 1.0
    img[~finger_mask] = 245.0

    # Sensor noise
    noise = rng.normal(0, 5.0, (h, w))
    img += noise
    img = np.clip(img, 0, 255).astype(np.uint8)

    # Apply synthetic alterations matching SOCOFing benchmark types
    if alteration == "CR":
        # Central Rotation (CR): Rotates central circular core
        core_r = min(w, h) * 0.28
        core_mask = (dx**2 + dy**2) <= core_r**2
        center = (int(cx), int(cy))
        rot_mat = cv2.getRotationMatrix2D(center, 22.0, 1.0)
        rotated = cv2.warpAffine(img, rot_mat, (w, h), borderMode=cv2.BORDER_REFLECT)
        img[core_mask] = rotated[core_mask]

    elif alteration == "Obl":
        # Obliteration (Obl): Erases / scratches across ridge sections
        scratch_y = int(cy + rng.uniform(-10, 10))
        cv2.line(img, (int(w * 0.15), scratch_y), (int(w * 0.85), scratch_y + 4), (220, 220, 220), 4)
        cv2.line(img, (int(w * 0.2), scratch_y + 8), (int(w * 0.75), scratch_y + 12), (230, 230, 230), 3)

    elif alteration == "Zcut":
        # Z-Cut: Diagonal cut displacement simulating surgical or trauma distortion
        for i in range(int(h * 0.35), int(h * 0.65)):
            shift = int(3 * np.sin((i - h * 0.35) / 5.0))
            if 0 <= i < h:
                img[i, :] = np.roll(img[i, :], shift)
        cv2.line(img, (int(w * 0.2), int(h * 0.35)), (int(w * 0.8), int(h * 0.65)), (210, 210, 210), 2)

    return img


def generate_socofing_samples(output_dir: str = None) -> list:
    """
    Generates demonstration SOCOFing samples (Real and Altered) in standard BMP format.
    """
    if output_dir is None:
        output_dir = str(Path(__file__).parent / "sample_pairs")

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    samples = [
        # Subject 1 - Left Index Finger (Real + 3 Alterations)
        (1, "M", "Left", "index", None, "1__M_Left_index_finger.BMP"),
        (1, "M", "Left", "index", "CR", "1__M_Left_index_finger_CR.BMP"),
        (1, "M", "Left", "index", "Obl", "1__M_Left_index_finger_Obl.BMP"),
        (1, "M", "Left", "index", "Zcut", "1__M_Left_index_finger_Zcut.BMP"),

        # Subject 2 - Left Index Finger (Impostor to Subject 1)
        (2, "M", "Left", "index", None, "2__M_Left_index_finger.BMP"),
        (2, "M", "Left", "index", "CR", "2__M_Left_index_finger_CR.BMP"),

        # Subject 3 - Right Thumb (Female subject)
        (3, "F", "Right", "thumb", None, "3__F_Right_thumb_finger.BMP"),
        (3, "F", "Right", "thumb", "CR", "3__F_Right_thumb_finger_CR.BMP"),
    ]

    generated_files = []
    for sub_id, gender, hand, finger, alt, filename in samples:
        img = generate_socofing_impression(sub_id, gender, hand, finger, alt)
        filepath = out_path / filename
        cv2.imwrite(str(filepath), img)
        generated_files.append(str(filepath))

    return generated_files


if __name__ == "__main__":
    files = generate_socofing_samples()
    print(f"Generated {len(files)} SOCOFing benchmark impressions in {Path(files[0]).parent}")
