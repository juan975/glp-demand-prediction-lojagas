"""ERA5-Land sin internet: la descarga se reemplaza por un NetCDF falso con valores conocidos."""

import numpy as np
import pandas as pd
import pytest

xr = pytest.importorskip("xarray")

from lojagas.ingesta.externas.era5_land import ERA5Land, a_unidades, solicitud_cds  # noqa: E402

FECHAS = pd.to_datetime(["2024-11-01", "2024-12-01", "2025-01-01"])


def _netcdf_falso(destino, t2m=293.15, d2m=283.15, tp=0.005, mes_sin_publicar=True):
    """2 × 2 píxeles y 3 meses. El último mes llega vacío, como los que CDS aún no publica."""
    forma = (len(FECHAS), 2, 2)
    datos = {v: np.full(forma, val) for v, val in (("t2m", t2m), ("d2m", d2m), ("tp", tp))}
    if mes_sin_publicar:
        for v in datos.values():
            v[-1] = np.nan
    xr.Dataset(
        {v: (("valid_time", "latitude", "longitude"), arr) for v, arr in datos.items()},
        coords={"valid_time": FECHAS, "latitude": [-4.0, -4.1], "longitude": [-79.2, -79.1]},
    ).to_netcdf(destino)


def test_solicitud_pide_todos_los_meses_del_rango():
    s = solicitud_cds([-3.3, -80.6, -4.9, -79.0], [2023, 2024])
    assert s["year"] == ["2023", "2024"]
    assert len(s["month"]) == 12
    assert s["area"] == [-3.3, -80.6, -4.9, -79.0]


def test_extraer_una_fila_por_mes_y_pixel_sin_meses_vacios():
    solicitudes = []

    def descargador(solicitud, destino):
        solicitudes.append(solicitud)
        _netcdf_falso(destino)

    df = ERA5Land(descargador=descargador, anio_inicio=2024).extraer("2025-01-01")

    assert len(solicitudes) == 2  # una por provincia
    assert solicitudes[0]["year"] == ["2024", "2025"]
    # 2 provincias × 2 meses publicados × 4 píxeles; enero (sin publicar) se descarta
    assert len(df) == 2 * 2 * 4
    assert set(df["provincia_area"]) == {"LOJA", "ZAMORA CHINCHIPE"}
    assert df["fecha"].max() == pd.Timestamp("2024-12-01")
    assert df["t2m"].iloc[0] == pytest.approx(293.15)  # Raw conserva las unidades de CDS


def test_conversion_de_unidades():
    df = pd.DataFrame(
        {
            "fecha": pd.to_datetime(["2024-11-01", "2024-12-01"]),
            "t2m": [293.15, 293.15],
            "d2m": [293.15, 283.15],
            "tp": [0.005, 0.005],
        }
    )
    out = a_unidades(df)
    assert out["temp_media_c"].tolist() == pytest.approx([20.0, 20.0])
    # 0.005 m/día × 1000 × días del mes: noviembre 30, diciembre 31
    assert out["precip_mm"].tolist() == pytest.approx([150.0, 155.0])
    # Punto de rocío igual a la temperatura = aire saturado
    assert out["humedad_rel_pct"].iloc[0] == pytest.approx(100.0)
    assert 50 < out["humedad_rel_pct"].iloc[1] < 60


def test_declara_latencia_del_preliminar():
    # Se usa hasta el último mes completo (preliminar): menos de un mes de latencia
    assert 0 < ERA5Land.disponible_desde_dias < 28
