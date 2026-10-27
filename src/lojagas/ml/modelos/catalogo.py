"""Catálogo de candidatos. Cada entrada es una fábrica: devuelve un modelo nuevo por fold.

Con ~46 meses × 5 segmentos, los hiperparámetros por defecto de los árboles
sobreajustan. Los valores de abajo son conservadores; Optuna los ajusta después
SIEMPRE dentro del walk-forward (nunca con todo el histórico).
"""

from __future__ import annotations

from collections.abc import Callable

from sklearn.base import RegressorMixin
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet, Lasso, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from lojagas.ml.modelos.baselines import EstacionalIngenuo, Ingenuo

SEMILLA = 42


def _xgboost() -> RegressorMixin:
    from xgboost import XGBRegressor

    return XGBRegressor(
        n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=SEMILLA
    )


def _lightgbm() -> RegressorMixin:
    from lightgbm import LGBMRegressor

    return LGBMRegressor(
        n_estimators=300,
        num_leaves=8,
        learning_rate=0.05,
        min_child_samples=5,
        random_state=SEMILLA,
        verbose=-1,
    )


CATALOGO: dict[str, Callable[[], RegressorMixin]] = {
    "ingenuo": Ingenuo,
    "estacional_ingenuo": EstacionalIngenuo,
    "lasso": lambda: make_pipeline(StandardScaler(), Lasso(alpha=0.1, random_state=SEMILLA)),
    "ridge": lambda: make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
    "elastic_net": lambda: make_pipeline(
        StandardScaler(), ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=SEMILLA)
    ),
    "random_forest": lambda: RandomForestRegressor(
        n_estimators=300, max_depth=4, min_samples_leaf=3, random_state=SEMILLA
    ),
    "xgboost": _xgboost,
    "lightgbm": _lightgbm,
    # "lstm": ver modelos/lstm.py — se agrega solo si el volumen de datos lo justifica
}

BASELINES = ("ingenuo", "estacional_ingenuo")
