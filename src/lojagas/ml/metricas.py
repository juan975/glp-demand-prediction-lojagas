"""Métricas de regresión.

WAPE es la métrica principal y la del criterio de éxito: superar al estacional
ingenuo (ver `evaluacion.supera_baseline`). Pondera por volumen y no se indefine.

MAPE se sigue reportando porque el documento lo usa (< 10 %, issue I-13), pero no
decide: se indefine cuando y = 0, explota con segmentos de bajo volumen y el
estacional ingenuo ya cumple ese umbral sin aprendizaje automático.
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


def mejora_relativa(modelo, referencia):
    """En %. Cuánto reduce el modelo el error de la referencia (positivo = mejor)."""
    return (referencia - modelo) / referencia * 100


TODAS = {"mae": mae, "rmse": rmse, "mape": mape, "wape": wape, "r2": r2}


def calcular(y, p) -> dict[str, float]:
    return {nombre: f(y, p) for nombre, f in TODAS.items()}
