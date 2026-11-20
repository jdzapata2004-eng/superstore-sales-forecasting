# Ficha inicial del modelo

El sistema estima las ventas totales del siguiente mes calendario a partir de
un cierre mensual conocido. La cifra apoya la revisión de la meta comercial.

- **Referencia.** Ingenuo estacional que repite las ventas del mismo mes del año anterior.
- **Candidato.** Regresión Ridge con estandarización ajustada dentro de cada fold,
  `alpha=10` y solver SVD determinista. No hay muestreo ni operaciones aleatorias que
  requieran semilla. El valor de alpha está fijo y el bloque de evaluación no se
  usa para ajustarlo.
- **Evaluación.** Walk-forward de un paso con entrenamiento creciente y cortes
  fijos de enero a diciembre de 2018. Ambos métodos se comparan en los mismos
  meses mediante MAE y RMSE en la unidad original de ventas.
- **Selección.** El menor MAE identifica la recomendación local. En empate gana
  la referencia. Inferencia elige el modelo explícitamente y por defecto usa la referencia.
- **Evidencia.** El entrenamiento guarda métricas y predicciones por fold en
  `artifacts/evaluation/`. Esos archivos se regeneran desde el snapshot fijado.

Hay solo cuatro ciclos anuales observados antes de aplicar los rezagos y menos
muestras útiles para estimar Ridge. La agregación oculta cambios por categoría o
región. Ridge produce un punto estimado y puede extrapolar a valores negativos.
Esta versión no estima incertidumbre, no mide utilidad comercial en producción
y no promueve ni registra modelos automáticamente.
