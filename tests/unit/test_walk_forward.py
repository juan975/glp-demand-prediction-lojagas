import pytest

from lojagas.ml.walk_forward import particiones


def test_sin_fuga_temporal(serie_mensual):
    for tr, te in particiones(serie_mensual["mes"], min_entrenamiento=24):
        assert serie_mensual["mes"].iloc[tr].max() < serie_mensual["mes"].iloc[te].min()


def test_mes_completo_en_prueba(serie_mensual):
    """Los 3 segmentos de un mes van juntos: nunca se parte un mes."""
    _, te = next(particiones(serie_mensual["mes"], min_entrenamiento=24))
    assert len(te) == 3
    assert serie_mensual["mes"].iloc[te].nunique() == 1


def test_numero_de_folds(serie_mensual):
    folds = list(particiones(serie_mensual["mes"], min_entrenamiento=24))
    assert len(folds) == 46 - 24


def test_error_si_no_alcanzan_los_meses(serie_mensual):
    with pytest.raises(ValueError):
        list(particiones(serie_mensual["mes"], min_entrenamiento=60))
