"""Clima por provincia y rezago de las fuentes externas, con píxeles sintéticos."""

import pandas as pd
import pytest

from lojagas.procesamiento.clima import (
    cargar_provincias,
    clima_mensual,
    provincia_de_pixeles,
    variables_clima,
)
from lojagas.procesamiento.contratos import clima_mensual_curated
from lojagas.procesamiento.ingenieria_caracteristicas import construir
from lojagas.procesamiento.temporales import rezago_minimo_externo

# Centros de píxel verificados con referencias/provincias.geojson
LOJA = (-4.0, -79.2)
ZAMORA = (-4.0, -78.9)
ZAMORA_OESTE = (-4.6, -79.3)  # solo está en el rectángulo de descarga de Loja
SUPERPUESTO = (-4.8, -79.1)  # Zamora, dentro de los dos rectángulos de descarga
FUERA = (-4.5, -80.5)  # Perú


def _raw(pixel, meses, t2m=290.15, area="LOJA", expver="0001"):
    """Filas de Raw como las deja la ingesta: unidades de CDS (Kelvin, m/día)."""
    meses = pd.to_datetime(meses)
    return pd.DataFrame(
        {
            "fecha": meses,
            "provincia_area": area,
            "lat": pixel[0],
            "lon": pixel[1],
            "t2m": t2m,
            "d2m": t2m - 5,
            "tp": 0.005,
            "expver": expver,
        }
    )


@pytest.mark.parametrize(
    ("dias", "dia_ejecucion", "esperado"),
    [
        (7, 2, 3),  # ERA5-Land con la corrida del día 2: solo M − 2
        (7, 10, 2),  # con una corrida del día 10 ya estaría M − 1
        (0, 2, 2),  # publicada al inicio del mes: M − 1
        (60, 2, 5),  # dos meses de latencia, contada con el peor caso
        (-365, 2, 0),  # calendario: se conoce de antemano
    ],
)
def test_rezago_minimo_externo(dias, dia_ejecucion, esperado):
    assert rezago_minimo_externo(dias, dia_ejecucion, horizonte=2) == esperado


def test_provincia_de_cada_pixel_segun_el_contorno():
    pixeles = pd.DataFrame([LOJA, ZAMORA, ZAMORA_OESTE, FUERA], columns=["lat", "lon"])
    provincia = provincia_de_pixeles(pixeles, cargar_provincias())
    assert provincia.iloc[:3].tolist() == ["LOJA", "ZAMORA CHINCHIPE", "ZAMORA CHINCHIPE"]
    assert pd.isna(provincia.iloc[3])


def test_promedia_por_contorno_y_descarta_lo_de_fuera():
    mes = ["2021-01-01"]
    raw = pd.concat(
        [
            _raw(LOJA, mes, t2m=290.15),
            _raw(FUERA, mes, t2m=400.0),  # Perú, en el rectángulo de Loja: no debe pesar
            _raw(ZAMORA, mes, t2m=288.15, area="ZAMORA CHINCHIPE"),
            _raw(ZAMORA_OESTE, mes, t2m=286.15, area="LOJA"),
            _raw(SUPERPUESTO, mes, t2m=284.15, area="LOJA"),
            _raw(SUPERPUESTO, mes, t2m=284.15, area="ZAMORA CHINCHIPE"),
        ]
    )
    out = clima_mensual(raw, "2021-01-01", cargar_provincias())
    clima_mensual_curated.validate(out)
    por_provincia = out.set_index("provincia")

    assert por_provincia.loc["LOJA", "temp_media_c"] == pytest.approx(17.0)
    assert por_provincia.loc["LOJA", "pixeles"] == 1
    # Zamora: su píxel, el del oeste (descargado con Loja) y el superpuesto una sola vez
    assert por_provincia.loc["ZAMORA CHINCHIPE", "pixeles"] == 3
    assert por_provincia.loc["ZAMORA CHINCHIPE", "temp_media_c"] == pytest.approx(13.0)
    assert por_provincia.loc["LOJA", "precip_mm"] == pytest.approx(0.005 * 1000 * 31)


def test_solo_hasta_el_periodo_y_marca_el_preliminar():
    raw = pd.concat(
        [
            _raw(LOJA, ["2026-08-01"], expver="0001"),
            _raw(LOJA, ["2026-09-01"], expver="0005"),
            _raw(LOJA, ["2026-10-01"], expver="0005"),  # ya publicado, pero posterior al período
        ]
    )
    out = clima_mensual(raw, "2026-09-01", cargar_provincias())
    assert out["mes"].max() == pd.Timestamp("2026-09-01")
    assert out["preliminar"].tolist() == [False, True]


def test_anomalia_contra_la_normal_1991_2020_del_mismo_mes():
    raw = pd.concat(
        [
            _raw(LOJA, ["2019-01-01"], t2m=290.15),  # 17 °C
            _raw(LOJA, ["2020-01-01"], t2m=292.15),  # 19 °C: normal de enero = 18 °C
            _raw(LOJA, ["2020-02-01"], t2m=300.15),  # febrero no entra en la normal de enero
            _raw(LOJA, ["2024-01-01"], t2m=293.15),  # 20 °C, fuera de 1991-2020
        ]
    )
    out = clima_mensual(raw, "2024-01-01", cargar_provincias()).set_index("mes")
    assert out.loc["2024-01-01", "temp_anom_c"] == pytest.approx(2.0)
    assert out.loc["2019-01-01", "temp_anom_c"] == pytest.approx(-1.0)
    assert out.loc["2020-02-01", "temp_anom_c"] == pytest.approx(0.0)


def _clima(meses, temp):
    n = len(meses)
    return pd.DataFrame(
        {
            "mes": pd.to_datetime(meses),
            "provincia": "LOJA",
            "temp_media_c": temp,
            "precip_mm": [100.0] * n,
            "humedad_rel_pct": [80.0] * n,
            "temp_anom_c": [0.0] * n,
            "precip_anom_mm": [0.0] * n,
        }
    )


def test_variables_clima_corren_el_rezago():
    v = variables_clima(_clima(["2024-01-01", "2024-02-01"], [17.0, 18.0]), rezago=3)
    v = v.set_index("mes")
    # La fila de abril lleva el clima de enero
    assert v.loc["2024-04-01", "clima_loja_temp_media_c_lag3"] == 17.0
    assert v.loc["2024-05-01", "clima_loja_temp_media_c_lag3"] == 18.0
    assert {"clima_loja_precip_mm_lag3", "clima_loja_precip_anom_mm_lag3"} <= set(v.columns)


def test_construir_une_el_clima_por_mes_y_exige_el_rezago(serie_mensual):
    clima = _clima(["2026-07-01", "2026-08-01", "2026-09-01"], [15.0, 16.0, 17.0])
    df = construir(serie_mensual, horizonte=2, clima=clima, rezago_clima=3)

    assert len(df) == len(construir(serie_mensual, horizonte=2))  # no duplica filas
    # Diciembre (fila futura) lleva el clima de septiembre, ya publicado al correr
    diciembre = df[df["mes"] == "2026-12-01"]
    assert (diciembre["clima_loja_temp_media_c_lag3"] == 17.0).all()
    with pytest.raises(ValueError, match="rezago"):
        construir(serie_mensual, horizonte=2, clima=clima)
