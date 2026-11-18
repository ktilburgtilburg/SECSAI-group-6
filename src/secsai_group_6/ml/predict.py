"""Predict whether a URL is malicious."""

import json
import os

import joblib
import numpy as np

from secsai_group_6.ml.build_dataset import COUNT_FEATURES
from secsai_group_6.ml.features import extract_features, feature_names

MODEL_DIR = "models"
THRESHOLD = 0.55

_MODEL = None
_CLASSES = None
_FEATURE_NAMES = None


def _load():
    global _MODEL, _CLASSES, _FEATURE_NAMES
    if _MODEL is None:
        _MODEL = joblib.load(f"{MODEL_DIR}/classifier.joblib")
        _MODEL.n_jobs = 1
        with open(f"{MODEL_DIR}/label_classes.json") as f:
            _CLASSES = json.load(f)
        _FEATURE_NAMES = feature_names()
    return _MODEL, _CLASSES, _FEATURE_NAMES


def _build_vector(feats: dict, names: list[str]) -> np.ndarray:
    x = np.array([[feats[n] for n in names]], dtype=float)
    for j, name in enumerate(names):
        if name in COUNT_FEATURES:
            x[0, j] = np.log1p(x[0, j])
    return x


def _explanations(feats: dict) -> list[str]:
    reasons = []

    if feats["is_exact_brand_domain"] == 0:
        d = int(feats["edit_distance_to_nearest_brand"])
        if d == 1:
            reasons.append("domain is 1 character away from a well-known brand (typosquat)")
        elif d <= 3:
            reasons.append(f"domain closely resembles a well-known brand ({d} characters off)")

    if feats["tld_risk"] >= 0.5:
        reasons.append(f"hosted on a domain with elevated abuse rate (risk score {feats['tld_risk']:.2f})")

    if feats["num_sensitive_words"] > 0:
        reasons.append(
            f"URL contains {int(feats['num_sensitive_words'])} credential-related "
            f"keyword(s) such as 'login', 'verify', 'bank'"
        )

    if feats["is_ip_host"]:
        reasons.append("host is a raw IP address instead of a domain name")

    if feats["brand_in_subdomain_not_registrable"]:
        reasons.append("well-known brand name appears in a subdomain of an unrelated domain")

    if feats["has_punycode"]:
        reasons.append("hostname uses punycode encoding (possible homograph attack)")

    if len(reasons) < 2:
        if feats["num_subdomains"] >= 3:
            reasons.append(f"unusually deep subdomain nesting ({int(feats['num_subdomains'])} levels)")
        if feats["num_hyphens"] >= 3:
            reasons.append(f"unusually many hyphens in the URL ({int(feats['num_hyphens'])})")
        if feats["digit_ratio"] >= 0.3:
            reasons.append(f"high proportion of digits in the URL ({feats['digit_ratio']:.0%})")

    return reasons[:3] if reasons else ["flagged by model on combined signals"]


def predict(url: str) -> dict:
    """Classify a URL. Returns a verdict dict for the extension."""
    model, classes, names = _load()

    feats = extract_features(url)
    x = _build_vector(feats, names)
    proba = model.predict_proba(x)[0]
    mal_idx = classes.index("malicious")
    p_mal = float(proba[mal_idx])

    rule_fired = (
        feats["is_ip_host"]
        or feats["brand_in_subdomain_not_registrable"]
        or (feats["tld_risk"] >= 0.6 and feats["num_sensitive_words"] > 0)
        or (feats["edit_distance_to_nearest_brand"] == 1 and not feats["is_exact_brand_domain"])
    )

    if rule_fired or p_mal >= THRESHOLD:
        return _malicious(p_mal, _explanations(feats))

    return {
        "is_malicious": False,
        "category": "benign",
        "confidence": 1.0 - p_mal,
        "explanations": [],
    }


def _malicious(confidence: float, reasons: list[str]) -> dict:
    return {
        "is_malicious": True,
        "category": "malicious",
        "confidence": confidence,
        "explanations": reasons,
    }


if __name__ == "__main__":
    for u in [
        "google.com",
        "google.com/search?q=test",
        "amazon.co.uk/Pbs-Kids-Pack-Region-NTSC/dp/B000J3EG94",
        "wikipedia.org/wiki/Python",
        "gooogle.com",
        "paypal-secure-login.xyz/login",
        "google.com.verify-account.ru",
        "192.168.1.1/admin",
        "37.49.226.178/deusbins/deus.sh4",
        "myblog.com/post/123",
        "https://www.tilburguniversity.edu/",
    ]:
        r = predict(u)
        verdict = "MALICIOUS" if r["is_malicious"] else "benign   "
        print(f"{verdict}  conf={r['confidence']:.2f}  {u}")
        for e in r["explanations"]:
            print(f"           - {e}")
        print()