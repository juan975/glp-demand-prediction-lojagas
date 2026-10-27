"""Baselines ingenuos. Todo modelo de ML se reporta CONTRA estos.

Si XGBoost no le gana al estacional ingenuo, el MAPE < 10 % no demuestra
que el aprendizaje automático aporte algo; solo que la serie es estable.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin


class _BaselineLag(BaseEstimator, RegressorMixin):
    columna: str = ""

    def fit(self, X: pd.DataFrame, y=None):
        if self.columna not in X.columns:
            raise ValueError(f"El baseline necesita la feature '{self.columna}'")
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return X[self.columna].to_numpy(dtype=float)


class Ingenuo(_BaselineLag):
    """ŷ_t = y_{t-1}"""

    columna = "lag_1"


class EstacionalIngenuo(_BaselineLag):
    """ŷ_t = y_{t-12}"""

    columna = "lag_12"
