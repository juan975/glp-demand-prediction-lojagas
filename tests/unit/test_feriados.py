"""Feriados nacionales como variable: conteo por mes, días de venta y años sin calendario."""

import numpy as np
import pandas as pd

from lojagas.ingesta.externas.calendario import CalendarioEventos
from lojagas.procesamiento.eventos import TIPO_FERIADO, dias_de_eventos, dias_feriado
from lojagas.procesamiento.ingenieria_caracteristicas import construir


def _anios_con_feriados(eventos):
    feriados = eventos[eventos["tipo_evento"] == TIPO_FERIADO]
    return set(feriados["fecha_inicio"].dt.year)


def test_dias_feriado_cuenta_y_deja_vacios_los_anios_sin_calendario():
    eventos = CalendarioEventos().extraer()
    # El primer año que el calendario todavía no tiene: no se rompe al agregar un año nuevo
    sin_calendario = max(_anios_con_feriados(eventos)) + 1
    meses = pd.Series(pd.to_datetime(["2024-02-01", "2024-06-01", f"{sin_calendario}-02-01"]))
    dias = dias_feriado(meses, eventos)
    assert dias.iloc[:2].tolist() == [2, 0]  # Carnaval; junio sin feriados
    assert np.isnan(dias.iloc[2])  # año sin calendario: vacío, no 0


def test_dias_de_eventos_expande_los_rangos():
    eventos = CalendarioEventos().extraer()
    feriados = pd.Series(dias_de_eventos(eventos, TIPO_FERIADO))
    assert {pd.Timestamp("2024-02-12"), pd.Timestamp("2024-02-13")} <= set(feriados)
    # 10 feriados por año, y Carnaval son dos días: 11 días en cada año cargado
    por_anio = feriados.dt.year.value_counts()
    assert set(por_anio.index) == _anios_con_feriados(eventos)
    assert (por_anio == 11).all(), por_anio.to_dict()


def test_dias_de_venta_con_feriados(serie_mensual):
    segmentos = serie_mensual["segmento"].unique()
    pesos = pd.DataFrame(
        [(s, d, 0.0 if d == 6 else 1.0) for s in segmentos for d in range(7)],
        columns=["segmento", "dia_semana", "peso"],
    )
    df = construir(serie_mensual, CalendarioEventos().extraer(), horizonte=2, pesos=pesos)
    domestico = df[df["segmento"] == "domestico"].set_index("mes")

    # Febrero de 2024: 29 días, 4 domingos y Carnaval el lunes 12 y el martes 13
    assert domestico.loc["2024-02-01", "dias_venta"] == 25
    assert domestico.loc["2024-02-01", "dias_venta_feriados"] == 23
    assert domestico.loc["2024-02-01", "dias_feriado"] == 2
    # Diciembre de 2026 (fila futura): 4 domingos y Navidad el viernes 25
    assert domestico.loc["2026-12-01", "dias_venta"] == 27
    assert domestico.loc["2026-12-01", "dias_venta_feriados"] == 26
