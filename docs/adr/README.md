# Architecture Decision Records

Formato: contexto → decisión → alternativas → consecuencias. Un ADR **no se edita** después de aceptado. Si la decisión cambia, se crea uno nuevo que lo reemplaza (`Reemplaza a: 000X`).

| # | Decisión | Estado |
|---|---|---|
| [0001](0001-on-premise.md) | Despliegue on-premise | Aceptado |
| [0002](0002-docker-compose-dockeroperator-proxy.md) | Docker Compose + DockerOperator + proxy del socket | Aceptado |
| [0003](0003-postgresql-unico-motor.md) | PostgreSQL como único motor (db_airflow, db_mlflow) | Aceptado |
| [0004](0004-mlflow-proxy-artefactos.md) | MLflow como proxy de artefactos | Aceptado (la tercera consecuencia la reemplaza el 0015) |
| [0005](0005-ingesta-odoo-api.md) | Ingesta de Odoo por API | **Propuesto**: falta versión de Odoo |
| [0006](0006-delta-lake-sin-dvc.md) | Versionado de datos con Delta Lake, sin DVC | Aceptado |
| [0011](0011-interfaz-contenedor-unico.md) | Interfaz de consulta en un único contenedor, desacoplada por archivos | Aceptado |
| [0012](0012-acceso-sin-autenticacion-segmentacion.md) | Acceso sin autenticación por segmentación de red, y retiro del SMB | Aceptado |
| [0013](0013-vistas-documentadas-con-diagrama.md) | Vistas de arquitectura que se documentan con diagrama | Aceptado |
| [0014](0014-calendario-horizonte.md) | Calendario de ejecución y horizonte de predicción | **Propuesto**: falta la fecha límite de pedido de Lojagas |
| [0015](0015-segmentacion-red.md) | Segmentación de red de la plataforma | Aceptado |

## Pendientes (ya comprometidos en la tesis)

- 0007: política de promoción de modelos (manual o automática). Mientras no exista, la promoción es **manual**.
- 0008: umbrales de monitoreo de degradación (qué WAPE dispara el reentrenamiento).
- 0009: mecanismo de entrada para validar cuotas (archivo manual o API).
- 0010: escenario ad hoc. Definir si existe y en qué forma (issue de I-03, etiqueta `tesis`).
