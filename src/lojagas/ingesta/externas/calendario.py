"""Calendario de eventos regionales (construcción manual, versionado en git).

Es dato público y conocido de antemano, por eso es una de las pocas variables
externas que sí está disponible para el mes a predecir.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

# En la imagen, referencias/ se copia a /app (WORKDIR); en local, se corre desde la raíz del repo
RUTA = Path(os.environ.get("LOJAGAS_REFERENCIAS", "referencias")) / "calendario_eventos.csv"
COLUMNAS = ["fecha_inicio", "fecha_fin", "tipo_evento", "nombre", "provincia", "canton"]


class CalendarioEventos:
    nombre = "calendario_eventos"
    disponible_desde_dias = -365  # se conoce con anticipación

    def __init__(self, ruta: Path = RUTA) -> None:
        self.ruta = ruta

    def extraer(self, periodo: str | None = None) -> pd.DataFrame:
        df = pd.read_csv(self.ruta, parse_dates=["fecha_inicio", "fecha_fin"])
        faltantes = set(COLUMNAS) - set(df.columns)
        if faltantes:
            raise ValueError(f"calendario_eventos.csv sin columnas: {faltantes}")
        if (df["fecha_fin"] < df["fecha_inicio"]).any():
            raise ValueError("Hay eventos con fecha_fin anterior a fecha_inicio")
        return df
