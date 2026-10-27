"""INAMHI: precipitación total y temperatura media mensual (datosabiertos.gob.ec).

Caveat de modelado: el dato del mes a predecir NO existe al momento de predecir.
Opciones: usar el mes anterior (rezago), la normal climatológica del mes, o
pronóstico estacional. Documentar la elección en la model card.
"""

from __future__ import annotations

import pandas as pd


class INAMHI:
    nombre = "inamhi"
    disponible_desde_dias = 60  # supuesto: verificar la latencia real de publicación

    def extraer(self, periodo: str) -> pd.DataFrame:
        raise NotImplementedError
