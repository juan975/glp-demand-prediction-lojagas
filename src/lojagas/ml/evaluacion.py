"""evaluacion.py — Selección del candidato y explicabilidad.

Compara las corridas de pipeline_entrenamiento en MLflow, exige que el mejor
supere al estacional ingenuo y lo registra en el Model Registry con alias
"candidato". La promoción a "produccion" es manual hasta el ADR-0007.
SHAP se calcula sobre el último fold (datos no vistos).
"""

from __future__ import annotations

import pandas as pd

from lojagas.ml import metricas


def supera_baseline(resumen: pd.DataFrame, metrica: str = "wape") -> pd.DataFrame:
    """Criterio de éxito: modelos con menor WAPE medio que el estacional ingenuo
    (el método actual de Lojagas), con su mejora relativa en `mejora_sobre_ingenuo` (%).

    Un umbral fijo de MAPE no sirve como criterio: en el EDA, el estacional ingenuo
    ya da ~3,6 % sobre la serie total. Si ningún modelo lo supera, el resultado vacío
    es un HALLAZGO que se reporta, no un error que se oculta."""
    vara = resumen.loc["estacional_ingenuo", metrica]
    out = resumen[resumen[metrica] < vara].sort_values(metrica).copy()
    out["mejora_sobre_ingenuo"] = metricas.mejora_relativa(out[metrica], vara)
    return out


def registrar_candidato(run_id: str, nombre_modelo: str) -> None:
    raise NotImplementedError


def valores_shap(modelo, X):
    raise NotImplementedError
