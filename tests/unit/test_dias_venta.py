"""Días de venta con casos que se pueden contar a mano en el calendario."""

import numpy as np
import pandas as pd
import pytest

from lojagas.procesamiento.dias_venta import dias_venta, pesos_dia_semana
from lojagas.procesamiento.ingenieria_caracteristicas import construir
from lojagas.procesamiento.temporales import calendario

MAPA = pd.DataFrame(
    {
        "categoria": ["GLP / GLP DOMESTICO", "GLP / GLP INDUSTRIAL", "CILINDROS / ENVASE"],
        "segmento": ["domestico", "industrial", "excluir"],
    }
)


def _lineas(fechas, categoria="GLP / GLP DOMESTICO", kg=100.0, move_type="out_invoice"):
    fechas = pd.to_datetime(fechas)
    return pd.DataFrame(
        {
            "fecha_factura": fechas,
            "categoria": categoria,
            "kg_glp": kg,
            "move_type": move_type,
        }
    )


def _pesos(segmentos, valores):
    """Pesos fijos por día de la semana (lunes a domingo), iguales para cada segmento."""
    return pd.DataFrame(
        [(s, d, v) for s in segmentos for d, v in enumerate(valores)],
        columns=["segmento", "dia_semana", "peso"],
    )


def test_pesos_de_lunes_a_sabado_iguales_y_domingo_cero():
    """Enero de 2024 empieza en lunes. Se vende lo mismo cada día salvo los domingos."""
    dias = pd.date_range("2024-01-01", "2024-01-31")
    lineas = pd.concat(
        [
            _lineas(dias[dias.day_of_week < 6]),
            # Una nota de crédito un domingo no es venta de ese día
            _lineas(["2024-01-07"], kg=500.0, move_type="out_refund"),
            # Fuera de la ventana de un mes: no cambia los pesos
            _lineas(["2024-02-04"], kg=9999.0),
            # Envases: no son demanda de gas
            _lineas(["2024-01-14"], categoria="CILINDROS / ENVASE", kg=50.0),
        ]
    )
    pesos = pesos_dia_semana(lineas, MAPA, meses=1)
    dom = pesos[pesos["segmento"] == "domestico"].set_index("dia_semana")["peso"]
    # Por día: 100 kg de lunes a sábado y 0 el domingo; promedio 600/7 → pesos 7/6 y 0
    assert dom.loc[0:5].tolist() == pytest.approx([7 / 6] * 6)
    assert dom.loc[6] == pytest.approx(0.0)
    assert dom.mean() == pytest.approx(1.0)
    assert set(pesos["segmento"]) == {"domestico"}
    assert pesos["desde"].iloc[0] == pd.Timestamp("2024-01-01")
    assert pesos["hasta"].iloc[0] == pd.Timestamp("2024-01-31")


def test_pesos_corrigen_por_cuantas_veces_aparece_cada_dia():
    """Enero de 2024 tiene 5 lunes y 4 jueves. Si cada día vende 100 kg, pesan lo mismo."""
    pesos = pesos_dia_semana(_lineas(pd.date_range("2024-01-01", "2024-01-31")), MAPA, meses=1)
    assert pesos["peso"].tolist() == pytest.approx([1.0] * 7)


def test_segmento_sin_ventas_en_la_ventana_queda_con_peso_uno():
    lineas = pd.concat(
        [
            _lineas(pd.date_range("2024-01-01", "2024-01-31")),
            _lineas(["2024-02-05"], categoria="GLP / GLP INDUSTRIAL"),
        ]
    )
    pesos = pesos_dia_semana(lineas, MAPA, meses=1)
    industrial = pesos[pesos["segmento"] == "industrial"]
    assert industrial["peso"].tolist() == [1.0] * 7


def test_dias_venta_febrero_bisiesto():
    """Febrero de 2024: 29 días, 4 domingos (4, 11, 18 y 25). Carnaval: lunes 12 y martes 13."""
    df = pd.DataFrame({"mes": pd.to_datetime(["2024-02-01"]), "segmento": ["domestico"]})
    pesos = _pesos(["domestico"], [1, 1, 1, 1, 1, 1, 0])

    assert dias_venta(df, _pesos(["domestico"], [1] * 7)).item() == 29
    assert dias_venta(df, pesos).item() == 25
    carnaval = pd.to_datetime(["2024-02-12", "2024-02-13"])
    assert dias_venta(df, pesos, feriados=carnaval).item() == 23
    # Un feriado que cae en domingo no cambia nada
    assert dias_venta(df, pesos, feriados=pd.to_datetime(["2024-02-04"])).item() == 25


def test_dias_venta_falla_si_un_segmento_no_tiene_pesos():
    df = pd.DataFrame({"mes": pd.to_datetime(["2024-02-01"]), "segmento": ["agroindustrial"]})
    with pytest.raises(ValueError, match="agroindustrial"):
        dias_venta(df, _pesos(["domestico"], [1] * 7))


def test_construir_agrega_dias_de_venta_y_estacional_ajustado(serie_mensual):
    pesos = _pesos(serie_mensual["segmento"].unique(), [1] * 7)
    df = construir(serie_mensual, horizonte=2, pesos=pesos)

    # Con todos los pesos en 1, los días de venta son los días del mes, también en el futuro
    assert (df["dias_venta"] == df["mes"].dt.days_in_month).all()
    feb = df[(df["mes"] == "2024-02-01") & (df["segmento"] == "domestico")].iloc[0]
    assert feb["ratio_dias_12"] == pytest.approx(29 / 28)
    assert feb["estacional_dias"] == pytest.approx(feb["lag_12"] * 29 / 28)
    # El primer año no tiene mes de referencia
    assert df.loc[df["mes"] < "2024-01-01", "estacional_dias"].isna().all()


def test_segundo_armonico_repite_cada_seis_meses():
    df = calendario(pd.DataFrame({"mes": pd.date_range("2024-01-01", periods=12, freq="MS")}))
    assert np.allclose(df["mes_sin2"].iloc[:6], df["mes_sin2"].iloc[6:])
    assert np.allclose(df["mes_cos2"].iloc[:6], df["mes_cos2"].iloc[6:])
    assert not np.allclose(df["mes_sin"].iloc[:6], df["mes_sin"].iloc[6:])
