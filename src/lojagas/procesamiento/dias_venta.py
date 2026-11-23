"""Días de venta: los días de cada mes, ponderados por la actividad de su día de la semana.

Casi no se vende los domingos y el sábado es medio día, así que un mismo mes puede tener
hasta un 7 % más o menos de días de venta de un año a otro (experimento A, notebook 03).
Es calendario: se conoce de antemano para cualquier mes, también para los que se predicen.

Los pesos salen de los primeros `MESES_PESOS` meses de historia y quedan fijos. Así ningún
mes de prueba del walk-forward influye en ellos: en el experimento A los pesos son de 2023
y la prueba empieza en 2025.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd

from lojagas.procesamiento.agregacion import EXCLUIR, asignar_segmento

MESES_PESOS = 12
DOMINGO = 6


def pesos_dia_semana(
    lineas: pd.DataFrame, mapa: pd.DataFrame, meses: int = MESES_PESOS
) -> pd.DataFrame:
    """Actividad relativa de cada día de la semana por segmento (1 = día promedio).

    Solo facturas con kg de GLP: una nota de crédito se emite el día en que se corrige, no
    el día en que se vendió. Un segmento sin ventas en la ventana queda con peso 1 en todos
    los días (cuentan como días comunes).
    """
    df = lineas[(lineas["kg_glp"].fillna(0) > 0) & (lineas["move_type"] == "out_invoice")].copy()
    df["segmento"] = asignar_segmento(df, mapa)
    df = df[df["segmento"] != EXCLUIR]
    fecha = pd.to_datetime(df["fecha_factura"])

    desde = fecha.min().to_period("M").to_timestamp()
    hasta = min(
        desde + pd.DateOffset(months=meses), (fecha.max().to_period("M") + 1).to_timestamp()
    )
    en_ventana = (fecha >= desde) & (fecha < hasta)
    kg = (
        df[en_ventana]
        .assign(dia_semana=fecha[en_ventana].dt.day_of_week)
        .groupby(["segmento", "dia_semana"])["kg_glp"]
        .sum()
    )
    rejilla = pd.MultiIndex.from_product(
        [sorted(df["segmento"].unique()), range(7)], names=["segmento", "dia_semana"]
    )
    kg = kg.reindex(rejilla, fill_value=0.0)

    # Cuántas veces aparece cada día de la semana en la ventana
    veces = np.bincount(
        pd.date_range(desde, hasta - pd.Timedelta(days=1)).day_of_week, minlength=7
    ).astype(float)
    veces[veces == 0] = np.nan
    por_dia = kg / veces[kg.index.get_level_values("dia_semana")]
    peso = (por_dia / por_dia.groupby(level="segmento").transform("mean")).fillna(1.0)
    return peso.rename("peso").reset_index().assign(desde=desde, hasta=hasta - pd.Timedelta(days=1))


def _conteo_dias(mes: pd.Timestamp, feriados: list[pd.Timestamp]) -> np.ndarray:
    """Cuántos lunes, martes… domingos tiene el mes; un feriado cuenta como domingo."""
    dias = pd.date_range(mes, mes + pd.offsets.MonthEnd(0))
    dia_semana = np.where(dias.isin(feriados), DOMINGO, dias.day_of_week)
    return np.bincount(dia_semana, minlength=7)


def dias_venta(
    df: pd.DataFrame,
    pesos: pd.DataFrame,
    feriados: Iterable[pd.Timestamp] | None = None,
    col_mes: str = "mes",
    grupo: str = "segmento",
) -> pd.Series:
    """Días de venta de cada fila: la suma del peso de cada día del mes.

    Con `feriados`, un feriado vale lo mismo que un domingo. Es un supuesto: falta que
    Lojagas confirme qué feriados no se trabajan (PENDIENTES, sección 5.6).
    """
    tabla = pesos.pivot_table(index="segmento", columns="dia_semana", values="peso")
    tabla = tabla.reindex(columns=range(7))
    faltan = set(df[grupo]) - set(tabla.index)
    if faltan:
        raise ValueError(f"Segmentos sin pesos de días de la semana: {sorted(faltan)}")

    lista_feriados = [] if feriados is None else list(pd.to_datetime(list(feriados)))
    meses = pd.to_datetime(df[col_mes])
    conteos = {m: _conteo_dias(m, lista_feriados) for m in pd.DatetimeIndex(meses.unique())}
    vectores = {s: fila.to_numpy() for s, fila in tabla.iterrows()}
    return pd.Series(
        [float(conteos[m] @ vectores[s]) for m, s in zip(meses, df[grupo], strict=True)],
        index=df.index,
        name="dias_venta",
    )
