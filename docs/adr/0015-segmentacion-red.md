# 0015 — Segmentación de red de la plataforma

**Estado:** Aceptado (nov 2026). Reemplaza la tercera consecuencia del ADR-0004.

## Contexto
El 11 de noviembre se levantó la plataforma completa por primera vez (prueba de humo). MLflow y el API server de Airflow publicaban su puerto en `127.0.0.1` del host, como indicaba el ADR-0004. Desde el contenedor de la interfaz, que vive en una red propia, los dos resultaron alcanzables **por IP**, aunque no por nombre. La documentación de Docker lo explica: un puerto publicado queda disponible fuera del host y también para los contenedores de otras redes bridge. PostgreSQL y el proxy, que no publicaban nada, sí eran inalcanzables.

MLflow no tiene autenticación, así que una interfaz comprometida podía cambiar el alias del modelo en el Model Registry y alterar las predicciones del mes.

Además, el proxy del socket compartía `lojagas_net` con los contenedores de trabajo, incluida la ingesta, que tiene salida a internet. El proxy equivale a acceso de root en el host (ADR-0002, R7).

## Decisión
1. MLflow y el API server de Airflow **no publican puertos** en `docker-compose.yml`. Tienen una IP fija en `lojagas_net` (subred `172.30.0.0/24`): MLflow en `172.30.0.10` y Airflow en `172.30.0.11`. El administrador entra con `ssh -L 5000:172.30.0.10:5000 -L 8080:172.30.0.11:8080 usuario@servidor`.
2. `compose.dev.yml` publica esos dos puertos **solo en desarrollo**, porque con Docker Desktop el host no llega a las IP de los contenedores. Nunca se usa en el servidor.
3. El proxy vive en `proxy_net`, una red `internal` que comparte únicamente con `airflow-scheduler`. Con LocalExecutor, las tareas corren dentro del scheduler, así que nadie más necesita el proxy.
4. Quedan tres redes: `lojagas_net` (plataforma y contenedores de trabajo), `proxy_net` (scheduler y proxy) e `interfaz_net` (solo la interfaz).

## Evidencia (prueba de humo, 11 nov 2026)

| Desde | Hacia | Resultado |
|---|---|---|
| Interfaz | MLflow, Airflow y PostgreSQL, por IP | Inalcanzables (`TimeoutError`) |
| Interfaz | Proxy, por IP en `proxy_net` | Inalcanzable (`TimeoutError`) |
| Interfaz | `lakehouse/predicciones/` | Solo lectura |
| Contenedor de trabajo | MLflow, por nombre | `/health` responde OK |
| Contenedor de trabajo | Proxy, por nombre | No resuelve |
| Scheduler | Proxy | Lanza el contenedor de trabajo (DAG `prueba_humo` en `success`) |
| Scheduler | Proxy, endpoint `VOLUMES` | Rechazado |

Que los contenedores de trabajo no alcanzan el proxy se comprobó por nombre, no por IP. Se infiere por el mismo mecanismo que sí se verificó por IP desde la interfaz.

## Alternativas descartadas
- **Mantener los puertos en `127.0.0.1`.** Era la configuración anterior y es justo la que falló.
- **Activar autenticación en MLflow.** Es una defensa en profundidad razonable a futuro, pero no reemplaza el aislamiento de red y obliga a repartir credenciales a los contenedores de trabajo.

## Consecuencias
- El túnel depende de las IP fijas. Si cambia la subred, hay que actualizar este ADR y el procedimiento del administrador. Falta confirmar con Lojagas que `172.30.0.0/24` no coincide con su LAN.
- En desarrollo, con `compose.dev.yml`, la fuga vuelve a existir. Es aceptable en una laptop sin datos de producción; no en el servidor.
- El proxy sigue permitiendo crear contenedores privilegiados y hacer `inspect` de los demás, lo que expone sus variables de entorno. La segmentación reduce quién llega al proxy, no lo que el proxy permite (R7).
- La versión de MLflow queda fijada en 3.18.0, en el servidor y en el cliente, porque es la que se probó. La CVE-2026-2652 que cita el ADR-0004 solo afecta a servidores con `--app-name basic-auth`, que no es el caso: se mantiene como argumento de defensa en profundidad, no como vulnerabilidad de este despliegue.
- Fe de erratas del ADR-0012: las zonas del Lakehouse se llaman `lakehouse/raw/`, `lakehouse/curated/` y `lakehouse/feature/`, no `zona_raw/`.
