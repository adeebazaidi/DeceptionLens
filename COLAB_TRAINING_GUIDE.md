# 🎓 DeceptionLens — Image Forgery Detection Model Training Guide (Google Colab)

This guide walks you through training the **Random Forest Image Forgery Detection Model** for **DeceptionLens** using Google Colab's cloud resources and the **CASIA v2 dataset**.

By training on Google Colab, you avoid downloading gigabytes of image data to your local machine. The output model (`forgery_model.joblib`) and feature schema (`feature_names.json`) will be exported and placed directly into `backend/ml/models/` for inference in your DeceptionLens API.

---

## 📋 Overview of the Forensic Pipeline

The trained model uses **17 handcrafted forensic features** extracted across four forensic disciplines:

| Domain | Features (17 Total) | Purpose |
| :--- | :--- | :--- |
| **Entropy Analysis** | `entropy_global`, `entropy_mean_local`, `entropy_std_local`, `entropy_min_local`, `entropy_max_local`, `entropy_anomaly_score` | Measures information density and local statistical inconsistencies across 8×8 grids. |
| **Error Level Analysis (ELA)** | `ela_mean`, `ela_std`, `ela_max` | Detects compression rate discrepancies by re-saving at 90% quality and scaling difference by 10x. |
| **Noise Residual Analysis** | `noise_mean`, `noise_std`, `noise_max` | Estimates high-frequency sensor noise variance using Gaussian blur subtraction. |
| **GLCM Texture Analysis** | `texture_contrast`, `texture_dissimilarity`, `texture_homogeneity`, `texture_energy`, `texture_correlation` | Analyzes Gray-Level Co-occurrence Matrix (64 quantized levels, 4 angles) for texture irregularities. |

---

## 🔑 Step 1: Get Your Kaggle API Token (`kaggle.json`)

1. Go to [kaggle.com](https://www.kaggle.com/) and log in (or create an account).
2. Click on your profile picture in the top-right corner and select **Settings** (or go to `https://www.kaggle.com/settings`).
3. Scroll down to the **API** section.
4. Click **Create New Token**.
5. A file named `kaggle.json` will be automatically downloaded to your computer. This file contains your Kaggle username and API key.

---

## 🌐 Step 2: Open Google Colab & Upload `kaggle.json`

1. Open a new notebook at [colab.research.google.com](https://colab.research.google.com/).
2. In Colab, create a new code cell and run the following code to upload your `kaggle.json`:

```python
from google.colab import files
import os

# Upload kaggle.json from your local machine
print("Please select and upload your 'kaggle.json' file:")
uploaded = files.upload()

# Configure Kaggle directory and permissions
!mkdir -p ~/.kaggle
!cp kaggle.json ~/.kaggle/
!chmod 600 ~/.kaggle/kaggle.json
print("✅ Kaggle API token successfully configured!")
```

---

## 📦 Step 3: Download & Extract CASIA v2 Dataset

In a new code cell in Colab, run the following bash commands to install required libraries, download the dataset, and unzip it:

```bash
# 1. Install/Update required dependencies
!pip install --quiet opencv-python-headless Pillow scikit-image scikit-learn joblib tqdm

# 2. Download CASIA v2 Dataset from Kaggle
!kaggle datasets download -d sophatvathana/casia-dataset

# 3. Unzip dataset into a dedicated folder
!mkdir -p ./casia_dataset
!unzip -q casia-dataset.zip -d ./casia_dataset

# 4. Check folder structure
!ls -lh ./casia_dataset
```

> [!TIP]
> The CASIA v2 dataset contains two main image categories:
> - **`Au`**: Authentic / pristine camera images (Class `0`)
> - **`Tp`**: Tampered / forged / spliced images (Class `1`)

---

## 🚀 Step 4: End-to-End Feature Extraction & Model Training Script

Create a new code cell in Colab and paste the complete Python script below.

This script contains the **exact forensic feature calculation logic** from `backend/modules/` so that the trained model has **100% feature consistency** with your local DeceptionLens backend. It also utilizes multi-threaded batch processing with `tqdm` for fast extraction.

```python
"""
DeceptionLens — Forensic Feature Extraction & Model Training
=============================================================
Extracts 17 forensic features (Entropy, ELA, Noise, GLCM Texture)
and trains a Random Forest Classifier on the CASIA v2 dataset.
"""

import os
import io
import sys
import json
import glob
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed

import cv2
import numpy as np
import joblib
from PIL import Image
from skimage.feature import graycomatrix, graycoprops
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
)
from tqdm.auto import tqdm

# =====================================================================
# 1. CANONICAL FEATURE NAMES (17 Features in Exact Backend Order)
# =====================================================================
FEATURE_NAMES: List[str] = [
    # Entropy features (6)
    "entropy_global",
    "entropy_mean_local",
    "entropy_std_local",
    "entropy_min_local",
    "entropy_max_local",
    "entropy_anomaly_score",
    # ELA features (3)
    "ela_mean",
    "ela_std",
    "ela_max",
    # Noise features (3)
    "noise_mean",
    "noise_std",
    "noise_max",
    # Texture features (5)
    "texture_contrast",
    "texture_dissimilarity",
    "texture_homogeneity",
    "texture_energy",
    "texture_correlation",
]

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}

# =====================================================================
# 2. EXACT BACKEND FORENSIC ALGORITHMS
# =====================================================================

def load_image(path: str) -> Tuple[Image.Image, np.ndarray, np.ndarray]:
    """Load image returning PIL Image (RGB), OpenCV (BGR), Grayscale (uint8)."""
    pil_img = Image.open(path).convert("RGB")
    cv_img = cv2.imread(path)
    if cv_img is None:
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    return pil_img, cv_img, gray


def calculate_global_entropy(gray: np.ndarray) -> float:
    """Compute Shannon entropy over the entire grayscale histogram."""
    hist, _ = np.histogram(gray.ravel(), bins=256, range=(0, 256))
    hist = hist[hist > 0]
    probs = hist / hist.sum()
    return float(-np.sum(probs * np.log2(probs)))


def calculate_local_entropy(gray: np.ndarray, grid_size: int = 8) -> np.ndarray:
    """Divide image into (grid_size x grid_size) blocks and compute per-block entropy."""
    h, w = gray.shape
    block_h = max(1, h // grid_size)
    block_w = max(1, w // grid_size)

    rows = h // block_h
    cols = w // block_w
    entropy_map = np.zeros((rows, cols), dtype=np.float32)

    for r in range(rows):
        for c in range(cols):
            block = gray[r * block_h : (r + 1) * block_h, c * block_w : (c + 1) * block_w]
            entropy_map[r, c] = calculate_global_entropy(block)

    return entropy_map


def compute_entropy_stats(gray: np.ndarray, grid_size: int = 8) -> Dict[str, float]:
    """Compute global and local entropy statistics matching backend logic."""
    global_e = calculate_global_entropy(gray)
    local_map = calculate_local_entropy(gray, grid_size=grid_size)

    mean_local = float(np.mean(local_map))
    std_local = float(np.std(local_map))
    min_local = float(np.min(local_map))
    max_local = float(np.max(local_map))

    if mean_local > 0:
        anomaly_score = float(min(std_local / mean_local, 1.0))
    else:
        anomaly_score = 0.0

    return {
        "global": round(global_e, 4),
        "mean_local": round(mean_local, 4),
        "std_local": round(std_local, 4),
        "min_local": round(min_local, 4),
        "max_local": round(max_local, 4),
        "anomaly_score": round(anomaly_score, 4),
    }


def perform_ela(image_path: str, quality: int = 90, scale: int = 10) -> Image.Image:
    """Perform Error Level Analysis (re-save to JPEG in-memory & compute difference)."""
    original = Image.open(image_path).convert("RGB")
    buffer = io.BytesIO()
    original.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    recompressed = Image.open(buffer).convert("RGB")

    orig_arr = np.array(original, dtype=np.float32)
    recomp_arr = np.array(recompressed, dtype=np.float32)
    diff = np.abs(orig_arr - recomp_arr) * scale
    diff = np.clip(diff, 0, 255).astype(np.uint8)
    return Image.fromarray(diff, mode="RGB")


def compute_ela_stats(ela_image: Image.Image) -> Dict[str, float]:
    """Compute mean, std, max from ELA difference image."""
    arr = np.array(ela_image, dtype=np.float32)
    gray = arr.mean(axis=2)
    return {
        "mean": round(float(gray.mean()), 4),
        "std": round(float(gray.std()), 4),
        "max": round(float(gray.max()), 4),
    }


def estimate_noise_map(gray: np.ndarray, blur_kernel: int = 3) -> np.ndarray:
    """Estimate spatial noise via Gaussian blur subtraction."""
    if blur_kernel % 2 == 0:
        blur_kernel += 1
    blurred = cv2.GaussianBlur(gray, (blur_kernel, blur_kernel), 0)
    noise_map = np.abs(gray.astype(np.float32) - blurred.astype(np.float32))
    return noise_map


def compute_noise_stats(noise_map: np.ndarray) -> Dict[str, float]:
    """Compute summary statistics for estimated noise."""
    return {
        "mean": round(float(noise_map.mean()), 4),
        "std": round(float(noise_map.std()), 4),
        "max": round(float(noise_map.max()), 4),
    }


def compute_glcm_features(gray: np.ndarray) -> Dict[str, float]:
    """Extract GLCM texture features (64 quantized levels, 4 angles averaged)."""
    gray_q = (gray // 4).astype(np.uint8)
    glcm = graycomatrix(
        gray_q,
        distances=[1],
        angles=[0, np.pi / 4, np.pi / 2, 3 * np.pi / 4],
        levels=64,
        symmetric=True,
        normed=True,
    )

    def _mean_prop(prop: str) -> float:
        return float(np.mean(graycoprops(glcm, prop)))

    return {
        "contrast": round(_mean_prop("contrast"), 6),
        "dissimilarity": round(_mean_prop("dissimilarity"), 6),
        "homogeneity": round(_mean_prop("homogeneity"), 6),
        "energy": round(_mean_prop("energy"), 6),
        "correlation": round(_mean_prop("correlation"), 6),
    }


def extract_single_image(img_path: str, label: int) -> Optional[Tuple[List[float], int]]:
    """Worker function to extract 17 features from a single image."""
    try:
        pil_img, cv_img, gray = load_image(img_path)
        entropy = compute_entropy_stats(gray)
        ela_img = perform_ela(img_path)
        ela = compute_ela_stats(ela_img)
        noise_map = estimate_noise_map(gray)
        noise = compute_noise_stats(noise_map)
        texture = compute_glcm_features(gray)

        raw = {
            "entropy_global": entropy["global"],
            "entropy_mean_local": entropy["mean_local"],
            "entropy_std_local": entropy["std_local"],
            "entropy_min_local": entropy["min_local"],
            "entropy_max_local": entropy["max_local"],
            "entropy_anomaly_score": entropy["anomaly_score"],
            "ela_mean": ela["mean"],
            "ela_std": ela["std"],
            "ela_max": ela["max"],
            "noise_mean": noise["mean"],
            "noise_std": noise["std"],
            "noise_max": noise["max"],
            "texture_contrast": texture["contrast"],
            "texture_dissimilarity": texture["dissimilarity"],
            "texture_homogeneity": texture["homogeneity"],
            "texture_energy": texture["energy"],
            "texture_correlation": texture["correlation"],
        }

        # Format vector strictly adhering to canonical FEATURE_NAMES order
        vector = [
            float(raw[name]) if np.isfinite(raw.get(name, 0.0)) else 0.0
            for name in FEATURE_NAMES
        ]
        return vector, label
    except Exception as e:
        return None


# =====================================================================
# 3. LOCATE CASIA V2 DATASET DIRECTORIES
# =====================================================================
def find_casia_folders(base_path: str = "./casia_dataset"):
    """Locate authentic ('Au') and tampered ('Tp') folders recursively."""
    au_folders = []
    tp_folders = []

    for root, dirs, _ in os.walk(base_path):
        for d in dirs:
            if d.lower() == "au":
                au_folders.append(os.path.join(root, d))
            elif d.lower() == "tp":
                tp_folders.append(os.path.join(root, d))

    if not au_folders or not tp_folders:
        raise FileNotFoundError(
            f"Could not find Au and Tp folders inside {base_path}. "
            f"Found Au: {au_folders}, Tp: {tp_folders}"
        )

    print(f"[INFO] Located Authentic (Au) folder: {au_folders[0]}")
    print(f"[INFO] Located Tampered (Tp) folder:  {tp_folders[0]}")
    return au_folders[0], tp_folders[0]


# =====================================================================
# 4. DATASET LOADER & FEATURE EXTRACTION PIPELINE
# =====================================================================
def load_and_extract_dataset(max_samples_per_class: Optional[int] = None):
    """
    Scans dataset and parallelizes feature extraction across available CPUs.
    Set max_samples_per_class to an integer (e.g., 2000) for faster test runs,
    or leave as None to train on the entire dataset.
    """
    au_dir, tp_dir = find_casia_folders()

    au_images = [
        os.path.join(au_dir, f) for f in os.listdir(au_dir)
        if Path(f).suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    tp_images = [
        os.path.join(tp_dir, f) for f in os.listdir(tp_dir)
        if Path(f).suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if max_samples_per_class:
        au_images = au_images[:max_samples_per_class]
        tp_images = tp_images[:max_samples_per_class]

    print(f"\n[INFO] Found {len(au_images)} Authentic (Au) images")
    print(f"[INFO] Found {len(tp_images)} Tampered (Tp) images")

    tasks = [(p, 0) for p in au_images] + [(p, 1) for p in tp_images]
    np.random.seed(42)
    np.random.shuffle(tasks)

    X, y = [], []
    failed = 0

    num_workers = max(1, os.cpu_count() or 2)
    print(f"[INFO] Extracting features using {num_workers} parallel workers...\n")

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(extract_single_image, path, label) for path, label in tasks]
        for f in tqdm(as_completed(futures), total=len(futures), desc="Extracting Forensic Features"):
            res = f.result()
            if res is not None:
                vec, label = res
                X.append(vec)
                y.append(label)
            else:
                failed += 1

    print(f"\n[INFO] Successfully extracted {len(X)} samples ({failed} failed/skipped).")
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int64)


# =====================================================================
# 5. MODEL TRAINING, EVALUATION & SAVING
# =====================================================================
def train_and_export():
    print("=" * 65)
    print(" 🔍 DeceptionLens — Forensic Classifier Training (Google Colab)")
    print("=" * 65)

    # 1. Extract Features
    X, y = load_and_extract_dataset(max_samples_per_class=None) # Set e.g. 2500 for fast run

    if len(X) < 50:
        raise ValueError(f"Insufficient samples extracted: {len(X)}. Check image paths.")

    unique, counts = np.unique(y, return_counts=True)
    for cls, cnt in zip(unique, counts):
        label_str = "Authentic (Au)" if cls == 0 else "Tampered (Tp)"
        print(f"  - Class {cls} ({label_str}): {cnt} samples")

    # 2. Stratified Train / Test Split (80% Train, 20% Test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"\n[INFO] Dataset split: {len(X_train)} Train samples | {len(X_test)} Test samples")

    # 3. Initialize and Train Random Forest (matching backend/ml/train_classifier.py)
    print("\n[INFO] Training Random Forest Classifier...")
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_split=2,
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    # 4. Evaluate Performance
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    try:
        roc_auc = roc_auc_score(y_test, y_prob)
    except Exception:
        roc_auc = None

    print("\n" + "═" * 65)
    print(" 📊 EVALUATION METRICS ON HELD-OUT TEST SET")
    print("═" * 65)
    print(f"  Accuracy  : {acc * 100:.2f}%")
    print(f"  Precision : {prec * 100:.2f}%")
    print(f"  Recall    : {rec * 100:.2f}%")
    print(f"  F1-Score  : {f1 * 100:.2f}%")
    if roc_auc is not None:
        print(f"  ROC-AUC   : {roc_auc:.4f}")

    print("\n--- Detailed Classification Report ---")
    print(classification_report(y_test, y_pred, target_names=["Authentic", "Tampered"]))

    print("--- Confusion Matrix ---")
    print(confusion_matrix(y_test, y_pred))

    # 5. Feature Importances
    print("\n--- Top Forensic Feature Importances ---")
    importances = clf.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    for rank, idx in enumerate(sorted_idx, 1):
        print(f"  {rank:2d}. {FEATURE_NAMES[idx]:<25}: {importances[idx] * 100:.2f}%")

    # 6. Save Model Artifacts
    output_model = "forgery_model.joblib"
    output_features = "feature_names.json"

    joblib.dump(clf, output_model)
    with open(output_features, "w") as f:
        json.dump(FEATURE_NAMES, f, indent=2)

    print("\n" + "═" * 65)
    print(f" ✅ Saved Model:         {output_model}")
    print(f" ✅ Saved Feature Names: {output_features}")
    print("═" * 65)

# Execute the training pipeline
if __name__ == "__main__":
    train_and_export()
```

---

## 📥 Step 5: Download Model Files to Your Local Machine

In a new code cell in Colab, run this snippet to trigger your browser's file download dialog for both generated files:

```python
from google.colab import files

print("Downloading trained model and feature definitions...")
files.download('forgery_model.joblib')
files.download('feature_names.json')
```

---

## 📂 Step 6: Place Files in Your Local DeceptionLens Project

Once the files finish downloading to your computer:

1. Locate `forgery_model.joblib` and `feature_names.json` in your downloads folder.
2. Move both files into your project directory at:
   ```text
   backend/ml/models/
   ```
3. Your local folder tree will look like:
   ```text
   backend/
   └── ml/
       ├── models/
       │   ├── feature_names.json      <-- (Placed here)
       │   └── forgery_model.joblib    <-- (Placed here)
       ├── predict.py
       └── train_classifier.py
   ```

---

## ✨ Step 7: Verify Local Prediction API

1. Start your local DeceptionLens backend:
   ```powershell
   cd backend
   python main.py
   ```
2. When an image is uploaded through the API (`/api/analyze/image`) or frontend, `backend/ml/predict.py` will automatically load `forgery_model.joblib`, format the 17 extracted features, and return real ML predictions:
   ```json
   {
     "available": true,
     "label": "AUTHENTIC",
     "probability_suspicious": 0.085
   }
   ```
