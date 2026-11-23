from collections import Counter

import pytest

from secsai_group_6.backend.stub_model import predict
from tests.conftest import URL_CASES
from tests.contracts import assert_verdict


def test_url_corpus():
    assert len(URL_CASES) == 10
    assert len({case["url"] for case in URL_CASES}) == 10
    assert Counter(case["category"] for case in URL_CASES) == {
        "benign": 5,
        "malicious": 5,
    }
    assert {"wikipedia", "github"} <= {case["id"] for case in URL_CASES}


def test_prediction_contract(url_case):
    assert_verdict(predict(url_case["url"]))


@pytest.mark.parametrize(
    "url, category",
    [
        ("https://www.wikipedia.org/", "benign"),
        ("https://example.test/login", "malicious"),
        ("https://example.test/LOGIN", "malicious"),
    ],
)
def test_week1_stub_behavior(url, category):
    """Characterize the placeholder rule, not trained-model accuracy."""
    result = predict(url)
    assert_verdict(result)
    assert result["category"] == category
