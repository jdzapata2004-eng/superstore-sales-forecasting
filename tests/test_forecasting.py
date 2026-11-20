import pandas as pd
import pytest

from superstore_forecasting.features import aggregate_monthly, make_features
from superstore_forecasting.model import BASELINE, CANDIDATE, seasonal_naive
from superstore_forecasting.predict import predict_next_month
from superstore_forecasting.train import evaluate_walk_forward


@pytest.fixture
def orders():
    dates = pd.date_range("2015-01-01", periods=48, freq="MS")
    return pd.DataFrame(
        {"Order Date": dates, "Order ID": dates.astype(str), "Sales": range(100, 148)}
    )


def test_features_exclude_current_and_future_observations(orders):
    monthly = aggregate_monthly(orders)
    target = pd.Period("2018-01", freq="M")
    changed = monthly.copy()
    changed.loc[target:, :] *= 20
    original = make_features(monthly)
    pd.testing.assert_frame_equal(
        original.loc[:target], make_features(changed).loc[:target]
    )
    assert original.loc[target].to_dict() == {
        "sales_lag_1": 135,
        "sales_lag_12": 124,
        "orders_lag_1": 1,
        "ticket_lag_1": 135,
    }
    assert seasonal_naive(original).loc[target] == 124


@pytest.mark.parametrize("model", [BASELINE, CANDIDATE])
def test_prediction_ignores_rows_after_cutoff(orders, model):
    full = predict_next_month(orders, through="2017-12", model=model)
    past = predict_next_month(orders.iloc[:36], through="2017-12", model=model)
    assert full == past
    assert full["month"] == "2018-01"
    if model == BASELINE:
        assert full["predicted_sales"] == 124


def test_walk_forward_does_not_train_on_fold_target(orders):
    monthly = aggregate_monthly(orders)
    original, summary = evaluate_walk_forward(monthly)
    changed = monthly.copy()
    changed.loc["2018-01":, "sales"] *= 100
    alternative, _ = evaluate_walk_forward(changed)
    assert original.loc[0, [BASELINE, CANDIDATE]].equals(
        alternative.loc[0, [BASELINE, CANDIDATE]]
    )
    assert original.loc[0, "actual"] != alternative.loc[0, "actual"]
    assert summary["folds"] == 12
    assert summary["metrics"][BASELINE] == {"mae": 12.0, "rmse": 12.0}
    assert summary["selected_model"] == CANDIDATE
