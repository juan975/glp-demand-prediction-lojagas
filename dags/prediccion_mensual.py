"""Escenario +1 (a): generación mensual programada de la predicción.

Ingesta → Procesamiento (curación, ingeniería de características) → ML (predicción, reportes).
Corre el día 2 de cada mes para dar margen al cierre contable del mes anterior
(supuesto a validar con Lojagas: ¿cuándo quedan publicadas todas las facturas?).
"""

from __future__ import annotations

import pendulum
from _comun import tarea
from airflow.sdk import DAG

with DAG(
    dag_id="prediccion_mensual",
    schedule="0 6 2 * *",
    start_date=pendulum.datetime(2026, 11, 1, tz="America/Guayaquil"),
    catchup=False,
    max_active_runs=1,
    tags=["lojagas", "batch"],
) as dag:
    periodo = "{{ data_interval_start | ds }}"

    ingesta_odoo = tarea("ingesta_odoo", "ingesta", ["ingesta-odoo", "--periodo", periodo])
    ingesta_externas = tarea(
        "ingesta_externas", "ingesta", ["ingesta-externas", "--periodo", periodo]
    )
    curacion = tarea("curacion", "procesamiento", ["curacion"])
    caracteristicas = tarea(
        "ingenieria_caracteristicas", "procesamiento", ["ingenieria-caracteristicas"]
    )
    predecir = tarea("predecir", "ml", ["predecir", "--periodo", periodo])
    reportes = tarea("generar_reportes", "ml", ["generar-reportes", "--periodo", periodo])

    [ingesta_odoo, ingesta_externas] >> curacion >> caracteristicas >> predecir >> reportes
