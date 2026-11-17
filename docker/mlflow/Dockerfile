FROM python:3.11.18-slim-trixie

# >=3.10 corrige CVE-2026-2652 (rutas FastAPI sin autenticación).
# Versiones exactas: mlflow igual al del extra "ml" de uv.lock (cliente y servidor coinciden).
# pip avisa que corre como root: dentro de una imagen es inofensivo.
RUN pip install --no-cache-dir "mlflow==3.18.0" "psycopg2-binary==2.9.13"

EXPOSE 5000

# --serve-artifacts: MLflow actúa como proxy de artefactos (el contenedor ML no monta mlruns/)
# --allowed-hosts: desde MLflow 3.5 se valida el Host; "mlflow" no es IP privada y se rechazaría
# sh -c para expandir MLFLOW_BACKEND_URI; exec deja a mlflow como PID 1 y recibe las señales
CMD ["sh", "-c", "exec mlflow server \
    --backend-store-uri \"$MLFLOW_BACKEND_URI\" \
    --artifacts-destination /mlruns \
    --serve-artifacts \
    --host 0.0.0.0 --port 5000 \
    --allowed-hosts 'mlflow:5000,localhost:*,127.0.0.1:*'"]
