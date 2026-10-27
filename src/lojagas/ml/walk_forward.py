"""Validación walk-forward con ventana expansiva sobre meses.

Fold k: entrena con todos los meses < m_k, evalúa en [m_k, m_k + horizonte).
Las particiones son por MES, no por fila: así los 5 segmentos de un mismo mes
nunca quedan repartidos entre entrenamiento y prueba.
"""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np
import pandas as pd


def particiones(
    meses: pd.Series, min_entrenamiento: int, horizonte: int = 1, paso: int = 1
) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    unicos = np.sort(pd.to_datetime(meses).unique())
    if len(unicos) < min_entrenamiento + horizonte:
        raise ValueError(
            f"Hay {len(unicos)} meses; se necesitan al menos {min_entrenamiento + horizonte}"
        )
    valores = pd.to_datetime(meses).to_numpy()
    for i in range(min_entrenamiento, len(unicos) - horizonte + 1, paso):
        corte, fin = unicos[i], unicos[i + horizonte - 1]
        entrenamiento = valores < corte
        prueba = (valores >= corte) & (valores <= fin)
        assert valores[entrenamiento].max() < valores[prueba].min(), "Fuga temporal"
        yield np.flatnonzero(entrenamiento), np.flatnonzero(prueba)
