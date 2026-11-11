"""«Contenedor Interfaz» (diagrama de despliegue).

Único contenedor persistente de los cuatro aplicativos: los de ingesta, procesamiento
y ML son efímeros y los levanta Airflow en cada ejecución, mientras que este queda
escuchando. Sirve el tablero de consulta del área de planificación.

- app.py  → lee la zona Predicciones y el volumen de reportes; sirve el tablero

Restricciones que no son opcionales (ADR-0011 y ADR-0012):

1. **Solo lectura.** No escribe en el lakehouse, no lanza procesos y no dispara DAGs.
2. **Sin red hacia dentro.** No habla con PostgreSQL, ni con MLflow, ni con el socket
   de Docker. Las métricas del modelo vigente las lee de un archivo que
   `generar_reportes.py` deja en la zona Predicciones.
3. **Sin PII.** Solo monta `predicciones/` y `reportes/`. Las zonas Raw, Curated y
   Feature contienen cédulas, RUC, nombres y coordenadas, y este contenedor no las ve.
4. **Solo agregados.** Todo lo que publica está agregado por segmento y por mes. El día
   que haga falta un desglose por cliente, la decisión de no exigir autenticación deja
   de ser defendible y hay que reemplazar el ADR-0012.
"""
