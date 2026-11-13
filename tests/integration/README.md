# Tests de integración

Requieren `docker compose up -d` (PostgreSQL y MLflow) **con `compose.dev.yml`**: sin él, MLflow no publica su puerto y los tests no llegan desde el host (ADR-0015). Se marcan con `@pytest.mark.integracion` y se corren con:

```bash
uv run pytest -m integracion
```

Pendientes: registro de un modelo en MLflow con alias `candidato`; DAG de punta a punta con datos sintéticos.
