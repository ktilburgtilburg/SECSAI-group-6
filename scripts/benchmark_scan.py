"""Measure real, warm model scans; exit nonzero unless mean is strictly <50ms."""

import argparse
import hashlib
import json
import platform
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from time import perf_counter_ns


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=100)
    parser.add_argument("--output", type=Path, default=Path("docs/speed-results.json"))
    args = parser.parse_args()
    if args.rounds < 1:
        parser.error("--rounds must be positive")
    for artifact in ("classifier.joblib", "label_classes.json"):
        if not (Path("models") / artifact).is_file():
            parser.error(
                f"models/{artifact} missing; supply the trained model before measuring speed"
            )
    from secsai_group_6.ml.predict import predict

    cases = json.loads(Path("tests/fixtures/urls.json").read_text())
    # Loading and first-use initialization are reported separately, never hidden.
    start = perf_counter_ns()
    predict(cases[0]["url"])
    cold_ms = (perf_counter_ns() - start) / 1e6
    for case in cases:
        predict(case["url"])
    timings = []
    for _ in range(args.rounds):
        for case in cases:
            start = perf_counter_ns()
            predict(case["url"])
            timings.append((perf_counter_ns() - start) / 1e6)
    ordered = sorted(timings)
    result = {
        "measured_at": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "model_sha256": hashlib.sha256(
            Path("models/classifier.joblib").read_bytes()
        ).hexdigest(),
        "labels_sha256": hashlib.sha256(
            Path("models/label_classes.json").read_bytes()
        ).hexdigest(),
        "samples": len(timings),
        "cold_first_scan_ms": cold_ms,
        "mean_ms": mean(timings),
        "p95_ms": ordered[(95 * len(ordered) + 99) // 100 - 1],
        "max_ms": max(timings),
        "threshold_ms": 50,
        "passed": mean(timings) < 50,
        "scope": "Warm predict(url), including feature extraction; excludes HTTP/browser latency",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
