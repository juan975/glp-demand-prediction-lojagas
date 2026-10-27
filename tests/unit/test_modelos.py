import pandas as pd

from lojagas.ml.pipeline_entrenamiento import validacion_cruzada
from lojagas.procesamiento.temporales import calendario, rezagos


def _features(serie):
    df = calendario(rezagos(serie))
    return pd.get_dummies(df, columns=["segmento"], dtype=float)


def test_rezagos_no_usan_el_mes_actual(serie_mensual):
    df = rezagos(serie_mensual).query("segmento == 'domestico'").reset_index(drop=True)
    assert df.loc[13, "lag_1"] == df.loc[12, "toneladas"]
    assert df.loc[13, "media_3"] == df.loc[10:12, "toneladas"].mean()


def test_estacional_ingenuo_supera_a_ingenuo_en_serie_estacional(serie_mensual):
    df = _features(serie_mensual)
    feats = ["lag_1", "lag_12"]
    ingenuo = validacion_cruzada("ingenuo", df, feats, min_entrenamiento=12)
    estacional = validacion_cruzada("estacional_ingenuo", df, feats, min_entrenamiento=12)
    assert estacional["wape"].mean() < ingenuo["wape"].mean()


def test_ridge_corre_en_walk_forward(serie_mensual):
    df = _features(serie_mensual)
    feats = ["lag_1", "lag_12", "media_3", "mes_sin", "mes_cos"] + [
        c for c in df.columns if c.startswith("segmento_")
    ]
    folds = validacion_cruzada("ridge", df, feats, min_entrenamiento=12)
    assert len(folds) > 0 and folds["wape"].notna().all()
