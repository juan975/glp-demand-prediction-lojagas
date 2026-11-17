import pandas as pd
import pytest

from lojagas.comun import lakehouse as delta_io


def test_time_travel_recupera_version_anterior(tmp_path):
    v0 = delta_io.escribir(pd.DataFrame({"a": [1]}), tmp_path, "raw", "t")
    v1 = delta_io.escribir(pd.DataFrame({"a": [2]}), tmp_path, "raw", "t")
    assert (v0, v1) == (0, 1)
    assert delta_io.leer(tmp_path, "raw", "t", version=0)["a"].tolist() == [1]
    assert len(delta_io.leer(tmp_path, "raw", "t")) == 2


def _escribir_mes(raiz, periodo, valores):
    df = pd.DataFrame({"_periodo": periodo, "kg": valores})
    return delta_io.reemplazar_periodo(df, raiz, "raw", "t", "_periodo", periodo)


def test_reintentar_un_periodo_no_lo_duplica(tmp_path):
    _escribir_mes(tmp_path, "2026-09-01", [1.0, 2.0])
    _escribir_mes(tmp_path, "2026-10-01", [3.0])
    v = _escribir_mes(tmp_path, "2026-10-01", [4.0, 5.0])  # reintento con datos corregidos

    tabla = delta_io.leer(tmp_path, "raw", "t").sort_values("kg")
    assert tabla.groupby("_periodo")["kg"].sum().to_dict() == {"2026-09-01": 3.0, "2026-10-01": 9.0}
    assert delta_io.leer(tmp_path, "raw", "t", version=v - 1)["kg"].sum() == 6.0  # time travel


def test_reemplazar_periodo_rechaza_filas_de_otro_mes(tmp_path):
    df = pd.DataFrame({"_periodo": ["2026-10-01", "2026-09-01"], "kg": [1.0, 2.0]})
    with pytest.raises(ValueError):
        delta_io.reemplazar_periodo(df, tmp_path, "raw", "t", "_periodo", "2026-10-01")
