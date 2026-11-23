"""Fábrica de tareas DockerOperator compartida por los DAGs.

Airflow no ejecuta lógica de negocio: lanza las imágenes ingesta/ml con un
subcomando de `lojagas` (ver src/lojagas/cli.py).
"""

from __future__ import annotations

import os

from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

DATA_ROOT = os.environ["LOJAGAS_DATA_ROOT"]  # ruta en el HOST, no en el contenedor Airflow
IMAGE_TAG = os.environ.get("LOJAGAS_IMAGE_TAG", "dev")
DOCKER_URL = os.environ.get("LOJAGAS_DOCKER_URL", "tcp://docker-proxy:2375")
NETWORK = os.environ.get("LOJAGAS_NETWORK", "lojagas_net")

# Los bind mounts se resuelven en el host: source debe ser una ruta del servidor
MOUNT_LAKEHOUSE = Mount(source=f"{DATA_ROOT}/lakehouse", target="/data/lakehouse", type="bind")
MOUNT_REPORTES = Mount(source=f"{DATA_ROOT}/reportes", target="/data/reportes", type="bind")

ENV_COMUN = {
    "LOJAGAS_LAKEHOUSE": "/data/lakehouse",
    "LOJAGAS_REPORTES": "/data/reportes",
    "MLFLOW_TRACKING_URI": "http://mlflow:5000",
    "LOJAGAS_IMAGE_TAG": IMAGE_TAG,
}

# Día en que corre el DAG; el CLI deduce el mes cerrado (lojagas.comun.periodos).
# `params.fecha_ejecucion` permite simular o reprocesar una corrida desde la UI.
FECHA_EJECUCION = "{{ params.fecha_ejecucion or ds }}"

SECRETOS_ODOO = ("ODOO_URL", "ODOO_DB", "ODOO_API_KEY")
SECRETO_PII = ("LOJAGAS_PII_SALT",)
SECRETOS_CDS = ("CDSAPI_URL", "CDSAPI_KEY")  # ERA5-Land (Copernicus)


def tarea(
    task_id: str,
    imagen: str,
    comando: list[str],
    secretos: tuple[str, ...] = (),
    **kwargs,
) -> DockerOperator:
    """Crea una tarea que corre `lojagas <comando>` en la imagen indicada.

    Cada tarea recibe solo los secretos que usa (R12): la API de Odoo, la ingesta;
    la clave de Copernicus, la ingesta externa;
    la sal de PII, la curación. El resto no ve ninguno.
    """
    return DockerOperator(
        task_id=task_id,
        image=f"lojagas/{imagen}:{IMAGE_TAG}",
        command=comando,
        docker_url=DOCKER_URL,
        network_mode=NETWORK,
        mounts=[MOUNT_LAKEHOUSE, MOUNT_REPORTES],
        environment={**ENV_COMUN, "LOJAGAS_RUN_ID": "{{ run_id }}"},
        private_environment={k: os.environ.get(k, "") for k in secretos},  # no salen en la UI
        mount_tmp_dir=False,  # con el proxy, la carpeta temporal de Airflow no existe en el host
        auto_remove="success",
        do_xcom_push=False,  # C-08 (R11): nada de la salida del contenedor llega a db_airflow
        **kwargs,
    )
