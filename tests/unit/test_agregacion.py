import pandas as pd
import pytest

from lojagas.procesamiento.agregacion import a_mensual
from lojagas.procesamiento.contratos import ventas_mensual_curated


def test_notas_de_credito_restan_y_convierte_a_toneladas(lineas_factura, mapa_segmentos):
    out = a_mensual(lineas_factura, mapa_segmentos)
    granel_marzo = out[(out["segmento"] == "granel") & (out["mes"] == "2024-03-01")]
    assert granel_marzo["toneladas"].item() == pytest.approx(-0.3)


def test_completa_meses_sin_ventas_con_cero(lineas_factura, mapa_segmentos):
    out = a_mensual(lineas_factura, mapa_segmentos)
    febrero = out[out["mes"] == "2024-02-01"]
    assert len(febrero) == 2
    assert (febrero["toneladas"] == 0).all()


def test_cumple_contrato_curated(lineas_factura, mapa_segmentos):
    ventas_mensual_curated.validate(a_mensual(lineas_factura, mapa_segmentos))


def test_falla_si_hay_canal_sin_segmento(lineas_factura, mapa_segmentos):
    df = lineas_factura.copy()
    df.loc[0, "canal_venta"] = "turno"
    with pytest.raises(ValueError, match="sin segmento"):
        a_mensual(df, mapa_segmentos)


def test_coincidencia_exacta_gana_al_comodin(lineas_factura, mapa_segmentos):
    mapa = pd.concat(
        [
            mapa_segmentos,
            pd.DataFrame(
                {"canal_venta": ["despacho"], "cliente_tipo": ["HOGAR"], "segmento": ["especial"]}
            ),
        ]
    )
    out = a_mensual(lineas_factura, mapa)
    assert "especial" in set(out["segmento"])
