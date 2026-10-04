"""
ML Training Script — Random Forest Classifier
=============================================
Train a forensic image classification model using extracted features.

Usage:
    cd backend
    python ml/train_classifier.py

Dataset structure required:
    dataset/
    ├── authentic/   (authentic images)
    └── forged/      (forged/manipulated images)

The model is saved to backend/ml/models/forgery_model.joblib.
Feature names are saved to backend/ml/models/feature_names.json.

This model is a binary classifier (authentic vs. forged).
Never invent evaluation metrics — all values are computed from real data.
"""

import json
import sys
from pathlib import Path

# Allow imports from backend root
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from modules.feature_extraction import FEATURE_NAMES, extract_all_features

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}
MODELS_DIR = Path(__file__).parent / "models"
DATASET_DIR = BACKEND_DIR.parent / "dataset"


def load_dataset():
    """
    Load all images from dataset/authentic and dataset/forged.
    Returns (X, y) where y=0 is authentic, y=1 is forged.
    """
    X, y = [], []
    errors = 0

    for label, folder in [(0, "authentic"), (1, "forged")]:
        folder_path = DATASET_DIR / folder
        if not folder_path.exists():
            print(f"[WARNING] Dataset folder not found: {folder_path}")
            continue

        images = [
            p for p in folder_path.iterdir()
            if p.suffix.lower() in SUPPORTED
        ]
        print(f"[INFO] Found {len(images)} images in '{folder}'")

        for img_path in images:
            try:
                features = extract_all_features(str(img_path))
                vector = [features[name] for name in FEATURE_NAMES]
                X.append(vector)
                y.append(label)
            except Exception as exc:
                print(f"[ERROR] Skipping {img_path.name}: {exc}")
                errors += 1

    print(f"[INFO] Loaded {len(X)} samples ({errors} skipped)")
    return np.array(X), np.array(y)


def train():
    """Train and evaluate the Random Forest classifier."""
    print("=" * 60)
    print("DeceptionLens — ML Training")
    print("=" * 60)

    X, y = load_dataset()

    if len(X) < 10:
        print(
            "[ERROR] Not enough training data. "
            "Add images to dataset/authentic/ and dataset/forged/."
        )
        sys.exit(1)

    unique, counts = np.unique(y, return_counts=True)
    for cls, cnt in zip(unique, counts):
        label = "authentic" if cls == 0 else "forged"
        print(f"  Class {cls} ({label}): {cnt} samples")

    # 80/20 stratified split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n[INFO] Train: {len(X_train)} | Test: {len(X_test)}")

    # Train Random Forest
    print("\n[INFO] Training Random Forest classifier...")
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_split=2,
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]

    accuracy   = accuracy_score(y_test, y_pred)
    precision  = precision_score(y_test, y_pred, zero_division=0)
    recall     = recall_score(y_test, y_pred, zero_division=0)
    f1         = f1_score(y_test, y_pred, zero_division=0)
    try:
        roc_auc = roc_auc_score(y_test, y_prob)
    except ValueError:
        roc_auc = None

    print("\n── Evaluation Results ─────────────────────────────")
    print(f"  Accuracy : {accuracy:.4f}")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall   : {recall:.4f}")
    print(f"  F1 Score : {f1:.4f}")
    if roc_auc is not None:
        print(f"  ROC-AUC  : {roc_auc:.4f}")
    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["Authentic", "Forged"]))
    print("  Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # Save model and feature names
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODELS_DIR / "forgery_model.joblib"
    feature_path = MODELS_DIR / "feature_names.json"

    joblib.dump(clf, model_path)
    with open(feature_path, "w") as f:
        json.dump(FEATURE_NAMES, f, indent=2)

    print(f"\n[INFO] Model saved to: {model_path}")
    print(f"[INFO] Feature names saved to: {feature_path}")
    print("\n[DONE] Training complete.")


if __name__ == "__main__":
    train()
