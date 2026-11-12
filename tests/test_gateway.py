import json

import pytest

from secsai_group_6.backend import app as app_module
from secsai_group_6.backend.rpc_client import (
    BadReply,
    QueueTimeout,
    QueueUnavailable,
    _parse_reply,
)

GOOD = {
    "is_malicious": True,
    "category": "phishing",
    "confidence": 0.85,
    "explanations": ["x"],
}


@pytest.fixture
def client():
    return app_module.app.test_client()


def test_assess_returns_the_workers_verdict(client, monkeypatch):
    monkeypatch.setattr(app_module, "rpc_assess", lambda url: (GOOD, "w1"))
    resp = client.post("/api/v1/assess", json={"url": "https://example.com"})
    assert resp.status_code == 200
    assert resp.get_json() == GOOD


@pytest.mark.parametrize(
    "exc, status",
    [(QueueUnavailable("x"), 503), (QueueTimeout("x"), 504), (BadReply("x"), 502)],
)
def test_queue_failures_become_gateway_errors(client, monkeypatch, exc, status):
    def boom(url):
        raise exc

    monkeypatch.setattr(app_module, "rpc_assess", boom)  # patch where it's USED
    resp = client.post("/api/v1/assess", json={"url": "https://example.com"})
    assert resp.status_code == status
    assert "error" in resp.get_json()


def test_health_reports_queue_state(client, monkeypatch):
    monkeypatch.setattr(app_module, "queue_is_up", lambda: False)
    assert client.get("/health").get_json() == {"api": "ok", "queue": "down"}


def test_parse_reply_accepts_a_valid_verdict():
    verdict, worker_id = _parse_reply(json.dumps({**GOOD, "worker_id": "w1"}).encode())
    assert verdict == GOOD
    assert worker_id == "w1"


@pytest.mark.parametrize(
    "body",
    [
        b"not json",
        b"[]",
        json.dumps({"error": "boom"}).encode(),
        json.dumps({**GOOD, "category": "spam"}).encode(),
        json.dumps({**GOOD, "confidence": 7}).encode(),
        json.dumps(
            {**GOOD, "is_malicious": False}
        ).encode(),  # phishing but "not malicious"
    ],
)
def test_parse_reply_rejects_bad_replies(body):
    with pytest.raises(BadReply):
        _parse_reply(body)
