# Composed-system verification

Run from the repository root with Docker Compose, Python dependencies (`uv sync
--locked`), and Node 22 available. This uses a separate `secsai-system-test`
Compose project, local port 5000, and a disposable feedback volume. Ensure the
port is free. Do not point these failure commands at a shared deployment.

```sh
docker compose -f compose.test.yaml up -d --build --scale worker=3
uv run python -c "import sys; sys.path.insert(0, 'scripts'); from verify_system import wait_ready; wait_ready()"
uv run pytest -m integration --system-url http://127.0.0.1:5000
uv run python scripts/verify_system.py
docker compose -f compose.test.yaml down -v
```

The runner sends exactly 500 measured requests at concurrency 6 for each of 1
and 3 workers, after an excluded warmup. JSON files in `docs/system-results/`
record every response, elapsed wall time, total and successful throughput, status
counts, and nearest-rank p95 latency across all responses. Failed responses stay
in the latency distribution; a benchmark with any non-200 response fails.
Both runs use the same API configuration and worker delay (100 ms).
The default worker uses the deterministic stub: these are transport/queue
measurements, **not trained-model inference measurements**. Set `PREDICTOR=model`
in the environment and supply matching artifacts in `models/` to measure the real
predictor. Record that setting alongside the generated results.

Failure checks use a longer 800 ms worker delay to make an unacknowledged
request observable. During a separate 100-request load, the runner SIGKILLs a
worker and requires a logged redelivery with the same correlation ID on a
survivor. Recovery of the job does not imply recovery of its original HTTP
request: the API has a two-second deadline and failures/latencies are retained.
Then it stops RabbitMQ, asserts the exact JSON 503, and runs the actual extension
background script with real HTTP responses in Node (20 navigations). It restarts
the broker and recreates disconnected workers, stops all workers, requires JSON
504 within 1.5–5 seconds, restarts workers, and checks assessment recovery.
Broker reconnect is explicit; workers currently do not reconnect automatically.
The Node test mocks Chrome APIs; an actual browser check remains separate.
Failure JSON is written only when all assertions pass; CI also retains logs.

CI runs live pytest, load, and failure checks in the `composed-system` job.
The unit suite continues to block network access; only explicitly selected live
tests permit network calls. Fixture URLs are submitted as strings, never visited.

## Modeler 2 comparison

Use the respective code checkout **and matching artifacts** for each run. The
script records revision, artifact hashes, URL-bank hash, predictions, labels,
accuracy count, and latency. Missing artifacts fail; no stub fallback is used.

```sh
uv run python scripts/check_model_bank.py --label before --model-dir models-before --output docs/model-before.json
# Switch to Modeler 2's fixed code and artifacts before the next command.
uv run python scripts/check_model_bank.py --label after --model-dir models-after --compare docs/model-before.json --output docs/model-after.json
```

These ten reference URLs are a smoke bank, not a representative accuracy study.
The two historically schemeless fixture URLs are intentionally retained.

## Local execution record — 2026-11-13

- Python 3.12: `python -m pytest -q -p no:cacheprovider --basetemp .tmp-pytest-system`:
  **104 passed, 12 live checks skipped**, 1.86 seconds (retest).
- Ruff checks and Python compilation: passed.
- Bundled Node 20.18.0: extension outage/recovery test **passed**; live broker
  outage test skipped (no composed system).
- Docker executable unavailable. Composed HTTP tests, both 500-request
  benchmarks, and injected failures **not executed**.
- Throughput and p95 for 1 worker: **unmeasured**; 3 workers: **unmeasured**.
- No trained artifacts or identified Modeler 2 fix revision are present. Before/
  after model results **pending** those inputs.

Retest also verified the load client with 500 synthetic responses: bounded
concurrency, request count, status accounting, throughput formulas, nearest-rank
p95, connection errors, and non-JSON HTTP errors. Fixed Compose worker-delay
interpolation and preserved non-JSON HTTP errors as load samples. These checks
do not measure deployed performance.

No live-system pass or performance improvement is claimed from the unit results.
