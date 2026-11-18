import os
import time
import statistics

import pytest

from secsai_group_6.ml.predict import predict


MODEL_PATH = "models/classifier.joblib"

pytestmark = pytest.mark.skipif(
    not os.path.exists(MODEL_PATH),
    reason="Classifier model not available",
)


def test_prediction_speed():
    urls = [
        "https://www.google.com",
        "https://www.wikipedia.org",
        "http://192.168.1.1/login",
        "http://secure-login.example.com/verify",
        "http://a.b.c.d.example.com",
    ]

    # Warm up model
    for url in urls:
        predict(url)

    times = []
    for _ in range(100):
        for url in urls:
            start = time.perf_counter_ns()
            predict(url)
            elapsed = (time.perf_counter_ns() - start) / 1_000_000
            times.append(elapsed)

    times.sort()

    average = statistics.mean(times)
    median = statistics.median(times)
    p95 = times[int(0.95 * (len(times) - 1))]
    maximum = max(times)

    print(f"\nPredictions tested: {len(times)}")
    print(f"Average: {average:.3f} ms")
    print(f"Median: {median:.3f} ms")
    print(f"P95:     {p95:.3f} ms")
    print(f"Maximum: {maximum:.3f} ms")

    # Performance requirement
    assert p95 < 50, (
        f"P95 prediction time exceeded 50 ms: {p95:.3f} ms"
    )