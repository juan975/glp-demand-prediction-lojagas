# 0004 — MLflow como proxy de artefactos

**Estado:** Aceptado (oct 2026)

## Decisión
Solo el contenedor MLflow monta `mlruns/`. El contenedor ML sube y descarga modelos por HTTP (`mlflow server --serve-artifacts --artifacts-destination /mlruns`).

## Por qué
- Un solo punto de escritura sobre los artefactos y menos bind mounts compartidos.
- El contenedor ML no necesita conocer rutas del host.

## Consecuencias
- Desde MLflow 3.5 el servidor valida la cabecera `Host`. Como `mlflow` no es una IP privada, se declara en `--allowed-hosts`.
- Se exige MLflow ≥ 3.10 por la CVE-2026-2652 (rutas FastAPI sin autenticación).
- La UI se publica solo en `127.0.0.1` y se accede por túnel SSH. MLflow no tiene autenticación activada, así que la seguridad depende del túnel.
