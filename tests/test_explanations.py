
import pytest

from secsai_group_6.ml.features import extract_features
from secsai_group_6.ml.predict import _explanations


@pytest.mark.parametrize("url, expected", [
    (
        "http://192.168.1.1/login",
        "raw IP address"
    ),
    (
        "https://example.com/verify-password",
        "sensitive word"
    ),
    (
        "https://a.b.c.d.example.com",
        "many subdomains"
    ),
    (
        "https://xn--example-9d0b.com",
        "punycode"
    ),
    (
        "https://example.com/%20login",
        "percent-encoded"
    ),
    (
        "https://example.com/" + "a" * 70,
        "long path"
    ),
])


def test_explanation_rules(url, expected):
    features = extract_features(url)
    reasons = _explanations(features)

    assert any(
        expected in reason
        for reason in reasons
    ), f"Missing '{expected}' explanation for {url}"
