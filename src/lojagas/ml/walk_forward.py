"""Validación walk-forward con ventana expansiva sobre meses.

Fold k: evalúa en [m_k, m_k + meses_prueba) y entrena solo con los meses ≤ m_k − horizonte.
Con horizonte h, al predecir m_k los meses m_k − h + 1 … m_k − 1 todavía no están
cerrados: entrenar con ellos sería usar datos que en producción no existen.

Las particiones son por MES, no por fila: así los segmentos de un mismo mes
nunca quedan repartidos entre entrenamiento y prueba.
"""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np
import pandas as pd


def particiones(
    meses: pd.Series,
    min_entrenamiento: int,
    *,
    horizonte: int,
    meses_prueba: int = 1,
    paso: int = 1,
) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    unicos = np.sort(pd.to_datetime(meses).unique())
    separacion = horizonte - 1
    necesarios = min_entrenamiento + separacion + meses_prueba
    if len(unicos) < necesarios:
        raise ValueError(f"Hay {len(unicos)} meses; se necesitan al menos {necesarios}")
    valores = pd.to_datetime(meses).to_numpy()
    for i in range(min_entrenamiento + separacion, len(unicos) - meses_prueba + 1, paso):
        corte, fin = unicos[i], unicos[i + meses_prueba - 1]
        entrenamiento = valores < unicos[i - separacion]
        prueba = (valores >= corte) & (valores <= fin)
        ultimo = pd.Timestamp(valores[entrenamiento].max()).to_period("M")
        assert (pd.Timestamp(corte).to_period("M") - ultimo).n >= horizonte, "Fuga temporal"
        yield np.flatnonzero(entrenamiento), np.flatnonzero(prueba)
