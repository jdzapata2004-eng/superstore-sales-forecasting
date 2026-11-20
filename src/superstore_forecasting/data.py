"""Load and validate the fields used by forecasting and EDA."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from superstore_forecasting.config import RAW_PATH

REQUIRED_COLUMNS = {
    "Order ID",
    "Order Date",
    "Sales",
    "Postal Code",
    "Category",
    "Segment",
    "Region",
}


def load_orders(path: str | Path = RAW_PATH) -> pd.DataFrame:
    """Validate the input contract and retain all rows and optional fields.

    Postal codes remain strings, with missing values preserved for EDA.
    """
    orders = pd.read_csv(path, dtype="string", keep_default_na=False)
    missing = REQUIRED_COLUMNS.difference(orders.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    if orders.empty:
        raise ValueError("The CSV has no sales records.")

    for column in ("Order ID", "Category", "Segment", "Region"):
        if orders[column].str.strip().eq("").any():
            raise ValueError(f"{column} must be non-empty text.")

    dates = orders["Order Date"]
    parsed_dates = pd.to_datetime(dates, format="%d/%m/%Y", errors="coerce")
    if (
        not dates.str.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}").all()
        or parsed_dates.isna().any()
    ):
        raise ValueError("Order Date must contain valid dates in dd/mm/yyyy format.")
    sales = pd.to_numeric(orders["Sales"], errors="coerce").astype(float)
    if not (np.isfinite(sales) & sales.gt(0)).all():
        raise ValueError("Sales must contain only finite, positive numbers.")

    orders["Order Date"] = parsed_dates
    orders["Sales"] = sales
    orders["Postal Code"] = orders["Postal Code"].mask(
        orders["Postal Code"].str.strip().eq("")
    )
    return orders


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=RAW_PATH)
    orders = load_orders(parser.parse_args().input)
    dates = orders["Order Date"]
    print(
        f"Valid rows: {len(orders)} | {dates.min():%Y-%m-%d} to {dates.max():%Y-%m-%d}"
    )


if __name__ == "__main__":
    main()
