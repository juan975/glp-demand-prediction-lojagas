from __future__ import annotations

import numpy as np
import pandas as pd


def calendario(df: pd.DataFrame, col_mes: str = "mes") -> pd.DataFrame:
    """Mes codificado en seno/coseno: diciembre y enero quedan cerca."""
    out = df.copy()
    m = pd.to_datetime(out[col_mes]).dt.month
    out["mes_sin"] = np.sin(2 * np.pi * m / 12)
    out["mes_cos"] = np.cos(2 * np.pi * m / 12)
    # Segundo armónico: un solo seno/coseno no representa dos picos al año
    # (el agroindustrial tiene uno en junio y otro en octubre)
    out["mes_sin2"] = np.sin(4 * np.pi * m / 12)
    out["mes_cos2"] = np.cos(4 * np.pi * m / 12)
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


def rezago_minimo_externo(disponible_desde_dias: int, dia_ejecucion: int, horizonte: int) -> int:
    """Menor rezago, en meses respecto del mes a predecir, de una fuente externa que ya está
    publicada el día en que corre el DAG.

    El DAG corre el día `dia_ejecucion` del mes M y predice M + horizonte − 1. El dato del mes
    M − k se publica `disponible_desde_dias` días después de que ese mes termina. Se cuenta
    con el peor caso (meses de 28 días hacia atrás, de 31 hacia adelante), así que el rezago
    nunca es menor que el real. Con ERA5-Land (7 días) y la corrida del día 2 solo está M − 2:
    rezago 3. Una fuente que se conoce de antemano, como el calendario, puede entrar sin rezago.
    """
    k = 1 - horizonte  # el propio mes a predecir: rezago 0
    while disponible_desde_dias > (28 if k >= 1 else 31) * (k - 1) + dia_ejecucion:
        k += 1
    return horizonte - 1 + k


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
