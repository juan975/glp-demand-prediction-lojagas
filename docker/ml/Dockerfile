FROM python:3.11-slim

ARG GIT_SHA=dev
ENV LOJAGAS_GIT_SHA=${GIT_SHA} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# libgomp: requerido por LightGBM/XGBoost
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY referencias ./referencias

# El servidor no tiene GPU: torch CPU evita ~2 GB de librerías CUDA
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir ".[ml]"

RUN useradd --create-home lojagas
USER lojagas

ENTRYPOINT ["lojagas"]
