"""Entrenamiento y comparación de candidatos con walk-forward, registrado en MLflow.

Política (hasta que exista el ADR de promoción): el mejor modelo por WAPE medio
queda con alias "candidato". Pasarlo a "produccion" es una acción MANUAL y revisada.
"""

from __future__ import annotations

import pandas as pd

from lojagas.comun.config import Config
from lojagas.comun.trazabilidad import etiquetas_corrida
from lojagas.ml import metricas
from lojagas.ml.evaluacion import supera_baseline
from lojagas.ml.modelos.catalogo import CATALOGO, crear
from lojagas.ml.walk_forward import particiones


def lags_no_disponibles(features: list[str], horizonte: int) -> list[str]:
    """Lags que usan meses aún no cerrados al predecir con este horizonte."""
    return [f for f in features if f.startswith("lag_") and int(f[4:]) < horizonte]


def validacion_cruzada(
    nombre: str,
    df: pd.DataFrame,
    features: list[str],
    *,
    horizonte: int,
    target: str = "toneladas",
    min_entrenamiento: int = 24,
) -> pd.DataFrame:
    """Métricas por fold. Función pura: se testea sin MLflow."""
    fuga = lags_no_disponibles(features, horizonte)
    if fuga:
        raise ValueError(f"Features no disponibles con horizonte {horizonte}: {fuga}")
    datos = df.dropna(subset=features + [target]).reset_index(drop=True)
    filas = []
    folds = particiones(datos["mes"], min_entrenamiento, horizonte=horizonte)
    for k, (idx_tr, idx_te) in enumerate(folds):
        modelo = crear(nombre, horizonte)
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
        mlflow.log_param("horizonte_meses", cfg.horizonte_meses)
        for nombre in CATALOGO:
            with mlflow.start_run(run_name=nombre, nested=True):
                folds = validacion_cruzada(
                    nombre,
                    df,
                    features,
                    horizonte=cfg.horizonte_meses,
                    min_entrenamiento=cfg.meses_minimos_entrenamiento,
                )
                medias = folds.drop(columns=["fold", "mes_prueba"]).mean().to_dict()
                mlflow.log_metrics({f"{m}_medio": v for m, v in medias.items()})
                mlflow.log_table(folds, artifact_file="folds.json")
                resultados[nombre] = medias

        resumen = pd.DataFrame(resultados).T
        ganadores = supera_baseline(resumen)
        mlflow.log_metrics(
            {
                f"mejora_sobre_ingenuo.{nombre}": valor
                for nombre, valor in ganadores["mejora_sobre_ingenuo"].items()
            }
        )
        # Si ninguno supera al estacional ingenuo, es un hallazgo: se registra, no se oculta
        mejor = ganadores.index[0] if len(ganadores) else "estacional_ingenuo"
        mlflow.set_tag("mejor_modelo", mejor)
        mlflow.set_tag("supera_estacional_ingenuo", str(bool(len(ganadores))))
        # Modelo final: se reentrena con todo el histórico y se registra como candidato
        # (implementar: fit completo + mlflow.sklearn.log_model + set_registered_model_alias)
        return padre.info.run_id
