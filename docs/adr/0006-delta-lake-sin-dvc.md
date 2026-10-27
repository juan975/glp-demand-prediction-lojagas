# 0006 — Versionado de datos con Delta Lake, sin DVC

**Estado:** Propuesto

## Contexto
La Vista de Desarrollo (sección 3.4.4) cita DVC para el control de versiones de datos. El diagrama de despliegue, en cambio, usa Delta Lake como capa transaccional del Lakehouse, y Delta Lake ya versiona cada escritura con time travel.

## Decisión
Delta Lake es el **único** mecanismo de versionado de datos. DVC se retira del documento.

## Por qué
- Dos mecanismos para el mismo fin significan dos fuentes de verdad y una pregunta segura del tribunal: ¿cuál manda?
- DVC necesita un remoto de almacenamiento. Si ese remoto está fuera del servidor, choca con la ADR-0001.
- La trazabilidad se consigue registrando en cada corrida de MLflow la `delta_version` de cada tabla leída (`src/lojagas/comun/trazabilidad.py`).

## Consecuencias
- **Prohibido ejecutar `VACUUM` sin revisar la retención.** Las tablas se crean con `logRetentionDuration` y `deletedFileRetentionDuration` de 3650 días (`comun/lakehouse.py`). Sin eso, la promesa de reproducibilidad de la sección 3.6.2 deja de cumplirse.
- Los datos de `referencias/` (públicos y pequeños) se versionan con git.
