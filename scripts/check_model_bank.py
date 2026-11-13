"""Record URL-bank predictions with explicit model identity; never visit URLs."""

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

from secsai_group_6.ml import predict as model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", choices=["before", "after"], required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    model.MODEL_DIR = args.model_dir
    hashes = {
        name: hashlib.sha256((args.model_dir / name).read_bytes()).hexdigest()
        for name in ("classifier.joblib", "label_classes.json")
    }
    bank = Path("tests/fixtures/urls.json")
    rows = []
    for case in json.loads(bank.read_text()):
        started = time.perf_counter()
        verdict = model.predict(case["url"])
        rows.append(
            {
                **case,
                "verdict": verdict,
                "latency_ms": (time.perf_counter() - started) * 1000,
                "correct": verdict["category"] == case["category"],
            }
        )
    result = {
        "label": args.label,
        "artifact_sha256": hashes,
        "bank_sha256": hashlib.sha256(bank.read_bytes()).hexdigest(),
        "revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "correct": sum(r["correct"] for r in rows),
        "total": len(rows),
        "rows": rows,
    }
    if args.compare:
        before = json.loads(args.compare.read_text())
        assert before["bank_sha256"] == result["bank_sha256"], "URL banks differ"
        result["correct_delta"] = result["correct"] - before["correct"]
        result["changes"] = [
            {
                "id": a["id"],
                "before": b["verdict"]["category"],
                "after": a["verdict"]["category"],
            }
            for b, a in zip(before["rows"], rows)
            if b["verdict"]["category"] != a["verdict"]["category"]
        ]
    args.output.write_text(json.dumps(result, indent=2))
    print(f"{args.label}: {result['correct']}/{result['total']} correct")


if __name__ == "__main__":
    main()
