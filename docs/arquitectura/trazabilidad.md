# Trazabilidad arquitectura ↔ código

Esta tabla demuestra la correspondencia entre las vistas del 4+1 (ISO/IEC/IEEE 42010). Los nombres de archivo de **Despliegue_v3** existen literalmente en el código. Si una fila queda sin código o un archivo queda sin fila, hay una inconsistencia que se corrige en el mismo PR.

| Conceptual (DiseñoArquitectónico_v2) | Contenedor (Despliegue_v3) | Artefacto del diagrama → código | Tarea del DAG |
|---|---|---|---|
| Ingestión de datos | Ingesta | `ingesta.py` → `src/lojagas/ingesta/ingesta.py` (+ `odoo_api.py`, `externas/`) | `ingesta_odoo`, `ingesta_externas` |
| Zona Raw | `Data Lakehouse/Zona Raw/` | `comun/lakehouse.py` | — |
| (Módulo Tratamiento Datos) | Procesamiento | `curacion.py` → `procesamiento/curacion.py` | `curacion` |
| Zona Curated | `Data Lakehouse/Zona Curated/` | `comun/lakehouse.py` | — |
| (Módulo Tratamiento Datos) | Procesamiento | `ingenieria_caracteristicas.py` → `procesamiento/ingenieria_caracteristicas.py` | `ingenieria_caracteristicas` |
| Zona Feature | `Data Lakehouse/Zona Feature/` | `comun/lakehouse.py` | — |
| Motor ML: Entrenamiento | ML | `pipeline_entrenamiento.py` → `ml/pipeline_entrenamiento.py` | `pipeline_entrenamiento` |
| Motor ML: Evaluación | ML | `evaluacion.py` → `ml/evaluacion.py` (+ `walk_forward.py`, `metricas.py`) | `evaluacion` |
| Motor ML: Predictor | ML | `predictor.py` → `ml/predictor.py` | `predecir` |
| _(no existe en el conceptual)_ | `Data Lakehouse/Predicciones/` | `comun/lakehouse.py` (zona `predicciones`) | — |
| Generación de reporte | ML | `generar_reportes.py` → `ml/generar_reportes.py` | `generar_reportes` |
| _(no existe)_ | MLflow: Tracking + Model Registry | `comun/config.py` (alias `candidato` / `produccion`) | — |
| _(no existe)_ | Airflow: Scheduler + Webserver | `dags/` | — |
| _(no existe)_ | Proxy Docker (HAProxy, TCP 2375) | `docker-compose.yml` → `docker-proxy` | — |
| _(no existe)_ | PostgreSQL: `db_airflow`, `db_mlflow` → `pg_data/` | `docker/postgres/init/01-bases.sh` | — |
| Predicción → Generación de reportes / Filtros | `reportes/` + SMB 3 (TCP 445) → PC Planificación | `ml/generar_reportes.py` | — |

## Huecos detectados (ver `docs/inconsistencias.md`)

- **I-30:** Despliegue_v3 dibuja *Webserver* en Airflow. En Airflow 3 ese componente ya no existe: lo reemplaza el **API Server**, y el **DAG Processor** es un proceso aparte y obligatorio. `docker-compose.yml` usa Airflow 3.
- **I-31:** la zona **Predicciones/** existe en el despliegue, pero no en el diagrama conceptual ni en el Word, que hablan de tres zonas.
- **I-10:** el conceptual no tiene Model Registry ni bucle de reentrenamiento. El despliegue sí.
- **I-11:** ningún artefacto implementa el monitoreo de drift que promete la sección 2.5.2.
