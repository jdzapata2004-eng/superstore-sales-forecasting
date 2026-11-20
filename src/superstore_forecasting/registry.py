"""Explicit promotion and prediction for registered Superstore models."""

import argparse
import json
import math
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
from mlflow import MlflowClient

from superstore_forecasting.config import RAW_PATH
from superstore_forecasting.data import load_orders
from superstore_forecasting.experiments import (
    REGISTERED_MODEL,
    configure_tracking,
    next_feature_row,
)
from superstore_forecasting.features import aggregate_monthly

CHAMPION = "champion"


def promote_champion(version: str) -> None:
    """Move the champion alias to an explicitly chosen, backtested version."""
    client = MlflowClient()
    candidate = client.get_model_version(REGISTERED_MODEL, version)
    if (
        candidate.status != "READY"
        or candidate.tags.get("validation_status") != "backtested"
    ):
        raise ValueError("Champion must be a READY version tagged backtested.")
    client.set_registered_model_alias(REGISTERED_MODEL, CHAMPION, version)


def predict_registered(
    orders: pd.DataFrame, *, through: str, version: str | None = None
) -> dict:
    """Score the next month with an immutable version or the current champion."""
    client = MlflowClient()
    if version is None:
        candidate = client.get_model_version_by_alias(REGISTERED_MODEL, CHAMPION)
    else:
        candidate = client.get_model_version(REGISTERED_MODEL, version)

    cutoff = pd.Period(through, freq="M")
    trained_through = pd.Period(candidate.tags["trained_through"], freq="M")
    if cutoff < trained_through:
        raise ValueError(
            "The forecast cutoff precedes the registered model's training cutoff."
        )
    order_months = orders["Order Date"].dt.to_period("M")
    monthly = aggregate_monthly(orders.loc[order_months <= cutoff])
    if monthly.index[-1] != cutoff:
        raise ValueError(f"No sales records in the requested closing month {cutoff}.")
    features = next_feature_row(monthly)
    if features.isna().any(axis=None):
        raise ValueError("Insufficient observed history for the next-month features.")
    model = mlflow.pyfunc.load_model(f"models:/{REGISTERED_MODEL}/{candidate.version}")
    prediction = float(np.asarray(model.predict(features)).item())
    if not math.isfinite(prediction):
        raise ValueError("The registered model returned a non-finite prediction.")
    return {
        "model": REGISTERED_MODEL,
        "version": candidate.version,
        "through": str(cutoff),
        "month": str(cutoff + 1),
        "predicted_sales": prediction,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracking-uri", default=None)
    commands = parser.add_subparsers(dest="command", required=True)
    promote = commands.add_parser("promote")
    promote.add_argument("--version", required=True)
    predict = commands.add_parser("predict")
    predict.add_argument(
        "--version", help="Numeric version. Defaults to the champion alias."
    )
    predict.add_argument("--input", type=Path, default=RAW_PATH)
    predict.add_argument("--through", required=True)
    args = parser.parse_args()
    configure_tracking(args.tracking_uri)
    if args.command == "promote":
        promote_champion(args.version)
        print(f"models:/{REGISTERED_MODEL}@{CHAMPION} -> version {args.version}")
    else:
        prediction = predict_registered(
            load_orders(args.input), through=args.through, version=args.version
        )
        print(json.dumps(prediction, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
