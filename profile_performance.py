import time
import statistics
import numpy as np

from secsai_group_6.ml.predict import _load
from secsai_group_6.ml.features import extract_features, feature_names

urls = [
    "https://www.google.com",
    "https://www.wikipedia.org",
    "http://192.168.1.1/login",
    "http://secure-login.example.com/verify",
    "http://a.b.c.d.example.com",
]

model, classes = _load()
model.n_jobs = 1
names = feature_names()

feature_times = []
model_times = []

# Warm up
for url in urls:
    features = extract_features(url)
    X = np.array([[features[n] for n in names]], dtype=float)
    model.predict_proba(X)

for _ in range(100):
    for url in urls:
        start = time.perf_counter_ns()
        features = extract_features(url)
        X = np.array([[features[n] for n in names]], dtype=float)
        middle = time.perf_counter_ns()

        model.predict_proba(X)
        end = time.perf_counter_ns()

        feature_times.append((middle - start) / 1_000_000)
        model_times.append((end - middle) / 1_000_000)

print(f"Feature extraction: {statistics.mean(feature_times):.3f} ms")
print(f"Model prediction:   {statistics.mean(model_times):.3f} ms")
print(f"Total:              {statistics.mean(feature_times) + statistics.mean(model_times):.3f} ms")