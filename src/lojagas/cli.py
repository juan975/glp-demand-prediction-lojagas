"""Entrypoint `lojagas <subcomando>`. Es lo único que Airflow invoca en los contenedores.

Cada subcomando corresponde a un artefacto de Despliegue_v3:
    Contenedor Ingesta        → ingesta-odoo, ingesta-externas   (ingesta.py)
    Contenedor Procesamiento  → curacion                         (curacion.py)
                              → ingenieria-caracteristicas       (ingenieria_caracteristicas.py)
    Contenedor ML             → entrenar                         (pipeline_entrenamiento.py)
                              → evaluar                          (evaluacion.py)
                              → predecir                         (predictor.py)
                              → generar-reportes                 (generar_reportes.py)
"""

from __future__ import annotations

import argparse
import json
import sys


def _ingesta_odoo(cfg, a):
    from lojagas.ingesta.ingesta import ejecutar_odoo

    return ejecutar_odoo(cfg, a.periodo)


def _ingesta_externas(cfg, a):
    from lojagas.ingesta.ingesta import ejecutar_externas

    return ejecutar_externas(cfg, a.periodo)


def _curacion(cfg, a):
    from lojagas.procesamiento.curacion import ejecutar

    return ejecutar(cfg)


def _ingenieria(cfg, a):
    from lojagas.procesamiento.ingenieria_caracteristicas import ejecutar

    return ejecutar(cfg)


def _pendiente(cfg, a):
    raise NotImplementedError(f"'{a.comando}' aún no implementado")


# Importaciones diferidas: cada imagen Docker solo instala las dependencias de su contenedor
SUBCOMANDOS = {
    "ingesta-odoo": ("Odoo API → Raw", _ingesta_odoo),
    "ingesta-externas": ("Fuentes externas → Raw", _ingesta_externas),
    "curacion": ("Raw → Curated", _curacion),
    "ingenieria-caracteristicas": ("Curated → Feature", _ingenieria),
    "entrenar": ("Walk-forward de candidatos → MLflow Tracking", _pendiente),
    "evaluar": ("Selección + SHAP → Model Registry (alias candidato)", _pendiente),
    "predecir": ("Model Registry → zona Predicciones", _pendiente),
    "generar-reportes": ("Predicciones → Excel/PDF en reportes/", _pendiente),
}


def main(argv: list[str] | None = None) -> int:
    from lojagas.comun.config import cargar

    parser = argparse.ArgumentParser(prog="lojagas")
    sub = parser.add_subparsers(dest="comando", required=True)
    for nombre, (ayuda, _) in SUBCOMANDOS.items():
        p = sub.add_parser(nombre, help=ayuda)
        p.add_argument("--periodo", help="Primer día del mes procesado (YYYY-MM-DD)")
    args = parser.parse_args(argv)

    try:
        resultado = SUBCOMANDOS[args.comando][1](cargar(), args)
    except NotImplementedError as e:
        print(f"[lojagas] {e}", file=sys.stderr)
        return 2
    # Airflow muestra esta línea en el log: versiones Delta escritas → linaje
    print(json.dumps({"comando": args.comando, "resultado": resultado}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
