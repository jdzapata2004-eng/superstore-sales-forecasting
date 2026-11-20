# Ficha del modelo de pronóstico mensual

El sistema estima las ventas totales del siguiente mes calendario a partir de
un cierre mensual conocido. La cifra apoya la revisión de la meta comercial.

- **Referencia.** Ingenuo estacional que repite las ventas del mismo mes del año anterior.
  El estimador serializable expone la misma regla mediante `predict`.
- **Candidato.** Regresión Ridge con estandarización ajustada dentro de cada fold,
  solver SVD determinista y cuatro valores de alpha comparados con walk-forward
  durante 2017. Se fija el valor de menor MAE antes de evaluar 2018.
- **Evaluación.** Walk-forward de un paso con entrenamiento creciente y cortes
  fijos de enero a diciembre de 2018. Ambos métodos se comparan en los mismos
  meses mediante MAE y RMSE en la unidad original de ventas.
- **Selección.** El menor MAE de 2018 determina el modelo que se registra con
  `--register-best`. En empate gana la referencia. La asignación de `champion`
  se realiza mediante un comando explícito y separado.
- **Evidencia.** Las corridas de `superstore-monthly-sales` guardan el hash y la
  versión del CSV, los parámetros, las métricas, `walk_forward.csv`,
  `evaluation.json` y un modelo MLflow con firma y ejemplo de entrada.
  El artefacto de evaluación final está preparado para pronosticar tras el cierre
  de diciembre de 2018. Sus métricas corresponden al ajuste independiente de cada
  fold histórico, con los datos disponibles al momento de pronosticar.

## Resultados observados

| Ridge en 2017 | MAE | RMSE |
|---|---:|---:|
| alpha 0,1 | 12.387,63 | 13.761,33 |
| alpha 1 | 12.773,03 | 14.447,85 |
| alpha 10 | 13.760,24 | 16.327,22 |
| alpha 100 | 17.408,52 | 21.802,17 |

| Comparación en 2018 | MAE | RMSE |
|---|---:|---:|
| Ingenuo estacional | 15.444,18 | 18.932,10 |
| Ridge con alpha 0,1 | 15.740,08 | 19.303,74 |

El ingenuo estacional ganó por MAE y quedó registrado como versión 1 de
`superstore-monthly-forecast` en el backend de verificación. Las métricas se
expresan en la unidad de `Sales`. El comando local `train` conserva el alpha
fijo de la fase 1. La comparación de esta ficha procede de `experiments`.

## Límites

Hay solo cuatro ciclos anuales observados antes de aplicar los rezagos y menos
muestras útiles para estimar Ridge. La agregación oculta cambios por categoría o
región. Ridge produce un punto estimado y puede extrapolar a valores negativos.
La evaluación termina en 2018. Quedan sin medir el rendimiento del ganador
en un periodo posterior independiente, la incertidumbre del pronóstico y su
utilidad comercial en producción. El despliegue debe obtener las cuatro
variables numéricas del historial disponible al corte de inferencia.
