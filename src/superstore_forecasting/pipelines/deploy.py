"""Despliegue del pipeline para ejecución programada con Prefect."""

from superstore_forecasting.pipelines.training import training_pipeline

if __name__ == "__main__":
    # Desplegar el flow para que corra automáticamente todos los domingos a medianoche
    # (Ejemplo: reentrenamiento semanal)
    training_pipeline.serve(
        name="reentrenamiento-semanal",
        cron="0 0 * * 0",
        tags=["superstore", "produccion"],
        parameters={"register_best": True},
    )
