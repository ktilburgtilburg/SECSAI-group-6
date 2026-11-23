"""Live HTTP/AMQP/SQLite checks; opt in with --system-url."""

import json
import subprocess
import uuid

import pytest
import requests

from tests.contracts import assert_verdict

pytestmark = pytest.mark.integration


def test_live_contract(request, url_case):
    base = request.config.getoption("--system-url").rstrip("/")
    response = requests.post(
        base + "/api/v1/assess", json={"url": url_case["url"]}, timeout=10
    )
    assert response.status_code == 200, response.text
    assert_verdict(response.json())


def test_live_validation(request):
    base = request.config.getoption("--system-url").rstrip("/")
    for body in ({}, {"url": 42}, {"url": ""}):
        response = requests.post(base + "/api/v1/assess", json=body, timeout=10)
        assert response.status_code == 400
        assert set(response.json()) == {"error"}


def test_live_feedback_committed(request):
    base = request.config.getoption("--system-url").rstrip("/")
    host = f"https://{uuid.uuid4().hex}.example.com"
    body = {
        "url": host + "/private?token=secret",
        "shown_category": "malicious",
        "reported_category": "benign",
    }
    for expected in ("saved", "duplicate"):
        response = requests.post(base + "/api/v1/feedback", json=body, timeout=10)
        assert response.status_code == 200
        assert response.json() == {"status": expected}
    # A separate process/connection reads the deployed database, not a mock.
    code = (
        "import sqlite3,json,os; c=sqlite3.connect(os.environ['DB_PATH']); "
        "print(json.dumps(c.execute('SELECT url,shown_category,reported_category "
        "FROM feedback WHERE url=?', (" + repr(host) + ",)).fetchall()))"
    )
    output = subprocess.check_output(
        [
            "docker",
            "compose",
            "-f",
            "compose.test.yaml",
            "exec",
            "-T",
            "api",
            "python",
            "-c",
            code,
        ],
        text=True,
    )
    assert json.loads(output) == [[host, "malicious", "benign"]]
