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

## Run

Prefix everything with `uv run`. No environment activation needed.

```bash
# Start the API server (http://127.0.0.1:5000)
uv run flask --app secsai_group_6.backend.app run --host 127.0.0.1 --port 5000 --debug

# Scan a URL from the terminal (exit code: 0 safe, 1 threat, 2 error)
uv run secsai --check https://example.com

# Run the tests
uv run pytest
```

The API contract is in [docs/api_spec.md](docs/api_spec.md). Test details are in
[tests/README.md](tests/README.md). GitHub Actions runs the tests on every push and pull request.

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
├── docs/api_spec.md
├── src/secsai_group_6/
│   ├── backend/        # Flask API: app.py, validation.py, db.py, stub_model.py
│   ├── ml/             # model and features
│   ├── categories.py   # the four verdict categories
│   └── cli.py          # terminal scanner
├── extension/          # browser extension
├── data/
├── notebooks/
└── tests/
```