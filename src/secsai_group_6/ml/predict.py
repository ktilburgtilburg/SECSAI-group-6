"""Predict whether a URL is malicious.

Loads a trained RandomForest from models/classifier.joblib. The model
predicts one of four classes: 'benign', 'defacement', 'malware', 'phishing'.
"""

import json
from pathlib import Path

import joblib
import numpy as np

from secsai_group_6.ml.features import extract_features, feature_names

MODEL_DIR = Path("models")
_MODEL = None
_CLASSES = None


def _load():
    """Load models"""
    global _MODEL, _CLASSES
    if _MODEL is None:
        model_path = MODEL_DIR / "classifier.joblib"
        if not model_path.exists():
            raise FileNotFoundError(
                f"{model_path} not found. Run: "
                "uv run python -m secsai_group_6.ml.train"
            )
        _MODEL = joblib.load(model_path)
        with open(MODEL_DIR / "label_classes.json") as f:
            _CLASSES = json.load(f)
    return _MODEL, _CLASSES


def _explanations(features: dict) -> list[str]:
    """Return up to 3 reasons based on strong signals."""
    reasons = []

    if features["is_ip_host"]:
        reasons.append("host is a raw IP address instead of a domain")
    if features["has_punycode"]:
        reasons.append("hostname uses punycode (possible homograph attack)")
    if features["num_sensitive_words"] > 0:
        reasons.append(
            f"contains {features['num_sensitive_words']} sensitive word(s) "
            "(login, verify, bank, ...)"
        )
    if features["hostname_randomness"] > 3.5:
        reasons.append("hostname is highly random (typical of bot-generated domains)")
    if features["has_percent_encoding"]:
        reasons.append("contains percent-encoded characters (possible obfuscation)")
    if features["num_subdomains"] >= 3:
        reasons.append(f"unusually many subdomains ({features['num_subdomains']})")
    if features["path_length"] > 60:
        reasons.append("unusually long path")
    if not features["is_https"] and features["has_sensitive_word"]:
        reasons.append("uses HTTP (not HTTPS) on a credential-related URL")

    return reasons[:3] if reasons else ["no strong structural signals detected"]


def predict(url: str) -> dict:
    """Classify a URL. Returns dict.

    Args:
        url: raw URL string.

    Returns:
        {
            "is_malicious": bool,
            "category": "benign" | "defacement" | "malware" | "phishing",
            "confidence": float in [0, 1],
            "explanations": list[str],
        }
    """
    model, classes = _load()
    model.n_jobs = 1

    feats = extract_features(url)
    names = feature_names()
    X = np.array([[feats[n] for n in names]], dtype=float)

    proba = model.predict_proba(X)[0]
    idx = int(np.argmax(proba))
    category = str(classes[idx])
    confidence = float(proba[idx])

    return {
        "is_malicious": category != "benign",
        "category": category,
        "confidence": confidence,
        "explanations": _explanations(feats),
    }