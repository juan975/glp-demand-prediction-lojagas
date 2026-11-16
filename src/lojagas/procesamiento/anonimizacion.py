"""Seudonimización de PII antes de Curated (LOPDP; riesgo R5 del registro de riesgos).

Lista blanca: a Curated pasan solo las columnas de `COLUMNAS_PERMITIDAS`, más los
identificadores seudonimizados y las coordenadas redondeadas. Todo lo demás se descarta,
incluidas las columnas que Raw agregue en el futuro: con una lista negra, una columna
nueva con PII (placas, guías, logins, pagos) pasaba a Curated sin que nadie la nombrara.

- Identificadores que se necesitan para unir o agrupar → HMAC-SHA256 con sal secreta.
  Es seudonimización, no anonimización: con la sal se puede revertir por fuerza bruta
  sobre cédulas válidas. La sal no sale del servidor.
- Coordenadas → se redondean (2 decimales ≈ 1,1 km) para conservar valor territorial.
"""

from __future__ import annotations

import hashlib
import hmac

import pandas as pd

COLUMNAS_PERMITIDAS = [
    # Línea, documento y metadatos de extracción
    "linea_id",
    "factura_id",
    "fecha_factura",
    "fecha_contable",
    "move_type",
    "state",
    "_fuente",
    "_periodo",
    "_extraido_en",
    # Producto y volumen (target)
    "categoria",
    "producto_codigo",
    "producto_nombre",
    "unidad_medida",
    "peso_unitario_kg",
    "cantidad",
    "kg_glp",
    # Candidatos a segmento (I-04) y territorio. Las claves de mapa_segmentos.csv deben estar aquí.
    "cliente_tipo",
    "tipo_distribuidor",
    "canal_venta",
    "es_subsidiado",
    "jerarquia_cliente",
    "canton",
    "sucursal",
]
COLUMNAS_HASH = ["cliente_id", "cliente_ruc"]
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
    conservar = set(COLUMNAS_PERMITIDAS + COLUMNAS_HASH + COLUMNAS_COORDENADAS)
    out = df[[c for c in df.columns if c in conservar]].copy()
    for col in COLUMNAS_HASH:
        if col in out.columns:
            out[col] = out[col].map(lambda v: _hmac(v, sal_b))
    for col in COLUMNAS_COORDENADAS:
        if col in out.columns:
            out[col] = out[col].round(DECIMALES_COORDENADAS)
    return out
