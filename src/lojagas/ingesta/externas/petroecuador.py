"""Petroecuador: precios de venta en terminal (nivel 1, Fuentes_Datos_Externos_Lojagas v4).

Para el ratio de sustitución GLP/diésel solo sirven los precios que se mueven: GLP industrial
(USD/kg) y diésel premium industrial (USD/galón). El GLP agrícola y el doméstico están fijos
por decreto (0,1935 y 0,11 USD/kg desde 2024): no varían y no aportan al modelo.

Petroecuador publica un PDF por período de vigencia, casi siempre del día 12 de un mes al 11
del siguiente, con nombres de archivo sin patrón fijo. El archivo histórico está en
https://www.eppetroecuador.ec/?p=20421 (Precios de venta de combustibles → Otros), una tabla
de año × mes con un enlace por PDF. Por eso la fuente es un CSV versionado en
referencias/precios_petroecuador.csv (una fila por período, con la URL del PDF de origen) y
no una descarga automática. Para agregar períodos: scripts/precios_petroecuador.py lee los
PDF descargados y devuelve las filas.

Raw guarda los períodos tal cual (con IVA, que pasó del 12 % al 15 % en abril de 2024; el
ratio no cambia porque afecta a los dos precios). El promedio de cada mes calendario,
ponderado por los días de cada período, y el ratio se calculan en Procesamiento.

Disponibilidad: el PDF sale hacia el día 11, antes de que empiece su período, así que al
cerrar un mes ya se conocen todos sus precios (disponible_desde_dias = 0).
"""

from __future__ import annotations

import os
import re
from datetime import date
from pathlib import Path

import pandas as pd

RUTA = Path(os.environ.get("LOJAGAS_REFERENCIAS", "referencias")) / "precios_petroecuador.csv"
PRECIOS = ["glp_industrial_usd_kg", "diesel_premium_industrial_usd_gal"]
COLUMNAS = ["vigencia_desde", "vigencia_hasta", *PRECIOS, "iva_pct", "fuente_url"]

MESES = {
    m: i
    for i, m in enumerate(
        [
            "ENERO",
            "FEBRERO",
            "MARZO",
            "ABRIL",
            "MAYO",
            "JUNIO",
            "JULIO",
            "AGOSTO",
            "SEPTIEMBRE",
            "OCTUBRE",
            "NOVIEMBRE",
            "DICIEMBRE",
        ],
        start=1,
    )
}


def validar(df: pd.DataFrame) -> pd.DataFrame:
    faltantes = set(COLUMNAS) - set(df.columns)
    if faltantes:
        raise ValueError(f"precios_petroecuador.csv sin columnas: {faltantes}")
    df = df.sort_values("vigencia_desde").reset_index(drop=True)
    if (df["vigencia_hasta"] < df["vigencia_desde"]).any():
        raise ValueError("Hay períodos con vigencia_hasta anterior a vigencia_desde")
    desde, hasta = df["vigencia_desde"].to_numpy(), df["vigencia_hasta"].to_numpy()
    if (desde[1:] <= hasta[:-1]).any():
        raise ValueError("Hay períodos de vigencia que se superponen")
    # `> 0` es falso con NaN: así una celda vacía también falla (con `<= 0` pasaba)
    if not (df[PRECIOS] > 0).all(axis=None):
        raise ValueError("Hay precios vacíos o no positivos")
    return df


def huecos(df: pd.DataFrame, desde: str, hasta: str) -> list[tuple[date, date]]:
    """Tramos entre `desde` y `hasta` que ningún período cubre.

    No se supone que todo período vaya del 12 al 11: hubo estructuras que cambiaron a mitad
    de período (cambio de IVA en 2024, Decretos 308 y 20), con archivos extra en el archivo
    histórico de Petroecuador (p. ej., "Junio (2)" de 2024).
    """
    inicio, fin = pd.Timestamp(desde), pd.Timestamp(hasta)
    tramos = []
    cursor = inicio
    for d, h in df.sort_values("vigencia_desde")[["vigencia_desde", "vigencia_hasta"]].itertuples(
        index=False
    ):
        d, h = pd.Timestamp(d), pd.Timestamp(h)
        if h < cursor:
            continue
        if d > cursor:
            tramos.append((cursor.date(), min(d - pd.Timedelta(days=1), fin).date()))
        cursor = max(cursor, h + pd.Timedelta(days=1))
        if cursor > fin:
            break
    if cursor <= fin:
        tramos.append((cursor.date(), fin.date()))
    return [t for t in tramos if t[0] <= t[1] and pd.Timestamp(t[0]) <= fin]


def resolver_superposiciones(df: pd.DataFrame) -> pd.DataFrame:
    """Una estructura posterior reemplaza a la anterior desde su fecha de inicio.

    Pasa cuando el precio cambia a mitad de período: el 1 de abril de 2024 (IVA del 12 % al
    15 %) cortó el período del 12 de marzo, que queda hasta el 31 de marzo.
    """
    df = df.sort_values("vigencia_desde").reset_index(drop=True)
    for i in range(len(df) - 1):
        siguiente = df.loc[i + 1, "vigencia_desde"]
        if siguiente <= df.loc[i, "vigencia_hasta"]:
            df.loc[i, "vigencia_hasta"] = siguiente - pd.Timedelta(days=1)
    return df


def _numero(texto: str) -> float:
    # Los PDF usan coma o punto decimal según el mes; los precios no llevan separador de miles
    return float(texto.replace(",", "."))


def leer_texto_pdf(texto: str, fuente_url: str = "") -> dict:
    """Texto de un PDF de "estructura de precios" → una fila del CSV."""
    t = " ".join(texto.upper().split())
    vig = re.search(
        # Variantes reales: "DEL 12 DE MAYO AL 11 DE JUNIO DE 2026", "DEL 12 ABRIL AL 11 DE
        # MAYO DE 2024" (sin DE), "DEL 01 AL 11 DE ABRIL DE 2024" (sin mes de inicio) y
        # "DEL 12 DE DICIEMBRE DE 2023 AL 11 DE ENERO DE 2024" (año en las dos fechas)
        r"PERIODO DE VIGENCIA:\s*DEL (\d{1,2})(?: DE)?(?: (?!AL\b)([A-Z]+))?(?: DE (\d{4}))?"
        r" AL (\d{1,2}) DE ([A-Z]+) DE (\d{4})",
        t,
    )
    glp = re.search(r"GAS LICUADO DE PETR[OÓ]LEO \(G\.?L\.?P\.?\) INDUSTRIAL\D*?(\d+[.,]\d+)", t)
    diesel = re.search(r"DIESEL PREMIUM INDUSTRIAL\D*?(\d+[.,]\d+)", t)
    iva = re.search(r"INCLUYE EL (\d+)\s*% DEL I\.?V\.?A", t)
    if not (vig and glp and diesel):
        raise ValueError("Falta el período, el GLP industrial o el diésel premium industrial")
    d1, m1, a1, d2, m2, a2 = vig.groups()
    m1 = m1 or m2  # "DEL 01 AL 11 DE ABRIL": el período empieza en el mismo mes
    anio_fin = int(a2)
    anio_ini = int(a1) if a1 else (anio_fin - 1 if MESES[m1] > MESES[m2] else anio_fin)
    return {
        "vigencia_desde": date(anio_ini, MESES[m1], int(d1)),
        "vigencia_hasta": date(anio_fin, MESES[m2], int(d2)),
        "glp_industrial_usd_kg": _numero(glp.group(1)),
        "diesel_premium_industrial_usd_gal": _numero(diesel.group(1)),
        "iva_pct": int(iva.group(1)) if iva else pd.NA,
        "fuente_url": fuente_url,
    }


class PreciosPetroecuador:
    nombre = "petroecuador_precios"
    disponible_desde_dias = 0  # el PDF sale hacia el día 11, antes de su período

    def __init__(self, ruta: Path = RUTA) -> None:
        self.ruta = ruta

    def extraer(self, periodo: str) -> pd.DataFrame:
        """Períodos que empiezan hasta el fin del mes `periodo` (igual que ERA5-Land)."""
        df = validar(pd.read_csv(self.ruta, parse_dates=["vigencia_desde", "vigencia_hasta"]))
        fin_mes = pd.Timestamp(periodo) + pd.offsets.MonthEnd(0)
        return df[df["vigencia_desde"] <= fin_mes].reset_index(drop=True)
