"""ERA5-Land monthly means (Copernicus CDS): clima mensual de Loja y Zamora Chinchipe.

Nivel 1 en Fuentes_Datos_Externos_Lojagas v4. Adaptado de los scripts validados
descarga_era5_loja.py y descarga_era5_zamora.py.

Qué guarda en Raw: una fila por mes y píxel (malla de 0.1°, unos 9 km), con las
variables tal como las entrega CDS (t2m y d2m en Kelvin, tp en m/día promedio del
mes). El rectángulo de cada provincia incluye píxeles de provincias vecinas y de
Perú: el promedio por provincia y la conversión de unidades (`a_unidades`) se
aplican en Procesamiento, no aquí.

Credenciales: cdsapi lee CDSAPI_URL y CDSAPI_KEY del entorno (las inyecta Airflow
desde el .env) o, en local, el archivo ~/.cdsapirc. Nunca van en el código.

Latencia: CDS entrega dos versiones, que se distinguen por `expver`:
    0005  preliminar (ERA5-Land-T): unos 5 días después del fin de mes.
    0001  final: 2-3 meses después (es la latencia que indica el catálogo).
Comprobado el 2026-11-22: final hasta agosto de 2026 y preliminar hasta octubre.
Se usa hasta el último mes completo, aunque sea preliminar, y cada corrida vuelve a
descargar todo, así que el preliminar se reemplaza solo cuando sale el final.
Consecuencia para el modelo: entrena con datos finales y predice con preliminares
(documentar en la model card). Como el preliminar sale hacia el día 5, una corrida
del día 2 (ADR-0014) todavía no tiene M−1: tendría hasta M−2.
"""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

DATASET = "reanalysis-era5-land-monthly-means"
VARIABLES = ["2m_temperature", "total_precipitation", "2m_dewpoint_temperature"]

# Formato CDS: [Norte, Oeste, Sur, Este], con margen para cubrir la malla de 0.1°
AREAS = {
    "LOJA": [-3.3, -80.6, -4.9, -79.0],
    "ZAMORA CHINCHIPE": [-3.3, -79.2, -5.1, -78.3],
}

# Desde 1991 para poder calcular la normal climatológica 1991-2020 (OMM) y tener
# el mismo mes de años anteriores para todo el histórico de ventas (2023 →).
ANIO_INICIO = 1991

COLUMNAS_RAW = ["fecha", "provincia_area", "lat", "lon", "t2m", "d2m", "tp"]

Descargador = Callable[[dict, Path], None]


def _descargar_cds(solicitud: dict, destino: Path) -> None:
    """Única función que sale a internet. Las pruebas la reemplazan."""
    import cdsapi

    cdsapi.Client().retrieve(DATASET, solicitud).download(str(destino))


def solicitud_cds(area: list[float], anios: list[int]) -> dict:
    return {
        "product_type": ["monthly_averaged_reanalysis"],
        "variable": VARIABLES,
        "year": [str(a) for a in anios],
        "month": [f"{m:02d}" for m in range(1, 13)],
        "time": ["00:00"],
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": area,
    }


def netcdf_a_tabla(ruta: Path, provincia_area: str) -> pd.DataFrame:
    """NetCDF de CDS → tabla larga mes × píxel, sin cambiar unidades."""
    import xarray as xr

    with xr.open_dataset(ruta) as ds:
        df = ds[["t2m", "d2m", "tp"]].to_dataframe().reset_index()
    tiempo = "valid_time" if "valid_time" in df.columns else "time"
    df = df.rename(columns={tiempo: "fecha", "latitude": "lat", "longitude": "lon"})
    df["fecha"] = pd.to_datetime(df["fecha"]).dt.to_period("M").dt.to_timestamp()
    df["provincia_area"] = provincia_area
    # Meses que CDS aún no publica llegan vacíos: no son ceros, se descartan
    df = df.dropna(subset=["t2m", "d2m", "tp"])
    extra = [c for c in ("expver",) if c in df.columns]  # expver distingue preliminar de final
    return df[COLUMNAS_RAW + extra].reset_index(drop=True)


def a_unidades(df: pd.DataFrame) -> pd.DataFrame:
    """Kelvin → °C, m/día → mm/mes y humedad relativa (Magnus). Para Procesamiento.

    Solo usa pandas/numpy, así que se puede importar desde la imagen de Procesamiento.
    """
    out = df.copy()
    temp = out["t2m"] - 273.15
    rocio = out["d2m"] - 273.15
    dias_mes = pd.to_datetime(out["fecha"]).dt.days_in_month
    out["temp_media_c"] = temp
    out["precip_mm"] = out["tp"] * 1000 * dias_mes
    out["humedad_rel_pct"] = 100 * (
        np.exp((17.625 * rocio) / (243.04 + rocio)) / np.exp((17.625 * temp) / (243.04 + temp))
    )
    return out


class ERA5Land:
    nombre = "era5_land"
    disponible_desde_dias = 7  # preliminar (expver 0005): unos 5 días + margen

    def __init__(
        self,
        descargador: Descargador = _descargar_cds,
        anio_inicio: int = ANIO_INICIO,
        areas: dict[str, list[float]] | None = None,
    ) -> None:
        self.descargador = descargador
        self.anio_inicio = anio_inicio
        self.areas = areas or AREAS

    def extraer(self, periodo: str) -> pd.DataFrame:
        """Descarga todo el histórico hasta `periodo` inclusive (se escribe en overwrite).

        CDS entrega el año completo publicado; se recorta en `periodo` para que reprocesar
        un mes pasado dé el mismo resultado y no deje en Raw meses posteriores.
        """
        anio_fin = date.fromisoformat(periodo).year
        anios = list(range(self.anio_inicio, anio_fin + 1))
        tablas = []
        with tempfile.TemporaryDirectory() as tmp:
            for provincia, area in self.areas.items():
                destino = Path(tmp) / f"era5_land_{provincia.replace(' ', '_').lower()}.nc"
                self.descargador(solicitud_cds(area, anios), destino)
                tablas.append(netcdf_a_tabla(destino, provincia))
        df = pd.concat(tablas, ignore_index=True)
        return df[df["fecha"] <= pd.Timestamp(periodo)].reset_index(drop=True)
