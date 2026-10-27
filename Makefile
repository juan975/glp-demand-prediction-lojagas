-include .env
export

GIT_SHA := $(shell git rev-parse --short HEAD 2>/dev/null || echo dev)

.PHONY: dirs build up down test lint dags-check

dirs:  ## Carpetas de datos fuera del repo (bind mounts)
	mkdir -p $(LOJAGAS_DATA_ROOT)/lakehouse/raw \
	         $(LOJAGAS_DATA_ROOT)/lakehouse/curated \
	         $(LOJAGAS_DATA_ROOT)/lakehouse/feature \
	         $(LOJAGAS_DATA_ROOT)/lakehouse/predicciones \
	         $(LOJAGAS_DATA_ROOT)/mlruns \
	         $(LOJAGAS_DATA_ROOT)/pg_data \
	         $(LOJAGAS_DATA_ROOT)/reportes

build:  ## Imágenes etiquetadas con el commit: trazabilidad código ↔ corrida
	LOJAGAS_IMAGE_TAG=$(GIT_SHA) docker compose --profile jobs build \
		--build-arg GIT_SHA=$(GIT_SHA)
	@echo "Actualiza LOJAGAS_IMAGE_TAG=$(GIT_SHA) en .env para que los DAGs usen esta versión"

up:
	docker compose up -d

down:
	docker compose down

test:
	uv run pytest --cov

lint:
	uv run ruff check . && uv run ruff format --check .

dags-check:  ## Valida sintaxis de DAGs sin instalar Airflow localmente
	python -m py_compile dags/*.py
