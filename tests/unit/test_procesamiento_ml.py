import pandas as pd

from lojagas.cli import main
from lojagas.ingesta.externas.calendario import CalendarioEventos
from lojagas.ml.evaluacion import supera_baseline
from lojagas.procesamiento.ingenieria_caracteristicas import construir


def test_construir_features_agrega_lags_calendario_y_eventos(serie_mensual):
    df = construir(serie_mensual, CalendarioEventos().extraer())
    assert {"lag_1", "lag_12", "media_3", "mes_sin", "mes_cos", "dias_religioso"} <= set(df.columns)
    septiembre = df[(df["mes"] == "2024-09-01") & (df["segmento"] == "domestico")]
    assert septiembre["dias_religioso"].item() == 30


def test_supera_baseline_filtra_y_ordena():
    resumen = pd.DataFrame(
        {"wape": [8.0, 12.0, 5.0, 9.0]},
        index=["estacional_ingenuo", "lasso", "xgboost", "ridge"],
    )
    assert supera_baseline(resumen).index.tolist() == ["xgboost"]


def test_cli_subcomando_pendiente_devuelve_2():
    assert main(["predecir", "--periodo", "2026-10-01"]) == 2


def test_curacion_de_punta_a_punta_sin_pii(tmp_path, lineas_factura):
    from lojagas.comun import lakehouse
    from lojagas.comun.config import Config
    from lojagas.procesamiento.curacion import ejecutar

    cfg = Config(lakehouse=tmp_path, pii_salt="sal-de-prueba-suficientemente-larga")
    lakehouse.escribir(lineas_factura, tmp_path, "raw", "ventas_lineas")

    versiones = ejecutar(cfg)

    lineas = lakehouse.leer(tmp_path, "curated", "ventas_lineas")
    assert "cliente_nombre" not in lineas.columns
    assert not lineas["cliente_ruc"].dropna().isin(lineas_factura["cliente_ruc"]).any()
    assert versiones["curated.ventas_mensual"] == 0
