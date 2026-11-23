"""Clima mensual por provincia desde ERA5-Land: Raw → Curated, y sus variables con rezago.

Raw trae una fila por mes y píxel de los rectángulos de descarga, que incluyen píxeles de
provincias vecinas y de Perú. Aquí cada píxel se asigna a su provincia con el contorno del
INEC (referencias/provincias.geojson) y se promedia. La parte oeste de Zamora Chinchipe cae
en el rectángulo de Loja: por eso primero se juntan los píxeles de las dos descargas.
"""

from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd
import pandas as pd

from lojagas.ingesta.externas.era5_land import a_unidades

RUTA_PROVINCIAS = Path(os.environ.get("LOJAGAS_REFERENCIAS", "referencias")) / "provincias.geojson"
VARIABLES = ["temp_media_c", "precip_mm", "humedad_rel_pct"]
ANOMALIAS = {"temp_media_c": "temp_anom_c", "precip_mm": "precip_anom_mm"}
NORMAL = (1991, 2020)  # normal climatológica de la OMM
PRELIMINAR = "0005"  # expver de ERA5-Land-T; el dato final es 0001


def cargar_provincias(ruta: Path = RUTA_PROVINCIAS) -> gpd.GeoDataFrame:
    return gpd.read_file(ruta)[["provincia", "geometry"]]


def provincia_de_pixeles(pixeles: pd.DataFrame, provincias: gpd.GeoDataFrame) -> pd.Series:
    """Provincia de cada píxel (centro en lat, lon); NA si cae fuera de todas."""
    # Índice propio (0…n−1): el de `pixeles` puede venir repetido de un concat
    puntos = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(pixeles["lon"], pixeles["lat"]), crs=provincias.crs
    )
    unido = gpd.sjoin(puntos, provincias, how="left", predicate="within")
    # Un punto justo sobre un límite podría quedar en dos provincias: se toma la primera
    unido = unido[~unido.index.duplicated()].sort_index()
    return pd.Series(unido["provincia"].to_numpy(), index=pixeles.index, name="provincia")


def clima_mensual(raw: pd.DataFrame, periodo: str, provincias: gpd.GeoDataFrame) -> pd.DataFrame:
    """Raw de ERA5-Land → una fila por mes y provincia, en °C, mm/mes y %.

    Solo meses hasta el período, igual que las ventas: Raw guarda todo lo que Copernicus ya
    publicó, que puede incluir meses posteriores. Las anomalías se miden contra la normal
    1991-2020 del mismo mes del año.
    """
    df = raw.assign(
        fecha=pd.to_datetime(raw["fecha"]), lat=raw["lat"].round(2), lon=raw["lon"].round(2)
    )
    df = df[df["fecha"] <= pd.Timestamp(periodo)]
    # Los rectángulos de Loja y Zamora se superponen: un píxel puede venir en los dos
    df = df.drop_duplicates(subset=["fecha", "lat", "lon"])

    pixeles = df[["lat", "lon"]].drop_duplicates().reset_index(drop=True)
    pixeles["provincia"] = provincia_de_pixeles(pixeles, provincias)
    df = a_unidades(df.merge(pixeles.dropna(subset=["provincia"]), on=["lat", "lon"]))
    if "expver" in df.columns:
        df["preliminar"] = df["expver"].astype(str).str.zfill(4) == PRELIMINAR
    else:
        df["preliminar"] = False

    out = (
        df.groupby(["fecha", "provincia"])
        .agg(
            **{v: (v, "mean") for v in VARIABLES},
            pixeles=("lat", "size"),
            preliminar=("preliminar", "any"),
        )
        .reset_index()
        .rename(columns={"fecha": "mes"})
    )
    out["mes_del_anio"] = out["mes"].dt.month
    en_normal = out["mes"].dt.year.between(*NORMAL)
    normal = (
        out[en_normal]
        .groupby(["provincia", "mes_del_anio"])[list(ANOMALIAS)]
        .mean()
        .add_suffix("_normal")
    )
    out = out.join(normal, on=["provincia", "mes_del_anio"])
    for variable, anomalia in ANOMALIAS.items():
        out[anomalia] = out[variable] - out[f"{variable}_normal"]
    return (
        out.drop(columns=["mes_del_anio", *normal.columns])
        .sort_values(["provincia", "mes"])
        .reset_index(drop=True)
    )


def _nombre(provincia: str) -> str:
    return provincia.lower().replace(" ", "_")


def variables_clima(clima: pd.DataFrame, rezago: int) -> pd.DataFrame:
    """Una fila por mes con el clima de `rezago` meses antes, por provincia.

    `clima_loja_precip_mm_lag3` en la fila de diciembre es la lluvia de septiembre en Loja.
    El rezago sale de `rezago_minimo_externo`: con uno menor, el modelo usaría clima que el
    día de la corrida todavía no está publicado.
    """
    columnas = [*VARIABLES, *ANOMALIAS.values()]
    corrido = clima.assign(
        mes=(pd.to_datetime(clima["mes"]).dt.to_period("M") + rezago).dt.to_timestamp()
    )
    # pivot y no pivot_table: con un mes repetido falla en vez de promediarlo en silencio,
    # y no descarta las columnas vacías (anomalías sin normal)
    ancho = corrido.pivot(index="mes", columns="provincia", values=columnas)  # noqa: PD010
    ancho.columns = [f"clima_{_nombre(p)}_{v}_lag{rezago}" for v, p in ancho.columns]
    ancho = ancho.reset_index()
    ancho["mes"] = ancho["mes"].astype("datetime64[ns]")
    return ancho
