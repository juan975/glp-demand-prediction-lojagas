"""Estado de vías del ECU911: paginación, tabla y foto del día."""

from pathlib import Path

import pytest

from lojagas.ingesta.externas.ecu911_vias import (
    CERT_INTERMEDIO,
    SIN_NOVEDADES,
    a_tabla,
    certificados,
    descargar_todo,
    foto_diaria,
)


def _via(nombre, provincia, canton, estado, obs="", alterna=None):
    """Registro con la forma que devuelve el servicio (ViasWeb.php)."""
    return {
        "id": f"id-{nombre}",
        "descripcion": nombre,
        "estado_actual_id": 594,
        "observaciones": obs,
        "created": "2025-10-19 10:00:18",
        "modified": "2026-04-19 09:10:15",
        "estado": "A",
        "GroupDetail": {"nombre": "ARTERIAL"},
        "EstadoActual": {"nombre": estado},
        "Provincia": {"descripcion": provincia},
        "Canton": {"descripcion": canton},
        "ViaAlterna": [{"descripcion": alterna}] if alterna else [],
        "DetalleViaAlterna": [],
    }


REGISTROS = [
    _via(
        "SAN PEDRO - LAS CHINCHAS - VIA A LA COSTA",
        "LOJA",
        "CATAMAYO",
        "PARCIALMENTE HABILITADA",
        "VARIOS DESLIZAMIENTOS DE TIERRA",
    ),
    _via(
        "VÍA ZAMORA - YANTZAZA",
        "ZAMORA CHINCHIPE",
        "ZAMORA",
        "CERRADA",
        alterna="VIA ANTIGUA ZAMORA - LOJA",
    ),
    _via("CUENCA-CAÑAR-ALAUSI", "AZUAY", "CUENCA", "PARCIALMENTE HABILITADA"),
]


def test_a_tabla_una_fila_por_via():
    df = a_tabla(REGISTROS, "2026-11-24")
    # Todo el país: los corredores de Lojagas pasan también por Azuay, El Oro y Guayas
    assert df["provincia"].tolist() == ["LOJA", "ZAMORA CHINCHIPE", "AZUAY"]
    assert df["estado"].tolist() == [
        "PARCIALMENTE HABILITADA",
        "CERRADA",
        "PARCIALMENTE HABILITADA",
    ]
    assert df["vias_alternas"].isna().tolist() == [True, False, True]
    assert df["vias_alternas"].iloc[1] == "VIA ANTIGUA ZAMORA - LOJA"
    assert (df["fecha"] == "2026-11-24").all()
    assert str(df["modificado"].iloc[0]) == "2026-04-19 09:10:15"


def test_descargar_todo_recorre_las_paginas():
    pedidos = []

    def descargador(inicio, limite):
        pedidos.append(inicio)
        return {"code": 200, "total": 3, "data": REGISTROS[inicio : inicio + 2]}

    assert len(descargar_todo(descargador)) == 3
    assert pedidos == [0, 2]


def test_descargar_todo_falla_si_el_servicio_da_error():
    with pytest.raises(RuntimeError, match="code=500"):
        descargar_todo(lambda i, n: {"code": 500, "total": 0, "data": []})


def test_foto_sin_novedades_deja_una_fila_marcadora():
    df = foto_diaria(lambda i, n: {"code": 200, "total": 0, "data": []}, fecha="2026-11-24")
    assert df["estado"].tolist() == [SIN_NOVEDADES]
    assert df["fecha"].tolist() == ["2026-11-24"]


def test_ejecutar_vias_reemplaza_el_dia(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from lojagas.comun import lakehouse
    from lojagas.ingesta import ingesta
    from lojagas.ingesta.externas import ecu911_vias

    # Sin internet: la foto del día sale de los registros de ejemplo
    monkeypatch.setattr(
        ingesta.ecu911_vias, "foto_diaria", lambda: ecu911_vias.a_tabla(REGISTROS, "2026-11-24")
    )
    cfg = SimpleNamespace(lakehouse=tmp_path)
    ingesta.ejecutar_vias(cfg)
    ingesta.ejecutar_vias(cfg)  # reintento el mismo día: no duplica
    df = lakehouse.leer(tmp_path, "raw", "ecu911_vias")
    assert len(df) == 3


def test_certificados_suma_el_intermedio_de_sectigo():
    # El servidor no envía el intermedio: sin él, requests rechaza la conexión
    texto = CERT_INTERMEDIO.read_text()
    assert texto.startswith("-----BEGIN CERTIFICATE-----")
    combinado = Path(certificados()).read_text()
    assert texto.strip() in combinado
    assert combinado.count("BEGIN CERTIFICATE") > 100  # raíces de certifi + el intermedio


def test_tabla_de_corredores():
    import pandas as pd

    df = pd.read_csv("referencias/corredores_lojagas.csv")
    assert set(df["corredor"]) == {"guayaquil_catamayo", "cuenca_catamayo", "catamayo_yantzaza"}
    # Dentro de un corredor, cada grupo ocupa un solo lugar en el recorrido
    assert (
        not df.drop_duplicates(["corredor", "grupo", "orden"])
        .duplicated(["corredor", "grupo"])
        .any()
    )
    assert not df.duplicated(["corredor", "via_ecu911"]).any()
