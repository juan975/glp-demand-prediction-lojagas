from __future__ import annotations

from typing import Protocol

import pandas as pd


class Fuente(Protocol):
    """Contrato de toda fuente externa.

    `disponible_desde_dias`: cuántos días después de terminar el mes se publica el dato.
    Es obligatorio: define si la variable puede usarse para predecir el mes siguiente
    o solo con rezago. Sin esto hay fuga de información del futuro.
    """

    nombre: str
    disponible_desde_dias: int

    def extraer(self, periodo: str) -> pd.DataFrame: ...
