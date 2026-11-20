"""Aggregate closed months and build predictors for the next month."""

import pandas as pd

from superstore_forecasting.config import SEASON

FEATURES = ("sales_lag_1", "sales_lag_12", "orders_lag_1", "ticket_lag_1")


def aggregate_monthly(orders: pd.DataFrame) -> pd.DataFrame:
    """Sum line sales and count distinct orders within each calendar month."""
    monthly = (
        orders.groupby(orders["Order Date"].dt.to_period("M"), sort=True)
        .agg(sales=("Sales", "sum"), orders=("Order ID", "nunique"))
        .rename_axis("month")
    )
    if monthly.empty:
        raise ValueError("At least one month of sales is required.")
    expected_months = pd.period_range(monthly.index[0], monthly.index[-1], freq="M")
    if not monthly.index.equals(expected_months):
        raise ValueError("Missing calendar months. Verify coverage before forecasting.")
    monthly["ticket"] = monthly["sales"] / monthly["orders"]
    return monthly


def make_features(monthly: pd.DataFrame) -> pd.DataFrame:
    """Build features for each observed month and one future month.

    Each predictor for month t uses data through month t-1 at the latest.
    """
    months = monthly.index.append(pd.PeriodIndex([monthly.index[-1] + 1]))
    observed = monthly.reindex(months)
    return pd.DataFrame(
        {
            "sales_lag_1": observed["sales"].shift(1),
            "sales_lag_12": observed["sales"].shift(SEASON),
            "orders_lag_1": observed["orders"].shift(1),
            "ticket_lag_1": observed["ticket"].shift(1),
        },
        index=months,
    )
