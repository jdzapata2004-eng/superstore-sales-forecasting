
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from mlflow import MlflowClient

from superstore_forecasting.config import RAW_PATH
from superstore_forecasting.data import load_orders
from superstore_forecasting.experiments import REGISTERED_MODEL, configure_tracking
from superstore_forecasting.registry import CHAMPION, predict_registered

from .schemas import (
    ForecastRequest,
    ForecastResponse,
    HealthResponse,
    ReadyResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_tracking()
    yield


app = FastAPI(
    title="Superstore Sales Forecasting API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness: the process is up."""
    return HealthResponse(status="ok")


@app.get("/ready", response_model=ReadyResponse)
def ready() -> ReadyResponse:
    """Readiness: a champion model is available in the registry."""
    try:
        mv = MlflowClient().get_model_version_by_alias(REGISTERED_MODEL, CHAMPION)
    except Exception as exc:
        return ReadyResponse(ready=False, detail=str(exc))
    return ReadyResponse(ready=True, model=REGISTERED_MODEL, version=str(mv.version))


@app.post("/predict", response_model=ForecastResponse)
def forecast(req: ForecastRequest) -> ForecastResponse:
    try:
        orders = load_orders(RAW_PATH)
        result = predict_registered(orders, through=req.through, version=req.version)
    except FileNotFoundError as exc:
        raise HTTPException(503, f"Training data not available: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(503, f"Model unavailable: {exc}") from exc
    return ForecastResponse(**result)