# Superstore Sales Forecasting

## Problema, objetivo y criterios de éxito

El área comercial necesita anticipar las ventas totales del próximo mes para preparar su plan, revisar la meta de ventas y prever recursos. El objetivo es generar un único pronóstico agregado para el mes calendario siguiente al último mes cerrado, sin desglose por región, categoría ni producto.

- **Éxito analítico.** El candidato debe obtener un MAE estrictamente menor que el del pronóstico estacional ingenuo, que usa las ventas del mismo mes del año anterior. Ambos se evalúan sobre los mismos meses y con los mismos cortes cronológicos. En empate se conserva la referencia.
- **Éxito de negocio.** El pronóstico debe estar disponible antes de cerrar el plan del mes siguiente y servir para revisar al menos una decisión comercial, como mantener o ajustar la meta de ventas. Este criterio está pendiente de validación con el área comercial.

La [fase 1 de CRISP-DM](docs/crisp-dm.md) detalla los criterios, supuestos, riesgos y decisiones pendientes. La implementación inicial usa una versión fija de Superstore, el baseline estacional y una regresión Ridge.

## Reproducir desde un clon limpio

Con uv y acceso a internet, ejecuta estos comandos desde la raíz del clon:

```text
uv sync --locked --group dev --python 3.11 --link-mode copy
uv run --locked python -m scripts.download_data
uv run --locked python -m superstore_forecasting.data
uv run --locked python -m scripts.eda
uv run --locked python -m superstore_forecasting.train
uv run --locked python -m pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked python -m superstore_forecasting.predict --through 2018-12 --model seasonal_naive