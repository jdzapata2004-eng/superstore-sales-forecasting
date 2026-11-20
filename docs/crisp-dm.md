# CRISP-DM · Fase 1. Comprensión del negocio

## 1. Problema de negocio

El área comercial necesita anticipar cuánto venderá en total el próximo mes para preparar su plan mensual. Una estimación disponible al inicio del ciclo de planificación le permitiría revisar su meta de ventas y prever recursos.

## 2. Pregunta de negocio

Al cierre de este mes, ¿cuánto esperamos vender en total el próximo mes para preparar nuestro plan comercial?

## 3. Objetivo de análisis

Construir una serie de ventas totales por mes calendario a partir del historial de Superstore y producir un pronóstico para el mes siguiente al último mes cerrado. La salida será un único total mensual en la unidad monetaria de la fuente. El alcance inicial cubre el conjunto de las ventas registradas, sin desglose por región, categoría o producto.

## 4. Criterio de éxito analítico

Un modelo candidato cumplirá el criterio si obtiene un error absoluto medio (MAE) estrictamente menor que el del pronóstico estacional ingenuo. Para cada mes evaluado, la referencia usará el total observado en el mismo mes del año anterior. El MAE es el promedio de las diferencias absolutas entre los totales observados y pronosticados, expresado en la unidad monetaria de la serie.

Se reservará un bloque cronológico final de meses completos. Ambos métodos se compararán sobre los mismos meses con pronósticos a un paso, usando en cada corte solo la información disponible hasta ese momento. El preprocesamiento que requiera ajuste se ajustará con el historial disponible en cada corte. La selección de candidatos y el ajuste de hiperparámetros se harán en periodos anteriores al bloque final. Si el candidato iguala o supera el MAE de la referencia, se conservará la referencia como método preferido para esa evaluación. Si el historial resulta insuficiente para una comparación estacional válida, el criterio quedará sin evaluar.

## 5. Criterio de éxito de negocio

En una validación con el área comercial, el pronóstico deberá estar disponible antes de cerrar el plan del mes siguiente y servir para revisar al menos una decisión concreta, como mantener o ajustar la meta mensual de ventas. La validación consistiría en registrar la fecha de disponibilidad, la decisión revisada y cómo se usó el pronóstico. En esta fase académica, el criterio es una propuesta pendiente de validación con usuarios del área.

## 6. Riesgos

- **Cobertura insuficiente.** Un historial corto o con meses incompletos puede impedir una comparación fiable con el mismo mes del año anterior. Se verificará la cobertura antes de fijar la ventana de evaluación.
- **Fuga temporal.** Usar ventas posteriores al corte, incluso para ajustar el preprocesamiento, produciría una estimación optimista del desempeño. Se mantendrán cortes cronológicos y se comprobará qué información estaba disponible en cada uno.
- **Cambios comerciales.** Promociones, cambios de precios o interrupciones pueden alterar las ventas y reducir la utilidad de los patrones históricos.
- **Disponibilidad operativa.** Un retraso en el cierre de ventas puede impedir emitir el pronóstico a tiempo para la planificación. Se deberá confirmar la fecha de corte con el área usuaria.

## Supuestos y limitaciones

- Se supone que el historial contiene una fecha de venta y un importe que puede sumarse por mes con una definición y unidad monetaria consistentes. La disponibilidad al cierre se verificará con la fuente.
- El total agregado puede ocultar variaciones entre productos o regiones. La serie histórica por sí sola tampoco permite atribuir cambios a campañas, precios u otras causas.
- La evaluación histórica estimará el error de pronóstico. La utilidad comercial deberá verificarse mediante la revisión de decisiones descrita en el criterio de negocio.

## Decisiones pendientes

- Confirmar la edición, procedencia, licencia, cobertura y unidad monetaria de Superstore y registrarlas en la ficha del conjunto de datos.
- Confirmar la columna de fecha y la definición del importe. Documentar el tratamiento de devoluciones, duplicados, montos faltantes y meses parciales o sin registros. Un mes sin registros requerirá verificar si hubo cero ventas o si faltan datos.
- Fijar el bloque de prueba y el mínimo de historial una vez comprobada la cobertura, antes de evaluar candidatos. Acordar con el área comercial la fecha de disponibilidad y quién validaría el uso del pronóstico.
