"""ingenieria_caracteristicas.py — Curated → Feature."""

from __future__ import annotations

import pandas as pd

from lojagas.comun import lakehouse
from lojagas.comun.config import Config
from lojagas.ingesta.externas.era5_land import ERA5Land
from lojagas.procesamiento.clima import variables_clima
from lojagas.procesamiento.curacion import TABLA_CLIMA, TABLA_PESOS
from lojagas.procesamiento.dias_venta import dias_venta
from lojagas.procesamiento.eventos import (
    TIPO_FERIADO,
    dias_de_eventos,
    dias_evento_en_mes,
    dias_feriado,
)
from lojagas.procesamiento.temporales import (
    calendario,
    extender_futuro,
    rezago_minimo_externo,
    rezagos,
)


def construir(
    mensual: pd.DataFrame,
    eventos: pd.DataFrame | None = None,
    *,
    horizonte: int,
    pesos: pd.DataFrame | None = None,
    clima: pd.DataFrame | None = None,
    rezago_clima: int | None = None,
) -> pd.DataFrame:
    """Función pura (se testea sin lakehouse). Incluye las filas futuras sin target."""
    df = calendario(rezagos(extender_futuro(mensual, horizonte), horizonte=horizonte))
    if eventos is not None:
        df["dias_religioso"] = dias_evento_en_mes(df["mes"], eventos, "religioso").to_numpy()
        df["dias_feriado"] = dias_feriado(df["mes"], eventos)
    if pesos is not None:
        # Calendario: se conoce de antemano, también para las filas futuras
        df["dias_venta"] = dias_venta(df, pesos)
        # Estacional ingenuo ajustado por días de venta: lo del mismo mes del año anterior,
        # escalado por cuántos días de venta tiene este mes frente a aquel
        df["ratio_dias_12"] = df["dias_venta"] / df.groupby("segmento")["dias_venta"].shift(12)
        df["estacional_dias"] = df["lag_12"] * df["ratio_dias_12"]
        if eventos is not None:
            # Variante con feriados (un feriado vale como un domingo). Queda aparte para
            # decidir si va en la configuración A o en la B.
            feriados = dias_de_eventos(eventos, TIPO_FERIADO)
            df["dias_venta_feriados"] = dias_venta(df, pesos, feriados).where(
                df["dias_feriado"].notna()
            )
    if clima is not None:
        if rezago_clima is None:
            raise ValueError("El clima necesita su rezago (ver rezago_minimo_externo)")
        df["mes"] = df["mes"].astype("datetime64[ns]")
        df = df.merge(variables_clima(clima, rezago_clima), on="mes", how="left")
    return df


def _leer_opcional(cfg: Config, tabla: str) -> pd.DataFrame | None:
    if not lakehouse.existe(cfg.lakehouse, "curated", tabla):
        return None
    return lakehouse.leer(cfg.lakehouse, "curated", tabla)


def ejecutar(cfg: Config) -> int:
    mensual = lakehouse.leer(cfg.lakehouse, "curated", "ventas_mensual")
    eventos = lakehouse.leer(cfg.lakehouse, "curated", "calendario_eventos")
    rezago = rezago_minimo_externo(
        ERA5Land.disponible_desde_dias, cfg.dia_ejecucion, cfg.horizonte_meses
    )
    features = construir(
        mensual,
        eventos,
        horizonte=cfg.horizonte_meses,
        pesos=_leer_opcional(cfg, TABLA_PESOS),
        clima=_leer_opcional(cfg, TABLA_CLIMA),
        rezago_clima=rezago,
    )
    return lakehouse.escribir(
        features, cfg.lakehouse, "feature", "demanda_mensual", modo="overwrite"
    )
