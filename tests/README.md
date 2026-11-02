# Test suite

Run from the repository root:

```sh
uv run --locked pytest
node --test tests/extension_failure.test.cjs
```

Python tests need no running server, dataset, trained model, or credentials.
They block network access. Flask's test client calls the application in process;
feedback tests use temporary SQLite files and read committed rows through new
connections. API and CLI contract tests explicitly inject the existing stub
predictor. Model unit tests characterize that stub, not classifier accuracy.
Both suites run in GitHub Actions; Node 22 or later is recommended locally.

`fixtures/urls.json` has five benign reference URLs, three historical phishing
URLs, and two historical malware URLs from the Malicious URLs dataset used by
the project notebook. Labels are metadata, not expected stub outputs. Malicious
URLs are only passed as strings; tests never visit them.

The extension test evaluates the actual background script in Node with mocked
Chrome events and fetch. It verifies repeated connection failures, HTTP errors,
invalid JSON, navigation filtering, and recovery without unhandled errors.
It does not replace a browser test.

For real model timings, run separately with the intended trained artifacts:

```sh
uv run --locked python scripts/benchmark_scan.py --rounds 100
```

The command fails if the model is missing or the mean is >=50 ms. It never uses
the stub. See [the test-results document](../docs/speed-failure-results.md) for
recorded results, measurement scope, and the backend-stop browser procedure.
