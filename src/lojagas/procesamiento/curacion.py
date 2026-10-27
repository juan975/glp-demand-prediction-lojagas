"""curacion.py — Raw → Curated. Orden obligatorio, no se altera:

1. Contrato Raw (si falla, el DAG se detiene).
2. Seudonimización (ninguna PII llega a Curated).
3. Agregación a toneladas por mes y segmento.
4. Contrato Curated.
"""

from __future__ import annotations

from pathlib import Path

from lojagas.comun import lakehouse
from lojagas.comun.config import Config
from lojagas.procesamiento.agregacion import a_mensual, cargar_mapa_segmentos
from lojagas.procesamiento.anonimizacion import seudonimizar
from lojagas.procesamiento.contratos import ventas_mensual_curated, ventas_raw

MAPA_SEGMENTOS = Path("referencias/mapa_segmentos.csv")


def ejecutar(cfg: Config) -> dict[str, int]:
    raw = lakehouse.leer(cfg.lakehouse, "raw", "ventas_lineas")
    version_raw = lakehouse.version_actual(cfg.lakehouse, "raw", "ventas_lineas")

    ventas_raw.validate(raw, lazy=True)
    lineas = seudonimizar(raw, cfg.pii_salt)
    lakehouse.escribir(lineas, cfg.lakehouse, "curated", "ventas_lineas", modo="overwrite")

    mensual = ventas_mensual_curated.validate(
        a_mensual(lineas, cargar_mapa_segmentos(MAPA_SEGMENTOS))
    )
    version = lakehouse.escribir(
        mensual, cfg.lakehouse, "curated", "ventas_mensual", modo="overwrite"
    )
    return {"raw.ventas_lineas": version_raw, "curated.ventas_mensual": version}
