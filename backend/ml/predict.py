"""
ML Prediction Module
====================
Loads a trained Random Forest model (if available) and runs inference.

If no model is found, returns a clear "not available" response.
Never invents confidence values or results.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import numpy as np

MODELS_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODELS_DIR / "forgery_model.joblib"
FEATURE_NAMES_PATH = MODELS_DIR / "feature_names.json"


def load_model() -> Optional[Any]:
    """
    Load the trained model from disk.
    Returns None if the model file does not exist.
    """
    if MODEL_PATH.exists():
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            return None
    return None


def _load_feature_names():
    """Load the saved feature name order."""
    if FEATURE_NAMES_PATH.exists():
        with open(FEATURE_NAMES_PATH) as f:
            return json.load(f)
    # Fallback to module default
    from modules.feature_extraction import FEATURE_NAMES
    return FEATURE_NAMES


def predict(
    model: Optional[Any],
    entropy_stats: dict,
    ela_stats: dict,
    noise_stats: dict,
    texture_stats: dict,
) -> Dict[str, Any]:
    """
    Run ML prediction using already-computed forensic stats.

    Returns:
      If model is available:
        {
          "available": true,
          "label": "AUTHENTIC" | "SUSPICIOUS",
          "probability_suspicious": <float 0-1>,
        }
      If model is not available:
        {
          "available": false,
          "message": "ML model has not been trained yet."
        }

    No values are invented. Only model outputs are returned.
    """
    if model is None:
        return {
            "available": False,
            "message": "ML model has not been trained yet. Run ml/train_classifier.py after adding dataset images.",
        }

    try:
        from modules.feature_extraction import stats_to_features, features_to_vector

        feature_names = _load_feature_names()
        features = stats_to_features(entropy_stats, ela_stats, noise_stats, texture_stats)
        vector = [features.get(name, 0.0) for name in feature_names]

        X = np.array([vector])
        pred = int(model.predict(X)[0])
        prob = float(model.predict_proba(X)[0][1])  # probability of "forged" class

        label = "SUSPICIOUS" if pred == 1 else "AUTHENTIC"

        return {
            "available": True,
            "label": label,
            "probability_suspicious": round(prob, 4),
        }
    except Exception as exc:
        return {
            "available": False,
            "message": f"Prediction error: {str(exc)}",
        }
