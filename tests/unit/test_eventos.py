import pandas as pd

from lojagas.ingesta.externas.calendario import CalendarioEventos
from lojagas.procesamiento.eventos import dias_evento_en_mes


def test_romeria_cubre_agosto_parcial_y_noviembre_un_dia():
    eventos = CalendarioEventos().extraer()
    meses = pd.Series(pd.to_datetime(["2024-08-01", "2024-09-01", "2024-11-01", "2024-12-01"]))
    dias = dias_evento_en_mes(meses, eventos, "religioso").tolist()
    assert dias == [15, 30, 1, 0]
