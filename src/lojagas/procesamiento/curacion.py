"""curacion.py — Raw → Curated. Orden obligatorio, no se altera:

1. Contrato Raw (si falla, el DAG se detiene).
2. Solo meses cerrados: se descarta todo lo posterior al período (último mes cerrado).
3. Seudonimización con lista blanca (ninguna PII llega a Curated).
4. Agregación a toneladas por mes y segmento.
5. Contrato Curated.
6. Pesos de los días de la semana (días de venta), desde las líneas ya seudonimizadas.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from lojagas.comun import lakehouse
from lojagas.comun.config import Config
from lojagas.procesamiento.agregacion import a_mensual, cargar_mapa_segmentos
from lojagas.procesamiento.anonimizacion import seudonimizar
from lojagas.procesamiento.contratos import (
    actividad_dia_semana_curated,
    ventas_mensual_curated,
    ventas_raw,
)
from lojagas.procesamiento.dias_venta import pesos_dia_semana

MAPA_SEGMENTOS = Path("referencias/mapa_segmentos.csv")
TABLA_PESOS = "actividad_dia_semana"


def hasta_periodo(lineas: pd.DataFrame, periodo: str) -> pd.DataFrame:
    """Líneas hasta el último día del período. Un mes en curso o incompleto (p. ej., una
    exportación cortada a mitad de mes) parecería una caída de la demanda."""
    limite = pd.Timestamp(periodo) + pd.offsets.MonthBegin(1)
    return lineas[pd.to_datetime(lineas["fecha_factura"]) < limite]


def ejecutar(cfg: Config, periodo: str) -> dict[str, int]:
    raw = lakehouse.leer(cfg.lakehouse, "raw", "ventas_lineas")
    version_raw = lakehouse.version_actual(cfg.lakehouse, "raw", "ventas_lineas")

    ventas_raw.validate(raw, lazy=True)
    lineas = seudonimizar(hasta_periodo(raw, periodo), cfg.pii_salt)
    lakehouse.escribir(lineas, cfg.lakehouse, "curated", "ventas_lineas", modo="overwrite")

    mapa = cargar_mapa_segmentos(MAPA_SEGMENTOS)
    mensual = ventas_mensual_curated.validate(a_mensual(lineas, mapa))
    version = lakehouse.escribir(
        mensual, cfg.lakehouse, "curated", "ventas_mensual", modo="overwrite"
    )

    pesos = actividad_dia_semana_curated.validate(pesos_dia_semana(lineas, mapa))
    version_pesos = lakehouse.escribir(
        pesos, cfg.lakehouse, "curated", TABLA_PESOS, modo="overwrite"
    )

    # El calendario no tiene PII, pero pasa igual por Curated: Feature solo lee de Curated
    eventos = lakehouse.leer(cfg.lakehouse, "raw", "calendario_eventos")
    lakehouse.escribir(eventos, cfg.lakehouse, "curated", "calendario_eventos", modo="overwrite")
    return {
        "raw.ventas_lineas": version_raw,
        "curated.ventas_mensual": version,
        f"curated.{TABLA_PESOS}": version_pesos,
    }
