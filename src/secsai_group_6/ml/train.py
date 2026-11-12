"""Train the binary (benign vs malicious) URL classifier.

Model: RandomForestClassifier with tuned hyperparameters.
Reads:
    data/processed/X.npy
    data/processed/y.npy
    data/processed/feature_names.json

Writes:
    models/classifier.joblib
    models/label_classes.json
"""

import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, f1_score,
)
from sklearn.model_selection import train_test_split

DATA_DIR = "data/processed"
MODEL_DIR = "models"
SEED = 42

BEST_PARAMS = dict(
    n_estimators=200,
    max_depth=30,
    min_samples_leaf=1,
)


def build_model():
    return RandomForestClassifier(
        **BEST_PARAMS,
        class_weight="balanced",
        random_state=SEED,
        n_jobs=-1,
    )


def report(name, y_true, y_pred):
    print(f"\n{name} accuracy: {accuracy_score(y_true, y_pred):.4f}")
    print(f"{name} macro F1:  {f1_score(y_true, y_pred, average='macro', zero_division=0):.4f}")
    print(classification_report(y_true, y_pred, zero_division=0))


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)

    X = np.load(f"{DATA_DIR}/X.npy")
    y = np.load(f"{DATA_DIR}/y.npy", allow_pickle=True)
    names = json.load(open(f"{DATA_DIR}/feature_names.json"))

    if X.shape[0] != y.shape[0]:
        raise ValueError(f"row mismatch: X={X.shape[0]}, y={y.shape[0]}")

    print(f"X: {X.shape}  features: {len(names)}")
    print(f"classes: {dict(zip(*np.unique(y, return_counts=True)))}")

    idx = np.arange(len(y))
    idx_tv, idx_te = train_test_split(idx, test_size=0.10, stratify=y, random_state=SEED)
    idx_tr, idx_va = train_test_split(idx_tv, test_size=1/9, stratify=y[idx_tv], random_state=SEED + 1)

    X_tr, y_tr = X[idx_tr], y[idx_tr]
    X_va, y_va = X[idx_va], y[idx_va]
    X_te, y_te = X[idx_te], y[idx_te]
    print(f"train: {len(X_tr)}  val: {len(X_va)}  test: {len(X_te)}")

    print(f"\ntraining RandomForestClassifier ({BEST_PARAMS})...")
    model = build_model()
    model.fit(X_tr, y_tr)

    report("val", y_va, model.predict(X_va))
    y_te_pred = model.predict(X_te)
    report("test", y_te, y_te_pred)

    print("test confusion matrix (rows=true, cols=pred):")
    labels = ["benign", "malicious"]
    cm = confusion_matrix(y_te, y_te_pred, labels=labels)
    print(pd.DataFrame(cm, index=labels, columns=labels).to_string())

    proba = model.predict_proba(X_te)
    mal_idx = int(np.where(model.classes_ == "malicious")[0][0])
    mal_p = proba[:, mal_idx]
    benign_true = y_te == "benign"
    mal_true = y_te == "malicious"

    print(f"\n{'thr':>6s} {'FPR':>8s} {'recall':>8s} {'prec':>8s} {'F1_mal':>8s} {'F1_macro':>10s}")
    for t in [0.30, 0.40, 0.50, 0.55, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95]:
        flagged = mal_p >= t
        pred = np.where(flagged, "malicious", "benign")
        fp = int((flagged & benign_true).sum())
        tp = int((flagged & mal_true).sum())
        fpr = fp / max(int(benign_true.sum()), 1)
        rec = tp / max(int(mal_true.sum()), 1)
        prec = tp / max(int(flagged.sum()), 1)
        f1_mal = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        f1_macro = f1_score(y_te, pred, average="macro", zero_division=0)
        print(f"{t:>6.2f} {fpr:>8.4f} {rec:>8.4f} {prec:>8.4f} "
              f"{f1_mal:>8.4f} {f1_macro:>10.4f}")

    print("\nfeature importance (top 15):")
    for i in np.argsort(model.feature_importances_)[::-1][:15]:
        print(f"  {names[i]:42s}  {model.feature_importances_[i]:.4f}")

    joblib.dump(model, f"{MODEL_DIR}/classifier.joblib")
    with open(f"{MODEL_DIR}/label_classes.json", "w") as f:
        json.dump(list(model.classes_), f, indent=2)
    print(f"\nsaved model -> {MODEL_DIR}/classifier.joblib")


if __name__ == "__main__":
    main()