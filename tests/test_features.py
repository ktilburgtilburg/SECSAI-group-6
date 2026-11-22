"""Direct production feature tests with deterministic, offline suffix parsing."""

import pytest

from secsai_group_6.ml import features


@pytest.mark.parametrize("host, expected", [
    ("192.0.2.1", True),
    ("[2001:db8::1]", True),
    ("256.1.1.1", False),
    ("example.com", False),
    ("", False),
])
def test_is_ip_address(host, expected):
    result = features.extract_features(host)
    assert result["is_ip_host"] is expected


def test_extract_features_parses_structure():
    result = features.extract_features("https://shop.example.com:8443/LOGIN?id=12&x=3")
    assert result["num_subdomains"] == 1
    assert result["num_query_params"] == 2
    assert result["num_sensitive_words"] >= 1
    assert result["has_port"] is True
    assert result["is_ip_host"] is False


def test_extract_features_detects_ip():
    result = features.extract_features("http://192.0.2.1/login")
    assert result["is_ip_host"] is True
    assert result["num_query_params"] == 0


def test_extract_features_detects_punycode():
    assert features.extract_features("https://xn--bcher-kva.de/")["has_punycode"] is True


def test_strip_url_canonicalizes():
    assert features.strip_url("https://WWW.Google.COM/") == "google.com"
    assert features.strip_url("http://example.com:80/") == "example.com:80"
    assert features.strip_url("example.com/") == "example.com"