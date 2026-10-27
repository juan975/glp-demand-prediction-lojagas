"""generar_reportes.py — zona Predicciones → reportes/ (carpeta compartida SMB).

Contenido mínimo (sección 3.5 del TIC): predicción por segmento, error esperado
(WAPE de validación), importancia de variables y versión del modelo.
Los "filtros por segmento / por tiempo" del diagrama conceptual se resuelven como
hojas y autofiltros del Excel, no como interfaz (ver I-03).
"""

from __future__ import annotations

from lojagas.comun.config import Config


def ejecutar(cfg: Config, periodo: str) -> list[str]:
    raise NotImplementedError("Excel con openpyxl y PDF con fpdf2")
