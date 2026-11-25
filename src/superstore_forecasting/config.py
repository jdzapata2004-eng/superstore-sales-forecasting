"""Defaults for the verified Superstore snapshot."""

from pathlib import Path

DATASET = "rohitsahoo/sales-forecasting/versions/2"
FILENAME = "train.csv"
SHA256 = "a9b35af6cf9530e61d42ec22ef6d485799c0ee7d2e4710f1f803a71b8f1c29cb"
RAW_PATH = Path("data/raw") / FILENAME
ARTIFACTS = Path("artifacts")
EVAL_START = "2018-01"
EVAL_END = "2018-12"
TUNING_START = "2017-01"
TUNING_END = "2017-12"
RIDGE_ALPHAS = (0.1, 1.0, 10.0, 100.0)
SEASON = 12
RIDGE_ALPHA = 10.0
