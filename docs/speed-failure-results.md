# Speed and failure verification

Branch: `test/speed-failure`, based on `origin/dev` at `c87781d`.
Local execution date: 2026-11-02. Environment: Windows, Python 3.12.15,
locked Python dependencies; Node 22.14.0 for extension tests.

## Results for the final report

| Requirement | Evidence | Result |
| --- | --- | --- |
| Average model scan strictly < 50 ms | `scripts/benchmark_scan.py` measures the real trained model | **Pending**: trained model artifacts absent; no valid speed number available |
| Extension handles backend failure | `tests/extension_failure.test.cjs`: 20 failed navigations, HTTP 503, invalid JSON, then recovery | **Passed** in isolated JavaScript runtime; browser smoke test pending |
| Reports save to database | Real Flask feedback endpoint, temporary SQLite file, read through independent connections; second client submits another report | **Passed** |
| Storage failure is recoverable | Real SQLite failure from missing parent directory returns JSON 500; subsequent valid storage saves successfully | **Passed** |

`uv run --locked pytest -q`: **61 passed in 1.30 s**.
`node --test tests/extension_failure.test.cjs`: **1 passed, 0 failed**.
The JavaScript test runs the actual extension source with a mocked Chrome event
API and fetch responses. Node treats uncaught asynchronous errors as test failures.
It verifies navigation handlers continue working after errors, but does not prove
that an actual browser survives a stopped Flask process.

The API and CLI contract tests explicitly inject the existing stub predictor;
these establish contracts and error handling, not trained-model speed or accuracy.
Feedback tests use real database writes with no storage mock except the existing
test of the custom storage exception handler. No user database is modified.

## Reproduce model speed

Run from the repository root with the intended deployment model at
`models/classifier.joblib` and its matching `models/label_classes.json`:

```sh
uv run --locked python scripts/benchmark_scan.py --rounds 100 --output docs/speed-results.json
```

Missing artifacts terminate with an error, rather than substituting a stub.
The benchmark records the first prediction separately, warms every corpus URL,
then performs 100 rounds over the 10 checked-in URLs (1,000 sequential scans).
Each timed scan includes feature extraction, model inference, and explanations.
URLs are input strings, never visited. Normal feature extraction may initialize
tldextract's suffix-list cache; use the same cache/network setup as deployment.
The mean must be **strictly less than 50 ms**; equality or a higher mean exits 1.
The JSON output records mean, p95 (nearest rank), maximum, first-scan latency,
sample count, runtime/platform, timestamp, and model/label hashes.

The requirement is interpreted as warm model time. HTTP round-trip, browser
scheduling, and startup time are excluded. If the course requires end-to-end or
cold-start latency below 50 ms, those need separate measurements. The fixed small
corpus is a reproducible smoke benchmark, not evidence for every possible URL.
Speed is deliberately separate from ordinary CI: CI has no deployment model and
shared runners cannot establish performance on the intended hardware.

## Browser smoke test: stop backend while browsing

Status: **not executed**. Use a disposable Chromium profile and record the browser
version, OS, result, and console evidence when executing these steps:

1. Load `extension/` as an unpacked extension. Open its service-worker console.
2. Start `uv run flask --app secsai_group_6.backend.app run --host 127.0.0.1 --port 5000`
   with the trained artifacts available. Visit `https://example.com/` and confirm
   a verdict log.
3. Stop Flask with Ctrl+C while the browser remains open. Navigate between safe
   public pages 20 times, including reloads. Confirm each page loads, the browser
   responds, and the service worker logs a caught `Failed to assess URL` error.
4. Restart Flask; navigate again and confirm verdict logging resumes without
   reloading the extension. Check the extension error panel for uncaught errors.
5. Record pass only if browsing remains responsive and assessment recovers.

Current behavior is fail open: an unavailable backend logs an error and supplies
no verdict; the extension does not cancel navigation. There is no user-facing
offline indicator and no explicit timeout for a server that accepts a request
but never responds. These are limits of current outage handling.

## Remaining evidence

Supply the intended trained model, run the benchmark, and add its generated JSON
to the final report. Execute the browser procedure before claiming the complete
course requirements have been proven. No speed figures or browser pass are
inferred from the stub or JavaScript test duration.
