import pandas as pd
import pytest

from lojagas.cli import main
from lojagas.ingesta.externas.calendario import CalendarioEventos
from lojagas.ml.evaluacion import supera_baseline
from lojagas.procesamiento.ingenieria_caracteristicas import construir


def test_construir_features_agrega_lags_calendario_y_eventos(serie_mensual):
    df = construir(serie_mensual, CalendarioEventos().extraer(), horizonte=2)
    assert {"lag_2", "lag_12", "media_3", "mes_sin", "mes_cos", "dias_religioso"} <= set(df.columns)
    assert "lag_1" not in df.columns
    septiembre = df[(df["mes"] == "2024-09-01") & (df["segmento"] == "domestico")]
    assert septiembre["dias_religioso"].item() == 30


def test_construir_agrega_noviembre_y_diciembre_sin_target(serie_mensual):
    """La serie llega a octubre de 2026: con horizonte 2 se agregan nov y dic por segmento."""
    df = construir(serie_mensual, horizonte=2)
    futuro = df[df["mes"] > "2026-10-01"]
    assert sorted(futuro["mes"].dt.strftime("%Y-%m").unique()) == ["2026-11", "2026-12"]
    assert len(futuro) == 2 * serie_mensual["segmento"].nunique()
    assert futuro["toneladas"].isna().all()


def test_supera_baseline_filtra_ordena_y_mide_la_mejora():
    resumen = pd.DataFrame(
        {"wape": [8.0, 12.0, 5.0, 9.0]},
        index=["estacional_ingenuo", "lasso", "xgboost", "ridge"],
    )
    ganadores = supera_baseline(resumen)
    assert ganadores.index.tolist() == ["xgboost"]
    assert ganadores.loc["xgboost", "mejora_sobre_ingenuo"] == pytest.approx(37.5)


def test_cli_subcomando_pendiente_devuelve_2():
    assert main(["predecir", "--fecha-ejecucion", "2026-11-02"]) == 2


@pytest.mark.parametrize(
    "argumentos",
    [
        ["curacion"],  # sin fecha ni período
        ["curacion", "--periodo", "2026-10-15"],  # el período es el día 1 de un mes
        ["curacion", "--periodo", "2026-10-01", "--fecha-ejecucion", "2026-11-02"],
    ],
)
def test_cli_rechaza_periodos_ambiguos(argumentos):
    with pytest.raises(SystemExit):
        main(argumentos)


def _curar(tmp_path, lineas, periodo):
    from lojagas.comun import lakehouse
    from lojagas.comun.config import Config
    from lojagas.procesamiento.curacion import ejecutar

    cfg = Config(lakehouse=tmp_path, pii_salt="sal-de-prueba-suficientemente-larga")
    lakehouse.escribir(lineas, tmp_path, "raw", "ventas_lineas")
    lakehouse.escribir(CalendarioEventos().extraer(), tmp_path, "raw", "calendario_eventos")
    return ejecutar(cfg, periodo)


def test_curacion_de_punta_a_punta_sin_pii(tmp_path, lineas_factura):
    from lojagas.comun import lakehouse

    versiones = _curar(tmp_path, lineas_factura, "2024-03-01")

    lineas = lakehouse.leer(tmp_path, "curated", "ventas_lineas")
    assert "cliente_nombre" not in lineas.columns
    assert not lineas["cliente_ruc"].dropna().isin(lineas_factura["cliente_ruc"]).any()
    assert versiones["curated.ventas_mensual"] == 0


def test_features_se_construyen_desde_curated(tmp_path, lineas_factura):
    """Curación → Feature de punta a punta: Feature lee ventas y calendario de Curated."""
    from lojagas.comun import lakehouse
    from lojagas.comun.config import Config
    from lojagas.procesamiento.ingenieria_caracteristicas import ejecutar

    _curar(tmp_path, lineas_factura, "2024-03-01")
    ejecutar(Config(lakehouse=tmp_path))
    features = lakehouse.leer(tmp_path, "feature", "demanda_mensual")
    assert features["mes"].max() == pd.Timestamp("2024-05-01")  # marzo + horizonte 2


def test_curacion_descarta_meses_posteriores_al_periodo(tmp_path, lineas_factura):
    """Con período enero, marzo (en curso o incompleto) no entra en Curated."""
    from lojagas.comun import lakehouse

    _curar(tmp_path, lineas_factura, "2024-01-01")
    mensual = lakehouse.leer(tmp_path, "curated", "ventas_mensual")
    assert mensual["mes"].max() == pd.Timestamp("2024-01-01")
