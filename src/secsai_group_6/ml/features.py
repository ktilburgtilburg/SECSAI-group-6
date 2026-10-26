"""Turn a URL into a table of numeric features."""

import ipaddress
import math
from collections import Counter
from urllib.parse import urlparse

import tldextract


SENSITIVE_WORDS = (
    "login", "log-in", "signin", "sign-in",
    "verify", "verification",
    "bank", "banking",
    "secure", "security",
    "account", "update",
    "confirm", "password", "credential", "auth",
    "wallet", "invoice", "payment", "billing",
    "support", "helpdesk",
)


def text_randomness(text):
    """How random a piece of text looks, in bits per character."""
    if not text:
        return 0.0
    counts = Counter(text)
    n = len(text)
    return max(0.0, -sum((c / n) * math.log2(c / n) for c in counts.values()))


def is_ip_address(host):
    """True if host is an IPv4 or IPv6 address"""
    try:
        ipaddress.ip_address(host.strip("[]"))
        return True
    except ValueError:
        return False


def extract_features(url):
    """Turn one URL into a dict of numeric features."""
    try:
        parts = urlparse(url)
    except ValueError:
        parts = urlparse("")

    ext = tldextract.extract(url)
    hostname = (parts.hostname or ext.fqdn or "").lower()
    path = parts.path or ""
    query = parts.query or ""

    url_length = len(url)
    digit_count = sum(c.isdigit() for c in url)
    combined_text = (hostname + " " + path + " " + query).lower()
    sensitive_count = sum(combined_text.count(w) for w in SENSITIVE_WORDS)

    subdomain = ext.subdomain or ""
    num_subdomains = len(subdomain.split(".")) if subdomain else 0

    return {
        # Lengths
        "url_length": url_length,
        "hostname_length": len(hostname),
        "path_length": len(path),
        "query_length": len(query),

        # Character counts
        "num_dots": url.count("."),
        "num_hyphens": url.count("-"),
        "num_slashes": url.count("/"),
        "num_at": url.count("@"),
        "num_question": url.count("?"),
        "num_equals": url.count("="),
        "num_digits": digit_count,
        "num_underscores": url.count("_"),
        "num_special_chars": sum(not c.isalnum() for c in url),
        "digit_ratio": digit_count / url_length if url_length else 0.0,

        # Security indicators
        "is_ip_host": is_ip_address(hostname),
        "has_sensitive_word": sensitive_count > 0,
        "num_sensitive_words": sensitive_count,
        "has_port": parts.port is not None,
        "is_https": parts.scheme == "https",
        "has_punycode": "xn--" in hostname,
        "has_percent_encoding": "%" in url,

        # URL structure
        "num_subdomains": num_subdomains,
        "num_query_params": len(query.split("&")) if query else 0,

        # Randomness
        "hostname_randomness": text_randomness(hostname),
        "path_randomness": text_randomness(path),
        "url_randomness": text_randomness(url),
    }


def feature_names():
    """The fixed column order to use when building a training matrix."""
    return list(extract_features("http://example.com/").keys())