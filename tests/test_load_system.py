"""Exercise load accounting and client failures without contacting fixture URLs."""

import asyncio
import io
import socket
import threading
import time
import urllib.error

import pytest

from scripts import load_system

_SOCKET_CONNECT = socket.socket.connect


def test_load_sends_500_with_bounded_concurrency_and_counts_failures(monkeypatch):
    lock = threading.Lock()
    seen = set()
    active = 0
    peak = 0

    def assess(base, url):
        nonlocal active, peak
        index = int(url.rsplit("/", 1)[1])
        with lock:
            assert index not in seen
            seen.add(index)
            active += 1
            peak = max(peak, active)
        time.sleep(0.001)
        with lock:
            active -= 1
        return {
            "status": 503 if index % 10 == 0 else 200,
            "latency_ms": index + 1,
            "body": {},
        }

    monkeypatch.setattr(load_system, "assess", assess)
    # Windows asyncio creates an internal loopback socket pair at startup.
    # Permit that initialization, then restore the network guard for the load.
    with monkeypatch.context() as setup:
        setup.setattr(socket.socket, "connect", _SOCKET_CONNECT)
        runner = asyncio.Runner()
        runner.__enter__()
    try:
        result = runner.run(load_system.load("http://unused", 500, 6))
    finally:
        runner.close()
    assert seen == set(range(500))
    assert 1 < peak <= 6
    assert result["statuses"] == {"503": 50, "200": 450}
    assert len(result["samples"]) == 500
    assert result["p95_latency_ms"] == 475
    assert result["throughput_rps"] == pytest.approx(500 / result["duration_s"])
    assert result["successful_throughput_rps"] == pytest.approx(
        450 / result["duration_s"]
    )


@pytest.mark.parametrize(
    "body", [b'{"error":"unavailable"}', b"<html>bad gateway</html>"]
)
def test_http_errors_are_recorded_even_without_json(monkeypatch, body):
    def fail(*args, **kwargs):
        raise urllib.error.HTTPError(
            "http://unused", 503, "Unavailable", {}, io.BytesIO(body)
        )

    monkeypatch.setattr(load_system.urllib.request, "urlopen", fail)
    sample = load_system.assess("http://unused", "https://example.com")
    assert sample["status"] == 503
    assert sample["body"]["error"]
    assert sample["latency_ms"] >= 0


def test_connection_failure_is_recorded(monkeypatch):
    def fail(*args, **kwargs):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(load_system.urllib.request, "urlopen", fail)
    sample = load_system.assess("http://unused", "https://example.com")
    assert sample["status"] == 0
    assert "connection refused" in sample["body"]["error"]
