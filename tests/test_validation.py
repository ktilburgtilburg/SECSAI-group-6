"""Unit tests for production input validation; no API or storage involved."""

import pytest

from secsai_group_6.backend.validation import (
    InvalidInput,
    clean_url,
    redact_url,
)


def test_clean_url_trims_surrounding_whitespace():
    assert clean_url(" \t https://example.com/login \n") == "https://example.com/login"


@pytest.mark.parametrize("value", [None, 42, False, [], {}, "", " \t\n"])
def test_clean_url_rejects_missing_wrong_type_or_blank_input(value):
    with pytest.raises(InvalidInput):
        clean_url(value)


def test_clean_url_accepts_limit_and_rejects_one_character_over():
    # Literal contract limit, independent of the implementation constant.
    assert clean_url("a" * 2048) == "a" * 2048
    with pytest.raises(InvalidInput, match="at most 2048 characters"):
        clean_url("a" * 2049)


def test_redact_url_removes_credentials_port_path_query_and_fragment():
    assert (
        redact_url("https://user:secret@Example.com:8080/reset?token=private#details")
        == "https://example.com"
    )


@pytest.mark.parametrize(
    "url",
    ["example.com", "https:///missing-host", "file:///tmp/private", "https://[broken"],
)
def test_redact_url_rejects_invalid_or_non_web_urls(url):
    with pytest.raises(InvalidInput):
        redact_url(url)
