"""Machine-learning package for malicious URL classification."""

from secsai_group_6.ml.dataset import clean_data, load_data
from secsai_group_6.ml.features import extract_features, feature_names, strip_url
from secsai_group_6.ml.predict import predict

__all__ = [
    "clean_data",
    "extract_features",
    "feature_names",
    "load_data",
    "predict",
    "strip_url",
]
