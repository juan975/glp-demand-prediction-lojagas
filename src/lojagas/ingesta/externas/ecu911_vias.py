"""Estado de las vías del país según el ECU911 (bloque vías, nivel 4).

Corredores que importan a Lojagas: Guayaquil → Catamayo (GLP a granel desde Pascuales o El
Salitral hasta la planta envasadora San José), Cuenca ↔ Catamayo por Saraguro (cilindros) y
Catamayo → Loja y Catamayo → Yantzaza (reparto). Pasan por Guayas, El Oro, Azuay, Loja y
Zamora Chinchipe, así que se guarda la foto de todo el país (unas decenas de filas por día) y
los corredores se eligen en Procesamiento, cuando Lojagas confirme la ruta exacta de sus
cisternas. Un cierre de vía puede bajar la venta de un mes porque no se
pudo entregar, no porque bajara la demanda (como un stockout): se usa como alerta junto a la
predicción y para marcar esos meses en el entrenamiento, no como variable para predecir.

Fuente: el servicio que usa la página pública https://www.ecu911.gob.ec/consulta-de-vias/
para armar su tabla. Devuelve solo las vías **con novedades** (cerradas, parcialmente
habilitadas, con restricción): una vía que no aparece está habilitada.

El servicio da el estado de hoy, sin historial. Por eso se guarda una foto por día (DAG
`vias_diario`); la historia se va juntando desde que empieza a correr. Para 2023-2026 hace
falta pedir el histórico al ECU911 por la Ley de Transparencia.
"""

from __future__ import annotations

import logging
import tempfile
from collections.abc import Callable
from datetime import datetime
from functools import cache
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

log = logging.getLogger(__name__)

URL = "https://ecu911.gob.ec/Services/WSVias/ViasWeb.php"
# Mismos parámetros que la página: vías activas, sin las habilitadas (593), por provincia
PARAMETROS = {
    "estado": "A",
    "and:<>:EstadoActual-id": "593",
    "order": "Provincia-descripcion",
}
POR_PAGINA = 200
ZONA = ZoneInfo("America/Guayaquil")
SIN_NOVEDADES = "SIN NOVEDADES"
COLUMNAS = [
    "fecha",
    "via_id",
    "via",
    "provincia",
    "canton",
    "categoria",
    "estado",
    "observaciones",
    "vias_alternas",
    "creado",
    "modificado",
]

# El servidor del ECU911 entrega su certificado sin el intermedio de Sectigo. El navegador lo
# completa solo; Python no, y rechaza la conexión. En vez de desactivar la verificación, se
# agrega ese intermedio (público, de Sectigo) a los certificados raíz de certifi.
CERT_INTERMEDIO = Path(__file__).with_name("sectigo_dv_r36.pem")

# (inicio, límite) → respuesta JSON del servicio
Descargador = Callable[[int, int], dict]


@cache
def certificados() -> str:
    """Ruta a un archivo con las raíces de certifi más el intermedio de Sectigo."""
    import certifi

    texto = Path(certifi.where()).read_text() + "\n" + CERT_INTERMEDIO.read_text()
    archivo = Path(tempfile.gettempdir()) / "lojagas_ca_ecu911.pem"
    archivo.write_text(texto)
    return str(archivo)


def _descargar(inicio: int, limite: int) -> dict:
    """Única función que sale a internet."""
    import requests

    r = requests.get(
        URL,
        params={**PARAMETROS, "limit": limite, "start": inicio},
        headers={"User-Agent": "Mozilla/5.0 (lojagas-ingesta)"},
        timeout=60,
        verify=certificados(),
    )
    r.raise_for_status()
    return r.json()


def descargar_todo(descargador: Descargador = _descargar) -> list[dict]:
    """Todas las vías con novedades del país, página por página."""
    registros: list[dict] = []
    while True:
        resp = descargador(len(registros), POR_PAGINA)
        if str(resp.get("code", "200")) not in ("200", "0"):
            raise RuntimeError(f"El servicio del ECU911 respondió code={resp.get('code')}")
        pagina = resp.get("data") or []
        registros += pagina
        total = int(resp.get("total") or 0)
        if not pagina or len(registros) >= total:
            return registros


def _nombre(obj: dict | None, campo: str) -> str | None:
    return (obj or {}).get(campo)


def _alternas(r: dict) -> str | None:
    vias = [v.get("descripcion") or v.get("nombre") for v in r.get("ViaAlterna") or []]
    detalle = [
        d.get("descripcion") or d.get("observaciones") for d in r.get("DetalleViaAlterna") or []
    ]
    texto = " / ".join(x for x in [*vias, *detalle] if x)
    return texto or None


def a_tabla(registros: list[dict], fecha: str) -> pd.DataFrame:
    """Respuesta del servicio → una fila por vía con novedades. Función pura."""
    filas = [
        {
            "fecha": fecha,
            "via_id": r.get("id"),
            "via": (r.get("descripcion") or "").strip(),
            "provincia": _nombre(r.get("Provincia"), "descripcion"),
            "canton": _nombre(r.get("Canton"), "descripcion"),
            "categoria": _nombre(r.get("GroupDetail"), "nombre"),
            "estado": _nombre(r.get("EstadoActual"), "nombre"),
            "observaciones": (r.get("observaciones") or "").strip() or None,
            "vias_alternas": _alternas(r),
            "creado": r.get("created"),
            "modificado": r.get("modified"),
        }
        for r in registros
    ]
    df = pd.DataFrame(filas, columns=COLUMNAS)
    for col in ("creado", "modificado"):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def hoy() -> str:
    return datetime.now(ZONA).date().isoformat()


def foto_diaria(descargador: Descargador = _descargar, fecha: str | None = None) -> pd.DataFrame:
    """Estado de hoy de las vías con novedades en todo el país.

    La fecha es la del día en Ecuador en que se consulta: el servicio no da el estado de
    otros días, así que no se puede "reprocesar" una fecha pasada.
    """
    fecha = fecha or hoy()
    registros = descargar_todo(descargador)
    df = a_tabla(registros, fecha)
    if df.empty:
        # Muy raro. Se guarda una fila marcadora para distinguir "se consultó y no había
        # novedades" de "ese día no se consultó"
        log.warning("ECU911: ninguna vía con novedades en el país el %s", fecha)
        df = pd.DataFrame([{"fecha": fecha, "estado": SIN_NOVEDADES}], columns=COLUMNAS)
    return df
