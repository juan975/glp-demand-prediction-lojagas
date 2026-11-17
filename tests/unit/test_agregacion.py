from pathlib import Path

import pandas as pd
import pytest

from lojagas.procesamiento.agregacion import a_mensual, cargar_mapa_segmentos
from lojagas.procesamiento.contratos import ventas_mensual_curated

MAPA_REPO = Path(__file__).parents[2] / "referencias" / "mapa_segmentos.csv"


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


def test_mapa_del_repo_excluye_envases(lineas_factura):
    """Con el mapa de referencias/ (por categoría), la venta del envase no cuenta como GLP."""
    df = lineas_factura.copy()
    df.loc[1, "categoria"] = "CILINDROS / ENVASE CILINDROS PARA LA VENTA"
    out = a_mensual(df, cargar_mapa_segmentos(MAPA_REPO))
    assert set(out["segmento"]) == {"industrial", "domestico"}
    enero = out[out["mes"] == "2024-01-01"].set_index("segmento")["toneladas"]
    assert enero["domestico"] == 0  # la línea de enero de doméstico era un envase


def test_lineas_sin_kg_no_necesitan_segmento(lineas_factura):
    """Servicios e instalaciones no tienen kg: no se exigen en el mapa."""
    df = lineas_factura.copy()
    df.loc[3, ["categoria", "kg_glp"]] = ["INSTALACIONES CENTRALIZADAS / TUBERIAS", 0.0]
    a_mensual(df, cargar_mapa_segmentos(MAPA_REPO))


def test_falla_si_el_mapa_usa_una_columna_que_no_existe(lineas_factura):
    mapa = pd.DataFrame({"tipo_distribuidor": ["cupo"], "segmento": ["cupo"]})
    with pytest.raises(ValueError, match="tipo_distribuidor"):
        a_mensual(lineas_factura, mapa)


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
