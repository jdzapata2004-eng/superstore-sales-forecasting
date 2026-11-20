"""Evaluate forecasts on fixed, chronological walk-forward folds."""

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from superstore_forecasting.config import (
    ARTIFACTS,
    EVAL_END,
    EVAL_START,
    RAW_PATH,
    RIDGE_ALPHA,
    SEASON,
)
from superstore_forecasting.data import load_orders
from superstore_forecasting.features import aggregate_monthly
from superstore_forecasting.model import MODELS, forecast_models


def evaluate_walk_forward(
    monthly: pd.DataFrame,
    start: str = EVAL_START,
    end: str = EVAL_END,
    *,
    alpha: float = RIDGE_ALPHA,
) -> tuple[pd.DataFrame, dict]:
    """Predict each evaluation month using only months strictly before it."""
    months = pd.period_range(start, end, freq="M")
    if months.empty or not months.isin(monthly.index).all():
        raise ValueError("The evaluation window must contain observed months.")

    rows = []
    for month in months:
        forecast_month, forecasts = forecast_models(
            monthly.loc[monthly.index < month], alpha=alpha
        )
        if forecast_month != month:
            raise ValueError(f"Forecast cutoff does not precede {month}.")
        rows.append(
            {"month": str(month), "actual": monthly.at[month, "sales"], **forecasts}
        )

    predictions = pd.DataFrame(rows)
    metrics = {
        name: {
            "mae": float(mean_absolute_error(predictions["actual"], predictions[name])),
            "rmse": float(
                root_mean_squared_error(predictions["actual"], predictions[name])
            ),
        }
        for name in MODELS
    }
    # MODELS puts the seasonal baseline first, so it wins a tie.
    selected = min(MODELS, key=lambda name: metrics[name]["mae"])
    return predictions, {
        "evaluation_start": str(months[0]),
        "evaluation_end": str(months[-1]),
        "folds": len(months),
        "horizon_months": 1,
        "season_months": SEASON,
        "ridge_alpha": alpha,
        "metrics": metrics,
        "selected_model": selected,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=RAW_PATH)
    parser.add_argument("--start", default=EVAL_START)
    parser.add_argument("--end", default=EVAL_END)
    parser.add_argument("--output-dir", type=Path, default=ARTIFACTS / "evaluation")
    args = parser.parse_args()

    predictions, summary = evaluate_walk_forward(
        aggregate_monthly(load_orders(args.input)), args.start, args.end
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(args.output_dir / "predictions.csv", index=False)
    report = json.dumps(summary, indent=2, allow_nan=False)
    (args.output_dir / "metrics.json").write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
