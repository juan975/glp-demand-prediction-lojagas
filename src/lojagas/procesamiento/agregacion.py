"""De línea de factura a serie mensual por segmento, en toneladas.

Decisiones que este código hace explícitas (y que el documento aún no fija):
1. Notas de crédito restan (signo -1), según el caveat 1 del diccionario de datos.
2. El target es volumen físico (t), no USD. Solo cuentan las líneas con kg de GLP.
3. El segmento sale de `referencias/mapa_segmentos.csv`. Las columnas del mapa (salvo
   `segmento`) son las claves, así que cambiar el campo de segmentación (I-04) es editar
   el CSV, no este código. El segmento `excluir` saca líneas que no son demanda de gas
   (p. ej., la venta del envase). Si una combinación no está mapeada, falla en vez de
   asignar un segmento por defecto.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

KG_POR_TONELADA = 1000.0
COMODIN = "*"
EXCLUIR = "excluir"


def cargar_mapa_segmentos(ruta: Path) -> pd.DataFrame:
    # keep_default_na=False: una celda vacía es el valor "", no un nulo
    return pd.read_csv(ruta, dtype=str, keep_default_na=False)


def asignar_segmento(df: pd.DataFrame, mapa: pd.DataFrame) -> pd.Series:
    """Cada fila del mapa es una regla; `*` es comodín y gana la regla más específica."""
    mapa = mapa.reset_index(drop=True)
    claves = [c for c in mapa.columns if c != "segmento"]
    faltan = set(claves) - set(df.columns)
    if faltan:
        raise ValueError(f"Las líneas no tienen las columnas del mapa de segmentos: {faltan}")
    if mapa.duplicated(subset=claves).any():
        raise ValueError("mapa_segmentos.csv tiene reglas repetidas")

    valores = {c: df[c].astype("string").fillna("") for c in claves}
    especificidad = (mapa[claves] != COMODIN).sum(axis=1)
    seg = pd.Series(pd.NA, index=df.index, dtype="object")
    for i in especificidad.sort_values(ascending=False, kind="stable").index:
        regla = mapa.loc[i]
        cumple = seg.isna()
        for c in claves:
            if regla[c] != COMODIN:
                cumple &= valores[c] == regla[c]
        seg[cumple] = regla["segmento"]

    sin_mapear = df.loc[seg.isna(), claves].drop_duplicates()
    if not sin_mapear.empty:
        raise ValueError(
            "Combinaciones sin segmento en mapa_segmentos.csv:\n" + sin_mapear.to_string()
        )
    return seg


def a_mensual(lineas: pd.DataFrame, mapa: pd.DataFrame) -> pd.DataFrame:
    df = lineas[lineas["kg_glp"].fillna(0) > 0].copy()
    df["segmento"] = asignar_segmento(df, mapa)
    df = df[df["segmento"] != EXCLUIR]
    signo = df["move_type"].map({"out_invoice": 1.0, "out_refund": -1.0})
    df["toneladas"] = signo * df["kg_glp"] / KG_POR_TONELADA
    df["mes"] = pd.to_datetime(df["fecha_factura"]).dt.to_period("M").dt.to_timestamp()
    serie = df.groupby(["mes", "segmento"])["toneladas"].sum()

    # Un mes sin facturas en un segmento es 0, no un hueco: si no se completa,
    # los lags y el walk-forward se desalinean en silencio.
    meses = pd.date_range(serie.index.levels[0].min(), serie.index.levels[0].max(), freq="MS")
    grilla = pd.MultiIndex.from_product([meses, serie.index.levels[1]], names=["mes", "segmento"])
    return serie.reindex(grilla, fill_value=0.0).reset_index()
