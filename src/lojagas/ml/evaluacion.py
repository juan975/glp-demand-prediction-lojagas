"""evaluacion.py — Selección del candidato y explicabilidad.

Compara las corridas de pipeline_entrenamiento en MLflow, exige que el mejor
supere al estacional ingenuo y lo registra en el Model Registry con alias
"candidato". La promoción a "produccion" es manual hasta el ADR-0007.
SHAP se calcula sobre el último fold (datos no vistos).
"""

from __future__ import annotations

import pandas as pd


def supera_baseline(resumen: pd.DataFrame, metrica: str = "wape") -> pd.DataFrame:
    """Filtra los modelos que le ganan al estacional ingenuo. Si ninguno lo hace,
    el resultado vacío es un HALLAZGO que se reporta, no un error que se oculta."""
    vara = resumen.loc["estacional_ingenuo", metrica]
    return resumen[resumen[metrica] < vara].sort_values(metrica)


def registrar_candidato(run_id: str, nombre_modelo: str) -> None:
    raise NotImplementedError


def valores_shap(modelo, X):
    raise NotImplementedError
