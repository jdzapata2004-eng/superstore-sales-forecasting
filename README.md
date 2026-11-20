# Superstore Sales Forecasting

Pronóstico de las ventas totales del próximo mes para apoyar la revisión de la
meta comercial. El proyecto usa una versión fija de Superstore, un baseline
estacional y una regresión Ridge.

## Reproducir desde un clon limpio

Con uv y acceso a internet, ejecuta estos comandos desde la raíz del clon:

```text
uv sync --locked --python 3.11
uv run --locked python -m scripts.download_data
uv run --locked python -m superstore_forecasting.data
uv run --locked python -m scripts.eda
uv run --locked python -m superstore_forecasting.train
uv run --locked python -m pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked python -m superstore_forecasting.predict --through 2018-12 --model seasonal_naive
```

La descarga usa KaggleHub y verifica el SHA-256 de `train.csv` antes de
publicarlo en `data/raw/`. Una copia local con el hash esperado se reutiliza.
Los comandos de validación, EDA, entrenamiento y predicción aceptan
`--input` para usar un CSV con el mismo contrato.

El EDA genera cuatro gráficos PNG en `artifacts/eda/`. La evaluación escribe
`metrics.json` y `predictions.csv` en `artifacts/evaluation/`. Se evalúa un
pronóstico por mes entre enero y diciembre de 2018. Cada pronóstico usa los
meses disponibles hasta el corte anterior. El JSON contiene el menor MAE y el
modelo seleccionado; la predicción requiere una elección explícita para
usar `ridge` y por defecto usa `seasonal_naive`.

`--through` indica el último mes que el operador confirma como cerrado. Los
registros posteriores a ese mes quedan fuera de la predicción. Para el ejemplo
se usa diciembre de 2018 como cierre del snapshot. El entrenamiento permite
cambiar el bloque con `--start YYYY-MM --end YYYY-MM`.

## Interfaces de integración

| Responsabilidad | Interfaz |
|---|---|
| Adquisición | `scripts.download_data.download_data(destination)` devuelve el `Path` con el archivo verificado. |
| Validación | `data.load_orders(path)` devuelve transacciones validadas. |
| Preparación | `features.aggregate_monthly(orders)` devuelve totales, conteos y ticket por mes. `features.make_features(monthly)` añade una fila de predictores para el siguiente mes. |
| Entrenamiento | `model.fit_candidate(features, target)` devuelve un pipeline de scikit-learn que incluye el escalado. `train.evaluate_walk_forward(monthly, start, end)` devuelve predicciones por fold y un resumen serializable para tracking. |
| Inferencia | `predict.predict_next_month(orders, through=..., model=...)` devuelve un diccionario serializable con el corte, el mes objetivo, el método y el total previsto. |

Las interfaces del paquete se importan desde `superstore_forecasting`.
Consulta la [ficha de datos](docs/dataset-card.md) y la
[ficha de modelo](docs/model-card.md) para decisiones y limitaciones.
