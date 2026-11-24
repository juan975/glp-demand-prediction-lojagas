"""Precios al productor por provincia (MAG): selección de series, validación y lectura del CSV."""

from datetime import date

import pandas as pd
import pytest

from lojagas.ingesta.externas.precios_mag import (
    RUTA,
    PreciosProductorMAG,
    huecos,
    seleccionar,
    validar,
)

MAIZ = "Maíz duro seco (Quintal aprox. 100 Libra)"


def _crudo(filas):
    return pd.DataFrame(
        filas,
        columns=[
            "provincia",
            "anio",
            "mes",
            "producto",
            "precio_usd",
            "precio_mes_anterior",
            "precio_anio_anterior",
        ],
    )


def test_seleccionar_solo_series_elegidas():
    crudo = _crudo(
        [
            ("LOJA", 2023, 9, MAIZ, 13.8155, 15.47, 21.5),
            ("LOJA", 2023, 9, "Cebolla colorada (Quintal aprox. 100 Libra)", 33.6, None, None),
            ("LOJA", 2023, 9, "Café (Saco aprox. 120 Libra)", 180, None, None),  # otra presentación
            ("ZAMORA CHINCHIPE", 2023, 9, "Cacao (Quintal aprox. 100 Libra)", 119.48, None, None),
            ("ZAMORA CHINCHIPE", 2023, 9, "Café (Bulto aprox. 125 Libra)", 175, None, None),
        ]
    )
    df = seleccionar(crudo)
    assert list(zip(df["provincia"], df["producto"], strict=True)) == [
        ("LOJA", "maiz_duro_seco"),
        ("ZAMORA CHINCHIPE", "cacao"),
    ]
    assert df["mes"].tolist() == [pd.Timestamp("2023-09-01")] * 2
    assert df["presentacion"].iloc[0] == MAIZ


def test_seleccionar_descarta_precio_vacio():
    crudo = _crudo([("LOJA", 2024, 1, MAIZ, None, None, None)])
    assert seleccionar(crudo).empty


def _referencia(filas):
    return pd.DataFrame(
        [
            {
                "mes": pd.Timestamp(m),
                "provincia": p,
                "producto": c,
                "presentacion": "x",
                "precio_usd": v,
                "fuente_url": "u",
            }
            for m, p, c, v in filas
        ]
    )


def test_validar_rechaza_repetidos_y_ceros():
    with pytest.raises(ValueError, match="repetidos"):
        validar(_referencia([("2024-03-01", "LOJA", "arroz", 45)] * 2))
    for precio in (0, -1, None):  # None queda como celda vacía (NaN)
        with pytest.raises(ValueError, match="vacíos, en cero"):
            validar(_referencia([("2024-03-01", "LOJA", "arroz", precio)]))
    with pytest.raises(ValueError, match="no esperadas"):
        validar(_referencia([("2024-03-01", "LOJA", "cacao", 100)]))


def test_huecos_por_serie():
    df = _referencia(
        [
            ("2024-01-01", "LOJA", "arroz", 45),
            ("2024-03-01", "LOJA", "arroz", 45),
            ("2024-01-01", "LOJA", "maiz_duro_seco", 19),
            ("2024-02-01", "LOJA", "maiz_duro_seco", 19),
            ("2024-03-01", "LOJA", "maiz_duro_seco", 19),
        ]
    )
    assert huecos(df, date(2024, 1, 1), date(2024, 3, 1)) == {"LOJA/arroz": ["2024-02"]}


def test_extraer_corta_en_el_periodo(tmp_path):
    ruta = tmp_path / "p.csv"
    _referencia(
        [
            ("2026-08-01", "LOJA", "arroz", 29.07),
            ("2026-09-01", "LOJA", "arroz", 34.2),
            ("2026-10-01", "LOJA", "arroz", 45.86),
        ]
    ).to_csv(ruta, index=False)
    df = PreciosProductorMAG(ruta=ruta).extraer("2026-09-01")
    assert df["mes"].max() == pd.Timestamp("2026-09-01")
    assert len(df) == 2


def test_csv_versionado_es_valido():
    df = pd.read_csv(RUTA, parse_dates=["mes"])
    validar(df)
    loja = df[(df["provincia"] == "LOJA") & (df["mes"] == "2023-09-01")].set_index("producto")
    # Valores visibles en el tablero (Loja, septiembre 2023)
    assert loja.loc["maiz_duro_seco", "precio_usd"] == pytest.approx(13.82, abs=0.01)
    assert loja.loc["arroz", "precio_usd"] == pytest.approx(45.23, abs=0.01)
    assert loja.loc["cafe", "precio_usd"] == pytest.approx(170.08, abs=0.01)
