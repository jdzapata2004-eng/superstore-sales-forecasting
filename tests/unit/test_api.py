"""Smoke tests for the FastAPI service."""

from fastapi.testclient import TestClient

from superstore_forecasting.api.main import app


def test_health():
    with TestClient(app) as client:
        r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_predict_rejects_non_month_format():
    with TestClient(app) as client:
        r = client.post("/predict", json={"through": "not-a-month"})
    assert r.status_code == 422


def test_predict_missing_field():
    with TestClient(app) as client:
        r = client.post("/predict", json={})
    assert r.status_code == 422