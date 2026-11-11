# 0012 — Acceso sin autenticación por segmentación de red, y retiro del recurso compartido SMB

**Estado:** Aceptado (nov 2026)

## Contexto
La interfaz de consulta (ADR-0011) necesita una política de acceso. Hasta la v3 del diagrama de despliegue, Planificación recibía los reportes por una carpeta compartida SMB y el administrador entraba por túnel SSH a las interfaces de Airflow y MLflow.

## Decisión
La interfaz **no tiene autenticación de usuarios**. El control de acceso es de red:

- El contenedor publica su puerto sobre la IP de la red interna de Lojagas, nunca sobre `0.0.0.0`.
- El cortafuegos del servidor acepta ese puerto solo desde la subred de Planificación.
- El router perimetral no reenvía ese puerto. La interfaz no es alcanzable desde fuera de la red de Lojagas.
- Airflow y MLflow siguen sin publicar puerto al host: se llega a sus interfaces por túnel SSH, como ya estaba definido.

Se **elimina el recurso compartido SMB**. Los reportes Excel y PDF se descargan desde la interfaz. El directorio `reportes/` sigue existiendo en el servidor, pero deja de estar expuesto como carpeta de red.

## Condición que sostiene esta decisión
Ni la interfaz ni los reportes pueden mostrar información a nivel de cliente. Todo lo que sale hacia Planificación está agregado por segmento y por mes. El contenedor no monta `zona_raw/`, `zona_curated/` ni `zona_feature/`, que son las que contienen cédulas, RUC, nombres, direcciones y coordenadas.

Si en algún momento Lojagas pide un reporte desagregado por cliente, esta decisión deja de ser defendible y hay que reemplazarla por un ADR con autenticación.

## Alternativas descartadas
**Autenticación con usuarios en base de datos.** Añade una tercera base en PostgreSQL, gestión de contraseñas y sesiones, y una superficie de ataque que después habría que evaluar. Es alcance que no produce evidencia para la tesis: lo que se evalúa es el modelo predictivo, no un sistema de identidad.

**Mantener el SMB como respaldo.** Dejaría dos rutas de entrega para lo mismo y obligaría a sostener permisos de red sobre una carpeta que ya nadie necesita. Se descarta a cambio de aceptar el riesgo que sigue.

## Consecuencias
- Cualquier equipo conectado a la subred de Planificación ve las predicciones sin identificarse. Es aceptable porque el contenido está agregado, pero queda registrado como riesgo asumido en `docs/registro_riesgos.md`.
- Si el contenedor de la interfaz se cae, Planificación se queda sin acceso a los reportes hasta que se levante. Antes el SMB cubría ese caso. El administrador puede entregar los archivos por otra vía mientras tanto, porque `reportes/` sigue en el servidor.
- La segmentación deja de ser una palabra y pasa a ser configuración verificable: publicación del puerto, regla de cortafuegos y ausencia de reenvío en el router. Las tres se comprueban en la demostración.
- El dispositivo `PC Planificación` deja de tener cliente SMB y pasa a tener navegador.
