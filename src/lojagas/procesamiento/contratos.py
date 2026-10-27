"""Contratos de datos (pandera). Evidencia medible de la dimensión "Calidad"
del instrumento de madurez y de los requisitos de calidad de ISO/IEC 5259.

Un contrato que falla detiene el DAG: es preferible no predecir a predecir con basura.
"""

from __future__ import annotations

import pandera.pandas as pa

ventas_raw = pa.DataFrameSchema(
    {
        "linea_id": pa.Column(int, unique=True),
        "factura_id": pa.Column(int),
        "fecha_factura": pa.Column("datetime64[ns]", nullable=False),
        "move_type": pa.Column(str, pa.Check.isin(["out_invoice", "out_refund"])),
        "state": pa.Column(str, pa.Check.eq("posted")),
        "canal_venta": pa.Column(
            str,
            pa.Check.isin(
                ["despacho", "planilla", "turno", "proyecto", "cotizacion", "sin_origen"]
            ),
        ),
        "cantidad": pa.Column(float),
        "kg_glp": pa.Column(float, pa.Check.ge(0), nullable=True),
    },
    strict=False,  # Raw trae ~150 columnas; aquí solo se exigen las críticas
    coerce=True,
)

ventas_mensual_curated = pa.DataFrameSchema(
    {
        "mes": pa.Column("datetime64[ns]"),
        "segmento": pa.Column(str),
        "toneladas": pa.Column(float),
    },
    unique=["mes", "segmento"],
    strict=True,
    coerce=True,
)
