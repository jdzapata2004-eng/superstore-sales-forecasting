"""Create deterministic PNGs for the pinned Superstore snapshot."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from superstore_forecasting.config import ARTIFACTS, RAW_PATH
from superstore_forecasting.data import load_orders
from superstore_forecasting.features import aggregate_monthly


def generate_eda(orders: pd.DataFrame, output_dir: Path) -> None:
    monthly = aggregate_monthly(orders)
    output_dir.mkdir(parents=True, exist_ok=True)
    plots = (
        (
            "monthly_sales",
            monthly["sales"].set_axis(monthly.index.to_timestamp()),
            "line",
            "Ventas mensuales",
            "Ventas",
        ),
        (
            "sales_distribution",
            orders["Sales"],
            "hist",
            "Importe por línea",
            "Frecuencia",
        ),
        (
            "missing_values",
            (orders.isna() | orders.eq("").fillna(False)).sum().sort_index(),
            "barh",
            "Valores faltantes por columna",
            "Columna",
        ),
        (
            "sales_by_category",
            orders.groupby("Category")["Sales"].sum().sort_index(),
            "bar",
            "Ventas por categoría",
            "Ventas",
        ),
    )
    for filename, values, kind, title, ylabel in plots:
        fig, ax = plt.subplots(figsize=(10, 6))
        if kind == "hist":
            values.plot.hist(ax=ax, bins=40)
            ax.set_xlabel("Sales")
        else:
            values.plot(kind=kind, ax=ax)
        if kind == "barh":
            ax.set_xlabel("Cantidad de valores faltantes")
        ax.set(title=title, ylabel=ylabel)
        fig.tight_layout()
        fig.savefig(output_dir / f"{filename}.png", dpi=120)
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=RAW_PATH)
    parser.add_argument("--output-dir", type=Path, default=ARTIFACTS / "eda")
    args = parser.parse_args()
    generate_eda(load_orders(args.input), args.output_dir)
    print(args.output_dir)


if __name__ == "__main__":
    main()
