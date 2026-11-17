from datetime import date

import pytest

from lojagas.comun.periodos import ultimo_mes_cerrado, validar_periodo


@pytest.mark.parametrize(
    ("ejecucion", "periodo"),
    [
        (date(2026, 11, 2), date(2026, 10, 1)),  # el 2 de noviembre procesa octubre
        (date(2027, 1, 2), date(2026, 12, 1)),  # cambio de año
        (date(2026, 3, 2), date(2026, 2, 1)),  # febrero corto
    ],
)
def test_procesa_el_mes_anterior_a_la_ejecucion(ejecucion, periodo):
    assert ultimo_mes_cerrado(ejecucion) == periodo


def test_periodo_es_el_dia_1_de_un_mes():
    assert validar_periodo("2026-10-01") == date(2026, 10, 1)
    with pytest.raises(ValueError):
        validar_periodo("2026-10-26")
