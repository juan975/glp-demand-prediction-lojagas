"""ingesta.py — artefacto del «Contenedor Ingesta» (Despliegue_v3).

Extrae de ERP Odoo (API) y Fuentes Externas (HTTPS 443) y escribe en la zona Raw
tal cual llega, con metadatos de extracción. No limpia ni anonimiza: eso es
responsabilidad del Contenedor Procesamiento.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pandas as pd

from lojagas.comun import lakehouse
from lojagas.comun.config import Config
from lojagas.ingesta import odoo_api
from lojagas.ingesta.externas.calendario import CalendarioEventos


def _con_metadatos(df: pd.DataFrame, fuente: str, periodo: str) -> pd.DataFrame:
    out = df.copy()
    out["_fuente"] = fuente
    out["_periodo"] = periodo
    out["_extraido_en"] = datetime.now(UTC)
    return out


def ejecutar_odoo(cfg: Config, periodo: str) -> int:
    inicio = date.fromisoformat(periodo)
    fin = (pd.Timestamp(inicio) + pd.offsets.MonthEnd(0)).date()
    df = odoo_api.extraer_facturas(cfg, inicio, fin)
    return lakehouse.escribir(
        _con_metadatos(df, "odoo", periodo),
        cfg.lakehouse,
        "raw",
        "ventas_lineas",
        particiones=["_periodo"],
    )


def ejecutar_externas(cfg: Config, periodo: str) -> dict[str, int]:
    versiones = {}
    for fuente in (CalendarioEventos(),):  # agregar INAMHI, Petroecuador... al implementarlas
        df = fuente.extraer(periodo)
        versiones[fuente.nombre] = lakehouse.escribir(
            _con_metadatos(df, fuente.nombre, periodo),
            cfg.lakehouse,
            "raw",
            fuente.nombre,
            modo="overwrite",
        )
    return versiones
