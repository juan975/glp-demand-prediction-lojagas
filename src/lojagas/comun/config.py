"""Configuración leída de variables de entorno (las inyecta Airflow o el .env local)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Config:
    lakehouse: Path = field(
        default_factory=lambda: Path(os.environ.get("LOJAGAS_LAKEHOUSE", "/data/lakehouse"))
    )
    reportes: Path = field(
        default_factory=lambda: Path(os.environ.get("LOJAGAS_REPORTES", "/data/reportes"))
    )
    mlflow_uri: str = field(
        default_factory=lambda: os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    )
    odoo_url: str = field(default_factory=lambda: os.environ.get("ODOO_URL", ""))
    odoo_db: str = field(default_factory=lambda: os.environ.get("ODOO_DB", ""))
    odoo_api_key: str = field(default_factory=lambda: os.environ.get("ODOO_API_KEY", ""))
    pii_salt: str = field(default_factory=lambda: os.environ.get("LOJAGAS_PII_SALT", ""))

    # Decisiones de modelado (cambian solo con un ADR)
    experimento_mlflow: str = "lojagas_demanda_glp"
    modelo_registrado: str = "lojagas_demanda_glp"
    alias_produccion: str = "produccion"
    alias_candidato: str = "candidato"
    horizonte_meses: int = 1
    meses_minimos_entrenamiento: int = 24


def cargar() -> Config:
    return Config()
