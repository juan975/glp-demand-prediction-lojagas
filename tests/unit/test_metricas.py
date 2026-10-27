import math

import pytest

from lojagas.ml import metricas


def test_mape_es_nan_con_ceros():
    assert math.isnan(metricas.mape([0, 10], [1, 10]))


def test_wape_pondera_por_volumen():
    # Error de 1 sobre un valor de 1 (100 %) casi no pesa frente a 1000
    assert metricas.wape([1, 1000], [2, 1000]) == pytest.approx(1 / 1001 * 100)


def test_prediccion_perfecta():
    m = metricas.calcular([1, 2, 3], [1, 2, 3])
    assert m["mae"] == 0 and m["rmse"] == 0 and m["r2"] == 1
