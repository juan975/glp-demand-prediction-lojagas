"""Acceso a las zonas del Data Lakehouse (Raw, Curated, Feature, Predicciones) sobre Delta Lake.

Regla: ningún módulo escribe archivos en el lakehouse por fuera de este módulo.
Así la retención del historial y el versionado se controlan en un solo lugar.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd
from deltalake import DeltaTable, write_deltalake

Zona = Literal["raw", "curated", "feature", "predicciones"]
ZONAS: tuple[Zona, ...] = ("raw", "curated", "feature", "predicciones")

# Sin esto, un VACUUM borra versiones antiguas y se pierde el time travel,
# es decir, la reproducibilidad que se promete en la sección 3.6.2.
RETENCION = {
    "delta.logRetentionDuration": "interval 3650 days",
    "delta.deletedFileRetentionDuration": "interval 3650 days",
}


def ruta_tabla(raiz: Path, zona: Zona, tabla: str) -> Path:
    if zona not in ZONAS:
        raise ValueError(f"Zona inválida: {zona}")
    return raiz / zona / tabla


def escribir(
    df: pd.DataFrame,
    raiz: Path,
    zona: Zona,
    tabla: str,
    modo: Literal["append", "overwrite"] = "append",
    particiones: list[str] | None = None,
) -> int:
    """Escribe y devuelve la versión Delta resultante (se registra en MLflow)."""
    ruta = ruta_tabla(raiz, zona, tabla)
    write_deltalake(
        str(ruta),
        df,
        mode=modo,
        partition_by=particiones,
        configuration=RETENCION,
        schema_mode="merge" if modo == "append" else "overwrite",
    )
    return DeltaTable(str(ruta)).version()


def reemplazar_periodo(
    df: pd.DataFrame, raiz: Path, zona: Zona, tabla: str, columna: str, valor: str
) -> int:
    """Reemplaza solo las filas con `columna == valor` y devuelve la versión Delta.

    Idempotente: si Airflow reintenta la corrida de un mes, ese mes se reescribe en vez
    de duplicarse, y el resto del historial no se toca. La versión anterior sigue
    disponible por time travel.
    """
    if not (df[columna] == valor).all():
        raise ValueError(f"Todas las filas deben tener {columna} = {valor}")
    ruta = ruta_tabla(raiz, zona, tabla)
    if not DeltaTable.is_deltatable(str(ruta)):
        return escribir(df, raiz, zona, tabla, modo="append", particiones=[columna])
    write_deltalake(
        str(ruta),
        df,
        mode="overwrite",
        predicate=f"{columna} = '{valor}'",
        schema_mode="merge",
    )
    return DeltaTable(str(ruta)).version()


def leer(raiz: Path, zona: Zona, tabla: str, version: int | None = None) -> pd.DataFrame:
    """Lee la última versión o una versión exacta (time travel)."""
    ruta = ruta_tabla(raiz, zona, tabla)
    dt = DeltaTable(str(ruta), version=version) if version is not None else DeltaTable(str(ruta))
    return dt.to_pandas()


def existe(raiz: Path, zona: Zona, tabla: str) -> bool:
    return DeltaTable.is_deltatable(str(ruta_tabla(raiz, zona, tabla)))


def version_actual(raiz: Path, zona: Zona, tabla: str) -> int:
    return DeltaTable(str(ruta_tabla(raiz, zona, tabla))).version()
