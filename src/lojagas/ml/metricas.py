"""Métricas de regresión.

MAPE se mantiene porque es el criterio de éxito del documento (< 10 %), pero se
indefine cuando y = 0 y explota con valores pequeños (segmentos de bajo volumen).
Por eso se reporta también WAPE, que pondera por volumen y no se indefine.
"""

from __future__ import annotations

import numpy as np


def mae(y, p) -> float:
    return float(np.mean(np.abs(np.asarray(y) - np.asarray(p))))


def rmse(y, p) -> float:
    return float(np.sqrt(np.mean((np.asarray(y) - np.asarray(p)) ** 2)))


def mape(y, p) -> float:
    """En %. Devuelve NaN si algún valor real es 0 (no se oculta el problema)."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    if np.any(y == 0):
        return float("nan")
    return float(np.mean(np.abs((y - p) / y)) * 100)


def wape(y, p) -> float:
    """En %. Σ|y − ŷ| / Σ|y|."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    den = np.sum(np.abs(y))
    return float(np.sum(np.abs(y - p)) / den * 100) if den else float("nan")


def r2(y, p) -> float:
    y, p = np.asarray(y, float), np.asarray(p, float)
    ss_tot = np.sum((y - y.mean()) ** 2)
    return float(1 - np.sum((y - p) ** 2) / ss_tot) if ss_tot else float("nan")


TODAS = {"mae": mae, "rmse": rmse, "mape": mape, "wape": wape, "r2": r2}


def calcular(y, p) -> dict[str, float]:
    return {nombre: f(y, p) for nombre, f in TODAS.items()}
