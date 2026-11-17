# Protección de datos

Tratamiento de datos personales según la LOPDP: qué zonas del Lakehouse contienen PII, seudonimización con HMAC y qué sale hacia planificación (solo agregados por segmento y mes, ADR-0012).

## Qué llega a cada zona

| Zona | PII | Regla |
|---|---|---|
| Raw | Sí, tal como sale de Odoo | Solo en el servidor; ningún contenedor de consulta la monta |
| Curated | No: seudonimizada | **Lista blanca** (`procesamiento/anonimizacion.py`): pasan solo las columnas que el modelo necesita; los identificadores de cliente se reemplazan por un HMAC y las coordenadas se redondean a 2 decimales. Cualquier otra columna, incluidas las que Raw agregue en el futuro, se descarta |
| Feature, Predicciones, `reportes/` | No | Agregados por mes y segmento |

## Custodia de la sal en producción (I-45)

La seudonimización solo protege frente a quien no conoce la sal. Si el equipo del TIC la generara o la conociera, podría reidentificar a los clientes probando cédulas y RUC válidos: frente a los desarrolladores, que son terceros, no protegería nada. Por eso se separan funciones:

1. **La genera el administrador de Lojagas, en el servidor**, con `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`, y la escribe directamente en el `.env` del servidor (`chmod 600`, propietario el administrador). El TIC entrega este procedimiento, no el valor.
2. **Solo la ve un contenedor:** `airflow-scheduler` la tiene en su entorno y solo la tarea `curacion` la recibe (`dags/_comun.py`, R12). No aparece en la UI de Airflow ni se guarda en `db_airflow`.
3. **Respaldo:** el administrador la guarda en el gestor de contraseñas de Lojagas. Ningún miembro del TIC tiene acceso a ese gestor.
4. **Pérdida o rotación:** no se pierden datos. Raw conserva los identificadores originales, así que Curated se reconstruye con una sal nueva volviendo a correr la curación. Lo que cambia son los seudónimos: no se pueden comparar los de antes con los de después.
5. **Desarrollo:** la sal del equipo es distinta de la de producción y nunca se usa en el servidor.
