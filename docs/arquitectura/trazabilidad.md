# Trazabilidad arquitectura ↔ código

Esta tabla demuestra la correspondencia entre las vistas del 4+1 (ISO/IEC/IEEE 42010). Los nombres de archivo de **Despliegue_v4** existen literalmente en el código. Si una fila queda sin código o un archivo queda sin fila, hay una inconsistencia que se corrige en el mismo PR.

| Conceptual (DiseñoArquitectónico_v3) | Contenedor (Despliegue_v4) | Artefacto del diagrama → código | Tarea del DAG |
|---|---|---|---|
| Ingesta e integración de datos | Ingesta | `ingesta.py` → `src/lojagas/ingesta/ingesta.py` (+ `odoo_api.py`, `externas/`) | `ingesta_odoo`, `ingesta_externas` |
| Lakehouse: zona cruda | `Data Lakehouse/Zona Raw/` | `comun/lakehouse.py` | — |
| Preparación de datos | Procesamiento | `curacion.py` → `procesamiento/curacion.py` | `curacion` |
| Lakehouse: zona curada | `Data Lakehouse/Zona Curated/` | `comun/lakehouse.py` | — |
| Preparación de datos | Procesamiento | `ingenieria_caracteristicas.py` → `procesamiento/ingenieria_caracteristicas.py` | `ingenieria_caracteristicas` |
| Lakehouse: zona de características | `Data Lakehouse/Zona Feature/` | `comun/lakehouse.py` | — |
| Modelado: selección del modelo | ML | `pipeline_entrenamiento.py` → `ml/pipeline_entrenamiento.py` | `pipeline_entrenamiento` |
| Modelado: entrenamiento | ML | `pipeline_entrenamiento.py` (+ `walk_forward.py`) | `pipeline_entrenamiento` |
| Modelado: evaluación | ML | `evaluacion.py` → `ml/evaluacion.py` (+ `metricas.py`) | `evaluacion` |
| Gestión: registro de experimentos | MLflow: Tracking | `comun/config.py` (`experimento_mlflow`) | — |
| Gestión: modelo seleccionado | MLflow: Model Registry | `comun/config.py` (alias `candidato` / `produccion`) | — |
| Gestión: monitoreo de desempeño | _(sin artefacto, ver I-11)_ | — | — |
| _(implícito en el modelado)_ | ML | `predictor.py` → `ml/predictor.py` | `predecir` |
| Lakehouse: zona de predicciones | `Data Lakehouse/Predicciones/` | `comun/lakehouse.py` (zona `predicciones`) | — |
| Reportes: entrega periódica | ML → `reportes/` | `generar_reportes.py` → `ml/generar_reportes.py` | `generar_reportes` |
| Tablero de consulta: interfaz web | Interfaz | `app.py` → `src/lojagas/interfaz/app.py` | — |
| Aprovisionamiento de resultados | Interfaz (solo lectura sobre `predicciones/` y `reportes/`) | `interfaz/app.py` | — |
| Orquestación de procesos | Airflow: API Server + Scheduler + DAG Processor | `dags/` | — |
| _(no aparece en el conceptual)_ | Proxy Docker (HAProxy, TCP 2375) | `docker-compose.yml` → `docker-proxy` | — |
| _(no aparece en el conceptual)_ | PostgreSQL: `db_airflow`, `db_mlflow` → `pg_data/` | `docker/postgres/init/01-bases.sh` | — |

El proxy del socket y PostgreSQL no aparecen en el diagrama conceptual a propósito: son decisiones de despliegue, no capacidades del sistema. Mezclarlas en la vista conceptual la volvería una vista de infraestructura, que es justamente lo que el docente pidió evitar.

## Huecos detectados (ver `docs/inconsistencias.md`)

- **I-11 (abierto):** el conceptual promete «monitoreo de desempeño» dentro de la gestión del modelo, y la sección 2.5.2 del Word habla de detección de drift, pero ningún artefacto lo implementa. Hasta que exista, el monitoreo es una lectura manual de las métricas que `generar_reportes.py` deja en la zona de predicciones.
- **I-30 (resuelto):** Despliegue_v4 ya dibuja API Server, Scheduler y DAG Processor. El *Webserver* no existe en Airflow 3 y el diagrama dejó de nombrarlo.
- **I-31 (resuelto):** la zona de predicciones aparece ahora en las dos vistas y en el Word.
- **I-10 (resuelto):** el conceptual v3 incorpora el bloque de gestión del modelo, con registro de experimentos y modelo seleccionado, y el modelado se dibuja como proceso iterativo.
- **I-36 a I-40 (resueltos):** la interfaz de consulta está en las cuatro vistas, en el despliegue y en el código. El acceso sin autenticación quedó registrado en el ADR-0012 y la sección 1.6 ya declara DSR como metodología y CRISP-DM como subproceso.
