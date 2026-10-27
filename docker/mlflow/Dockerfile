FROM python:3.11-slim

# >=3.10 corrige CVE-2026-2652 (rutas FastAPI sin autenticación)
RUN pip install --no-cache-dir "mlflow>=3.10,<4" "psycopg2-binary>=2.9"

EXPOSE 5000

# --serve-artifacts: MLflow actúa como proxy de artefactos (el contenedor ML no monta mlruns/)
# --allowed-hosts: desde MLflow 3.5 se valida el Host; "mlflow" no es IP privada y se rechazaría
CMD mlflow server \
    --backend-store-uri "${MLFLOW_BACKEND_URI}" \
    --artifacts-destination /mlruns \
    --serve-artifacts \
    --host 0.0.0.0 --port 5000 \
    --allowed-hosts "mlflow:5000,localhost:*,127.0.0.1:*"
