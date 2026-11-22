"""Shared assertions for the documented assess/predict response."""

import math

CATEGORIES = {"benign", "malicious"}


def assert_verdict(payload):
    assert isinstance(payload, dict)
    assert set(payload) == {"is_malicious", "category", "confidence", "explanations"}
    assert isinstance(payload["category"], str)
    assert payload["category"] in CATEGORIES
    assert type(payload["is_malicious"]) is bool
    assert payload["is_malicious"] == (payload["category"] != "benign")
    assert type(payload["confidence"]) is float
    assert math.isfinite(payload["confidence"])
    assert 0.0 <= payload["confidence"] <= 1.0
    assert isinstance(payload["explanations"], list)
    assert all(isinstance(reason, str) for reason in payload["explanations"])
