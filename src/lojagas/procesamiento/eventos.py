from __future__ import annotations

import pandas as pd


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
