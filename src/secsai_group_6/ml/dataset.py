"""Load and clean the phishing URL dataset, and build the feature matrix.

After cleaning:
  - each URL appears exactly once
  - each URL has exactly one label
  - URLs with conflicting labels are removed entirely
"""

import json
import os

import numpy as np
import pandas as pd

from secsai_group_6.ml.features import extract_features, feature_names

URL_COL = "url"
LABEL_COL = "type"


def load_data(path: str) -> pd.DataFrame:
    """Read the raw CSV and return it as a DataFrame."""
    df = pd.read_csv(path)
    if URL_COL not in df.columns or LABEL_COL not in df.columns:
        raise ValueError(
            f"CSV must have columns '{URL_COL}' and '{LABEL_COL}'. "
            f"Found: {list(df.columns)}"
        )
    return df


def clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Remove duplicate URLs and URLs with conflicting labels.

    Returns the cleaned DataFrame plus a dict of counts.
    """
    info = {}
    info["rows_before"] = len(df)
    info["labels_before"] = df[LABEL_COL].value_counts().to_dict()

    # 1. Find URLs that have more than one label.
    labels_per_url = df.groupby(URL_COL)[LABEL_COL].nunique()
    bad_urls = labels_per_url[labels_per_url > 1].index

    info["bad_url_count"] = len(bad_urls)
    info["bad_url_rows"] = int(df[URL_COL].isin(bad_urls).sum())

    # 2. Remove every row whose URL is in bad_urls.
    df = df[~df[URL_COL].isin(bad_urls)].copy()

    # 3. Remove leftover repeated URLs (same label repeated).
    rows_before = len(df)
    df = df.drop_duplicates(subset=URL_COL, keep="first").reset_index(drop=True)
    info["extra_duplicate_rows"] = rows_before - len(df)

    info["rows_after"] = len(df)
    info["labels_after"] = df[LABEL_COL].value_counts().to_dict()

    # Safety checks
    assert df[URL_COL].is_unique, "clean_data() still has duplicate URLs"
    assert (
        info["rows_before"]
        == info["rows_after"] + info["bad_url_rows"] + info["extra_duplicate_rows"]
    ), "clean_data() row counts don't add up"

    return df, info


def build_features(clean_df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Turn a cleaned URL DataFrame into an X matrix and y label array.

    Args:
        clean_df: output of clean_data() — columns 'url' and 'type'.

    Returns:
        (X, y, names):
          - X: numpy array, shape (n_urls, n_features), dtype float
          - y: numpy array of string labels, shape (n_urls,)
          - names: list of feature column names, in the order X uses
    """
    names = feature_names()
    rows = []

    total = len(clean_df)
    for i, url in enumerate(clean_df[URL_COL]):
        feats = extract_features(url)
        rows.append([feats[n] for n in names])
        if i % 50000 == 0:
            print(f"  extracted {i} / {total}")

    X = np.array(rows, dtype=float)
    y = clean_df[LABEL_COL].to_numpy()

    # Safety check
    if np.isnan(X).any():
        raise ValueError("X contains NaN")
    if np.isinf(X).any():
        raise ValueError("X contains Inf")

    return X, y, names


def save_features(X: np.ndarray, y: np.ndarray, names: list[str], out_dir: str) -> None:
    """Save X, y and feature names to disk as .npy/.json files."""
    os.makedirs(out_dir, exist_ok=True)
    np.save(f"{out_dir}/X.npy", X)
    np.save(f"{out_dir}/y.npy", y)
    with open(f"{out_dir}/feature_names.json", "w") as f:
        json.dump(names, f, indent=2)
    print(f"saved X {X.shape}, y {y.shape}, feature names to {out_dir}")