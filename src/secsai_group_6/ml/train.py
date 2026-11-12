"""Train a phishing URL classifier on handcrafted features.

Reads X.npy / y.npy from data/processed/ ,
trains a RandomForestClassifier, saves the model to models/classifier.joblib,
and prints a validation classification report.
"""

import json
import os
import shutil

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

DATA_DIR = "data/processed"
MODEL_DIR = "models"


def main():
    # Load
    print("loading features...")
    X = np.load(f"{DATA_DIR}/X.npy")
    y = np.load(f"{DATA_DIR}/y.npy", allow_pickle=True)
    print(f"  X: {X.shape}  y: {y.shape}")
    print(f"  classes: {sorted(set(y))}")

    # Split
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, stratify=y_temp, random_state=42
    )
    print(f"  train: {len(X_train)}  val: {len(X_val)}  test: {len(X_test)}")

    # Train
    print("training RandomForest (100 trees)...")
    model = RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42)
    model.fit(X_train, y_train)

    # Validate
    y_val_pred = model.predict(X_val)
    print(f"\nval accuracy: {accuracy_score(y_val, y_val_pred):.4f}")
    print("\nclassification report (val):")
    print(classification_report(y_val, y_val_pred))

    # Test
    y_test_pred = model.predict(X_test)
    print(f"test accuracy: {accuracy_score(y_test, y_test_pred):.4f}")

    # Save
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, f"{MODEL_DIR}/classifier.joblib")
    print(f"\nsaved model to {MODEL_DIR}/classifier.joblib")

    # Save labels + feature names so predict.py uses the exact order the model was trained on.
    with open(f"{MODEL_DIR}/label_classes.json", "w") as f:
        json.dump(list(model.classes_), f, indent=2)
    shutil.copy(f"{DATA_DIR}/feature_names.json", f"{MODEL_DIR}/feature_names.json")
    print(f"saved labels and feature names to {MODEL_DIR}/")


if __name__ == "__main__":
    main()