"""Entrenamiento y comparación de candidatos con walk-forward, registrado en MLflow.

Política (hasta que exista el ADR de promoción): el mejor modelo por WAPE medio
queda con alias "candidato". Pasarlo a "produccion" es una acción MANUAL y revisada.
"""

from __future__ import annotations

import pandas as pd

from lojagas.comun.config import Config
from lojagas.comun.trazabilidad import etiquetas_corrida
from lojagas.ml import metricas
from lojagas.ml.modelos.catalogo import CATALOGO
from lojagas.ml.walk_forward import particiones


def validacion_cruzada(
    nombre: str,
    df: pd.DataFrame,
    features: list[str],
    target: str = "toneladas",
    min_entrenamiento: int = 24,
) -> pd.DataFrame:
    """Métricas por fold. Función pura: se testea sin MLflow."""
    datos = df.dropna(subset=features + [target]).reset_index(drop=True)
    filas = []
    for k, (idx_tr, idx_te) in enumerate(particiones(datos["mes"], min_entrenamiento)):
        modelo = CATALOGO[nombre]()
        modelo.fit(datos.loc[idx_tr, features], datos.loc[idx_tr, target])
        pred = modelo.predict(datos.loc[idx_te, features])
        fila = metricas.calcular(datos.loc[idx_te, target], pred)
        fila.update(fold=k, mes_prueba=datos.loc[idx_te, "mes"].min())
        filas.append(fila)
    return pd.DataFrame(filas)


def entrenar(df: pd.DataFrame, features: list[str], cfg: Config, versiones_delta: dict) -> str:
    import mlflow

    mlflow.set_tracking_uri(cfg.mlflow_uri)
    mlflow.set_experiment(cfg.experimento_mlflow)
    resultados = {}

    with mlflow.start_run(run_name="comparacion_candidatos") as padre:
        mlflow.set_tags(etiquetas_corrida(versiones_delta))
        mlflow.log_param("features", ",".join(features))
        for nombre in CATALOGO:
            with mlflow.start_run(run_name=nombre, nested=True):
                folds = validacion_cruzada(
                    nombre, df, features, min_entrenamiento=cfg.meses_minimos_entrenamiento
                )
                medias = folds.drop(columns=["fold", "mes_prueba"]).mean().to_dict()
                mlflow.log_metrics({f"{m}_medio": v for m, v in medias.items()})
                mlflow.log_table(folds, artifact_file="folds.json")
                resultados[nombre] = medias["wape"]

        mejor = min(resultados, key=resultados.get)
        mlflow.set_tag("mejor_modelo", mejor)
        # Modelo final: se reentrena con todo el histórico y se registra como candidato
        # (implementar: fit completo + mlflow.sklearn.log_model + set_registered_model_alias)
        return padre.info.run_id
