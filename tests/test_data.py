import pandas as pd
import pytest

from superstore_forecasting.data import load_orders
from superstore_forecasting.features import aggregate_monthly

HEADER = "Order ID,Order Date,Sales,Postal Code,Category,Segment,Region"
VALID = "A,02/03/2018,10,,Furniture,Consumer,West"


def test_validation_preserves_missing_postal_code_and_leading_zero(tmp_path):
    path = tmp_path / "orders.csv"
    path.write_text(
        f"{HEADER}\n{VALID}\nA,02/03/2018,20,01234,Furniture,Consumer,West\n"
        "B,03/03/2018,30,,Furniture,Consumer,West\n",
        encoding="utf-8",
    )
    orders = load_orders(path)
    assert orders["Order Date"].iat[0] == pd.Timestamp("2018-03-02")
    assert pd.isna(orders["Postal Code"].iat[0])
    assert orders["Postal Code"].iat[1] == "01234"
    monthly = aggregate_monthly(orders)
    assert monthly.index[0] == pd.Period("2018-03", freq="M")
    assert monthly.iloc[0].to_dict() == {"sales": 60, "orders": 2, "ticket": 30}


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("Order ID", "other", "Missing columns"),
        ("02/03/2018", "31/02/2018", "Order Date"),
        ("02/03/2018", "2018-03-02", "Order Date"),
        (",10,", ",0,", "Sales"),
        (",10,", ",-2,", "Sales"),
        (",10,", ",inf,", "Sales"),
        (",10,", ",NaN,", "Sales"),
    ],
)
def test_rejects_invalid_orders(tmp_path, old, new, message):
    path = tmp_path / "orders.csv"
    path.write_text(f"{HEADER}\n{VALID}\n".replace(old, new), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_orders(path)


def test_rejects_missing_calendar_month():
    orders = pd.DataFrame(
        {
            "Order Date": pd.to_datetime(["2018-01-02", "2018-03-02"]),
            "Order ID": ["A", "B"],
            "Sales": [10, 20],
        }
    )
    with pytest.raises(ValueError, match="Missing calendar months"):
        aggregate_monthly(orders)
