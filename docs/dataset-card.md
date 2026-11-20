# Ficha de datos

| Campo | Valor |
|---|---|
| Publicación | Superstore Sales Dataset de Rohit Sahoo en [Kaggle](https://www.kaggle.com/datasets/rohitsahoo/sales-forecasting/versions/2) |
| Identificador | `rohitsahoo/sales-forecasting/versions/2` |
| Archivo | `train.csv`, 9.800 filas, 18 columnas, 2.129.689 bytes |
| Licencia declarada en Kaggle | GPL 2 |
| SHA-256 | `dbb0f167b27ccf02d7ff8cb0446a9abc6dbc3522e83cf9daa6939801acfdd196` |
| Cobertura de pedidos | 03/01/2015 a 30/12/2018, 48 meses con registros |

La descarga anónima con KaggleHub se verificó para esta versión. La procedencia
anterior a la publicación de Kaggle y la moneda de `Sales` siguen por confirmar.

## Esquema y contrato

| Columnas | Significado y tratamiento |
|---|---|
| `Order Date` | Fecha del pedido, obligatoria y válida en formato día/mes/año. Define el mes del pronóstico. |
| `Sales` | Importe por línea, convertido a numérico y validado como finito y estrictamente positivo. |
| `Order ID` | Identificador textual obligatorio. Varias líneas pueden corresponder al mismo pedido. |
| `Category`, `Segment`, `Region` | Categóricas obligatorias de producto, segmento comercial y región. |
| `Postal Code` | Código geográfico textual. Se conservan ceros iniciales y los 11 valores faltantes en Burlington, Vermont. |
| `Row ID`, `Customer ID`, `Product ID` | Identificadores de fila, cliente y producto. |
| `Ship Date`, `Ship Mode` | Fecha y modalidad de envío. |
| `Country`, `City`, `State` | Geografía de la transacción. |
| `Customer Name`, `Sub-Category`, `Product Name` | Nombre del cliente, subcategoría y nombre del producto. |

El loader conserva los campos auxiliares como texto. Los faltantes de código
postal se mantienen como nulos, sin imputar ni eliminar filas. El EDA mide esos
faltantes. El entrenamiento excluye el código postal y los nombres de clientes.
El contrato rechaza registros operativos inválidos mediante un error explícito.
Se conservan importes extremos y filas duplicadas. Los importes inválidos
provocan un error de validación.
Un mes ausente se trata como un problema de cobertura y detiene el flujo.

## Derivadas y cortes

El objetivo es la suma de importes por mes. Para cada mes se cuentan los
pedidos distintos y se divide el total de ventas entre ese conteo para obtener
el ticket promedio. Los predictores son ventas con rezagos de 1 y 12 meses,
pedidos del mes anterior y ticket promedio del mes anterior. Los valores del
mes objetivo solo se usan al evaluar el pronóstico una vez observados.

Los folds del bloque enero–diciembre de 2018 usan historia creciente hasta el
mes inmediatamente anterior. Para un futuro reporte de drift se pueden evaluar
periodos reales comparables, por ejemplo 2017 y 2018 con las mismas ventanas de
calendario y con análisis de estacionalidad.

## Limitaciones

Los registros describen las ventas incluidas en esta copia. No hay confirmación
de su representatividad, moneda ni completitud operativa en los extremos.
Para los ejercicios con el snapshot se trabaja bajo el supuesto de que
diciembre de 2018 se puede usar como cierre histórico. Tener registros en cada
mes no demuestra completitud. Las 9.800 líneas aportan solo 48 observaciones
mensuales. El archivo contiene nombres e identificadores de clientes y se
mantiene fuera del repositorio.
