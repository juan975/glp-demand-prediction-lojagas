"""Qué mes procesa cada corrida (ADR-0014).

El DAG corre el día 2 del mes M y procesa el último mes cerrado, M−1: el 2 de noviembre
procesa octubre y, con horizonte 2, predice diciembre. El cálculo vive aquí y no en una
plantilla de Airflow: en Airflow 3 un cron sin intervalos hace que `data_interval_start`
sea la fecha de la propia corrida, no el inicio del mes anterior.
"""

from __future__ import annotations

from datetime import date, timedelta


def ultimo_mes_cerrado(fecha_ejecucion: date) -> date:
    """Primer día del mes anterior a la fecha de ejecución."""
    return (fecha_ejecucion.replace(day=1) - timedelta(days=1)).replace(day=1)


def validar_periodo(texto: str) -> date:
    """Un período es el primer día de un mes (YYYY-MM-01)."""
    periodo = date.fromisoformat(texto)
    if periodo.day != 1:
        raise ValueError(f"El período debe ser el día 1 de un mes: {texto}")
    return periodo
