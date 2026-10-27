import sqlite3
from contextlib import closing

import pytest

from secsai_group_6.backend import app as app_module
from secsai_group_6.backend.db import StorageError

URL = "/api/v1/feedback"
VALID = {
    "url": "https://user:pw@Example.com:8080/reset?token=abc#frag",
    "shown_category": "phishing",
    "reported_category": "benign",
}


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    monkeypatch.setitem(
        app_module.app.config, "DB_PATH", path
    )  # restored after the test
    return path


@pytest.fixture
def client(db_path):
    return app_module.app.test_client()


def read_rows(db_path):
    with closing(sqlite3.connect(db_path)) as conn:
        return conn.execute(
            "SELECT url, shown_category, reported_category FROM feedback"
        ).fetchall()


def test_saves_only_the_redacted_host(client, db_path):
    resp = client.post(URL, json=VALID)
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "saved"}
    assert read_rows(db_path) == [("https://example.com", "phishing", "benign")]


def test_duplicate_report_is_ignored(client, db_path):
    client.post(URL, json=VALID)
    resp = client.post(URL, json=VALID)
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "duplicate"}
    assert len(read_rows(db_path)) == 1


@pytest.mark.parametrize(
    "payload",
    [
        {**VALID, "url": "not a url"},
        {**VALID, "url": ""},
        {**VALID, "url": 123},
        {**VALID, "reported_category": "spam"},
        {**VALID, "shown_category": None},
        {"url": VALID["url"]},
        {},
    ],
)
def test_bad_payload_returns_400_json(client, db_path, payload):
    resp = client.post(URL, json=payload)
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_no_body_returns_400(client):
    assert client.post(URL).status_code == 400


def test_storage_failure_returns_500_json(client, monkeypatch):
    def boom(*args, **kwargs):
        raise StorageError("disk on fire")

    monkeypatch.setattr(app_module, "save_feedback", boom)  # patch where it's USED
    resp = client.post(URL, json=VALID)
    assert resp.status_code == 500
    assert resp.get_json() == {"error": "Could not save feedback"}
