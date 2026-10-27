# Tests de integración

Requieren `docker compose up -d` (PostgreSQL y MLflow). Se marcan con `@pytest.mark.integracion` y se corren con:

```bash
uv run pytest -m integracion
```

Pendientes: registro de un modelo en MLflow con alias `candidato`; DAG de punta a punta con datos sintéticos.
