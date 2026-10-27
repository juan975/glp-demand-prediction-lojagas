import pandas as pd

from lojagas.comun import lakehouse as delta_io


def test_time_travel_recupera_version_anterior(tmp_path):
    v0 = delta_io.escribir(pd.DataFrame({"a": [1]}), tmp_path, "raw", "t")
    v1 = delta_io.escribir(pd.DataFrame({"a": [2]}), tmp_path, "raw", "t")
    assert (v0, v1) == (0, 1)
    assert delta_io.leer(tmp_path, "raw", "t", version=0)["a"].tolist() == [1]
    assert len(delta_io.leer(tmp_path, "raw", "t")) == 2
