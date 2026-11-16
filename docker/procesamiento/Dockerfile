FROM python:3.11.18-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
# Versiones exactas de uv.lock: el contenedor corre las mismas librerías que pasaron los tests.
# --locked falla si uv.lock no coincide con pyproject.toml, en vez de resolver otras versiones.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --locked --no-dev --extra procesamiento --no-install-project
COPY src ./src
COPY referencias ./referencias
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --locked --no-dev --extra procesamiento --no-editable

# Al final: cambia en cada commit y no debe invalidar la capa de dependencias
ARG GIT_SHA=dev
ENV LOJAGAS_GIT_SHA=${GIT_SHA}

# Usuario sin privilegios
RUN useradd --create-home lojagas
USER lojagas

ENTRYPOINT ["lojagas"]
