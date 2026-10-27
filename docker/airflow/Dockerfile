ARG AIRFLOW_VERSION
FROM apache/airflow:${AIRFLOW_VERSION}-python3.11
# Un ARG declarado antes de FROM no es visible después: se vuelve a declarar
ARG AIRFLOW_VERSION

# Solo lo que necesitan los DAGs. La lógica de negocio NO se instala aquí:
# vive en las imágenes ingesta/ml y Airflow solo las orquesta.
RUN pip install --no-cache-dir \
    "apache-airflow==${AIRFLOW_VERSION}" \
    apache-airflow-providers-docker \
    apache-airflow-providers-fab
