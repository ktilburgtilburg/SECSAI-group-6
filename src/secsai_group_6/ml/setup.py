"""Build feature matrices and train the model. Run once after cloning.

Usage:
    uv run python -m secsai_group_6.ml.setup

Requires data/malicious_phish.csv. Produces:
    data/processed/X.npy, y.npy, feature_names.json
    models/classifier.joblib, label_classes.json, feature_names.json
"""

import os
from pathlib import Path

from secsai_group_6.ml.dataset import (
    build_features,
    clean_data,
    load_data,
    save_features,
)
from secsai_group_6.ml.train import main as train_main
os.chdir(Path(__file__).resolve().parents[3])


def build():
    """Load raw CSV, clean it, extract features, save matrices."""
    print("== building feature matrices ==")
    df = load_data("data/malicious_phish.csv")
    clean, info = clean_data(df)
    print(f"  cleaned: {info['rows_after']} rows")
    X, y, names = build_features(clean)
    save_features(X, y, names, "data/processed")


def main():
    build()
    print()
    train_main()


if __name__ == "__main__":
    main()