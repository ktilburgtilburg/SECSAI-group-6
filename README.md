# SECSAI-group-6

URL threat assessment: a local API, a CLI scanner, and a browser extension.
Group 6, Software Engineering for CSAI.

## Set up

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/):

   ```bash
   # macOS / Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   Reopen your terminal and check with `uv --version`.

2. Clone and install:

   ```bash
   git clone https://github.com/ktilburgtilburg/SECSAI-group-6.git
   cd SECSAI-group-6
   uv sync
   ```

## Run (Local Development)

Prefix everything with `uv run`. No environment activation needed.

```bash
# Start the API server (http://127.0.0.1:5000)
uv run flask --app secsai_group_6.backend.app run --host 127.0.0.1 --port 5000 --debug

# Scan a URL from the terminal (exit code: 0 safe, 1 threat, 2 error)
uv run secsai --check https://example.com

# Run the tests
uv run pytest
node --test tests/extension_failure.test.cjs
```

The API contract is in [docs/api_spec.md](docs/api_spec.md). Test details are in
[tests/README.md](tests/README.md). GitHub Actions runs the tests on every push and pull request.

---

## How to run the distributed system

The distributed system decouples the web ingress from ML inference using RabbitMQ as a message broker:
- **`rabbitmq`**: RabbitMQ message broker with management dashboard.
- **`interface`**: Flask HTTP REST API accepting requests from the browser extension and dispatching RPC scan jobs.
- **`worker`**: Background ML workers consuming scan jobs from RabbitMQ, running model inference, and replying with threat verdicts.

### 1. Start the distributed system

Start all services with a single command:

```bash
docker compose up --build
```

### 2. Scale workers

To scale the number of inference workers (e.g. running 3 parallel model workers):

```bash
docker compose up --build --scale worker=3
```

### 3. Verify services

- **RabbitMQ Dashboard**: Open `http://localhost:15672` (username: `guest`, password: `guest`).
  - Navigate to the **Queues** tab and select `url_scans`.
  - When `--scale worker=3` is active, the dashboard will show **3 Consumers**.
- **Interface API**:
  - Health check: `curl http://localhost:5000/health`
    Returns `{"status": "ok", "queue": "ok"}` when the queue is connected.
  - Assess URL:
    ```bash
    curl -X POST http://localhost:5000/api/v1/assess \
         -H "Content-Type: application/json" \
         -d '{"url": "https://example.com/login"}'
    ```
- **Browser Extension**:
  1. Open Chrome/Chromium and navigate to `chrome://extensions`.
  2. Enable **Developer mode** (top right).
  3. Click **Load unpacked** and select the `extension/` folder.
  4. The toolbar popup status dot reflects the system state:
     - **Green ("Online")**: API and RabbitMQ queue are healthy.
     - **Orange ("Queue Down")**: API is running, but RabbitMQ is unreachable or down.
     - **Red ("API Down")**: API server is completely offline.
  5. If the queue is down or a scan request times out, the backend returns HTTP 503 and the extension calmly displays a neutral **"COULDN'T VERIFY"** badge without interrupting navigation or crashing.

### 4. Stop the distributed system

```bash
docker compose down
```

---

## Dependencies

```bash
uv add <package>         # add a dependency
uv add --dev <package>   # add a dev-only dependency
uv sync                  # after pulling someone else's changes
```

Commit both `pyproject.toml` and `uv.lock` after changing dependencies.

## Layout

```
SECSAI-group-6
├── docker-compose.yml  # multi-service orchestration (rabbitmq, interface, worker)
├── Dockerfile          # container image for interface and worker
├── docs/api_spec.md
├── src/secsai_group_6/
│   ├── backend/        # Flask API: app.py, worker.py, validation.py, db.py, stub_model.py
│   ├── ml/             # model and features
│   ├── categories.py   # the four verdict categories
│   └── cli.py          # terminal scanner
├── extension/          # browser extension (service worker, popup UI, warning screen)
├── data/
├── notebooks/
└── tests/
```
