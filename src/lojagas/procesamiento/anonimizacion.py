"""Seudonimización de PII antes de Curated (LOPDP; riesgo R5 del registro de riesgos).

- Identificadores que se necesitan para unir o agrupar → HMAC-SHA256 con sal secreta.
  Es seudonimización, no anonimización: con la sal se puede revertir por fuerza bruta
  sobre cédulas válidas. La sal no sale del servidor.
- Texto libre y nombres → se eliminan.
- Coordenadas → se redondean (2 decimales ≈ 1,1 km) para conservar valor territorial.
"""

from __future__ import annotations

import hashlib
import hmac

import pandas as pd

COLUMNAS_HASH = [
    "cliente_ruc",
    "conductor_documento",
    "despacho_recibido_cedula",
]
COLUMNAS_ELIMINAR = [
    "cliente_nombre",
    "padre_nombre",
    "conductor_nombre",
    "despacho_recibido_por",
    "guia_origen",
    "guia_destino",
    "pago_cheques",
    "pago_referencias",
    "pago_referencias_pago",
    "pago_descripciones",
    "reference",
]
COLUMNAS_COORDENADAS = ["partner_latitude", "partner_longitude"]
DECIMALES_COORDENADAS = 2


def _hmac(valor: object, sal: bytes) -> object:
    if pd.isna(valor):
        return valor
    return hmac.new(sal, str(valor).strip().encode(), hashlib.sha256).hexdigest()[:16]


def seudonimizar(df: pd.DataFrame, sal: str) -> pd.DataFrame:
    if not sal or len(sal) < 16:
        raise ValueError("LOJAGAS_PII_SALT ausente o demasiado corta (mínimo 16 caracteres)")
    sal_b = sal.encode()
    out = df.drop(columns=[c for c in COLUMNAS_ELIMINAR if c in df.columns])
    for col in COLUMNAS_HASH:
        if col in out.columns:
            out[col] = out[col].map(lambda v: _hmac(v, sal_b))
    for col in COLUMNAS_COORDENADAS:
        if col in out.columns:
            out[col] = out[col].round(DECIMALES_COORDENADAS)
    return out
