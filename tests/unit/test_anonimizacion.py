import pytest

from lojagas.procesamiento.anonimizacion import seudonimizar

SAL = "sal-de-prueba-suficientemente-larga"


def test_elimina_nombres_y_seudonimiza_ruc(lineas_factura):
    out = seudonimizar(lineas_factura, SAL)
    assert "cliente_nombre" not in out.columns
    assert not out["cliente_ruc"].dropna().isin(lineas_factura["cliente_ruc"]).any()


def test_mismo_ruc_mismo_seudonimo(lineas_factura):
    out = seudonimizar(lineas_factura, SAL)
    assert out.loc[0, "cliente_ruc"] == out.loc[2, "cliente_ruc"]


def test_conserva_nulos(lineas_factura):
    out = seudonimizar(lineas_factura, SAL)
    assert out["cliente_ruc"].isna().sum() == 1


def test_redondea_coordenadas(lineas_factura):
    out = seudonimizar(lineas_factura, SAL)
    assert out.loc[0, "partner_latitude"] == -3.99


def test_rechaza_sal_corta(lineas_factura):
    with pytest.raises(ValueError):
        seudonimizar(lineas_factura, "corta")
