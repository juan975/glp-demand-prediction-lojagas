"""DAG de humo de la plataforma.

Comprueba, sin tocar datos reales, que Airflow lanza un contenedor de trabajo
a través del proxy, que ese contenedor monta el Lakehouse del host y que
alcanza MLflow por la red interna. Se ejecuta solo a mano.
"""

from __future__ import annotations

import pendulum
from _comun import DOCKER_URL, IMAGE_TAG, MOUNT_LAKEHOUSE, NETWORK
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.sdk import DAG

SCRIPT = """
import os, urllib.request
ruta = "/data/lakehouse/raw/_prueba_humo.txt"
with open(ruta, "w") as f:
    f.write(os.environ["LOJAGAS_RUN_ID"])
leido = open(ruta).read()
os.remove(ruta)
print("uid:", os.getuid(), "| escritura y lectura en Raw:", leido == os.environ["LOJAGAS_RUN_ID"])
salud = urllib.request.urlopen("http://mlflow:5000/health", timeout=10).read().decode()
print("mlflow /health:", salud)
"""

with DAG(
    dag_id="prueba_humo",
    schedule=None,
    start_date=pendulum.datetime(2026, 11, 1, tz="America/Guayaquil"),
    catchup=False,
    tags=["plataforma"],
):
    DockerOperator(
        task_id="contenedor_lakehouse_mlflow",
        image=f"lojagas/procesamiento:{IMAGE_TAG}",
        entrypoint=["python", "-c"],
        command=[SCRIPT],
        docker_url=DOCKER_URL,
        network_mode=NETWORK,
        mounts=[MOUNT_LAKEHOUSE],
        environment={"LOJAGAS_RUN_ID": "{{ run_id }}"},
        mount_tmp_dir=False,
        auto_remove="success",
    )
