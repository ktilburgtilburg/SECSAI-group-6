import pytest

from tests.contracts import assert_verdict


def assert_error(response, status):
    assert response.status_code == status
    assert response.is_json
    body = response.get_json()
    assert set(body) == {"error"}
    assert isinstance(body["error"], str) and body["error"]


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == {"status": "ok", "queue": "ok"}


def test_assess_contract(client, url_case):
    response = client.post("/api/v1/assess", json={"url": url_case["url"]})
    assert response.status_code == 200
    assert response.is_json
    assert_verdict(response.get_json())


@pytest.mark.parametrize(
    "body",
    [
        None,
        [],
        "url",
        42,
        True,
        {},
        {"url": None},
        {"url": 123},
        {"url": False},
        {"url": []},
        {"url": {}},
        {"url": ""},
        {"url": " \t\n"},
    ],
)
def test_invalid_body(client, body):
    assert_error(client.post("/api/v1/assess", json=body), 400)


@pytest.mark.parametrize(
    "data, content_type",
    [
        ("", "application/json"),
        ('{"url":', "application/json"),
        ('{"url":"https://example.test"}', "text/plain"),
    ],
)
def test_invalid_json(client, data, content_type):
    assert_error(
        client.post("/api/v1/assess", data=data, content_type=content_type), 400
    )


def test_assess_passes_trimmed_url_to_model(client, api_module, monkeypatch):
    calls = []
    verdict = {
        "is_malicious": True,
        "category": "malware",
        "confidence": 0.93,
        "explanations": ["Model reason"],
    }

    def predict(url):
        calls.append(url)
        return verdict

    monkeypatch.setattr(api_module, "rpc_assess", lambda url: (predict(url), "unit"))
    response = client.post("/api/v1/assess", json={"url": "  https://example.test/  "})
    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == verdict
    assert calls == ["https://example.test/"]


def test_prediction_failure_returns_json(client, api_module, monkeypatch):
    def fail(url):
        from secsai_group_6.backend.rpc_client import BadReply

        raise BadReply("internal model detail")

    monkeypatch.setattr(api_module, "rpc_assess", fail)
    response = client.post("/api/v1/assess", json={"url": "https://example.test/"})
    assert_error(response, 502)
    assert response.get_json() == {"error": "Invalid reply from prediction service"}


@pytest.mark.parametrize(
    "method, path, status",
    [
        ("get", "/missing", 404),
        ("get", "/api/v1/assess", 405),
    ],
)
def test_http_errors_are_json(client, method, path, status):
    assert_error(getattr(client, method)(path), status)
