from __future__ import annotations

import pandas as pd

TIPO_FERIADO = "feriado_nacional"


def dias_evento_en_mes(meses: pd.Series, eventos: pd.DataFrame, tipo: str) -> pd.Series:
    """Días del mes cubiertos por eventos de un tipo (p. ej., Romería: 17-ago a 1-nov).

    Mejor que un binario "hay evento": la Romería ocupa parcialmente agosto y noviembre.
    """
    ev = eventos[eventos["tipo_evento"] == tipo]
    resultado = []
    for inicio_mes in pd.to_datetime(meses):
        fin_mes = inicio_mes + pd.offsets.MonthEnd(0)
        dias = 0
        for _, e in ev.iterrows():
            ini = max(inicio_mes, e["fecha_inicio"])
            fin = min(fin_mes, e["fecha_fin"])
            if fin >= ini:
                dias += (fin - ini).days + 1
        resultado.append(dias)
    return pd.Series(resultado, index=meses.index, name=f"dias_{tipo}")


def dias_de_eventos(eventos: pd.DataFrame, tipo: str) -> pd.DatetimeIndex:
    """Cada día cubierto por los eventos de un tipo."""
    ev = eventos[eventos["tipo_evento"] == tipo]
    dias = {
        d
        for i, f in zip(ev["fecha_inicio"], ev["fecha_fin"], strict=True)
        for d in pd.date_range(i, f)
    }
    return pd.DatetimeIndex(sorted(dias))


def anios_con_eventos(eventos: pd.DataFrame, tipo: str) -> set[int]:
    ev = eventos[eventos["tipo_evento"] == tipo]
    return set(pd.to_datetime(ev["fecha_inicio"]).dt.year)


def dias_feriado(meses: pd.Series, eventos: pd.DataFrame) -> pd.Series:
    """Días de feriado nacional del mes; NaN en los años que el calendario todavía no tiene.

    Un año sin feriados cargados no es un año sin feriados: con 0, el modelo creería que ese
    febrero no tiene Carnaval.
    """
    dias = dias_evento_en_mes(meses, eventos, TIPO_FERIADO).astype(float)
    cubiertos = pd.to_datetime(meses).dt.year.isin(anios_con_eventos(eventos, TIPO_FERIADO))
    return dias.where(cubiertos).rename("dias_feriado")
