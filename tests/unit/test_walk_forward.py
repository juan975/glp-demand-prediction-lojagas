import pandas as pd
import pytest

from lojagas.ml.walk_forward import particiones


@pytest.mark.parametrize("horizonte", [1, 2, 3])
def test_entrena_solo_con_meses_cerrados(serie_mensual, horizonte):
    """Con horizonte h, entre el último mes de entrenamiento y el de prueba hay h meses."""
    meses = serie_mensual["mes"]
    for tr, te in particiones(meses, min_entrenamiento=24, horizonte=horizonte):
        ultimo = meses.iloc[tr].max().to_period("M")
        prueba = meses.iloc[te].min().to_period("M")
        assert (prueba - ultimo).n == horizonte


def test_noviembre_2_predice_diciembre(serie_mensual):
    """Para probar diciembre con horizonte 2, el entrenamiento llega hasta octubre."""
    meses = serie_mensual["mes"]
    folds = particiones(meses, min_entrenamiento=24, horizonte=2)
    diciembre = pd.Timestamp("2025-12-01")
    tr, _ = next((tr, te) for tr, te in folds if meses.iloc[te].min() == diciembre)
    assert meses.iloc[tr].max() == pd.Timestamp("2025-10-01")


def test_mes_completo_en_prueba(serie_mensual):
    """Los 3 segmentos de un mes van juntos: nunca se parte un mes."""
    _, te = next(particiones(serie_mensual["mes"], min_entrenamiento=24, horizonte=2))
    assert len(te) == 3
    assert serie_mensual["mes"].iloc[te].drop_duplicates().size == 1


@pytest.mark.parametrize(("horizonte", "esperados"), [(1, 46 - 24), (2, 46 - 24 - 1)])
def test_numero_de_folds(serie_mensual, horizonte, esperados):
    folds = list(particiones(serie_mensual["mes"], min_entrenamiento=24, horizonte=horizonte))
    assert len(folds) == esperados


def test_error_si_no_alcanzan_los_meses(serie_mensual):
    with pytest.raises(ValueError):
        list(particiones(serie_mensual["mes"], min_entrenamiento=60, horizonte=2))
