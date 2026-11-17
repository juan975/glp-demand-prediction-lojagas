FROM python:3.11.18-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

# libgomp: requerido por LightGBM/XGBoost
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# Versiones exactas de uv.lock: el contenedor corre las mismas librerías que pasaron los tests.
# --locked falla si uv.lock no coincide con pyproject.toml, en vez de resolver otras versiones.
# Sin el extra "lstm": torch aún no se usa, y en uv.lock viene con CUDA (~2 GB) porque se
# resolvió desde PyPI. Al implementar la LSTM, declarar el índice CPU de PyTorch en
# [tool.uv.sources], volver a generar el lock y agregar --extra lstm aquí.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --locked --no-dev --extra ml --no-install-project
COPY src ./src
COPY referencias ./referencias
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --locked --no-dev --extra ml --no-editable

# Al final: cambia en cada commit y no debe invalidar la capa de dependencias
ARG GIT_SHA=dev
ENV LOJAGAS_GIT_SHA=${GIT_SHA}

RUN useradd --create-home lojagas
USER lojagas

ENTRYPOINT ["lojagas"]
