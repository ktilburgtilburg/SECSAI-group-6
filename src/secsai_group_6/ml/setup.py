import os
from pathlib import Path

from secsai_group_6.ml.build_dataset import main as build_dataset_main
from secsai_group_6.ml.train import main as train_main


def main():
    os.chdir(Path(__file__).resolve().parents[3])
    print("=" * 70)
    print("STEP 1 / 2 — build feature matrix")
    print("=" * 70)
    build_dataset_main()
    print()
    print("=" * 70)
    print("STEP 2 / 2 — train classifier")
    print("=" * 70)
    train_main()


if __name__ == "__main__":
    main()