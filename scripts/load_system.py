"""Bounded concurrent HTTP load, using only the standard library."""

import argparse
import asyncio
import json
import math
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


def assess(base, url):
    started = time.perf_counter()
    req = urllib.request.Request(
        base + "/api/v1/assess",
        data=json.dumps({"url": url}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            status, body = response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        status = exc.code
        try:
            body = json.load(exc)
        except (OSError, ValueError) as parse_error:
            body = {"error": f"Invalid HTTP error response: {parse_error}"}
        finally:
            exc.close()
    except (OSError, ValueError) as exc:
        status, body = 0, {"error": str(exc)}
    return {
        "status": status,
        "latency_ms": (time.perf_counter() - started) * 1000,
        "body": body,
    }


async def load(base, count=500, concurrency=6):
    semaphore = asyncio.Semaphore(concurrency)

    async def one(i):
        async with semaphore:
            return await asyncio.to_thread(
                assess, base, f"https://example.com/load/{i}"
            )

    started = time.perf_counter()
    samples = await asyncio.gather(*(one(i) for i in range(count)))
    duration = time.perf_counter() - started
    latencies = sorted(s["latency_ms"] for s in samples)
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "requests": count,
        "concurrency": concurrency,
        "duration_s": duration,
        "throughput_rps": count / duration,
        "successful_throughput_rps": sum(s["status"] == 200 for s in samples)
        / duration,
        "p95_latency_ms": latencies[math.ceil(0.95 * count) - 1],
        "statuses": dict(Counter(str(s["status"]) for s in samples)),
        "samples": samples,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:5000")
    parser.add_argument("--requests", type=int, default=500)
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.requests < 1 or args.concurrency < 1:
        parser.error("requests and concurrency must be positive")
    result = asyncio.run(load(args.url, args.requests, args.concurrency))
    args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != "samples"}, indent=2))
    raise SystemExit(0 if result["statuses"] == {"200": args.requests} else 1)
