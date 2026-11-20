"""Track temporal Ridge tuning and held-out model comparisons in MLflow."""

import argparse
import hashlib
import json
import os
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4

import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow.models import infer_signature

from superstore_forecasting.config import (
    DATASET,
    EVAL_END,
    FILENAME,
    RAW_PATH,
    RIDGE_ALPHAS,
    SEASON,
    SHA256,
    TUNING_END,
    TUNING_START,
)
from superstore_forecasting.data import load_orders
from superstore_forecasting.features import FEATURES, aggregate_monthly, make_features
from superstore_forecasting.model import (
    BASELINE,
    CANDIDATE,
    MODELS,
    fit_ridge_on_history,
    seasonal_estimator,
)
from superstore_forecasting.train import evaluate_walk_forward

TRACKING_URI = "http://127.0.0.1:5000"
EXPERIMENT = "superstore-monthly-sales"


def next_feature_row(monthly: pd.DataFrame) -> pd.DataFrame:
    """Prepare a one-row, named float64 input for either logged model."""
    return make_features(monthly).loc[:, list(FEATURES)].iloc[[-1]].astype("float64")


def _log_run(
    *, model, phase, alpha, history, predictions, summary, dataset_hash, comparison_id
) -> dict:
    example = next_feature_row(history).reset_index(drop=True)
    estimator = (
        seasonal_estimator().fit(example)
        if model == BASELINE
        else fit_ridge_on_history(history, alpha=alpha)
    )
    output = estimator.predict(example)
    metrics = summary["metrics"][model]
    train_through = str(history.index[-1])
    params = {
        "algorithm": model,
        "dataset": DATASET,
        "dataset_version": 2,
        "dataset_file": FILENAME,
        "dataset_sha256": dataset_hash,
        "history_start": str(history.index[0]),
        "artifact_trained_through": train_through,
        "artifact_example_target": str(history.index[-1] + 1),
        "evaluation_start": summary["evaluation_start"],
        "evaluation_end": summary["evaluation_end"],
        "folds": summary["folds"],
        "horizon_months": 1,
        "season_months": SEASON,
    }
    if model == CANDIDATE:
        params.update(alpha=alpha, solver="svd", scaler="StandardScaler")

    run_name = f"{phase}-{model}"
    if model == CANDIDATE:
        run_name += f"-alpha-{alpha:g}"
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.set_tags({"phase": phase, "comparison_id": comparison_id})
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        folds = predictions.loc[:, ["month", "actual", model]].rename(
            columns={model: "prediction"}
        )
        mlflow.log_text(folds.to_csv(index=False), "walk_forward.csv")
        mlflow.log_dict({"parameters": params, "metrics": metrics}, "evaluation.json")
        info = mlflow.sklearn.log_model(
            estimator,
            name="forecast",
            signature=infer_signature(example, output),
            input_example=example,
            serialization_format="cloudpickle",
            pip_requirements=[
                f"{package}=={version(package)}"
                for package in (
                    "mlflow",
                    "scikit-learn",
                    "pandas",
                    "numpy",
                    "scipy",
                    "cloudpickle",
                )
            ],
        )
        return {
            "run_id": run.info.run_id,
            "model_uri": info.model_uri,
            "trained_through": train_through,
            **metrics,
        }


def run_experiments(path: Path = RAW_PATH) -> dict:
    """Run fixed temporal experiments against the configured MLflow backend."""
    with path.open("rb") as source:
        dataset_hash = hashlib.file_digest(source, "sha256").hexdigest()
    if dataset_hash != SHA256:
        raise ValueError(
            f"SHA-256 mismatch: expected {SHA256}, received {dataset_hash}."
        )

    monthly = aggregate_monthly(load_orders(path))
    tuning = monthly.loc[:TUNING_END]
    holdout = monthly.loc[:EVAL_END]
    prepared_trials = {
        alpha: evaluate_walk_forward(tuning, TUNING_START, TUNING_END, alpha=alpha)
        for alpha in RIDGE_ALPHAS
    }
    selected_alpha = min(
        RIDGE_ALPHAS,
        key=lambda alpha: (
            prepared_trials[alpha][1]["metrics"][CANDIDATE]["mae"],
            alpha,
        ),
    )
    predictions, summary = evaluate_walk_forward(holdout, alpha=selected_alpha)

    mlflow.set_experiment(EXPERIMENT)
    comparison_id = uuid4().hex
    trials = [
        {
            "alpha": alpha,
            **_log_run(
                model=CANDIDATE,
                phase="tuning",
                alpha=alpha,
                history=tuning,
                predictions=trial_predictions,
                summary=trial_summary,
                dataset_hash=dataset_hash,
                comparison_id=comparison_id,
            ),
        }
        for alpha, (trial_predictions, trial_summary) in prepared_trials.items()
    ]
    comparison = {
        model: _log_run(
            model=model,
            phase="holdout",
            alpha=selected_alpha,
            history=holdout,
            predictions=predictions,
            summary=summary,
            dataset_hash=dataset_hash,
            comparison_id=comparison_id,
        )
        for model in MODELS
    }
    selected_model = summary["selected_model"]
    result = {
        "comparison_id": comparison_id,
        "selected_alpha": selected_alpha,
        "selected_model": selected_model,
        "tuning": trials,
        "holdout": comparison,
    }
    return result


def configure_tracking(uri: str | None = None) -> None:
    """Use the same backend for tracking and model versions."""
    uri = uri or os.environ.get("MLFLOW_TRACKING_URI") or TRACKING_URI
    # Keep CLI JSON readable in redirected terminals, including Windows CP1252.
    os.environ.setdefault("MLFLOW_SUPPRESS_PRINTING_URL_TO_STDOUT", "true")
    mlflow.set_tracking_uri(uri)
    mlflow.set_registry_uri(uri)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=RAW_PATH)
    parser.add_argument("--tracking-uri", default=None)
    args = parser.parse_args()
    configure_tracking(args.tracking_uri)
    print(json.dumps(run_experiments(args.input), indent=2))


if __name__ == "__main__":
    main()
