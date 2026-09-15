# SECSAI-group-6
The repo for the members of group 6 for the course Software Engineering for CSAI

---

## Project layout

```
SECSAI-group-6
├── .python-version        # Python version
├── pyproject.toml         # dependencies + project metadata
├── uv.lock                # exact pinned versions
├── .venv/                 # local environment
├── README.md
├── src/                   # source code
│   ├── text/
│   ├── image/
│   ├── link/
│   └── fusion/
├── data/                  # datasets
├── notebooks/             # exploration
└── tests/                 # pytest tests
```

---

## Set up

### 1. Install uv

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Alternatives**, if you'd rather use a package manager you already have:
```bash
# macOS (Homebrew)
brew install uv

# Windows (winget)
winget install --id=astral-sh.uv -e

# Any OS, if you already have pip somewhere
pip install uv
```

After installing, **close and reopen your terminal**, then check it worked:
```bash
uv --version
```

To update uv later:
```bash
uv self update
```

### 2. Get the project and set up the environment

Clone the repo, then let uv build the environment from the lockfile.
```bash
git clone https://github.com/ktilburgtilburg/SECSAI-group-6.git
cd SECSAI-group-6
uv sync
```

### 3. Running code

Prefix commands with `uv run` and they execute inside the project environment automatically - no activation needed:

```bash
uv run python main.py            # run a script
uv run python -m src.detector    # run a module
uv run pytest                    # run the tests
uv run jupyter lab               # start a notebook server
```

### 4. Adding, removing, and updating dependencies

Always manage packages through uv so `pyproject.toml` and `uv.lock` stay in sync. **After changing dependencies, commit both files** so teammates get the update on their next `uv sync`.

```bash
# Add a runtime dependency
uv add pillow                 # e.g. image handling
uv add "transformers>=4.40"   # version constraints work too

# Add a dev-only dependency (tests, linting - not shipped)
uv add --dev pytest ruff

# Remove a dependency
uv remove pillow

# Update everything to the newest allowed versions and re-lock
uv lock --upgrade
uv sync
```

When a teammate has pushed new dependencies and you pull their changes, just run:
```bash
uv sync
```
to bring your environment back in line with the updated lockfile.

---