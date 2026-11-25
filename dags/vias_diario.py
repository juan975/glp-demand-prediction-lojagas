"""Foto diaria del estado de vías del país (ECU911), para las alertas de los corredores de Lojagas.

El servicio del ECU911 solo da el estado de hoy, así que la historia se arma guardando una
foto cada día. Corre después de la actualización de la mañana del ECU911 (hacia las 06:30).
No depende del DAG mensual: si falla un día, ese día queda sin foto y el resto sigue.
"""

from __future__ import annotations

from datetime import timedelta

import pendulum
from _comun import tarea
from airflow.sdk import DAG

with DAG(
    dag_id="vias_diario",
    schedule="15 8 * * *",
    start_date=pendulum.datetime(2026, 12, 1, tz="America/Guayaquil"),
    catchup=False,  # sin historial en la fuente: no tiene sentido rellenar días pasados
    tags=["lojagas", "ingesta"],
    max_active_runs=1,
):
    # Un reintento cubre una caída breve del servicio; si sigue caído, ese día queda sin foto
    tarea(
        "ingesta_vias",
        "ingesta",
        ["ingesta-vias"],
        retries=2,
        retry_delay=timedelta(minutes=30),
        execution_timeout=timedelta(minutes=10),
    )
