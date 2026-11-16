import pandas as pd
import pytest

from lojagas.ml.modelos.baselines import Ingenuo
from lojagas.ml.modelos.catalogo import crear
from lojagas.ml.pipeline_entrenamiento import validacion_cruzada
from lojagas.procesamiento.temporales import calendario, extender_futuro, rezagos

H = 2


def _features(serie):
    df = calendario(rezagos(serie, horizonte=H))
    return pd.get_dummies(df, columns=["segmento"], dtype=float)


def test_rezagos_solo_usan_meses_cerrados(serie_mensual):
    """Con horizonte 2, la fila del mes t usa como máximo el mes t − 2."""
    df = rezagos(serie_mensual, horizonte=H).query("segmento == 'domestico'")
    df = df.reset_index(drop=True)
    assert "lag_1" not in df.columns
    assert df.loc[13, "lag_2"] == df.loc[11, "toneladas"]
    assert df.loc[13, "media_3"] == df.loc[9:11, "toneladas"].mean()


def test_rezagos_rechaza_lags_menores_que_el_horizonte(serie_mensual):
    with pytest.raises(ValueError):
        rezagos(serie_mensual, horizonte=H, lags=(1, 12))


def test_fila_de_diciembre_con_datos_hasta_octubre(serie_mensual):
    """El 2 de noviembre (datos hasta octubre) el predictor necesita la fila de diciembre."""
    df = rezagos(extender_futuro(serie_mensual, H), horizonte=H)
    dom = df[df["segmento"] == "domestico"].set_index("mes")
    dic = dom.loc["2026-12-01"]
    assert pd.isna(dic["toneladas"])
    assert dic["lag_2"] == dom.loc["2026-10-01", "toneladas"]
    assert dic["media_3"] == dom.loc["2026-08-01":"2026-10-01", "toneladas"].mean()


def test_ingenuo_copia_el_ultimo_mes_cerrado():
    assert crear("ingenuo", H).get_params()["horizonte"] == H
    with pytest.raises(ValueError):
        Ingenuo().fit(pd.DataFrame({"lag_2": [1.0]}))


def test_validacion_rechaza_features_del_futuro(serie_mensual):
    df = _features(serie_mensual)
    df["lag_1"] = df["toneladas"]
    with pytest.raises(ValueError, match="lag_1"):
        validacion_cruzada("ridge", df, ["lag_1", "lag_12"], horizonte=H)


def test_estacional_ingenuo_supera_a_ingenuo_en_serie_estacional(serie_mensual):
    df = _features(serie_mensual)
    feats = ["lag_2", "lag_12"]
    ingenuo = validacion_cruzada("ingenuo", df, feats, horizonte=H, min_entrenamiento=12)
    estacional = validacion_cruzada(
        "estacional_ingenuo", df, feats, horizonte=H, min_entrenamiento=12
    )
    assert estacional["wape"].mean() < ingenuo["wape"].mean()


def test_ridge_corre_en_walk_forward(serie_mensual):
    df = _features(serie_mensual)
    feats = ["lag_2", "lag_12", "media_3", "mes_sin", "mes_cos"] + [
        c for c in df.columns if c.startswith("segmento_")
    ]
    folds = validacion_cruzada("ridge", df, feats, horizonte=H, min_entrenamiento=12)
    assert len(folds) > 0 and folds["wape"].notna().all()
