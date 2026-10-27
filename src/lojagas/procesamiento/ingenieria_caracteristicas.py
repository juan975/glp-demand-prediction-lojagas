"""ingenieria_caracteristicas.py — Curated → Feature."""

from __future__ import annotations

import pandas as pd

from lojagas.comun import lakehouse
from lojagas.comun.config import Config
from lojagas.procesamiento.eventos import dias_evento_en_mes
from lojagas.procesamiento.temporales import calendario, rezagos


def construir(mensual: pd.DataFrame, eventos: pd.DataFrame | None = None) -> pd.DataFrame:
    """Función pura (se testea sin lakehouse)."""
    df = calendario(rezagos(mensual))
    if eventos is not None:
        df["dias_religioso"] = dias_evento_en_mes(df["mes"], eventos, "religioso").to_numpy()
    return df


def ejecutar(cfg: Config) -> int:
    mensual = lakehouse.leer(cfg.lakehouse, "curated", "ventas_mensual")
    eventos = lakehouse.leer(cfg.lakehouse, "raw", "calendario_eventos")
    return lakehouse.escribir(
        construir(mensual, eventos),
        cfg.lakehouse,
        "feature",
        "demanda_mensual",
        modo="overwrite",
    )
