# Architecture Decision Records

Formato: contexto → decisión → alternativas → consecuencias. Un ADR **no se edita** después de aceptado. Si la decisión cambia, se crea uno nuevo que lo reemplaza (`Reemplaza a: 000X`).

| # | Decisión | Estado |
|---|---|---|
| [0001](0001-on-premise.md) | Despliegue on-premise | Aceptado |
| [0002](0002-docker-compose-dockeroperator-proxy.md) | Docker Compose + DockerOperator + proxy del socket | Aceptado (faltaba documentarlo) |
| [0003](0003-postgresql-unico-motor.md) | PostgreSQL como único motor (db_airflow, db_mlflow) | Aceptado |
| [0004](0004-mlflow-proxy-artefactos.md) | MLflow como proxy de artefactos | Aceptado |
| [0005](0005-ingesta-odoo-api.md) | Ingesta de Odoo por API | **Propuesto**: falta versión de Odoo |
| [0006](0006-delta-lake-sin-dvc.md) | Versionado de datos con Delta Lake, sin DVC | **Propuesto** |

## Pendientes (ya comprometidos en la tesis)

- 0007: política de promoción de modelos (manual o automática). Mientras no exista, la promoción es **manual**.
- 0008: umbrales de monitoreo de degradación (qué WAPE dispara el reentrenamiento).
- 0009: mecanismo de entrada para validar cuotas (archivo manual o API).
- 0010: escenario ad hoc. Definir si existe y en qué forma (ver `docs/inconsistencias.md`, I-03).
