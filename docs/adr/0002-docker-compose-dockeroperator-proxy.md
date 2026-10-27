# 0002 — Docker Compose, DockerOperator y proxy del socket de Docker

**Estado:** Aceptado (oct 2026)

## Contexto
Lojagas necesita instalar y operar la solución sin un equipo de plataforma. Hay un solo nodo. Los trabajos de ingesta y ML tienen dependencias pesadas y distintas entre sí (pdfplumber, geopandas, torch y xgboost), y no deben mezclarse con las de Airflow.

## Decisión
1. **Docker Compose** para los servicios de larga duración: PostgreSQL, MLflow, Airflow (api-server, scheduler, dag-processor) y docker-proxy.
2. **DockerOperator**: Airflow lanza los contenedores efímeros `ingesta`, `procesamiento` y `ml` por cada tarea. Las imágenes se etiquetan con el SHA del commit.
3. **Proxy del socket de Docker** (`tecnativa/docker-socket-proxy`): Airflow no monta `/var/run/docker.sock`. Habla con un proxy que solo habilita los endpoints `CONTAINERS`, `IMAGES` y `POST`.

## Alternativas descartadas
- **Kubernetes:** sobredimensionado para un nodo y una carga mensual.
- **Montar el socket directo en Airflow:** equivale a dar root del host a cualquier código de un DAG.
- **PythonOperator con todo instalado en la imagen de Airflow:** acopla versiones y rompe el aislamiento entre ingesta y ML.

## Consecuencias
- Los bind mounts de las tareas se resuelven en el **host**. Por eso los DAGs usan `LOJAGAS_DATA_ROOT` (ruta del servidor) y no rutas internas del contenedor Airflow.
- `mount_tmp_dir=False`: con el proxy, la carpeta temporal de Airflow no existe en el host.
- El proxy reduce la superficie de ataque, pero no la elimina: `POST` en contenedores sigue permitiendo crear contenedores. Esto se registra como riesgo residual R7.
- Fijar la imagen del proxy por digest antes de pasar a producción.
