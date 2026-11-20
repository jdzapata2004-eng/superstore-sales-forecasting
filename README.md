# Superstore Sales Forecasting

## Problema, objetivo y criterios de éxito

El área comercial necesita anticipar las ventas totales del próximo mes para
preparar su plan, revisar la meta de ventas y prever recursos. El objetivo es
generar un único pronóstico agregado para el mes calendario siguiente al
último mes cerrado, sin desglose por región, categoría ni producto.

- **Éxito analítico.** El candidato debe obtener un MAE estrictamente menor
  que el del pronóstico estacional ingenuo, que usa las ventas del mismo mes
  del año anterior. Ambos se evalúan sobre los mismos meses y con los mismos
  cortes cronológicos. En empate se conserva la referencia.
- **Éxito de negocio.** El pronóstico debe estar disponible antes de cerrar el
  plan del mes siguiente y servir para revisar al menos una decisión comercial,
  como mantener o ajustar la meta de ventas. Este criterio está pendiente de
  validación con el área comercial.

La [fase 1 de CRISP-DM](docs/crisp-dm.md) detalla los criterios, supuestos, riesgos
y decisiones pendientes. La implementación inicial usa una versión fija de
Superstore, el baseline estacional y una regresión Ridge.

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

## Experimentos y registro con MLflow

Desde la raíz del repositorio, inicia el servidor en una terminal después de
instalar las dependencias. SQLite guarda el tracking y el registro.
MLflow sirve los artefactos desde un directorio local.

```text
uv run --locked mlflow server --backend-store-uri sqlite:///mlflow.db --serve-artifacts --artifacts-destination ./mlartifacts --host 127.0.0.1 --port 5000 --workers 1
```

Abre [MLflow](http://127.0.0.1:5000). En **Experiments**, elige
`superstore-monthly-sales`. Filtra por `comparison_id` para ver un lote y por
`phase` para separar ajuste y evaluación final. En otra terminal, desde la raíz:

```text
uv run --locked python -m scripts.download_data
uv run --locked python -m superstore_forecasting.experiments --register-best
```

Cada corrida registra los parámetros, el hash y la versión del CSV, los cortes,
MAE, RMSE, el CSV de predicciones por fold y un modelo MLflow con firma y
ejemplo de entrada. Las corridas `tuning` comparan cuatro valores de alpha en
2017. Las dos corridas `holdout` comparan el ingenuo estacional y Ridge con el
alpha seleccionado en los mismos 12 folds de 2018. El modelo que se guarda al
final de cada corrida se ajusta hasta el cierre de esa fase. Las métricas
corresponden al walk-forward, en el que el ajuste de cada fold usa solo la
historia anterior al mes pronosticado.

En el experimento verificado, el ajuste de 2017 eligió `alpha=0.1`.
En 2018 el ingenuo estacional obtuvo MAE **15.444,18** y RMSE **18.932,10**.
Ridge obtuvo MAE **15.740,08** y RMSE **19.303,74**. La
[ficha del modelo](docs/model-card.md) incluye las cuatro corridas de ajuste.
`python -m superstore_forecasting.train` conserva la configuración de Ridge de
la fase 1 para las comparaciones locales.

Con `--register-best`, la mejor corrida de 2018 por MAE crea una versión en
**Models → superstore-monthly-forecast**. En empate se elige el baseline.
El JSON de salida indica el número de versión. Sustituye `1` por ese número
si el registro ya contiene otras versiones:

```text
uv run --locked python -m superstore_forecasting.registry predict --version 1 --through 2018-12
```

La promoción es una operación separada. Tras revisar la versión registrada,
puedes asignarle el alias `champion` y comprobar la inferencia por alias:

```text
uv run --locked python -m superstore_forecasting.registry promote --version 1
uv run --locked python -m superstore_forecasting.registry predict --through 2018-12
```

`MLFLOW_TRACKING_URI` o `--tracking-uri` antes del subcomando permiten apuntar
a otro servidor. El tracking y el registro usan el mismo backend.
`mlflow.db`, `mlartifacts/` y `mlruns/` se mantienen fuera de Git.

## Interfaces de integración

| Responsabilidad | Interfaz |
|---|---|
| Adquisición | `scripts.download_data.download_data(destination)` devuelve el `Path` con el archivo verificado. |
| Validación | `data.load_orders(path)` devuelve transacciones validadas. |
| Preparación | `features.aggregate_monthly(orders)` devuelve totales, conteos y ticket por mes. `features.make_features(monthly)` añade una fila de predictores para el siguiente mes. |
| Entrenamiento | `model.fit_candidate(features, target)` devuelve un pipeline de scikit-learn que incluye el escalado. `train.evaluate_walk_forward(monthly, start, end)` devuelve predicciones por fold y un resumen serializable para tracking. |
| Inferencia | `predict.predict_next_month(orders, through=..., model=...)` devuelve un diccionario serializable con el corte, el mes objetivo, el método y el total previsto. |
| Tracking | `experiments.configure_tracking(uri)` y `experiments.run_experiments(path, register_best=True)` devuelven los identificadores, métricas y la versión registrada para que Prefect los recoja. Configura MLflow una vez por proceso. |
| Modelo registrado | `registry.predict_registered(orders, through=...)` resuelve `champion` a una versión, comprueba el corte y devuelve una predicción serializable. Para cargar el artefacto en el arranque de una API, usa `mlflow.pyfunc.load_model("models:/superstore-monthly-forecast@champion")` y pasa las cuatro columnas numéricas de `experiments.next_feature_row(monthly)`. |

Las interfaces del paquete se importan desde `superstore_forecasting`.
En Docker, monta volúmenes persistentes para SQLite y artefactos y apunta el
contenedor cliente a la URL interna del servidor MLflow. Conserva la validación
del corte de entrenamiento antes de predecir con un modelo cargado en memoria.
Consulta la [ficha de datos](docs/dataset-card.md) y la
[ficha de modelo](docs/model-card.md) para decisiones y limitaciones.
