"""Ingesta desde Odoo (en la nube) hacia la zona Raw, por API.

PENDIENTE (ADR-0005, ver docs/inconsistencias.md):
- Confirmar versión de Odoo de Lojagas. Desde Odoo 19, XML-RPC y JSON-RPC están
  deprecados y se reemplazan por la API JSON-2 con API key (bearer). En Odoo
  Online se retiran en 21.1; en self-hosted/Odoo.sh, en Odoo 22.
- `ventas_ml_dataset.md` se armó con SQL directo sobre PostgreSQL, uniendo
  modelos propios (loj_turns, despacho_granelero, consumption_spreadsheet...).
  Por API hay que replicar esos joins modelo por modelo o pedir a Lojagas una
  vista/endpoint del lado del servidor. Decidir antes de programar este módulo.

Regla de Raw: se guarda tal cual llega (más metadatos de extracción), sin limpiar.
La anonimización ocurre en Raw → Curated, pero Raw vive solo en el servidor on-premise.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from lojagas.comun.config import Config


def extraer_facturas(cfg: Config, desde: date, hasta: date) -> pd.DataFrame:
    """Líneas de factura publicadas (out_invoice, out_refund) de company_id=1."""
    raise NotImplementedError("Definir cliente JSON-2 o JSON-RPC según versión de Odoo (ADR-0005)")
