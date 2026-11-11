# 0011 — Interfaz de consulta en un único contenedor, desacoplada por archivos

**Estado:** Aceptado (nov 2026)

## Contexto
La interfaz de consulta de resultados estuvo planteada desde el inicio del proyecto y se retomó tras la revisión del diseño arquitectónico v3. Lojagas pidió además contener el consumo de recursos del servidor on-premise, que ya corre Airflow, PostgreSQL, MLflow y tres contenedores efímeros.

## Decisión
La interfaz es **un solo contenedor persistente** que sirve el backend y el frontend juntos. No se separa en API y cliente.

Ese contenedor **no se comunica con ningún otro contenedor**. Lee únicamente dos rutas del host, montadas en solo lectura:

- `lakehouse/predicciones/` — las predicciones del período vigente y los meses ya cerrados.
- `reportes/` — los archivos Excel y PDF que genera el pipeline.

Las métricas del modelo vigente (WAPE, comparación contra el estacional ingenuo, fecha del último entrenamiento) no se consultan a MLflow por HTTP: `generar_reportes.py` las escribe como un artefacto más dentro de `lakehouse/predicciones/` al cerrar cada ejecución mensual.

## Alternativas descartadas
**Backend y frontend separados.** Son dos contenedores persistentes en vez de uno y obligan a justificar una frontera que ninguna carga de este sistema necesita: la interfaz atiende a un puñado de personas de Planificación una vez al mes.

**Consultar MLflow por HTTP desde la interfaz.** Obligaría a poner la interfaz en la misma red que MLflow y a cargar el cliente de MLflow en la imagen. Como el sistema es por lotes mensuales, las métricas vivas no aportan nada frente a las métricas de la última corrida, y a cambio se gana aislamiento total.

## Consecuencias
- La interfaz no tiene ruta hacia PostgreSQL, MLflow ni `docker.sock`. El aislamiento no depende de configurar bien una red: depende de que el contenedor no tenga a dónde ir.
- Lo que muestra la interfaz corresponde a la última ejecución del pipeline, no al estado instantáneo de MLflow. Para una predicción mensual esto es lo correcto, pero hay que decirlo en la documentación para que no se lea como un retraso.
- `generar_reportes.py` pasa a tener una responsabilidad más: volcar el resumen de métricas. Entra en el contrato de esa función y en sus pruebas.
- La imagen no necesita cliente de base de datos ni de MLflow, solo la librería de lectura de Delta y el framework web.
