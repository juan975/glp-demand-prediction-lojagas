"""Petroecuador: estructura mensual de precios de venta en terminal (PDF).

Se extraen precio GLP industrial, agrícola, doméstico y diésel industrial para
construir ratios de sustitución (GLP/diésel en secado agroindustrial).
"""

from __future__ import annotations

import pandas as pd


class PreciosPetroecuador:
    nombre = "petroecuador_precios"
    disponible_desde_dias = 0  # se publica al inicio del mes: verificar

    def extraer(self, periodo: str) -> pd.DataFrame:
        raise NotImplementedError
