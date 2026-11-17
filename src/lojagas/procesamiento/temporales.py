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


def extender_futuro(
    df: pd.DataFrame, horizonte: int, col_mes: str = "mes", grupo: str = "segmento"
) -> pd.DataFrame:
    """Agrega, por segmento, los `horizonte` meses posteriores al último observado, sin target.

    Con datos hasta octubre y horizonte 2 agrega noviembre y diciembre: la fila de
    diciembre es la que usa el predictor. En el entrenamiento se descartan por no tener target.
    """
    ultimo = pd.to_datetime(df[col_mes]).max()
    futuros = pd.date_range(ultimo + pd.offsets.MonthBegin(1), periods=horizonte, freq="MS")
    nuevas = pd.MultiIndex.from_product(
        [futuros, df[grupo].unique()], names=[col_mes, grupo]
    ).to_frame(index=False)
    return pd.concat([df, nuevas], ignore_index=True)


def rezagos(
    df: pd.DataFrame,
    *,
    horizonte: int,
    lags: tuple[int, ...] | None = None,
    ventanas: tuple[int, ...] = (3,),
    col: str = "toneladas",
    grupo: str = "segmento",
) -> pd.DataFrame:
    """Lags y medias móviles por segmento, disponibles al predecir con `horizonte` meses.

    Al predecir el mes t solo están cerrados los meses hasta t − horizonte: ningún lag
    puede ser menor que el horizonte y las medias se desplazan `horizonte` meses.
    """
    if lags is None:
        lags = (horizonte, horizonte + 1, horizonte + 2, 12)
    if min(lags) < horizonte:
        raise ValueError(f"Lags {lags} no disponibles con horizonte {horizonte}")
    out = df.sort_values([grupo, "mes"]).copy()
    g = out.groupby(grupo)[col]
    for k in lags:
        out[f"lag_{k}"] = g.shift(k)
    for w in ventanas:
        out[f"media_{w}"] = g.transform(lambda s, w=w: s.shift(horizonte).rolling(w).mean())
    return out
