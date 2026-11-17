# Valor por defecto = el de .env: sin .env la imagen base sigue siendo válida
ARG AIRFLOW_VERSION=3.3.2
FROM apache/airflow:${AIRFLOW_VERSION}-python3.11
# Un ARG declarado antes de FROM no es visible después: se vuelve a declarar
ARG AIRFLOW_VERSION

# Solo lo que necesitan los DAGs. La lógica de negocio NO se instala aquí:
# vive en las imágenes ingesta/ml y Airflow solo las orquesta.
# Las restricciones oficiales de Airflow fijan la versión de cada paquete para esta
# versión de Airflow y Python 3.11: cumplen aquí el papel de uv.lock.
RUN pip install --no-cache-dir \
    "apache-airflow==${AIRFLOW_VERSION}" \
    apache-airflow-providers-docker \
    apache-airflow-providers-fab \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-3.11.txt"
