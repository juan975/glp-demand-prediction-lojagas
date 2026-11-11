"""generar_reportes.py — zona Predicciones → reportes/ y resumen de métricas.

Último paso del flujo mensual. Produce dos cosas:

1. **Los reportes** en Excel y PDF, que se depositan en `reportes/`. Contenido mínimo
   (sección 3.5 del TIC): predicción por segmento, error esperado, importancia de
   variables y versión del modelo. Los filtros por segmento y por período se resuelven
   como hojas y autofiltros del Excel.

2. **El resumen del modelo vigente**, que se escribe como una tabla más de la zona
   Predicciones. Es lo que lee el tablero de consulta para mostrar las métricas sin
   tener que consultar MLflow por HTTP, y es la razón por la que el contenedor de la
   interfaz no necesita conexión de red hacia ningún otro contenedor (ADR-0011).

   Columnas del resumen: `version_modelo`, `alias`, `fecha_entrenamiento`, `mape`,
   `mae`, `rmse`, `r2`, `mejora_sobre_ingenuo` y `periodo_evaluado`.

Lo que sale de aquí lo consume el área de planificación, así que **todo va agregado por
segmento y por mes**. Nada a nivel de cliente: el tablero no exige autenticación y esa
decisión (ADR-0012) solo se sostiene mientras esta condición se cumpla.

Vive en el contenedor de ML aun cuando no usa el modelo. El porqué, y el costo que eso
tiene, están en `docs/arquitectura/06-vista-despliegue/README.md`.
"""

from __future__ import annotations

from lojagas.comun.config import Config

TABLA_METRICAS = "metricas_modelo_vigente"


def ejecutar(cfg: Config, periodo: str) -> list[str]:
    """Genera los reportes del período y devuelve las rutas de los archivos escritos."""
    raise NotImplementedError("Excel con openpyxl y PDF con fpdf2")


def escribir_resumen_metricas(cfg: Config, periodo: str) -> int:
    """Deja el resumen del modelo vigente en la zona Predicciones.

    Devuelve la versión Delta resultante. Se ejecuta siempre al final de `ejecutar`,
    incluso si la generación de un formato falla: si el tablero se queda sin este
    resumen, muestra métricas de un mes anterior sin avisar, que es peor que no
    mostrarlas.
    """
    raise NotImplementedError(f"escribir {TABLA_METRICAS} en la zona predicciones")
