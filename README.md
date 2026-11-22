# SECSAI — Real-Time URL Phishing & Threat Detector

Protect your browser from malicious websites and phishing links in real time using a Chrome extension powered by machine learning.

---

## Quick Start: Try the App in 3 Steps

### Step 1: Requirements

Make sure you have the following installed on your computer:
1. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** (start it before running the app).
2. **Google Chrome** (or any Chromium browser like Edge or Brave).
3. **[uv](https://docs.astral.sh/uv/)** (package tool for Python):
   - **macOS / Linux**:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   - **Windows (PowerShell)**:
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```

---

### Step 2: Download & Start the App

Open your terminal and run:

```bash
# Clone the repository
git clone https://github.com/ktilburgtilburg/SECSAI-group-6.git
cd SECSAI-group-6

# Start the complete backend (API, message broker, and AI worker)
docker compose up --build
```

> **Note:** Wait a few moments until you see `Running on http://127.0.0.1:5000`. The backend is now ready!

---

### Step 3: Add the Extension to Chrome

1. Open Chrome and go to the address `chrome://extensions`.
2. Toggle **Developer mode** in the top-right corner to **ON**.
3. Click **Load unpacked** in the top-left corner.
4. Select the `extension` folder inside the `SECSAI-group-6` directory.
5. In your browser toolbar, click the puzzle piece icon and **Pin** the SECSAI extension so its icon is visible.

---


Once the extension is installed and the backend is running, test it out:

1. **Safe Website**:
   - Go to `https://www.wikipedia.org` or `https://github.com`.
   - The extension will let you visit the website.

2. **Malicious / Phishing Website**:
   - Go to `http://icloudvsmapalocaliza.click`.
   - The page is blocked! You will see a  warning screen explaining the threat, with buttons to return safely or proceed if you choose.

3. **Check Connection Status**:
   - Click the SECSAI icon in your browser toolbar to open the popup:
     - 🟢 **Green ("Online")**: Connected and actively protecting your browser.
     - 🟠 **Orange ("Queue Down")**: Server is reachable, but background queue is offline.
     - 🔴 **Red ("API Down")**: Backend server is offline.

4. **Manual Scan**:
   - You can also type or paste any URL directly into the popup input box and click **Assess URL** to check it manually.

---

## Stopping the App

When you are finished testing, press `Ctrl + C` in the terminal where Docker is running, or run:

```bash
docker compose down
```

---

## For Developers & Testing

<details>
<summary><strong>Click to view testing and developer commands</strong></summary>

### Scan a URL from Terminal (CLI)

```bash
uv run secsai --check https://example.com
```

### Run Automated Tests

```bash
# Run unit and contract tests (106 tests)
uv run pytest

# Run extension resilience tests
node --test tests/extension_failure.test.cjs

# Run full distributed system verification (load, worker crash, broker outage, recovery)
uv run python scripts/verify_system.py
```

### Scale Inference Workers

To run 3 parallel background AI workers:

```bash
docker compose up --build --scale worker=3
```

Check the RabbitMQ queue dashboard at [http://localhost:15672](http://localhost:15672) (Username: `guest`, Password: `guest`).

### Retrain the Machine Learning Model

The Random Forest model artifacts are stored in `models/` (`classifier.joblib` and `label_classes.json`). To rebuild features and retrain from `data/malicious_phish.csv`:

```bash
uv run python -m secsai_group_6.ml.setup
```

### Project Layout

```
SECSAI-group-6
├── extension/          # Chrome extension (manifest.json, background.js, popup UI, warning screen)
├── src/secsai_group_6/
│   ├── backend/        # Flask REST API, RabbitMQ client, background worker, SQLite database
│   ├── ml/             # ML model inference, feature extraction, training pipeline
│   ├── categories.py   # Verdict categories (benign, malicious)
│   └── cli.py          # Terminal scanner CLI
├── docker-compose.yml  # Multi-service setup (rabbitmq, interface, worker)
├── models/             # Pretrained model artifacts
├── data/               # Raw and processed datasets
└── tests/              # Test suite and contracts
```

</details>
