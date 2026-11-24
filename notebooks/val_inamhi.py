"""Utilidades de la validación de ERA5-Land con estaciones de INAMHI (notebook 07).

Nivel 3 del documento de fuentes v4: las estaciones no entran al modelo; sirven para comprobar
que ERA5-Land representa bien el clima de Loja y Zamora Chinchipe y para decidir si hace falta
corregir un sesgo. No es código de producción: si una corrección se adopta, va a
`src/lojagas/procesamiento/` con sus tests (regla de notebooks/README.md).

Datos públicos (sin PII): las estaciones están en referencias/ y ERA5-Land se lee de la zona
Raw del lakehouse de la plataforma.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

from lojagas.comun import lakehouse
from lojagas.ingesta.externas.era5_land import a_unidades

REFERENCIAS = Path(__file__).resolve().parents[1] / "referencias"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
VARIABLES = ["precip_mm", "temp_media_c"]

# Superposición de las dos fuentes: ERA5-Land empieza en 1991 en Raw y la entrega de INAMHI
# termina en diciembre de 2019
PERIODO = (1991, 2019)
# Una estación entra a las métricas con al menos 10 años de meses comparables
MIN_MESES = 120
# Valores mensuales imposibles en Loja y Zamora: errores de digitación (p. ej., 5544,9 mm)
RANGOS = {"precip_mm": (0.0, 1500.0), "temp_media_c": (0.0, 35.0)}
# Gradiente térmico estándar de la atmósfera: la temperatura baja ~6,5 °C por km
GRADIENTE_C_POR_KM = 6.5


def raiz_lakehouse() -> Path:
    """Lakehouse de la plataforma (donde la ingesta dejó raw.era5_land)."""
    return Path(os.environ.get("LOJAGAS_LAKEHOUSE", "~/lojagas_datos/lakehouse")).expanduser()


# --- Estaciones ----------------------------------------------------------------------------


def cargar_estaciones() -> tuple[pd.DataFrame, pd.DataFrame]:
    """(estaciones, valores en formato largo: estacion, variable, mes, valor)."""
    estaciones = pd.read_csv(REFERENCIAS / "inamhi_estaciones.csv")
    ancho = pd.read_csv(REFERENCIAS / "inamhi_valores.csv")
    largo = ancho.melt(
        id_vars=["estacion", "variable", "anio"], value_vars=MESES, var_name="m", value_name="valor"
    ).dropna(subset=["valor"])
    largo["mes"] = pd.to_datetime(
        dict(year=largo["anio"], month=largo["m"].map(MESES.index) + 1, day=1)
    )
    return estaciones, largo[["estacion", "variable", "mes", "valor"]]


def filtrar_valores(largo: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(valores dentro del período y de rangos físicos, valores descartados por rango)."""
    en_periodo = largo[largo["mes"].dt.year.between(*PERIODO)]
    minimo = en_periodo["variable"].map(lambda v: RANGOS[v][0])
    maximo = en_periodo["variable"].map(lambda v: RANGOS[v][1])
    ok = en_periodo["valor"].between(minimo, maximo)
    return en_periodo[ok].copy(), en_periodo[~ok].copy()


# --- ERA5-Land -----------------------------------------------------------------------------


def era5_por_pixel(raiz: Path | None = None) -> pd.DataFrame:
    """raw.era5_land → una fila por píxel y mes, en °C y mm/mes, dentro del período."""
    raw = lakehouse.leer(raiz or raiz_lakehouse(), "raw", "era5_land")
    df = raw.assign(
        fecha=pd.to_datetime(raw["fecha"]), lat=raw["lat"].round(2), lon=raw["lon"].round(2)
    )
    # Los rectángulos de Loja y Zamora se superponen: un píxel puede venir dos veces
    df = df.drop_duplicates(["fecha", "lat", "lon"])
    df = a_unidades(df[df["fecha"].dt.year.between(*PERIODO)])
    return df.rename(columns={"fecha": "mes"})[["mes", "lat", "lon", *VARIABLES]]


def pixel_mas_cercano(estaciones: pd.DataFrame, pixeles: pd.DataFrame) -> pd.DataFrame:
    """Para cada estación, el centro de píxel de ERA5-Land más cercano y la distancia en km."""
    centros = pixeles[["lat", "lon"]].drop_duplicates().to_numpy()
    lat1 = np.radians(estaciones["lat"].to_numpy())[:, None]
    lon1 = np.radians(estaciones["lon"].to_numpy())[:, None]
    lat2, lon2 = np.radians(centros[:, 0])[None, :], np.radians(centros[:, 1])[None, :]
    # Haversine
    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    )
    distancias = 2 * 6371 * np.arcsin(np.sqrt(a))
    cerca = distancias.argmin(axis=1)
    return estaciones.assign(
        pixel_lat=centros[cerca, 0],
        pixel_lon=centros[cerca, 1],
        distancia_km=distancias[np.arange(len(estaciones)), cerca],
    )


def emparejar(valores: pd.DataFrame, pixeles: pd.DataFrame, cercanos: pd.DataFrame) -> pd.DataFrame:
    """Una fila por estación, variable y mes con el valor de la estación y el de su píxel."""
    era5 = pixeles.melt(
        id_vars=["mes", "lat", "lon"], value_vars=VARIABLES, var_name="variable", value_name="era5"
    ).rename(columns={"lat": "pixel_lat", "lon": "pixel_lon"})
    pares = valores.merge(
        cercanos[["estacion", "provincia", "altitud_m", "pixel_lat", "pixel_lon", "distancia_km"]],
        on="estacion",
    ).merge(era5, on=["mes", "variable", "pixel_lat", "pixel_lon"])
    # Ordenado por fecha: los valores vienen del formato ancho (todos los eneros, luego los
    # febreros...) y un gráfico de líneas sin ordenar salta de un año a otro
    pares = pares.sort_values(["estacion", "variable", "mes"]).reset_index(drop=True)
    return pares.rename(columns={"valor": "estacion_valor"})


def con_anomalias(pares: pd.DataFrame) -> pd.DataFrame:
    """Agrega la anomalía de cada serie frente a su propio promedio de ese mes del año.

    Compararlas quita los sesgos constantes (p. ej., la diferencia de altitud entre estación y
    píxel) y deja solo si las dos fuentes suben y bajan juntas, que es lo que usa el modelo.
    """
    pares = pares.assign(mes_del_anio=pares["mes"].dt.month)
    grupo = pares.groupby(["estacion", "variable", "mes_del_anio"])
    return pares.assign(
        estacion_anom=pares["estacion_valor"] - grupo["estacion_valor"].transform("mean"),
        era5_anom=pares["era5"] - grupo["era5"].transform("mean"),
    )


# --- Métricas ------------------------------------------------------------------------------


def _metricas(g: pd.DataFrame) -> pd.Series:
    error = g["era5"] - g["estacion_valor"]
    return pd.Series(
        {
            "meses": len(g),
            "estacion_media": g["estacion_valor"].mean(),
            "era5_media": g["era5"].mean(),
            "sesgo": error.mean(),  # ERA5 − estación: positivo si ERA5 da de más
            "sesgo_pct": 100 * error.sum() / g["estacion_valor"].sum(),
            "rmse": float(np.sqrt((error**2).mean())),
            "r": g["era5"].corr(g["estacion_valor"]),
            "r_anomalias": g["era5_anom"].corr(g["estacion_anom"]),
        }
    )


def metricas_por_estacion(pares: pd.DataFrame) -> pd.DataFrame:
    claves = ["provincia", "variable", "estacion", "altitud_m", "distancia_km"]
    tabla = pares.groupby(claves).apply(_metricas, include_groups=False).reset_index()
    return tabla[tabla["meses"] >= MIN_MESES].sort_values(["variable", "provincia", "estacion"])


def resumen(metricas: pd.DataFrame) -> pd.DataFrame:
    """Mediana entre estaciones por variable y provincia (robusta a una estación rara)."""
    return (
        metricas.groupby(["variable", "provincia"])
        .agg(
            estaciones=("estacion", "size"),
            sesgo=("sesgo", "median"),
            sesgo_pct=("sesgo_pct", "median"),
            rmse=("rmse", "median"),
            r=("r", "median"),
            r_anomalias=("r_anomalias", "median"),
        )
        .reset_index()
    )


def sesgo_por_altitud(metricas: pd.DataFrame) -> dict[str, float]:
    """Pendiente del sesgo de temperatura frente a la altitud de la estación, en °C por km.

    Si el sesgo de ERA5-Land se debe a que el píxel promedia terreno a otra altura, una
    estación más alta que su píxel es más fría: el sesgo (ERA5 − estación) crece con la
    altitud a un ritmo cercano al gradiente térmico (~6,5 °C/km).
    """
    t = metricas[metricas["variable"] == "temp_media_c"]
    if len(t) < 3:
        return {"estaciones": len(t), "pendiente_c_por_km": float("nan"), "r2": float("nan")}
    x, y = t["altitud_m"].to_numpy() / 1000, t["sesgo"].to_numpy()
    pendiente, ordenada = np.polyfit(x, y, 1)
    r2 = float(np.corrcoef(x, y)[0, 1] ** 2)
    return {
        "estaciones": len(t),
        "pendiente_c_por_km": float(pendiente),
        "r2": r2,
        "gradiente_esperado": GRADIENTE_C_POR_KM,
    }
