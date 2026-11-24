"""Lee PDF de "estructura de precios" de Petroecuador y agrega las filas al CSV de referencias.

Uso (desde la raíz del repo, con los PDF ya descargados de eppetroecuador.ec):

    uv run python scripts/precios_petroecuador.py carpeta_con_pdfs/*.pdf
    uv run python scripts/precios_petroecuador.py --escribir carpeta_con_pdfs/*.pdf

Sin --escribir solo muestra lo que encontró. Con --escribir agrega al CSV los períodos que no
estaban (nunca reemplaza uno existente) y lo deja ordenado. Al final lista los períodos que
todavía faltan desde diciembre de 2022, el primero que cubre las ventas de enero de 2023.

La URL de origen no está dentro del PDF; es la cita de la tesis, así que se reconstruye del
nombre del archivo, según cómo lo guardó la descarga:
    dm-3648.pdf                      → .../download-monitor/download.php?id=3648
    up-2026-05-NOMBRE-ORIGINAL.pdf   → .../wp-content/uploads/2026/05/NOMBRE-ORIGINAL.pdf
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd
import pdfplumber

from lojagas.ingesta.externas.petroecuador import (
    COLUMNAS,
    RUTA,
    huecos,
    leer_texto_pdf,
    resolver_superposiciones,
    validar,
)

PRIMER_PERIODO = "2022-12-12"  # el período que cubre enero de 2023, el primer mes de ventas


def _url_origen(pdf: Path) -> str:
    base = "https://www.eppetroecuador.ec/wp-content"
    if m := re.fullmatch(r"dm-(\d+)\.pdf", pdf.name):
        return f"{base}/plugins/download-monitor/download.php?id={m.group(1)}"
    if m := re.fullmatch(r"up-(\d{4})-(\d{2})-(.+\.pdf)", pdf.name):
        return f"{base}/uploads/{m.group(1)}/{m.group(2)}/{m.group(3)}"
    return ""  # nombre desconocido: completar la URL a mano en el CSV


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pdfs", nargs="+", type=Path)
    parser.add_argument("--escribir", action="store_true", help="agregar las filas nuevas al CSV")
    args = parser.parse_args()

    filas = []
    for pdf in args.pdfs:
        with pdfplumber.open(pdf) as doc:
            texto = "\n".join(p.extract_text() or "" for p in doc.pages)
        try:
            fila = leer_texto_pdf(texto)
        except ValueError as e:
            print(f"OMITIDO {pdf.name}: {e}")
            continue
        fila["fuente_url"] = _url_origen(pdf)
        filas.append(fila)
        print(
            f"{fila['vigencia_desde']} → {fila['vigencia_hasta']}  "
            f"GLP {fila['glp_industrial_usd_kg']:.6f} USD/kg  "
            f"diésel {fila['diesel_premium_industrial_usd_gal']:.6f} USD/gal  ({pdf.name})"
        )

    actual = pd.read_csv(RUTA, parse_dates=["vigencia_desde", "vigencia_hasta"])
    nuevas = pd.DataFrame(filas, columns=COLUMNAS)
    if not nuevas.empty:
        nuevas[["vigencia_desde", "vigencia_hasta"]] = nuevas[
            ["vigencia_desde", "vigencia_hasta"]
        ].apply(pd.to_datetime)
        nuevas = nuevas[~nuevas["vigencia_desde"].isin(actual["vigencia_desde"])]
        # El archivo histórico a veces sube el mismo PDF dos veces (p. ej., "Mayo (3)" de 2025)
        precios = ["vigencia_hasta", "glp_industrial_usd_kg", "diesel_premium_industrial_usd_gal"]
        distintos = nuevas.drop_duplicates(["vigencia_desde", *precios])
        choque = distintos[distintos.duplicated("vigencia_desde", keep=False)]
        if not choque.empty:
            print("\nCONFLICTO: el mismo período con precios distintos; revisar a mano:")
            print(choque.to_string(index=False))
            return 1
        nuevas = distintos
    junto = validar(resolver_superposiciones(pd.concat([actual, nuevas], ignore_index=True)))

    if args.escribir and not nuevas.empty:
        salida = junto.copy()
        for c in ("vigencia_desde", "vigencia_hasta"):
            salida[c] = salida[c].dt.strftime("%Y-%m-%d")
        salida.to_csv(RUTA, index=False, float_format="%.6f")
        print(f"\nAgregados {len(nuevas)} períodos a {RUTA}")

    hoy = pd.Timestamp.today().strftime("%Y-%m-%d")
    faltan = huecos(junto, PRIMER_PERIODO, hoy)
    print(f"\nTramos sin precio desde {PRIMER_PERIODO} ({len(faltan)}):")
    for d, h in faltan:
        print(f"  {d} → {h}")
    if not faltan:
        print("  ninguno")
    return 0


if __name__ == "__main__":
    sys.exit(main())
