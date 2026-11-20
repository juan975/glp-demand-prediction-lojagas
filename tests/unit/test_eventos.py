import pandas as pd

from lojagas.ingesta.externas.calendario import CalendarioEventos
from lojagas.procesamiento.eventos import dias_evento_en_mes


def test_romeria_cubre_agosto_parcial_y_noviembre_un_dia():
    eventos = CalendarioEventos().extraer()
    meses = pd.Series(pd.to_datetime(["2024-08-01", "2024-09-01", "2024-11-01", "2024-12-01"]))
    dias = dias_evento_en_mes(meses, eventos, "religioso").tolist()
    assert dias == [15, 30, 1, 0]


def test_feriados_nacionales_cuentan_dias_de_descanso():
    eventos = CalendarioEventos().extraer()
    meses = pd.Series(pd.to_datetime(["2024-02-01", "2024-06-01", "2024-11-01", "2025-11-01"]))
    dias = dias_evento_en_mes(meses, eventos, "feriado_nacional").tolist()
    # Carnaval (12 y 13 feb), ninguno en junio, Difuntos y Cuenca trasladados (1 y 4 nov; 3 y 4 nov)
    assert dias == [2, 0, 2, 2]


def test_diez_feriados_nacionales_por_anio():
    eventos = CalendarioEventos().extraer()
    feriados = eventos[eventos["tipo_evento"] == "feriado_nacional"]
    por_anio = feriados["fecha_inicio"].dt.year.value_counts()
    assert (por_anio == 10).all(), por_anio.to_dict()
