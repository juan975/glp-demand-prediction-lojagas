# 0003 — PostgreSQL como único motor de base de datos

**Estado:** Aceptado (oct 2026)

## Decisión
Un contenedor PostgreSQL con dos bases separadas, `db_airflow` y `db_mlflow`, cada una con su propio usuario (`docker/postgres/init/01-bases.sh`). MLflow deja de usar SQLite.

## Por qué
- SQLite no soporta escrituras concurrentes. Airflow ejecuta tareas en paralelo y MLflow recibe corridas anidadas.
- Un solo motor significa un solo respaldo, un solo monitoreo y un solo componente a parchear.
- Usuarios separados: una credencial filtrada de MLflow no da acceso a la metadata de Airflow.

## Consecuencias
- La tesis todavía menciona "MLflow (SQLite backend)" en material previo. Hay que actualizarla (I-07).
- El script de inicialización corre solo con `pg_data/` vacío. Los cambios posteriores se hacen a mano o con migraciones.
