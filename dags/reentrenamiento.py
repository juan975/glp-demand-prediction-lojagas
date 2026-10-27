"""Escenario +1 (c): reentrenamiento periódico.

Entrena candidatos con walk-forward (Tracking), evalúa y registra el mejor como
"candidato" (Model Registry). La promoción a "produccion" es MANUAL hasta el
ADR-0007 (política de promoción).
"""

from __future__ import annotations

import pendulum
from _comun import tarea
from airflow.sdk import DAG

with DAG(
    dag_id="reentrenamiento",
    schedule="0 3 5 1,7 *",  # semestral (enero y julio), según 3.4.4 del documento
    start_date=pendulum.datetime(2027, 1, 1, tz="America/Guayaquil"),
    catchup=False,
    max_active_runs=1,
    tags=["lojagas", "entrenamiento"],
) as dag:
    caracteristicas = tarea(
        "ingenieria_caracteristicas", "procesamiento", ["ingenieria-caracteristicas"]
    )
    entrenar = tarea("pipeline_entrenamiento", "ml", ["entrenar"])
    evaluar = tarea("evaluacion", "ml", ["evaluar"])

    caracteristicas >> entrenar >> evaluar
