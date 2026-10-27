from __future__ import annotations

import numpy as np
import pandas as pd


def calendario(df: pd.DataFrame, col_mes: str = "mes") -> pd.DataFrame:
    """Mes codificado en seno/coseno: diciembre y enero quedan cerca."""
    out = df.copy()
    m = pd.to_datetime(out[col_mes]).dt.month
    out["mes_sin"] = np.sin(2 * np.pi * m / 12)
    out["mes_cos"] = np.cos(2 * np.pi * m / 12)
    out["anio"] = pd.to_datetime(out[col_mes]).dt.year
    return out


def rezagos(
    df: pd.DataFrame,
    lags: tuple[int, ...] = (1, 2, 3, 12),
    ventanas: tuple[int, ...] = (3,),
    col: str = "toneladas",
    grupo: str = "segmento",
) -> pd.DataFrame:
    """Lags y medias móviles por segmento.

    Las medias usan shift(1): nunca incluyen el mes actual.
    """
    out = df.sort_values([grupo, "mes"]).copy()
    g = out.groupby(grupo)[col]
    for k in lags:
        out[f"lag_{k}"] = g.shift(k)
    for w in ventanas:
        out[f"media_{w}"] = g.transform(lambda s, w=w: s.shift(1).rolling(w).mean())
    return out
