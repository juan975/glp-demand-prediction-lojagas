"""Datos sintéticos. Ningún test usa datos reales de Lojagas (contienen PII)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

SEGMENTOS = ["domestico", "industrial", "granel"]


@pytest.fixture
def serie_mensual() -> pd.DataFrame:
    """46 meses (ene-2023 a oct-2026) × 3 segmentos, con estacionalidad anual."""
    rng = np.random.default_rng(0)
    meses = pd.date_range("2023-01-01", "2026-10-01", freq="MS")
    filas = []
    for i, seg in enumerate(SEGMENTOS):
        base = 100 * (i + 1)
        estacional = 10 * np.sin(2 * np.pi * meses.month / 12)
        y = base + estacional + rng.normal(0, 2, len(meses))
        filas.append(pd.DataFrame({"mes": meses, "segmento": seg, "toneladas": y}))
    return pd.concat(filas, ignore_index=True)


@pytest.fixture
def lineas_factura() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "linea_id": [1, 2, 3, 4],
            "factura_id": [10, 10, 11, 12],
            "fecha_factura": pd.to_datetime(
                ["2024-01-05", "2024-01-20", "2024-03-02", "2024-03-15"]
            ),
            "move_type": ["out_invoice", "out_invoice", "out_refund", "out_invoice"],
            "state": ["posted"] * 4,
            "canal_venta": ["despacho", "despacho", "despacho", "planilla"],
            "cliente_tipo": ["INDUSTRIAL", "HOGAR", "INDUSTRIAL", "HOGAR"],
            "cantidad": [1.0, 1.0, 1.0, 1.0],
            "kg_glp": [2000.0, 500.0, 300.0, 150.0],
            "cliente_ruc": ["1100000001", "1100000002", "1100000001", None],
            "cliente_nombre": ["A", "B", "A", "C"],
            "partner_latitude": [-3.99312, -4.0, -3.99312, None],
            "partner_longitude": [-79.20456, -79.2, -79.20456, None],
        }
    )


@pytest.fixture
def mapa_segmentos() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "canal_venta": ["despacho", "planilla"],
            "cliente_tipo": ["*", "*"],
            "segmento": ["granel", "domicilio_tuberia"],
        }
    )
