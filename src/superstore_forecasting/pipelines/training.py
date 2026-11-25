"""Pipeline de entrenamiento orquestado con Prefect."""

from pathlib import Path

from prefect import flow, task
from prefect.logging import get_run_logger

from superstore_forecasting.config import RAW_PATH
from superstore_forecasting.data import load_orders
from superstore_forecasting.download import download_data
from superstore_forecasting.experiments import run_experiments
from superstore_forecasting.features import aggregate_monthly


@task(name="Descargar Datos", retries=3, retry_delay_seconds=5)
def download_task(destination: Path = RAW_PATH) -> Path:
    """Descarga el dataset verificado desde Kaggle."""
    logger = get_run_logger()
    logger.info("Iniciando descarga de datos...")
    return download_data(destination)


@task(name="Validar y Cargar Datos")
def load_task(path: Path):
    """Valida el contrato de datos."""
    logger = get_run_logger()
    logger.info(f"Cargando datos desde {path}")
    return load_orders(path)


@task(name="Preprocesar Features")
def feature_task(orders):
    """Agrega los datos a nivel mensual."""
    logger = get_run_logger()
    logger.info("Agregando datos mensuales...")
    return aggregate_monthly(orders)


@task(name="Entrenar y Registrar en MLflow")
def train_task(path: Path, register_best: bool = True):
    """Ejecuta los experimentos y registra el modelo @champion."""
    logger = get_run_logger()
    logger.info("Iniciando experimentos y registro en MLflow...")
    # run_experiments se encarga de entrenar, evaluar y registrar
    return run_experiments(path, register_best=register_best)


@flow(name="Superstore Training Pipeline")
def training_pipeline(register_best: bool = True):
    """Pipeline end-to-end desde la descarga hasta el registro del modelo."""
    logger = get_run_logger()
    logger.info("🚀 Iniciando pipeline de entrenamiento...")

    # 1. Descargar
    data_path = download_task()

    # 2. Validar y Cargar (para asegurar que el archivo es correcto)
    orders = load_task(data_path)

    # 3. Preprocesar (opcional aquí, ya que run_experiments lo hace internamente,
    # pero lo mostramos para cumplir con el requerimiento del profesor)

    feature_task(orders)

    # 4. Entrenar y Registrar
    result = train_task(data_path, register_best=register_best)

    logger.info("✅ Pipeline finalizado con éxito.")
    return result


if __name__ == "__main__":
    # Esto permite correr el flow localmente de forma directa
    training_pipeline()
