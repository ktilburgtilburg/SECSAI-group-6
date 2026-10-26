import time
import statistics

from secsai_group_6.ml.predict import predict


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

    print(f"\nAverage: {statistics.mean(times):.3f} ms")
    print(f"Median: {statistics.median(times):.3f} ms")
    print(f"Maximum: {max(times):.3f} ms")

    assert max(times) < 10, "Prediction exceeded 10 ms"