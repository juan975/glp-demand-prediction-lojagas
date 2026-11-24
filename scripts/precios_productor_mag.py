"""Actualiza referencias/precios_productor_mag.csv desde el tablero «Cifras territoriales» del MAG.

Abre la página pública en un navegador automático y, con la API de Tableau que esa página ya
carga, recorre provincia × año × mes: elige la provincia (parámetro Provincia_P), filtra la hoja
`precios_pp` por año y mes, y guarda la tabla. Es lo mismo que hacerlo a mano en el tablero.

La descarga completa (todos los productos) queda en datos/externas/, que no se versiona; al
CSV de referencias pasan solo las series de `lojagas.ingesta.externas.precios_mag.SERIES`.

Uso, desde la raíz del repo (Playwright se usa solo para esta ejecución, no entra al entorno):
    uv run --with playwright playwright install --with-deps chromium   # una sola vez
    uv run --with playwright python scripts/precios_productor_mag.py            # descarga
    uv run --with playwright python scripts/precios_productor_mag.py --escribir # y actualiza

Si se corta, se puede volver a correr: salta los meses ya descargados. Para volver a bajar los
últimos meses (el MAG a veces los corrige), usar --rehacer 3.
"""

import argparse
import csv
import time
from datetime import date
from pathlib import Path

import pandas as pd
from playwright.sync_api import sync_playwright

from lojagas.ingesta.externas.precios_mag import RUTA, seleccionar, validar

PAGINA = "https://servicios.mag.gob.ec/tableros/Territorial_24/Cifras_territoriales"
HOJA = "precios_pp"
PROVINCIAS = ["LOJA", "ZAMORA CHINCHIPE"]
MESES = [
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
]
# Measure Names del tablero → columna del CSV
MEDIDAS = {
    "Avg. Precio": "precio_usd",
    "Avg. Mes A": "precio_mes_anterior",
    "Avg. Anio A": "precio_anio_anterior",
}
SALIDA = Path("datos/externas/precios_productor_mag_completo.csv")
COLUMNAS = ["provincia", "anio", "mes", "producto", *MEDIDAS.values()]
PAUSA_S = 1.5  # entre consultas, para no cargar el servidor del MAG

ELEGIR_PROVINCIA = """
async ([hoja, provincia]) => {
  const wb = window.viz.workbook;
  await wb.changeParameterValueAsync('Provincia_P', provincia);
  const ws = wb.activeSheet.worksheets.find(w => w.name === hoja);
  try { await ws.clearFilterAsync('Producto'); } catch (e) {}  // todos los productos
  return true;
}
"""

LEER_MES = """
async ([hoja, anio, mes]) => {
  const ws = window.viz.workbook.activeSheet.worksheets.find(w => w.name === hoja);
  await ws.applyFilterAsync('Anio', [anio], 'replace');
  await ws.applyFilterAsync('Mes N', [mes], 'replace');
  // Comprueba que el filtro quedó aplicado antes de leer
  const filtros = await ws.getFiltersAsync();
  const aplicado = n => (filtros.find(f => f.fieldName === n)?.appliedValues || [])
                          .map(v => v.formattedValue);
  const t = await ws.getSummaryDataAsync({ignoreSelection: true});
  const col = n => t.columns.findIndex(c => c.fieldName === n);
  const [ip, im, iv] = [col('Producto'), col('Measure Names'), col('Measure Values')];
  return {
    anio: aplicado('Anio'), mes: aplicado('Mes N'),
    filas: t.data.map(r => [r[ip].formattedValue, r[im].formattedValue, r[iv].value]),
  };
}
"""


def esperar_tablero(pag) -> None:
    for _ in range(90):
        if pag.evaluate(
            "() => { try { return !!window.viz.workbook.activeSheet.worksheets.length; }"
            " catch (e) { return false; } }"
        ):
            return
        time.sleep(2)
    raise SystemExit("El tablero no terminó de cargar")


def ya_descargados(rehacer: int) -> set[tuple[str, str, str]]:
    if not SALIDA.exists():
        return set()
    with SALIDA.open(encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    if rehacer:
        hoy = pd.Timestamp(date.today()).to_period("M")
        corte = hoy - rehacer
        filas = [r for r in filas if pd.Period(f"{r['anio']}-{int(r['mes']):02d}", "M") < corte]
        with SALIDA.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNAS)
            w.writeheader()
            w.writerows(filas)
    return {(r["provincia"], r["anio"], r["mes"]) for r in filas}


def escribir_referencia() -> None:
    crudo = pd.read_csv(SALIDA, na_values="%null%")
    df = seleccionar(crudo)
    validar(df)
    df["mes"] = df["mes"].dt.strftime("%Y-%m-%d")
    df.to_csv(RUTA, index=False)
    print(f"{RUTA}: {len(df)} filas, {df['mes'].min()} → {df['mes'].max()}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", type=int, default=2021)
    ap.add_argument("--rehacer", type=int, default=0, help="vuelve a bajar los últimos N meses")
    ap.add_argument("--escribir", action="store_true", help=f"actualiza {RUTA}")
    args = ap.parse_args()

    hoy = date.today()
    hechos = ya_descargados(args.rehacer)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not SALIDA.exists()

    with SALIDA.open("a", newline="", encoding="utf-8") as f, sync_playwright() as p:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS)
        if nuevo:
            escritor.writeheader()
        nav = p.chromium.launch()
        pag = nav.new_page(viewport={"width": 1300, "height": 2000})
        pag.goto(PAGINA, timeout=120_000)
        esperar_tablero(pag)

        for provincia in PROVINCIAS:
            pag.evaluate(ELEGIR_PROVINCIA, [HOJA, provincia])
            time.sleep(PAUSA_S)
            for anio in range(args.desde, hoy.year + 1):
                for n, mes in enumerate(MESES, start=1):
                    if (anio, n) >= (hoy.year, hoy.month):
                        break
                    if (provincia, str(anio), str(n)) in hechos:
                        continue
                    r = pag.evaluate(LEER_MES, [HOJA, str(anio), mes])
                    if r["anio"] != [str(anio)] or r["mes"] != [mes]:
                        raise SystemExit(
                            f"Filtro no aplicado: pedí {anio}-{mes}, quedó {r['anio']} {r['mes']}"
                        )
                    por_producto: dict[str, dict] = {}
                    for producto, medida, valor in r["filas"]:
                        if medida in MEDIDAS:
                            fila = por_producto.setdefault(
                                producto,
                                {
                                    "provincia": provincia,
                                    "anio": anio,
                                    "mes": n,
                                    "producto": producto,
                                },
                            )
                            fila[MEDIDAS[medida]] = valor
                    escritor.writerows(por_producto.values())
                    f.flush()
                    print(f"{provincia} {anio}-{n:02d}: {len(por_producto)} productos")
                    time.sleep(PAUSA_S)
        nav.close()
    print(f"\nDescarga completa: {SALIDA}")
    if args.escribir:
        escribir_referencia()


if __name__ == "__main__":
    main()
