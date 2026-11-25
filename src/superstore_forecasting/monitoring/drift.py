"""Genera un reporte de Data Drift usando Evidently."""

import argparse
from pathlib import Path

from evidently import Report
from evidently.presets import DataDriftPreset

from superstore_forecasting.config import RAW_PATH
from superstore_forecasting.data import load_orders
from superstore_forecasting.features import aggregate_monthly


def generate_drift_report(
    input_path: Path = RAW_PATH, out_dir: Path = Path("artifacts")
) -> None:
    """Compara datos de referencia (histórico) vs actuales (año nuevo)."""
    print("Cargando datos...")
    orders = load_orders(input_path)

    # Agregamos a nivel mensual (que es como el modelo ve los datos)
    monthly = aggregate_monthly(orders)

    # Separamos los datos:
    # Referencia: Todo antes de 2018
    # Actual: Año 2018 (simulando datos nuevos que llegan en producción)

    ref_data = monthly[monthly.index.year < 2018].reset_index(drop=True)
    current_data = monthly[monthly.index.year == 2018].reset_index(drop=True)

    if ref_data.empty or current_data.empty:
        raise ValueError("No hay suficientes datos para separar referencia y actual.")

    print(f"Datos de referencia: {len(ref_data)} meses (hasta 2017)")
    print(f"Datos actuales: {len(current_data)} meses (2018)")

    # Configurar el reporte de Evidently
    report = Report(metrics=[DataDriftPreset()])

    # Correr el análisis
    snapshot = report.run(reference_data=ref_data, current_data=current_data)

    # Guardar resultados
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / "drift_report.html"
    snapshot.save_html(str(html_path))

    print(f"✅ Reporte guardado en: {html_path}")

    # Mostrar resumen en consola
    result_dict = snapshot.dict()
    # El resultado de Evidently puede variar un poco según la versión,
    # así que buscamos de forma segura si hay drift.
    metrics = result_dict.get("metrics", [])
    drift_detected = False
    for metric in metrics:
        if metric.get("metric") == "DataDriftPreset" or "dataset_drift" in metric.get(
            "result", {}
        ):
            drift_detected = metric["result"].get("dataset_drift", False)
            break

    if drift_detected:
        print("⚠️ ALERTA: Se detectó Data Drift. El modelo debería reentrenarse.")
    else:
        print("✅ Todo estable. No se detectó Data Drift significativo.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reporte de Data Drift")
    parser.add_argument("--input", type=Path, default=RAW_PATH)
    args = parser.parse_args()

    generate_drift_report(args.input)
