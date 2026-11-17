# Seguridad

Riesgos de la plataforma y sus mitigaciones. Los riesgos están en [`registro_riesgos.md`](../../registro_riesgos.md) (R7 y R10 a R13), y la segmentación de red, con la evidencia de la prueba de humo, en el [ADR-0015](../../adr/0015-segmentacion-red.md).

Secretos (R12): cada tarea recibe solo los suyos (`dags/_comun.py`) y solo `airflow-scheduler` los tiene en su entorno; el API Server, el DAG Processor y `airflow-init` no los ven. La imagen del proxy del socket está fijada por versión y digest (`docker-compose.yml`).

Pendiente: declarar en el Word el riesgo residual del proxy del socket (I-42).
