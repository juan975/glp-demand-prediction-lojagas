FROM python:3.11.18-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
# Sin scikit-learn, sin torch, sin cliente de MLflow ni de PostgreSQL: este contenedor
# solo lee archivos. Mantenerlo liviano importa porque es el único que queda encendido.
# Versiones exactas de uv.lock (--locked falla si no coincide con pyproject.toml).
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --locked --no-dev --extra interfaz --no-install-project
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --locked --no-dev --extra interfaz --no-editable

# Al final: cambia en cada commit y no debe invalidar la capa de dependencias
ARG GIT_SHA=dev
ENV LOJAGAS_GIT_SHA=${GIT_SHA}

RUN useradd --create-home lojagas
USER lojagas

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/salud')"

CMD ["uvicorn", "lojagas.interfaz.app:app", "--host", "0.0.0.0", "--port", "8000"]
