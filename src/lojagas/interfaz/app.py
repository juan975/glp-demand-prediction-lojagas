"""app.py — tablero de consulta de solo lectura (ADR-0011).

Backend y frontend en un mismo proceso: FastAPI resuelve el acceso a los resultados y
Jinja2 renderiza las vistas. No se separan en dos contenedores porque el servidor es
uno solo y la carga son unas pocas consultas al mes.

Se levanta con:
    uvicorn lojagas.interfaz.app:app --host 0.0.0.0 --port 8000

Lo que publica:
    GET /          tablero: demanda estimada por segmento y predicho frente a observado
    GET /reportes  listado de los Excel y PDF disponibles para descarga
    GET /salud     comprobación de vida, para el healthcheck del contenedor

Todo lo que entrega sale de dos rutas montadas en solo lectura. Si una de las dos no
está disponible, el tablero lo dice en pantalla en lugar de fallar: para el área de
planificación es más útil un aviso que una página en blanco.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from lojagas.comun import lakehouse
from lojagas.comun.config import Config, cargar

TABLA_PREDICCIONES = "demanda_mensual"
TABLA_METRICAS = "metricas_modelo_vigente"
PLANTILLAS = Path(__file__).parent / "plantillas"

app = FastAPI(title="Lojagas — tablero de predicción de demanda", docs_url=None, redoc_url=None)
plantillas = Jinja2Templates(directory=str(PLANTILLAS))


def leer_predicciones(cfg: Config) -> pd.DataFrame:
    """Predicciones del período vigente y de los meses ya cerrados, por segmento.

    Devuelve las columnas del contrato: periodo, segmento, cantidad_predicha y
    cantidad_observada, esta última nula mientras el mes no se haya cerrado.
    """
    raise NotImplementedError("leer de la zona predicciones con lakehouse.leer")


def leer_metricas(cfg: Config) -> dict:
    """Resumen del modelo vigente que deja `generar_reportes.py` al cerrar cada corrida.

    Es la alternativa a consultar MLflow por HTTP: así este contenedor no necesita
    ninguna conexión de red hacia los demás (ADR-0011).
    """
    raise NotImplementedError(f"leer la tabla {TABLA_METRICAS} de la zona predicciones")


def listar_reportes(cfg: Config) -> list[dict]:
    """Archivos disponibles en el volumen de reportes, del más reciente al más antiguo."""
    raise NotImplementedError("recorrer cfg.reportes y devolver nombre, período y tamaño")


@app.get("/salud")
def salud() -> JSONResponse:
    cfg = cargar()
    return JSONResponse(
        {
            "estado": "vivo",
            "predicciones": lakehouse.ruta_tabla(
                cfg.lakehouse, "predicciones", TABLA_PREDICCIONES
            ).exists(),
            "reportes": cfg.reportes.exists(),
        }
    )


@app.get("/", response_class=HTMLResponse)
def tablero(request: Request) -> HTMLResponse:
    cfg = cargar()
    return plantillas.TemplateResponse(
        request=request,
        name="tablero.html",
        context={"predicciones": leer_predicciones(cfg), "metricas": leer_metricas(cfg)},
    )


@app.get("/reportes", response_class=HTMLResponse)
def reportes(request: Request) -> HTMLResponse:
    cfg = cargar()
    return plantillas.TemplateResponse(
        request=request, name="reportes.html", context={"archivos": listar_reportes(cfg)}
    )
