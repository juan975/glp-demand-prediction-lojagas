# Registro de riesgos (ISO/IEC 23894:2023)

Los riesgos R1 a R5 vienen de la sección 3.4.5. R6 a R13 aparecieron al pasar al diseño de despliegue, al código y a la prueba de humo de la plataforma. **La columna "Evidencia" es lo que vuelve operativa la norma**: un riesgo sin control verificable es solo una cita.

| ID | Riesgo | Prob. | Impacto | Tratamiento | Evidencia en el repo |
|---|---|---|---|---|---|
| R1 | Datos insuficientes o de baja calidad | Alta | Alto | Contratos de datos; documentar limitaciones | `procesamiento/contratos.py`; model card §6 |
| R2 | Sesgo por segmento o zona subrepresentada | Media | Medio | Error estratificado por segmento | _pendiente: `ml/evaluacion.py` por segmento_ |
| R3 | Degradación (data o concept drift) | Media | Alto | Reentrenamiento semestral; umbral de alerta | `dags/reentrenamiento.py`; ADR-0008 pendiente |
| R4 | Uso fuera del rango válido | Media | Medio | Rango de uso en la model card | model card §1 |
| R5 | Exposición de PII | Media | Alto | Seudonimización antes de Curated; nada de datos en git | `procesamiento/anonimizacion.py`; `.gitignore`; pre-commit; CI |
| R6 | Fuga temporal en la validación | Alta si no se controla | Alto | Particiones por mes con aserción | `ml/walk_forward.py`; `tests/unit/test_walk_forward.py` |
| R7 | Escape del contenedor vía la API de Docker: quien controla un DAG puede crear un contenedor privilegiado y leer las variables de entorno de los demás con `inspect` | Baja, mientras solo el administrador modifique `dags/` | Alto | Proxy con endpoints mínimos, en una red interna que solo comparte con el scheduler; `dags/` montado en solo lectura | ADR-0002, ADR-0015; prueba de humo: el proxy rechaza `VOLUMES` |
| R8 | Pérdida de reproducibilidad por `VACUUM` | Media | Alto | Retención de 3650 días | `comun/lakehouse.py`; ADR-0006 |
| R9 | Retiro de JSON-RPC/XML-RPC en Odoo | Alta (2027-2028) | Alto | Elegir JSON-2 o un endpoint propio | ADR-0005 |
| R10 | Acceso sin autenticación al tablero desde la subred de planificación | Media | Bajo, porque solo hay agregados por segmento y mes | Segmentación de red; nada a nivel de cliente | ADR-0012, ADR-0015; prueba de aislamiento de la interfaz |
| R11 | PII en los logs de Airflow o en XCom: todo lo que imprime un contenedor de trabajo queda en el log, y la última línea en `db_airflow` | Media | Alto | `do_xcom_push=False` en las tareas; prohibido imprimir registros de clientes | _pendiente: `dags/_comun.py`_; regla en `CONTRIBUTING.md` |
| R12 | Secretos (API de Odoo, sal de PII) como variables de entorno de todos los contenedores de Airflow y de todas las tareas | Media | Alto | Pasar a cada tarea solo los secretos que usa | _pendiente_ |
| R13 | Alteración del Model Registry desde otra red de Docker, si MLflow publica un puerto | Baja desde el ADR-0015 | Alto | MLflow sin puertos publicados, IP fija y túnel SSH | ADR-0015; prueba de aislamiento por IP |
