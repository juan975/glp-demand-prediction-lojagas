FROM python:3.11-slim

ARG GIT_SHA=dev
ENV LOJAGAS_GIT_SHA=${GIT_SHA} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src

# Sin scikit-learn, sin torch, sin cliente de MLflow ni de PostgreSQL: este contenedor
# solo lee archivos. Mantenerlo liviano importa porque es el único que queda encendido.
RUN pip install --no-cache-dir ".[interfaz]"

RUN useradd --create-home lojagas
USER lojagas

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/salud')"

CMD ["uvicorn", "lojagas.interfaz.app:app", "--host", "0.0.0.0", "--port", "8000"]
