"""Deterministic models for one-month-ahead forecasts."""

import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

from superstore_forecasting.config import RIDGE_ALPHA
from superstore_forecasting.features import FEATURES, make_features

BASELINE = "seasonal_naive"
CANDIDATE = "ridge"
MODELS = (BASELINE, CANDIDATE)


def seasonal_naive(features: pd.DataFrame) -> pd.Series:
    """Predict the observed sales of the same month one year earlier."""
    return features["sales_lag_12"].rename(BASELINE)


def fit_candidate(features: pd.DataFrame, target: pd.Series) -> Pipeline:
    """Fit only the supplied history. SVD is deterministic and uses no RNG."""
    if len(features) < 2 or not features.index.equals(target.index):
        raise ValueError("Ridge requires at least two aligned training months.")
    estimator = make_pipeline(StandardScaler(), Ridge(alpha=RIDGE_ALPHA, solver="svd"))
    return estimator.fit(features.loc[:, list(FEATURES)], target)


def forecast_models(monthly: pd.DataFrame) -> tuple[pd.Period, dict[str, float]]:
    """Fit on observed months and score exactly the subsequent month."""
    features = make_features(monthly)
    month = features.index[-1]
    future = features.iloc[[-1]]
    if future.isna().any(axis=None):
        raise ValueError("Insufficient observed history for the next-month features.")

    training = features.iloc[:-1].dropna()
    candidate = fit_candidate(training, monthly.loc[training.index, "sales"])
    return month, {
        BASELINE: float(seasonal_naive(future).iloc[0]),
        CANDIDATE: float(candidate.predict(future)[0]),
    }
