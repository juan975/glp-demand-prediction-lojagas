"""Baselines ingenuos. Todo modelo de ML se reporta CONTRA estos.

Si XGBoost no le gana al estacional ingenuo, el MAPE < 10 % no demuestra
que el aprendizaje automático aporte algo; solo que la serie es estable.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin


class _BaselineLag(BaseEstimator, RegressorMixin):
    def _columna(self) -> str:
        raise NotImplementedError

    def fit(self, X: pd.DataFrame, y=None):
        if self._columna() not in X.columns:
            raise ValueError(f"El baseline necesita la feature '{self._columna()}'")
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return X[self._columna()].to_numpy(dtype=float)


class Ingenuo(_BaselineLag):
    """ŷ_t = y_{t−h}: el último mes cerrado al predecir con horizonte h.

    Con h = 2, y_{t−1} todavía no existe: copiarlo sería usar información del futuro.
    """

    def __init__(self, horizonte: int | None = None):
        self.horizonte = horizonte

    def _columna(self) -> str:
        if self.horizonte is None:
            raise ValueError("Ingenuo necesita el horizonte (ver catalogo.crear)")
        return f"lag_{self.horizonte}"


class EstacionalIngenuo(_BaselineLag):
    """ŷ_t = y_{t−12}: el método actual de Lojagas. Válido con cualquier horizonte ≤ 12."""

    def _columna(self) -> str:
        return "lag_12"
