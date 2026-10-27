#!/bin/bash
# Se ejecuta solo la primera vez (carpeta postgres_data vacía).
# Un motor, dos bases separadas con usuarios propios (mínimo privilegio).
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-SQL
    CREATE ROLE airflow LOGIN PASSWORD '${AIRFLOW_DB_PASSWORD}';
    CREATE DATABASE db_airflow OWNER airflow;
    CREATE ROLE mlflow LOGIN PASSWORD '${MLFLOW_DB_PASSWORD}';
    CREATE DATABASE db_mlflow OWNER mlflow;
SQL
