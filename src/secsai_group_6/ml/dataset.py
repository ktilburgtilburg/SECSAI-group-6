"""Load and clean the malicious_phish dataset."""

import pandas as pd

from secsai_group_6.ml.features import strip_url

URL_COL = "url"
LABEL_COL = "type"


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if URL_COL not in df.columns or LABEL_COL not in df.columns:
        raise ValueError(
            f"CSV must have columns '{URL_COL}' and '{LABEL_COL}'. "
            f"Found: {list(df.columns)}"
        )
    df[URL_COL] = df[URL_COL].astype(str).map(strip_url)
    return df


def clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    info = {}
    info["rows_before"] = len(df)
    info["labels_before"] = df[LABEL_COL].value_counts().to_dict()

    df = df.copy()
    df[LABEL_COL] = df[LABEL_COL].map(
        lambda x: "benign" if x == "benign" else "malicious"
    )
    info["labels_after_merge"] = df[LABEL_COL].value_counts().to_dict()

    labels_per_url = df.groupby(URL_COL)[LABEL_COL].nunique()
    conflicting = labels_per_url[labels_per_url > 1].index
    info["conflict_rows"] = int(df[URL_COL].isin(conflicting).sum())
    df = df[~df[URL_COL].isin(conflicting)].copy()

    before = len(df)
    df = df.drop_duplicates(subset=URL_COL, keep="first").reset_index(drop=True)
    info["duplicate_rows"] = before - len(df)

    info["rows_after"] = len(df)
    info["labels_after"] = df[LABEL_COL].value_counts().to_dict()

    assert df[URL_COL].is_unique
    assert set(df[LABEL_COL].unique()) <= {"benign", "malicious"}

    return df, info
