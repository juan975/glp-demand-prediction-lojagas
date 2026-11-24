"""Precios de Petroecuador: CSV de referencias y lectura del texto de los PDF."""

from datetime import date

import pandas as pd
import pytest

from lojagas.ingesta.externas.petroecuador import (
    PreciosPetroecuador,
    huecos,
    leer_texto_pdf,
    resolver_superposiciones,
    validar,
)

# Fragmentos con el formato de los PDF reales: coma decimal y año solo al final (2026),
# punto decimal (2025) y año en las dos fechas cuando el período cruza de año (2023)
TEXTO_2026 = """PRECIOS DE VENTA EN TERMINAL PARA LAS COMERCIALIZADORAS
PERIODO DE VIGENCIA: DEL 12 DE MAYO AL 11 DE JUNIO DE 2026
PRECIO EN TERMINAL (Incluye el 15% del I.V.A.)
DIESEL PREMIUM INDUSTRIAL Galones $ 5,406379
GAS LICUADO DE PETROLEO (GLP) INDUSTRIAL Kilogramos $ 0,938916
GAS LICUADO DE PETROLEO (G.L.P.) AGRICOLA Kilogramos $ 0,193500"""

TEXTO_2025 = """PERIODO DE VIGENCIA: DEL 12 DE OCTUBRE AL 11 DE NOVIEMBRE DE 2025
(Incluye el 15% del I.V.A.)
DIESEL PREMIUM INDUSTRIAL Galones $ 2.988481
GAS LICUADO DE PETROLEO (GLP) INDUSTRIAL Kilogramos $ 0.829096"""

TEXTO_2023 = """PERIODO DE VIGENCIA: DEL 12 DE DICIEMBRE DE 2023 AL 11 DE ENERO DE 2024
(Incluye el 12% del I.V.A.)
DIESEL PREMIUM INDUSTRIAL Galones $ 3,411275
GAS LICUADO DE PETROLEO (GLP) INDUSTRIAL Kilogramos $ 0,783945"""


def _csv(filas):
    df = pd.DataFrame(
        filas,
        columns=[
            "vigencia_desde",
            "vigencia_hasta",
            "glp_industrial_usd_kg",
            "diesel_premium_industrial_usd_gal",
            "iva_pct",
            "fuente_url",
        ],
    )
    df[["vigencia_desde", "vigencia_hasta"]] = df[["vigencia_desde", "vigencia_hasta"]].apply(
        pd.to_datetime
    )
    return df


def test_lee_pdf_con_coma_decimal():
    fila = leer_texto_pdf(TEXTO_2026)
    assert fila["vigencia_desde"] == date(2026, 5, 12)
    assert fila["vigencia_hasta"] == date(2026, 6, 11)
    assert fila["glp_industrial_usd_kg"] == pytest.approx(0.938916)  # no el agrícola
    assert fila["diesel_premium_industrial_usd_gal"] == pytest.approx(5.406379)
    assert fila["iva_pct"] == 15


def test_lee_pdf_con_punto_decimal():
    fila = leer_texto_pdf(TEXTO_2025)
    assert fila["glp_industrial_usd_kg"] == pytest.approx(0.829096)
    assert fila["diesel_premium_industrial_usd_gal"] == pytest.approx(2.988481)


def test_periodo_que_cruza_de_anio():
    fila = leer_texto_pdf(TEXTO_2023)
    assert fila["vigencia_desde"] == date(2023, 12, 12)
    assert fila["vigencia_hasta"] == date(2024, 1, 11)
    assert fila["iva_pct"] == 12


def test_periodo_sin_mes_de_inicio():
    # Cambio de IVA de 2024: "DEL 01 AL 11 DE ABRIL DE 2024"
    fila = leer_texto_pdf(
        TEXTO_2023.replace(
            "DEL 12 DE DICIEMBRE DE 2023 AL 11 DE ENERO DE 2024", "DEL 01 AL 11 DE ABRIL DE 2024"
        )
    )
    assert fila["vigencia_desde"] == date(2024, 4, 1)
    assert fila["vigencia_hasta"] == date(2024, 4, 11)


def test_periodo_sin_de_despues_del_dia():
    fila = leer_texto_pdf(
        TEXTO_2023.replace(
            "DEL 12 DE DICIEMBRE DE 2023 AL 11 DE ENERO DE 2024",
            "DEL 12 ABRIL AL 11 DE MAYO DE 2024",
        )
    )
    assert fila["vigencia_desde"] == date(2024, 4, 12)
    assert fila["vigencia_hasta"] == date(2024, 5, 11)


def test_estructura_posterior_corta_a_la_anterior():
    df = _csv(
        [
            ("2024-04-01", "2024-04-11", 0.968961, 3.350808, 15, ""),  # IVA al 15 %
            ("2024-03-12", "2024-04-11", 0.943683, 3.263396, 12, ""),
            ("2024-04-12", "2024-05-11", 0.903335, 3.302647, 15, ""),
        ]
    )
    out = validar(resolver_superposiciones(df))
    assert out["vigencia_hasta"].dt.strftime("%Y-%m-%d").tolist() == [
        "2024-03-31",
        "2024-04-11",
        "2024-05-11",
    ]


def test_pdf_sin_precios_falla():
    with pytest.raises(ValueError):
        leer_texto_pdf("PERIODO DE VIGENCIA: DEL 08 AL 14 DE OCTUBRE DE 2026")


def test_validar_rechaza_periodos_superpuestos():
    df = _csv(
        [
            ("2026-05-12", "2026-06-11", 0.9, 5.4, 15, ""),
            ("2026-06-01", "2026-07-11", 0.9, 5.1, 15, ""),
        ]
    )
    with pytest.raises(ValueError, match="superponen"):
        validar(df)


@pytest.mark.parametrize("glp", [None, 0.0, -0.5])
def test_validar_rechaza_precio_vacio_cero_o_negativo(glp):
    df = _csv([("2026-05-12", "2026-06-11", glp, 5.4, 15, "")])
    with pytest.raises(ValueError, match="vacíos o no positivos"):
        validar(df)


def test_huecos_entre_periodos():
    df = _csv([("2026-05-12", "2026-06-11", 0.9, 5.4, 15, "")])
    assert huecos(df, "2026-05-01", "2026-06-30") == [
        (date(2026, 5, 1), date(2026, 5, 11)),
        (date(2026, 6, 12), date(2026, 6, 30)),
    ]


def test_periodo_irregular_a_mitad_de_mes_no_deja_hueco():
    # Como "Junio (2)" de 2024: una estructura nueva corta el período normal
    df = _csv(
        [
            ("2024-06-12", "2024-06-27", 0.9, 2.8, 15, ""),
            ("2024-06-28", "2024-07-11", 0.9, 2.7, 15, ""),
        ]
    )
    assert huecos(df, "2024-06-12", "2024-07-11") == []


def test_csv_del_repo_es_valido_y_se_recorta_en_el_periodo():
    df = PreciosPetroecuador().extraer("2026-05-01")
    assert len(df) > 0
    # El período que empieza el 12 de mayo ya rige en mayo; el de junio todavía no
    assert df["vigencia_desde"].max() == pd.Timestamp("2026-05-12")


def test_declara_disponibilidad():
    assert PreciosPetroecuador.disponible_desde_dias == 0
