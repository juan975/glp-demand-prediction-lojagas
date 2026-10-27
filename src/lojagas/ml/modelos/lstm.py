"""LSTM (PyTorch, CPU). Candidato condicionado.

Con ~46 observaciones mensuales por segmento, una LSTM tiene más parámetros que
datos. Se incluye para cumplir el objetivo comparativo, pero el resultado esperado
es que pierda contra los baselines; documentarlo como hallazgo, no como fallo.
"""

from __future__ import annotations


def crear():
    raise NotImplementedError("Implementar después de tener baselines y árboles evaluados")
