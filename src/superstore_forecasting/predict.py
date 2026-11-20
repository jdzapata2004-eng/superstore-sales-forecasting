"""Forecast the month after an explicitly closed calendar month."""

import argparse
import json
from pathlib import Path

import pandas as pd

from superstore_forecasting.config import RAW_PATH
from superstore_forecasting.data import load_orders
from superstore_forecasting.features import aggregate_monthly, make_features
from superstore_forecasting.model import (
    BASELINE,
    MODELS,
    forecast_models,
    seasonal_naive,
)


def predict_next_month(
    orders: pd.DataFrame, *, through: str, model: str = BASELINE
) -> dict[str, str | float]:
    """Return a JSON-ready prediction from validated transaction history."""
    if model not in MODELS:
        raise ValueError(f"Unsupported model: {model}")
    cutoff = pd.Period(through, freq="M")
    order_months = orders["Order Date"].dt.to_period("M")
    monthly = aggregate_monthly(orders.loc[order_months <= cutoff])
    if monthly.index[-1] != cutoff:
        raise ValueError(f"No sales records in the requested closing month {cutoff}.")

    if model == BASELINE:
        features = make_features(monthly).iloc[[-1]]
        prediction = float(seasonal_naive(features).iloc[0])
        if pd.isna(prediction):
            raise ValueError("At least 12 months are required for seasonal prediction.")
    else:
        _, predictions = forecast_models(monthly)
        prediction = predictions[model]
    return {
        "through": str(cutoff),
        "month": str(cutoff + 1),
        "model": model,
        "predicted_sales": prediction,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=RAW_PATH)
    parser.add_argument("--through", required=True, help="Last closed month, YYYY-MM")
    parser.add_argument("--model", choices=MODELS, default=BASELINE)
    args = parser.parse_args()
    result = predict_next_month(
        load_orders(args.input), through=args.through, model=args.model
    )
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
