"""Destructive checks against ONLY the disposable compose.test.yaml project."""

import asyncio
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

from load_system import assess, load

BASE = "http://127.0.0.1:5000"
COMPOSE = ["docker", "compose", "-f", "compose.test.yaml"]


def compose(*args):
    return subprocess.check_output([*COMPOSE, *args], text=True)


def wait_ready():
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(BASE + "/health", timeout=3) as response:
                if json.load(response).get("queue") == "ok":
                    return
        except OSError:
            pass
        time.sleep(1)
    raise RuntimeError("API/broker did not become ready")


async def failures():
    os.environ["WORKER_DELAY"] = "0.8"
    compose("up", "-d", "--force-recreate", "--scale", "worker=3", "worker")
    wait_ready()
    victim = compose("ps", "-q", "worker").splitlines()[0]
    # Pause before starting traffic, then resume briefly to observe an unacked job.
    compose("pause", "worker")
    traffic = asyncio.create_task(load(BASE, 100, 6))
    try:
        await asyncio.sleep(0.2)
        compose("unpause", "worker")
        deadline = time.monotonic() + 10
        received = []
        while time.monotonic() < deadline:
            logs = await asyncio.to_thread(
                subprocess.check_output, ["docker", "logs", victim], text=True
            )
            received = [
                json.loads(line) for line in logs.splitlines() if line.startswith("{")
            ]
            if received:
                break
            await asyncio.sleep(0.01)
        assert received, "worker never received a job"
        # SIGKILL bypasses shutdown/ack. Match the same correlation ID on redelivery.
        await asyncio.to_thread(
            subprocess.check_call, ["docker", "kill", "--signal", "KILL", victim]
        )
        compose("up", "-d", "--scale", "worker=3")
        result = await traffic
        logs = compose("logs", "--no-log-prefix", "worker")
        events = [
            json.loads(line) for line in logs.splitlines() if line.startswith("{")
        ]
        original = {event["id"] for event in received}
        assert any(e["redelivered"] and e["id"] in original for e in events), logs
        result["redelivery_verified"] = True
    finally:
        await traffic

    compose("stop", "rabbitmq")
    try:
        broker = await asyncio.to_thread(assess, BASE, "https://example.com")
        assert broker["status"] == 503, broker
        assert broker["body"] == {"error": "Prediction service unavailable"}
        await asyncio.to_thread(
            subprocess.check_call,
            ["node", "--test", "tests/extension_failure.test.cjs"],
            env={**os.environ, "SYSTEM_OUTAGE_URL": BASE},
        )
    finally:
        compose("start", "rabbitmq")
        wait_ready()
        # Workers' broker connections died; explicitly recreate them for recovery.
        compose("up", "-d", "--force-recreate", "--scale", "worker=3", "worker")
    compose("stop", "worker")
    try:
        timeout = await asyncio.to_thread(assess, BASE, "https://example.com")
        assert timeout["status"] == 504, timeout
        assert timeout["body"] == {"error": "Prediction service timed out"}
        assert 1500 <= timeout["latency_ms"] < 15000, timeout
    finally:
        compose("start", "worker")
    recovery = await asyncio.to_thread(assess, BASE, "https://example.com")
    assert recovery["status"] == 200, recovery
    return {
        "recovery": recovery,
        "worker_kill": result,
        "broker_stop": broker,
        "all_workers_stop": timeout,
    }


async def main():
    out = Path("docs/system-results")
    out.mkdir(exist_ok=True)
    compose("up", "-d", "--build", "--scale", "worker=1")
    wait_ready()
    for workers in (1, 3):
        compose("up", "-d", "--scale", f"worker={workers}")
        await asyncio.sleep(2)
        warmup = await asyncio.to_thread(assess, BASE, "https://example.com")
        assert warmup["status"] == 200, warmup
        result = await load(BASE)
        result["workers"] = workers
        result["predictor"] = "see PREDICTOR environment; default stub"
        (out / f"workers-{workers}.json").write_text(json.dumps(result, indent=2))
        assert result["statuses"] == {"200": 500}, result["statuses"]
    # Clear old logs so the receipt used for the kill test belongs to this load.
    compose("up", "-d", "--force-recreate", "--scale", "worker=1", "worker")
    result = await failures()
    (out / "failures.json").write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
