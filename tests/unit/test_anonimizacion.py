import pytest

from lojagas.procesamiento.anonimizacion import seudonimizar

SAL = "sal-de-prueba-suficientemente-larga"


def test_elimina_nombres_y_seudonimiza_ruc(lineas_factura):
    out = seudonimizar(lineas_factura, SAL)
    assert "cliente_nombre" not in out.columns
    assert not out["cliente_ruc"].dropna().isin(lineas_factura["cliente_ruc"]).any()


def test_descarta_toda_columna_fuera_de_la_lista_blanca(lineas_factura):
    """Una columna con PII que nadie listó (placas, guías, pagos) no llega a Curated."""
    df = lineas_factura.assign(
        vehiculo_placa="LBA-1234", guia_numero="001-002", pago_monto=10.0, columna_nueva="x"
    )
    out = seudonimizar(df, SAL)
    assert not {"vehiculo_placa", "guia_numero", "pago_monto", "columna_nueva"} & set(out.columns)
    assert {"linea_id", "kg_glp", "categoria", "cliente_ruc"} <= set(out.columns)


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
