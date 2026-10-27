"""De línea de factura a serie mensual por segmento, en toneladas.

Decisiones que este código hace explícitas (y que el documento aún no fija):
1. Notas de crédito restan (signo -1), según el caveat 1 del diccionario de datos.
2. El target es volumen físico (t), no USD.
3. El segmento sale de `referencias/mapa_segmentos.csv`. Si una combinación no
   está mapeada, falla en vez de asignar un segmento por defecto.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

KG_POR_TONELADA = 1000.0


def cargar_mapa_segmentos(ruta: Path) -> pd.DataFrame:
    return pd.read_csv(ruta, dtype=str)


def asignar_segmento(df: pd.DataFrame, mapa: pd.DataFrame) -> pd.Series:
    """Prioridad: coincidencia exacta (canal, tipo) > comodín (canal, *)."""
    exactas = mapa[mapa["cliente_tipo"] != "*"].set_index(["canal_venta", "cliente_tipo"])[
        "segmento"
    ]
    comodin = mapa[mapa["cliente_tipo"] == "*"].set_index("canal_venta")["segmento"]

    claves = pd.MultiIndex.from_arrays([df["canal_venta"], df["cliente_tipo"].fillna("")])
    seg = pd.Series(exactas.reindex(claves).to_numpy(), index=df.index)
    seg = seg.fillna(df["canal_venta"].map(comodin))

    sin_mapear = df.loc[seg.isna(), ["canal_venta", "cliente_tipo"]].drop_duplicates()
    if not sin_mapear.empty:
        raise ValueError(
            "Combinaciones sin segmento en mapa_segmentos.csv:\n" + sin_mapear.to_string()
        )
    return seg


def a_mensual(lineas: pd.DataFrame, mapa: pd.DataFrame) -> pd.DataFrame:
    df = lineas[lineas["kg_glp"].notna()].copy()
    signo = df["move_type"].map({"out_invoice": 1.0, "out_refund": -1.0})
    df["toneladas"] = signo * df["kg_glp"] / KG_POR_TONELADA
    df["segmento"] = asignar_segmento(df, mapa)
    df["mes"] = pd.to_datetime(df["fecha_factura"]).dt.to_period("M").dt.to_timestamp()
    serie = df.groupby(["mes", "segmento"])["toneladas"].sum()

    # Un mes sin facturas en un segmento es 0, no un hueco: si no se completa,
    # los lags y el walk-forward se desalinean en silencio.
    meses = pd.date_range(serie.index.levels[0].min(), serie.index.levels[0].max(), freq="MS")
    grilla = pd.MultiIndex.from_product([meses, serie.index.levels[1]], names=["mes", "segmento"])
    return serie.reindex(grilla, fill_value=0.0).reset_index()
