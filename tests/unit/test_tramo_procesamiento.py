"""Tramo de Procesamiento de punta a punta: Raw sintético → curación → Feature.

Comprueba en un lakehouse temporal lo que el modelo da por hecho: sin PII en Curated, nada
posterior al período y el clima con el rezago que ya está publicado el día de la corrida.
"""

import re
from pathlib import Path

import pandas as pd
import pytest

from lojagas.comun import lakehouse
from lojagas.comun.config import Config
from lojagas.ingesta.externas.calendario import CalendarioEventos
from lojagas.procesamiento import curacion, ingenieria_caracteristicas

PERIODO = "2024-03-01"
SAL = "sal-de-prueba-suficientemente-larga"
LOJA, ZAMORA, FUERA = (-4.0, -79.2), (-4.0, -78.9), (-4.5, -80.5)


def _ventas() -> pd.DataFrame:
    """Facturas diarias de 2023-01 a 2024-04-15, que pasa el período: 100 kg de lunes a
    viernes, 50 los sábados y nada los domingos. Con PII, como llega de Odoo."""
    dias = pd.date_range("2023-01-01", "2024-04-15")
    dias = dias[dias.day_of_week < 6]
    filas = []
    for categoria in ("GLP / GLP DOMESTICO", "GLP / GLP INDUSTRIAL"):
        kg = [50.0 if d.day_of_week == 5 else 100.0 for d in dias]
        filas.append(pd.DataFrame({"fecha_factura": dias, "categoria": categoria, "kg_glp": kg}))
    df = pd.concat(filas, ignore_index=True)
    n = len(df)
    return df.assign(
        linea_id=range(n),
        factura_id=range(n),
        move_type="out_invoice",
        state="posted",
        canal_venta="despacho",
        cantidad=1.0,
        cliente_ruc="1100000001",
        cliente_nombre="CLIENTE DE PRUEBA",
        partner_latitude=-3.99312,
        partner_longitude=-79.20456,
    )


def _era5() -> pd.DataFrame:
    """Clima de 2019-01 a 2024-05: Copernicus ya publicó abril y mayo (preliminares).
    La temperatura sube 0,1 °C por mes, así cada mes se reconoce por su valor."""
    meses = pd.date_range("2019-01-01", "2024-05-01", freq="MS")
    filas = [
        {
            "fecha": mes,
            "provincia_area": "LOJA",
            "lat": lat,
            "lon": lon,
            "t2m": 283.15 + 0.1 * i,
            "d2m": 278.15 + 0.1 * i,
            "tp": 0.004,
            "expver": "0005" if mes >= pd.Timestamp("2024-02-01") else "0001",
        }
        for i, mes in enumerate(meses)
        for lat, lon in (LOJA, ZAMORA, FUERA)
    ]
    return pd.DataFrame(filas)


def _correr(raiz: Path, con_clima: bool = True) -> dict:
    lakehouse.escribir(_ventas(), raiz, "raw", "ventas_lineas")
    lakehouse.escribir(CalendarioEventos().extraer(), raiz, "raw", "calendario_eventos")
    if con_clima:
        lakehouse.escribir(_era5(), raiz, "raw", "era5_land")
    cfg = Config(lakehouse=raiz, pii_salt=SAL)
    versiones = curacion.ejecutar(cfg, PERIODO)
    ingenieria_caracteristicas.ejecutar(cfg)
    return versiones


def test_curated_sin_pii_ni_meses_posteriores_al_periodo(tmp_path):
    versiones = _correr(tmp_path)

    lineas = lakehouse.leer(tmp_path, "curated", "ventas_lineas")
    assert "cliente_nombre" not in lineas.columns
    assert not (lineas["cliente_ruc"] == "1100000001").any()
    assert pd.to_datetime(lineas["fecha_factura"]).max() < pd.Timestamp("2024-04-01")

    mensual = lakehouse.leer(tmp_path, "curated", "ventas_mensual")
    clima = lakehouse.leer(tmp_path, "curated", "clima_mensual")
    assert mensual["mes"].max() == pd.Timestamp(PERIODO)
    assert clima["mes"].max() == pd.Timestamp(PERIODO)
    assert versiones["clima_hasta"] == "2024-03"
    # El píxel de Perú no forma una provincia
    assert set(clima["provincia"]) == {"LOJA", "ZAMORA CHINCHIPE"}


def test_pesos_del_primer_anio_reflejan_la_semana(tmp_path):
    _correr(tmp_path)
    pesos = lakehouse.leer(tmp_path, "curated", "actividad_dia_semana")
    domestico = pesos[pesos["segmento"] == "domestico"].set_index("dia_semana")["peso"]
    assert domestico.loc[6] == 0.0  # domingo
    assert domestico.loc[5] / domestico.loc[0] == pytest.approx(0.5)  # sábado, medio día
    assert pesos["hasta"].max() == pd.Timestamp("2023-12-31")


def test_feature_con_dias_de_venta_feriados_y_clima_con_rezago(tmp_path):
    _correr(tmp_path)
    features = lakehouse.leer(tmp_path, "feature", "demanda_mensual")
    clima = lakehouse.leer(tmp_path, "curated", "clima_mensual")
    temp_loja = clima[clima["provincia"] == "LOJA"].set_index("mes")["temp_media_c"]
    domestico = features[features["segmento"] == "domestico"].set_index("mes")

    assert domestico.index.max() == pd.Timestamp("2024-05-01")  # marzo + horizonte 2
    assert domestico["dias_venta"].notna().all()  # también en las filas futuras
    assert domestico.loc["2024-02-01", "dias_feriado"] == 2  # Carnaval

    # ERA5-Land sale ~7 días después del fin de mes y el DAG corre el día 2: rezago 3.
    # Mayo (la fila que se predice) lleva el clima de febrero, no el de marzo ni el de abril.
    columnas_clima = [c for c in features.columns if c.startswith("clima_")]
    assert columnas_clima and all(c.endswith("_lag3") for c in columnas_clima)
    assert domestico.loc["2024-05-01", "clima_loja_temp_media_c_lag3"] == pytest.approx(
        temp_loja.loc["2024-02-01"]
    )


def test_sin_clima_en_raw_el_tramo_sigue(tmp_path):
    """Si la ingesta de Copernicus nunca corrió, la configuración A se puede construir igual."""
    versiones = _correr(tmp_path, con_clima=False)
    features = lakehouse.leer(tmp_path, "feature", "demanda_mensual")
    assert "clima_hasta" not in versiones
    assert not lakehouse.existe(tmp_path, "curated", "clima_mensual")
    assert not any(c.startswith("clima_") for c in features.columns)
    assert features["dias_venta"].notna().all()


def test_dia_de_ejecucion_coincide_con_el_dag():
    """El rezago del clima depende del día en que corre el DAG: los dos valores van juntos."""
    dag = Path("dags/prediccion_mensual.py").read_text(encoding="utf-8")
    dia = re.search(r'schedule="\S+ \S+ (\d+) \* \*"', dag).group(1)
    assert int(dia) == Config().dia_ejecucion
