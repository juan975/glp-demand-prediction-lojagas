FROM python:3.11-slim

ARG GIT_SHA=dev
ENV LOJAGAS_GIT_SHA=${GIT_SHA} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY referencias ./referencias
RUN pip install --no-cache-dir ".[ingesta]"

# Usuario sin privilegios
RUN useradd --create-home lojagas
USER lojagas

ENTRYPOINT ["lojagas"]
