# System Requirements & Architecture Alignment

This document aligns the project requirements with the implemented system, explains architectural changes made during development, evaluates the latency requirement under the distributed queue architecture, and records the status of every requirement.

---

## 1. Model Change: 4-Class to Binary (`benign` vs. `malicious`)

**Original requirement:** Classify URLs into four categories (`benign`, `phishing`, `malware`, `defacement`).

**Implemented design:** Binary classification (`benign` vs. `malicious`) using a tuned Random Forest classifier combined with high-precision heuristic rules and human-readable explanations.

**Reason for change:**
- The `malicious_phish.csv` dataset contained significant label overlap and conflicting entries across the malicious sub-classes (`phishing`, `malware`, `defacement`), where lexical URL features alone could not reliably separate sub-types without hurting overall accuracy.
- From a user-protection perspective, the browser extension's core action is binary (allow vs. warn/block), while the `explanations` list already gives the user concrete context (e.g., typosquatting, risky TLD, IP host, credential keywords).
- Merging the three threat classes into `malicious` eliminated inter-threat confusion, simplified the API/extension contract, and improved detection reliability.

---

## 2. Distributed Architecture

Instead of running ML inference synchronously inside the Flask web server, the system is split into three containerized services orchestrated with Docker Compose (`docker-compose.yml`):

1. **Interface Server (`interface`)**: Flask HTTP REST API on port `5000`. Validates incoming URLs, checks broker health (`GET /health`), dispatches assessment jobs over RabbitMQ with a **2-second RPC timeout**, records request telemetry/feedback to SQLite, and returns strictly validated JSON responses.
2. **Message Broker (`rabbitmq`)**: RabbitMQ (`3-management`) on port `5672` (management UI on `15672`). Buffers scan requests on the `assess_requests` queue, load-balances jobs across workers (`prefetch_count=1`), and re-queues unacknowledged jobs if a worker crashes mid-request.
3. **ML Workers (`worker`)**: Stateless Python consumer processes (`src/secsai_group_6/backend/worker.py`) that warm up the Random Forest model at startup, pull jobs from `assess_requests`, run feature extraction and inference, publish verdicts back to each request's exclusive `reply_to` queue, and acknowledge messages only after replying. Workers scale horizontally via `docker compose up --build --scale worker=N`.

---

## 3. API Error Codes & Timeout Contract

Updated in [docs/api_spec.md](api_spec.md) to match the distributed gateway behavior:

- **2-second timeout**: `POST /api/v1/assess` enforces a 2.0 s RPC deadline waiting for a worker reply.
- **`400 Bad Request`**: Malformed JSON, wrong `Content-Type`, or invalid/empty/`>2048`-char URL.
- **`500 Internal Server Error`**: Unexpected internal error (`{"error": "Prediction failed"}` or `{"error": "Could not save feedback"}`).
- **`502 Bad Gateway`**: Worker returned an invalid or contract-violating reply (`{"error": "Invalid reply from prediction service"}`).
- **`503 Service Unavailable`**: RabbitMQ broker is unreachable or down (`{"error": "Prediction service unavailable"}`).
- **`504 Gateway Timeout`**: No worker replied within the 2-second timeout (`{"error": "Prediction service timed out"}`).

---

## 4. Speed Requirement (`< 50 ms`) Check with RabbitMQ in Between

| Measurement Scope | Evidence | Measured Result | `< 50 ms` Met? |
| --- | --- | --- | --- |
| **Warm ML inference only** (`predict(url)`, feature extraction + RF + explanations) | `docs/speed-results.json` (1,000 sequential scans on real model) | **14.65 ms mean**, **22.50 ms p95**, 63.66 ms max | **Yes** |
| **Live end-to-end with real model + RabbitMQ** (HTTP -> Flask -> RabbitMQ -> 3 ML Workers -> HTTP, 20 sequential requests) | Live measurement against `docker compose up --scale worker=3` | **57.3 ms mean**, **57.1 ms median** (min 46.3 ms, max 75.1 ms) | **Partly** (~7 ms over 50 ms due to per-request AMQP connect/teardown) |
| **Composed system under load** (HTTP -> Flask -> RabbitMQ -> Worker -> HTTP, concurrency 6, 100 ms stub delay) | `docs/system-results/workers-1.json` & `workers-3.json` | 1 worker: 9.80 rps, 615.5 ms p95; 3 workers: 29.38 rps, **208.9 ms p95** | **Partly** (transport + queueing overhead under concurrency) |

**Why `< 50 ms` does not strictly hold end-to-end through the queue:**
1. The model itself easily beats 50 ms (**14.65 ms** warm mean).
2. However, `predict_rpc()` currently opens a new TCP/AMQP connection, declares an exclusive reply queue, polls `process_data_events`, and tears down the connection on **every HTTP request**. That adds ~42 ms of HTTP + broker round-trip overhead on top of the ~15 ms model time, resulting in a **57.3 ms** live end-to-end mean.
3. Scaling from 1 to 3 workers triples throughput (9.80 -> 29.38 rps) and cuts p95 latency by ~3x, keeping typical interactive browsing well within the 2-second timeout budget, though strictly `< 50 ms` is only guaranteed for the warm model inference step itself.

---

## 5. Requirements Status Summary

| Requirement | Status | Explanation |
| --- | --- | --- |
| Classify URLs as benign or malicious | **Met** | Binary Random Forest + heuristic rules classify URLs accurately and return confidence + explanations. |
| 4-class threat categorization (`phishing`, `malware`, `defacement`) | **Dropped** | Replaced by binary `benign`/`malicious` due to noisy sub-class labels and simpler block/allow UX. |
| Human-readable threat explanations | **Met** | `predict()` returns up to 3 concrete reasons (e.g., typosquatting, risky TLD, IP host, credential words). |
| Distributed architecture (Interface + RabbitMQ + Workers) | **Met** | Decoupled Flask interface, RabbitMQ broker, and auto-reconnecting workers orchestrated via Docker Compose. |
| Horizontal worker scaling | **Met** | Verified with `--scale worker=3` (3x throughput gain from 9.80 to 29.38 rps and 3 active consumers). |
| Worker crash fault tolerance (job redelivery) | **Met** | Manual `basic_ack` ensures RabbitMQ re-queues unacknowledged jobs on worker SIGKILL (verified in `verify_system.py`). |
| API error contract (`400`, `500`, `502`, `503`, `504`) & 2 s timeout | **Met** | Implemented in `app.py` and verified by unit (`test_gateway.py`) and live system tests (`verify_system.py`). |
| Scan latency `< 50 ms` | **Partly Met** | Met for warm model inference (14.65 ms mean, 22.50 ms p95), but not guaranteed end-to-end through per-request RabbitMQ RPC overhead. |
| Real-time Chrome extension with warning screen & manual scan | **Met** | Monitors navigation, blocks malicious URLs with `warning.html`, supports bypass/back, and shows 3-state health dot. |
| Extension resilience during backend/broker outage (fail-open) | **Met** | Returns neutral `?` badge on 503/timeout without crashing or blocking navigation (verified in Node & Chrome). |
| User feedback persistence with URL privacy redaction | **Met** | `POST /api/v1/feedback` strips paths/queries/credentials to `scheme://hostname` and deduplicates in SQLite. |
| Terminal CLI scanner (`secsai --check`) | **Met** | Queries `/api/v1/assess` and exits with `0` (safe), `1` (malicious), or `2` (error). |
| Automated unit, integration & system test suites | **Met** | 106 unit tests, 12 live integration tests, Node extension tests, and `verify_system.py` all pass. |

