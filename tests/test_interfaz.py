"""El tablero es de solo lectura (ADR-0011) y eso tiene que quedar fijado por pruebas.

No se prueba la apariencia, se prueban las dos propiedades de las que depende la
decisión de no exigir autenticación: que no exponga rutas de escritura y que no
alcance las zonas con datos personales.
"""

from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi", reason="extra 'interfaz' no instalado")
from fastapi.testclient import TestClient  # noqa: E402

from lojagas.interfaz.app import app  # noqa: E402

cliente = TestClient(app)


def test_salud_responde():
    r = cliente.get("/salud")
    assert r.status_code == 200
    assert r.json()["estado"] == "vivo"


def test_solo_metodos_de_lectura():
    """Ninguna ruta acepta POST, PUT, PATCH ni DELETE."""
    escritura = {"POST", "PUT", "PATCH", "DELETE"}
    for ruta in app.routes:
        metodos = getattr(ruta, "methods", set()) or set()
        assert not (metodos & escritura), f"{ruta.path} expone {metodos & escritura}"


def test_no_referencia_zonas_con_pii():
    """El módulo no menciona raw, curated ni feature: solo lee predicciones."""
    from pathlib import Path

    import lojagas.interfaz.app as modulo

    codigo = Path(modulo.__file__).read_text(encoding="utf-8")
    cuerpo = codigo.split('"""', 2)[-1]  # fuera el docstring, que sí las nombra
    for zona in ('"raw"', '"curated"', '"feature"'):
        assert zona not in cuerpo, f"la interfaz no debe tocar la zona {zona}"
