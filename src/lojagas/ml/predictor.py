"""predictor.py — Inferencia con el modelo que tenga el alias "produccion" en el
Model Registry de MLflow. Escribe en la zona Predicciones/ del Lakehouse, con
la versión del modelo y la delta_version de Feature usadas (trazabilidad).

La predicción anual NO es un modelo aparte: con 3–4 años de historia no hay
suficientes puntos anuales. Se obtiene agregando las predicciones mensuales.
"""

from __future__ import annotations

import pandas as pd

from lojagas.comun.config import Config


def cargar_modelo(cfg: Config):
    import mlflow

    mlflow.set_tracking_uri(cfg.mlflow_uri)
    return mlflow.pyfunc.load_model(f"models:/{cfg.modelo_registrado}@{cfg.alias_produccion}")


def predecir(cfg: Config, X: pd.DataFrame) -> pd.DataFrame:
    raise NotImplementedError
