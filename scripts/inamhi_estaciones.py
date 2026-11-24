"""Arma los CSV de estaciones de INAMHI de Loja y Zamora desde los CSV nacionales.

Fuente: datosabiertos.gob.ec, datasets "Precipitación total mensual" y "Temperatura media
mensual" de INAMHI (entrega cerrada a diciembre de 2019). Los CSV traen una fila por estación y
año, con los 12 meses en columnas, coma decimal y codificación CP850 (MS-DOS).

Uso (desde la raíz del repo, con los dos CSV descargados del portal):

    uv run python scripts/inamhi_estaciones.py \\
        --precipitacion inamhi-precipitacion-2019diciembre.csv \\
        --temperatura inamhi-temperaturamedia-2019diciembre.csv

Deja solo las estaciones dentro de Loja y Zamora Chinchipe (contorno del INEC en
referencias/provincias.geojson) y escribe dos archivos, para no repetir los datos de cada
estación en cada fila y quedar bajo el límite de 500 KB del pre-commit:

    referencias/inamhi_estaciones.csv  una fila por estación: nombre, provincia, lat, lon, altitud
    referencias/inamhi_valores.csv     una fila por estación, variable y año, con los 12 meses

Los valores van tal cual vienen; el filtro de valores imposibles se hace en la validación.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
SALIDA_ESTACIONES = Path("referencias/inamhi_estaciones.csv")
SALIDA_VALORES = Path("referencias/inamhi_valores.csv")


def leer(ruta: Path, variable: str) -> pd.DataFrame:
    # CP850 (MS-DOS): el byte 0xA5 es Ñ; leído como latin-1 saldría ¥ ("CA¥AVERAL")
    df = pd.read_csv(ruta, sep=";", decimal=",", encoding="cp850")
    df = df.rename(
        columns={
            "Estacion": "estacion",
            "NombreEstacion": "nombre",
            "longitud2": "lon",
            "latitud2": "lat",
            "altitud": "altitud_m",
        }
    )
    df.insert(1, "variable", variable)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--precipitacion", type=Path, required=True)
    parser.add_argument("--temperatura", type=Path, required=True)
    parser.add_argument("--provincias", type=Path, default=Path("referencias/provincias.geojson"))
    args = parser.parse_args()

    datos = pd.concat(
        [leer(args.precipitacion, "precip_mm"), leer(args.temperatura, "temp_media_c")],
        ignore_index=True,
    )
    # Coordenadas y altitud de cada estación (iguales en los dos archivos)
    estaciones = datos[["estacion", "nombre", "lat", "lon", "altitud_m"]].drop_duplicates(
        "estacion"
    )
    provincias = gpd.read_file(args.provincias)[["provincia", "geometry"]]
    puntos = gpd.GeoDataFrame(
        estaciones,
        geometry=gpd.points_from_xy(estaciones["lon"], estaciones["lat"]),
        crs=provincias.crs,
    )
    dentro = gpd.sjoin(puntos, provincias, how="inner", predicate="within")
    dentro = dentro[["estacion", "nombre", "provincia", "lat", "lon", "altitud_m"]].sort_values(
        ["provincia", "estacion"]
    )
    dentro.to_csv(SALIDA_ESTACIONES, index=False)

    valores = datos[datos["estacion"].isin(dentro["estacion"])]
    valores = valores[["estacion", "variable", "anio", *MESES]].sort_values(
        ["estacion", "variable", "anio"]
    )
    valores.to_csv(SALIDA_VALORES, index=False)
    print(
        f"{len(dentro)} estaciones ({dentro.groupby('provincia').size().to_dict()}), "
        f"{valores[MESES].notna().sum().sum():,} valores mensuales"
    )


if __name__ == "__main__":
    main()
