"""Linaje de cada corrida: qué código, qué imagen y qué versión de datos.

Operacionaliza la trazabilidad que el documento declara (ISO/IEC 23053, serie
ISO/IEC 5259): toda corrida de MLflow debe llevar estas etiquetas.
"""

from __future__ import annotations

import os


def etiquetas_corrida(versiones_delta: dict[str, int] | None = None) -> dict[str, str]:
    etiquetas = {
        "git_sha": os.environ.get("LOJAGAS_GIT_SHA", "desconocido"),
        "imagen_tag": os.environ.get("LOJAGAS_IMAGE_TAG", "desconocido"),
        "airflow_run_id": os.environ.get("LOJAGAS_RUN_ID", "manual"),
    }
    for tabla, version in (versiones_delta or {}).items():
        etiquetas[f"delta_version.{tabla}"] = str(version)
    return etiquetas
