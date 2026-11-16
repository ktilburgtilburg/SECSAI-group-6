import requests

from secsai_group_6 import cli

SAFE = {
    "is_malicious": False,
    "category": "benign",
    "confidence": 0.9,
    "explanations": [],
}
THREAT = {
    "is_malicious": True,
    "category": "phishing",
    "confidence": 0.85,
    "explanations": ["x"],
}


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def api_returns(monkeypatch, status, payload):
    monkeypatch.setattr(
        cli.requests, "post", lambda *a, **kw: FakeResponse(status, payload)
    )


def test_safe_exits_0(monkeypatch, capsys):
    api_returns(monkeypatch, 200, SAFE)
    assert cli.main(["--check", "https://example.com"]) == 0
    assert "SAFE" in capsys.readouterr().out


def test_threat_exits_1(monkeypatch, capsys):
    api_returns(monkeypatch, 200, THREAT)
    assert cli.main(["--check", "https://evil.example"]) == 1
    assert "MALICIOUS" in capsys.readouterr().out


def test_api_error_exits_2_and_shows_the_message(monkeypatch, capsys):
    api_returns(monkeypatch, 400, {"error": "Field 'url' must be non-empty"})
    assert cli.main(["--check", "   "]) == 2
    assert "must be non-empty" in capsys.readouterr().err


def test_unreachable_api_exits_2(monkeypatch, capsys):
    def refuse(*args, **kwargs):
        raise requests.ConnectionError("refused")

    monkeypatch.setattr(cli.requests, "post", refuse)
    assert cli.main(["--check", "https://example.com"]) == 2
    assert "cannot reach" in capsys.readouterr().err
