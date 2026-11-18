
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
    "category": "malicious",
    "confidence": 0.85,
    "explanations": ["x"],
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setitem(app_module.app.config, "DB_PATH", tmp_path / "gateway.db")
    return app_module.app.test_client()


def test_assess_returns_the_workers_verdict(client, monkeypatch):
    monkeypatch.setattr(app_module, "predict_rpc", lambda url: GOOD)

    resp = client.post("/api/v1/assess", json={"url": "https://example.com"})

    assert resp.status_code == 200
    assert resp.get_json() == GOOD


@pytest.mark.parametrize(
    "exc",
    [
        QueueUnavailable("x"),
        QueueTimeout("x"),
        BadReply("x"),
    ],
)
def test_queue_failures_become_gateway_errors(client, monkeypatch, exc):
    def boom(url):
        raise exc

    monkeypatch.setattr(app_module, "predict_rpc", boom)

    resp = client.post("/api/v1/assess", json={"url": "https://example.com"})

    assert resp.status_code == 500
    assert "error" in resp.get_json()


def test_health_reports_queue_state(client, monkeypatch):
    monkeypatch.setattr(app_module, "queue_is_up", lambda: False)

    assert client.get("/health").get_json() == {
        "status": "degraded",
        "queue": "down",
    }


def test_parse_reply_accepts_a_valid_verdict():
    verdict, worker_id = _parse_reply(
        json.dumps({**GOOD, "worker_id": "w1"}).encode()
    )

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
        json.dumps({**GOOD, "is_malicious": False}).encode(),
    ],
)
def test_parse_reply_rejects_bad_replies(body):
    with pytest.raises(BadReply):
        _parse_reply(body)
