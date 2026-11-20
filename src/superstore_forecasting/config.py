"""Defaults for the verified Superstore snapshot."""

from pathlib import Path

DATASET = "rohitsahoo/sales-forecasting/versions/2"
FILENAME = "train.csv"
SHA256 = "dbb0f167b27ccf02d7ff8cb0446a9abc6dbc3522e83cf9daa6939801acfdd196"
RAW_PATH = Path("data/raw") / FILENAME
ARTIFACTS = Path("artifacts")
EVAL_START = "2018-01"
EVAL_END = "2018-12"
TUNING_START = "2017-01"
TUNING_END = "2017-12"
RIDGE_ALPHAS = (0.1, 1.0, 10.0, 100.0)
SEASON = 12
RIDGE_ALPHA = 10.0
