import pandas as pd
from dateutil.easter import easter

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


def _feriados():
    eventos = CalendarioEventos().extraer()
    return eventos[eventos["tipo_evento"] == "feriado_nacional"]


def test_carnaval_y_viernes_santo_siguen_a_la_pascua():
    # Reglas, no fechas copiadas del CSV: un error de digitación en el CSV sí se detecta
    feriados = _feriados()
    for _, f in feriados[feriados["nombre"] == "Carnaval"].iterrows():
        pascua = pd.Timestamp(easter(f["fecha_inicio"].year))
        assert f["fecha_inicio"] == pascua - pd.Timedelta(days=48), f["fecha_inicio"]
        assert f["fecha_fin"] == pascua - pd.Timedelta(days=47), f["fecha_fin"]
    for _, f in feriados[feriados["nombre"] == "Viernes Santo"].iterrows():
        pascua = pd.Timestamp(easter(f["fecha_inicio"].year))
        assert f["fecha_inicio"] == pascua - pd.Timedelta(days=2), f["fecha_inicio"]


def test_ningun_feriado_cae_en_domingo():
    # El sábado sí puede: desde el calendario 2026-2030, Año Nuevo, Navidad y el martes de
    # Carnaval no se trasladan (Navidad de 2027 cae sábado)
    feriados = _feriados()
    dias = pd.concat(
        [
            pd.Series(pd.date_range(i, f))
            for i, f in zip(feriados["fecha_inicio"], feriados["fecha_fin"], strict=True)
        ]
    )
    assert not (dias.dt.day_of_week == 6).any(), dias[dias.dt.day_of_week == 6].tolist()
