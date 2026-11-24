"""Precios al productor por provincia (MAG, tablero «Cifras territoriales»): bloque agrícola.

Los clientes agroindustriales de Lojagas secan maíz, arroz y café en Loja, y quizá cacao en
Zamora Chinchipe. El precio al productor de la provincia resume cómo viene la cosecha y el
mercado local; no lo captura la estacionalidad que el modelo ya tiene. Se prefiere al boletín
nacional del SIPA porque ese es un promedio ponderado por producción, dominado por Los Ríos y
Guayas (en septiembre de 2024 el maíz estaba en 18,34 USD/qq en Loja y en 16,69 a nivel nacional).

Fuente: tablero público del MAG (Tableau), hoja `precios_pp`, un precio promedio por provincia,
mes y producto-presentación:
    https://servicios.mag.gob.ec/tableros/Territorial_24/Cifras_territoriales

El tablero solo se puede leer con un navegador, así que no se consulta desde el contenedor: el
script `scripts/precios_productor_mag.py` lo descarga y actualiza
`referencias/precios_productor_mag.csv` (como el CSV de Petroecuador), y esta fuente lo lee.

Series elegidas (las que tienen datos casi todos los meses desde 2023):
- Loja: maíz duro seco, arroz y café, en quintal de 100 lb.
- Zamora Chinchipe: cacao, en quintal de 100 lb. El café de Zamora queda fuera: le falta la mitad
  de los meses.
Los meses sin dato (casi siempre enero y febrero, cuando el MAG no levanta precios en la
provincia) quedan vacíos; no se rellenan.
"""

from __future__ import annotations

import logging
import os
from datetime import date
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

RUTA = Path(os.environ.get("LOJAGAS_REFERENCIAS", "referencias")) / "precios_productor_mag.csv"
URL = "https://servicios.mag.gob.ec/tableros/Territorial_24/Cifras_territoriales"
# (provincia, producto tal como viene en el tablero) → clave del producto
SERIES = {
    ("LOJA", "Maíz duro seco (Quintal aprox. 100 Libra)"): "maiz_duro_seco",
    ("LOJA", "Arroz (Quintal aprox. 100 Libra)"): "arroz",
    ("LOJA", "Café (Quintal aprox. 100 Libra)"): "cafe",
    ("ZAMORA CHINCHIPE", "Cacao (Quintal aprox. 100 Libra)"): "cacao",
}
COLUMNAS = ["mes", "provincia", "producto", "presentacion", "precio_usd", "fuente_url"]
# Las ventas empiezan en enero de 2023; desde ahí se avisa de los meses sin dato
AVISAR_DESDE = date(2023, 1, 1)


def seleccionar(crudo: pd.DataFrame) -> pd.DataFrame:
    """Descarga completa del tablero → solo las series elegidas, en el formato del CSV."""
    claves = pd.Series(
        list(zip(crudo["provincia"], crudo["producto"], strict=True)), index=crudo.index
    )
    df = crudo[claves.isin(SERIES.keys())].copy()
    df["presentacion"] = df["producto"]
    df["producto"] = [
        SERIES[(p, n)] for p, n in zip(df["provincia"], df["presentacion"], strict=True)
    ]
    df["mes"] = pd.to_datetime(dict(year=df["anio"], month=df["mes"], day=1))
    df["precio_usd"] = pd.to_numeric(df["precio_usd"], errors="coerce").round(4)
    df["fuente_url"] = URL
    df = df.dropna(subset=["precio_usd"])
    return df[COLUMNAS].sort_values(["provincia", "producto", "mes"]).reset_index(drop=True)


def validar(df: pd.DataFrame) -> None:
    faltantes = set(COLUMNAS) - set(df.columns)
    if faltantes:
        raise ValueError(f"precios_productor_mag.csv sin columnas: {faltantes}")
    if df.duplicated(["mes", "provincia", "producto"]).any():
        raise ValueError("precios_productor_mag.csv tiene meses repetidos para un producto")
    # `> 0` es falso con NaN: así una celda vacía también falla (con `<= 0` pasaba)
    if not (df["precio_usd"] > 0).all():
        raise ValueError("precios_productor_mag.csv tiene precios vacíos, en cero o negativos")
    desconocidos = set(zip(df["provincia"], df["producto"], strict=True)) - {
        (p, c) for (p, _), c in SERIES.items()
    }
    if desconocidos:
        raise ValueError(f"Series no esperadas en precios_productor_mag.csv: {desconocidos}")


def huecos(df: pd.DataFrame, desde: date, hasta: date) -> dict[str, list[str]]:
    """Meses sin precio por serie, entre `desde` y `hasta` (inclusive)."""
    meses = pd.date_range(desde, hasta, freq="MS")
    res = {}
    for (provincia, producto), g in df.groupby(["provincia", "producto"]):
        faltan = meses.difference(pd.DatetimeIndex(g["mes"]))
        if len(faltan):
            res[f"{provincia}/{producto}"] = [f"{m:%Y-%m}" for m in faltan]
    return res


class PreciosProductorMAG:
    nombre = "precios_productor_mag"
    # El tablero publica el mes completo a inicios del siguiente (en noviembre ya estaba octubre)
    disponible_desde_dias = 10

    def __init__(self, ruta: Path = RUTA) -> None:
        self.ruta = ruta

    def extraer(self, periodo: str) -> pd.DataFrame:
        df = pd.read_csv(self.ruta, parse_dates=["mes"])
        validar(df)
        hasta = pd.Timestamp(periodo)
        df = df[df["mes"] <= hasta].reset_index(drop=True)
        faltan = huecos(df, AVISAR_DESDE, hasta.date())
        for serie, meses in faltan.items():
            log.warning("Precios MAG sin dato en %s: %s", serie, ", ".join(meses))
        if df.empty or df["mes"].max() < hasta - pd.DateOffset(months=2):
            log.warning(
                "precios_productor_mag.csv llega hasta %s: correr scripts/precios_productor_mag.py",
                f"{df['mes'].max():%Y-%m}" if not df.empty else "—",
            )
        return df
