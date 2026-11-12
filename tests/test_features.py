"""Direct production feature tests with deterministic, offline suffix parsing."""

import pytest
import tldextract

from secsai_group_6.ml import features


@pytest.mark.parametrize("text, expected", [("", 0.0), ("aaaa", 0.0), ("ab", 1.0), ("abcd", 2.0)])
def test_text_randomness_known_distributions(text, expected):
    assert features.text_randomness(text) == pytest.approx(expected)


@pytest.mark.parametrize("host, expected", [
    ("192.0.2.1", True), ("[2001:db8::1]", True),
    ("256.1.1.1", False), ("example.com", False), ("", False),
])
def test_is_ip_address_distinguishes_addresses_from_hostnames(host, expected):
    assert features.is_ip_address(host) is expected


@pytest.fixture
def offline_suffix_parser(monkeypatch):
    # Use the real parser and its bundled suffix list, without cache or HTTP.
    monkeypatch.setattr(
        features.tldextract, "extract",
        tldextract.TLDExtract(cache_dir=None, suffix_list_urls=()),
    )


def test_extract_features_parses_structure_and_sensitive_words(offline_suffix_parser):
    result = features.extract_features("https://shop.example.com:8443/LOGIN?id=12&x=3")
    assert result["hostname_length"] == 16
    assert result["path_length"] == 6
    assert result["query_length"] == 9
    assert result["num_subdomains"] == 1
    assert result["num_query_params"] == 2
    assert result["num_sensitive_words"] == 1
    assert result["has_sensitive_word"] is True
    assert result["is_https"] is True
    assert result["has_port"] is True
    assert result["is_ip_host"] is False


def test_extract_features_detects_ip_and_encoded_path(offline_suffix_parser):
    result = features.extract_features("http://192.0.2.1/%41")
    assert result["is_ip_host"] is True
    assert result["has_percent_encoding"] is True
    assert result["is_https"] is False
    assert result["has_port"] is False
    assert result["num_query_params"] == 0
    assert result["has_sensitive_word"] is False


def test_extract_features_detects_punycode(offline_suffix_parser):
    assert features.extract_features("https://xn--bcher-kva.de/")["has_punycode"] is True
