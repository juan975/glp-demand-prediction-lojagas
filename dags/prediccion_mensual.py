"""Escenario +1 (a): generación mensual programada de la predicción.

Ingesta → Procesamiento (curación, ingeniería de características) → ML (predicción, reportes).
Corre el día 2 del mes M, procesa el último mes cerrado (M−1) y, con horizonte 2, predice
M+1: el 2 de noviembre procesa octubre y predice diciembre (ADR-0014, provisional).

Si falla la ingesta de fuentes externas (p. ej., Copernicus caído o con la cola llena), la
predicción sigue con lo que Raw ya tiene: la configuración A no usa variables externas. La
corrida termina en verde y la tarea queda en rojo; la curación deja en el log hasta qué mes
llega el clima. Si falla la ingesta de Odoo, la corrida se detiene.
"""

from __future__ import annotations

from datetime import timedelta

import pendulum
from _comun import FECHA_EJECUCION, SECRETO_PII, SECRETOS_CDS, SECRETOS_ODOO, tarea
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.sdk import DAG, Param

with DAG(
    dag_id="prediccion_mensual",
    schedule="0 6 2 * *",
    start_date=pendulum.datetime(2026, 11, 1, tz="America/Guayaquil"),
    catchup=False,
    max_active_runs=1,
    tags=["lojagas", "batch"],
    params={
        "fecha_ejecucion": Param(
            None,
            type=["null", "string"],
            format="date",
            description="Simula o reprocesa una corrida: 2026-11-02 procesa octubre de 2026.",
        )
    },
) as dag:
    cuando = ["--fecha-ejecucion", FECHA_EJECUCION]

    ingesta_odoo = tarea("ingesta_odoo", "ingesta", ["ingesta-odoo", *cuando], SECRETOS_ODOO)
    # La descarga completa de ERA5-Land tarda ~3 min, pero CDS a veces deja los pedidos horas
    # en cola: al vencer el límite, Airflow detiene el contenedor y la tarea falla
    ingesta_externas = tarea(
        "ingesta_externas",
        "ingesta",
        ["ingesta-externas", *cuando],
        SECRETOS_CDS,
        execution_timeout=timedelta(hours=1),
    )
    # Termina siempre que ingesta_externas termine, bien o mal: su falla no frena la curación
    externas_listas = EmptyOperator(task_id="externas_listas", trigger_rule="all_done")
    curacion = tarea("curacion", "procesamiento", ["curacion", *cuando], SECRETO_PII)
    caracteristicas = tarea(
        "ingenieria_caracteristicas", "procesamiento", ["ingenieria-caracteristicas"]
    )
    predecir = tarea("predecir", "ml", ["predecir", *cuando])
    reportes = tarea("generar_reportes", "ml", ["generar-reportes", *cuando])

    ingesta_externas >> externas_listas
    [ingesta_odoo, externas_listas] >> curacion >> caracteristicas >> predecir >> reportes
