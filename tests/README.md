# Week 1 prototype tests

Run from the repository root:

```bash
uv run pytest
```

uv installs the locked dependencies, including pytest, automatically. No server,
dataset download, trained model, credentials, or internet access is needed during
the tests. Flask's test client calls the real application in process. An autouse
fixture rejects socket connections and DNS lookups.

## URL corpus

`fixtures/urls.json` contains five safe reference sites (Wikipedia, GitHub,
Python, Mozilla, Tilburg University), three historically labeled phishing URLs,
and two historically labeled malware URLs. The five malicious examples are the
first three phishing and first two malware rows in the local
`data/malicious_phish.csv` used by `notebooks/phishing_URL_EDA.ipynb`.
The notebook identifies its source as the
[Malicious URLs dataset](https://www.kaggle.com/datasets/sid321axn/malicious-urls-dataset).
The original URL strings, including absent schemes, are preserved. The small
JSON fixture is checked in so tests do not depend on the ignored CSV.

These are historical dataset labels, not a claim about current site contents.
Do not open the malicious examples. Tests pass them only as strings to the
local model and API.

## What passing means

The suite checks the `docs/api_spec.md` response contract: exact fields, JSON
types, finite confidence within [0, 1], a supported category (`benign`,
`phishing`, `malware`, `defacement`), and consistency with `is_malicious`.
Every corpus URL exercises both the real assess endpoint and the real stub
prediction function. Additional tests cover health, malformed requests, JSON
HTTP errors, trimmed URL forwarding, and model failures.

The corpus `category` is ground truth metadata, not an expected Week 1 output.
The Week 1 stub classifies only URLs containing `login` as phishing and all
others as benign. Its two branches and case handling are tested explicitly.
Passing contract tests does **not** establish detection accuracy on these
historical threats. Add separate accuracy tests when a trained model replaces
the stub; do not rewrite these labels to match the stub.

Feedback is documented but is not implemented on this baseline, so it is not
included in the Week 1 suite.

## Repository and GitHub baseline

- Branch `test/week1-prototype-suite` starts from `origin/dev` at `1076b46`
  (`BE: add assess endpoint`), which contains the Week 1 Flask API and stub.
- `origin/main` at inspection contains notebooks and a placeholder package;
  `origin/feature/mvp-prototype` has a separate, larger implementation. This
  suite targets the documented Week 1 API on `dev`.
- The baseline has pytest and Flask dependencies locked, but no tests,
  pytest configuration, or GitHub Actions workflow.
- `.github/workflows/tests.yml` now runs the same command on pushes and pull
  requests, using Python 3.12 and `uv sync --locked`. Failed tests fail the job.
- Remote branch protection and required-check settings were not inspected or
  changed. GitHub execution can be confirmed after the branch is pushed.

Local validation: `uv run pytest` on Python 3.12.13: **45 passed**.
