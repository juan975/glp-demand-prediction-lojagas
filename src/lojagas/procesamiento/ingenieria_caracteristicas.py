"""ingenieria_caracteristicas.py — Curated → Feature."""

from __future__ import annotations

import pandas as pd

from lojagas.comun import lakehouse
from lojagas.comun.config import Config
from lojagas.procesamiento.curacion import TABLA_PESOS
from lojagas.procesamiento.dias_venta import dias_venta
from lojagas.procesamiento.eventos import dias_evento_en_mes
from lojagas.procesamiento.temporales import calendario, extender_futuro, rezagos


def construir(
    mensual: pd.DataFrame,
    eventos: pd.DataFrame | None = None,
    *,
    horizonte: int,
    pesos: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Función pura (se testea sin lakehouse). Incluye las filas futuras sin target."""
    df = calendario(rezagos(extender_futuro(mensual, horizonte), horizonte=horizonte))
    if eventos is not None:
        df["dias_religioso"] = dias_evento_en_mes(df["mes"], eventos, "religioso").to_numpy()
    if pesos is not None:
        # Calendario: se conoce de antemano, también para las filas futuras
        df["dias_venta"] = dias_venta(df, pesos)
        # Estacional ingenuo ajustado por días de venta: lo del mismo mes del año anterior,
        # escalado por cuántos días de venta tiene este mes frente a aquel
        df["ratio_dias_12"] = df["dias_venta"] / df.groupby("segmento")["dias_venta"].shift(12)
        df["estacional_dias"] = df["lag_12"] * df["ratio_dias_12"]
    return df


def ejecutar(cfg: Config) -> int:
    mensual = lakehouse.leer(cfg.lakehouse, "curated", "ventas_mensual")
    eventos = lakehouse.leer(cfg.lakehouse, "curated", "calendario_eventos")
    pesos = (
        lakehouse.leer(cfg.lakehouse, "curated", TABLA_PESOS)
        if lakehouse.existe(cfg.lakehouse, "curated", TABLA_PESOS)
        else None
    )
    return lakehouse.escribir(
        construir(mensual, eventos, horizonte=cfg.horizonte_meses, pesos=pesos),
        cfg.lakehouse,
        "feature",
        "demanda_mensual",
        modo="overwrite",
    )
