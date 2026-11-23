"""Feriados nacionales como variable: conteo por mes, días de venta y años sin calendario."""

import numpy as np
import pandas as pd

from lojagas.ingesta.externas.calendario import CalendarioEventos
from lojagas.procesamiento.eventos import TIPO_FERIADO, dias_de_eventos, dias_feriado
from lojagas.procesamiento.ingenieria_caracteristicas import construir


def test_dias_feriado_cuenta_y_deja_vacios_los_anios_sin_calendario():
    meses = pd.Series(pd.to_datetime(["2024-02-01", "2024-06-01", "2027-02-01"]))
    dias = dias_feriado(meses, CalendarioEventos().extraer())
    assert dias.iloc[:2].tolist() == [2, 0]  # Carnaval; junio sin feriados
    assert np.isnan(dias.iloc[2])  # 2027 todavía no está en el calendario: no es 0


def test_dias_de_eventos_expande_los_rangos():
    feriados = dias_de_eventos(CalendarioEventos().extraer(), TIPO_FERIADO)
    assert {pd.Timestamp("2024-02-12"), pd.Timestamp("2024-02-13")} <= set(feriados)
    # 10 feriados por año, y Carnaval son dos días: 11 días × 4 años
    assert len(feriados) == 44


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
