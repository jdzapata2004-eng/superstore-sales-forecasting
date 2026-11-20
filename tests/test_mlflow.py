import hashlib
import math

import mlflow
import pandas as pd
import pytest
from mlflow import MlflowClient
from mlflow.exceptions import MlflowException

from superstore_forecasting import experiments
from superstore_forecasting.config import EVAL_END, RIDGE_ALPHAS, TUNING_END
from superstore_forecasting.data import load_orders
from superstore_forecasting.model import BASELINE
from superstore_forecasting.registry import predict_registered, promote_champion


@pytest.fixture
def isolated_tracking(tmp_path, monkeypatch):
    tracking_uri = mlflow.get_tracking_uri()
    registry_uri = mlflow.get_registry_uri()
    active_experiment = mlflow.tracking.fluent._active_experiment_id
    monkeypatch.chdir(tmp_path)
    experiments.configure_tracking(f"sqlite:///{(tmp_path / 'tracking.db').as_posix()}")
    client = MlflowClient()
    client.create_experiment(
        experiments.EXPERIMENT, artifact_location=(tmp_path / "models").as_uri()
    )
    try:
        yield client
    finally:
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_registry_uri(registry_uri)
        mlflow.tracking.fluent._active_experiment_id = active_experiment


def test_experiments_registry_and_explicit_promotion(
    tmp_path, monkeypatch, isolated_tracking
):
    dates = pd.date_range("2015-01-01", periods=48, freq="MS")
    data = pd.DataFrame(
        {
            "Order Date": dates.strftime("%d/%m/%Y"),
            "Order ID": dates.astype(str),
            "Sales": 100 + dates.month,
            "Postal Code": "",
            "Category": "Furniture",
            "Segment": "Consumer",
            "Region": "West",
        }
    )
    path = tmp_path / "train.csv"
    data.to_csv(path, index=False)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(experiments, "SHA256", digest)

    evaluations = []
    evaluate = experiments.evaluate_walk_forward

    def checked_evaluation(monthly, *args, **kwargs):
        evaluations.append(str(monthly.index[-1]))
        return evaluate(monthly, *args, **kwargs)

    monkeypatch.setattr(experiments, "evaluate_walk_forward", checked_evaluation)
    result = experiments.run_experiments(path, register_best=True)
    assert evaluations == [TUNING_END] * len(RIDGE_ALPHAS) + [EVAL_END]
    assert result["selected_model"] == BASELINE
    assert len(result["tuning"]) == len(RIDGE_ALPHAS)

    client = isolated_tracking
    name = experiments.REGISTERED_MODEL
    version = result["registered_model"]["version"]
    run = client.get_run(result["holdout"][BASELINE]["run_id"])
    assert run.data.params["dataset_sha256"] == digest
    assert run.data.params["folds"] == "12"
    assert run.data.metrics == {"mae": 0.0, "rmse": 0.0}
    assert {item.path for item in client.list_artifacts(run.info.run_id)} == {
        "evaluation.json",
        "walk_forward.csv",
    }
    with pytest.raises(MlflowException, match="champion"):
        client.get_model_version_by_alias(name, "champion")
    orders = load_orders(path)
    explicit = predict_registered(orders, through=EVAL_END, version=version)
    assert explicit["month"] == "2019-01"
    assert math.isfinite(explicit["predicted_sales"])
    assert explicit["predicted_sales"] == 101
    with pytest.raises(ValueError, match="precedes"):
        predict_registered(orders, through="2018-11", version=version)

    client.set_model_version_tag(name, version, "validation_status", "pending")
    with pytest.raises(ValueError, match="backtested"):
        promote_champion(version)
    client.set_model_version_tag(name, version, "validation_status", "backtested")
    promote_champion(version)
    assert predict_registered(orders, through=EVAL_END) == explicit


def test_experiments_reject_unverified_bytes_before_tracking(tmp_path):
    path = tmp_path / "train.csv"
    path.write_text("changed")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        experiments.run_experiments(path)
