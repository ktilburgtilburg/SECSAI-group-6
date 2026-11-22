"""Build the feature matrix from the cleaned dataset."""

import json
import os

import numpy as np

from secsai_group_6.ml.dataset import load_data, clean_data
from secsai_group_6.ml.features import extract_features, feature_names, strip_url

DATA_DIR = "data/processed"

COUNT_FEATURES = {
    "url_length", "hostname_length", "path_length", "query_length",
    "num_dots", "num_hyphens", "num_slashes", "num_at", "num_question",
    "num_equals", "num_digits", "num_underscores", "num_special_chars",
    "num_sensitive_words", "num_subdomains", "num_query_params",
    "edit_distance_to_nearest_brand", "num_subdomain_brand_matches",
}


def log_transform(X, names):
    X = X.copy()
    for j, name in enumerate(names):
        if name in COUNT_FEATURES:
            X[:, j] = np.log1p(X[:, j])
    return X


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    df = load_data("data/malicious_phish.csv")
    print(f"loaded: {len(df)} rows")

    clean, info = clean_data(df)
    print(f"cleaned: {info['rows_after']} rows "
          f"(dropped {info['conflict_rows']} conflicts, "
          f"{info['duplicate_rows']} duplicates)")
    print(f"labels: {info['labels_after']}")

    names = list(feature_names())
    rows, labels, keep = [], [], []
    skipped = 0
    total = len(clean)

    for i, (url, label) in enumerate(zip(clean["url"], clean["type"])):
        try:
            feats = extract_features(url)
            rows.append([feats[n] for n in names])
            labels.append(label)
            keep.append(i)
        except Exception as e:
            skipped += 1
            if skipped <= 5:
                print(f"  skip row {i}: {url!r} ({e!r})")
        if i and i % 50000 == 0:
            print(f"  extracted {i} / {total}")

    if skipped:
        print(f"  WARNING: skipped {skipped} malformed URLs")

    X = np.array(rows, dtype=float)
    y = np.array(labels, dtype=object)

    if np.isnan(X).any():
        raise ValueError("X contains NaN")
    if np.isinf(X).any():
        raise ValueError("X contains Inf")

    X = log_transform(X, names)

    np.save(f"{DATA_DIR}/X.npy", X)
    np.save(f"{DATA_DIR}/y.npy", y)
    with open(f"{DATA_DIR}/feature_names.json", "w") as f:
        json.dump(names, f, indent=2)

    print(f"saved X {X.shape}, y {y.shape}, features {len(names)}")


if __name__ == "__main__":
    main()