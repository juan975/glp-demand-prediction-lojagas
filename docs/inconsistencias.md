# Backlog de inconsistencias

Se encontraron al contrastar `CuartoAvance.docx`, los diagramas (Mapa de Capacidades v2, DiseñoArquitectónico_v2, Despliegue_v2), el diccionario de datos y las decisiones tomadas. **Cada fila se convierte en un issue con la etiqueta `tesis`.** Al cerrarla, se anota el commit o la versión del Word que la corrige.

Prioridad: **P0** es lo que el tribunal usará para cuestionar la coherencia del trabajo, o lo que bloquea el código. **P1** es un error técnico o conceptual. **P2** es redacción o formato.

## P0 — Bloqueantes

| ID | Dónde | Problema | Corrección |
|---|---|---|---|
| I-01 | 3.4.4, Vista de Despliegue | Sigue planteando "dos escenarios alternativos" (on-premise o nube) y "acceso directo al ERP Odoo". La decisión ya está tomada y Odoo está en la nube, accesible por API. | Reescribir la vista con Despliegue_v2 y citar las ADR 0001 a 0004. |
| I-02 | 2.5.3 | "Microservicios ligeros", "servicio REST", "nube de bajo costo" y frecuencia "mensual o semanal". Todo contradice el despliegue aprobado. | Reescribir: batch mensual en contenedores orquestados por Airflow, on-premise. |
| I-03 | 3.4.4 (Procesos y Escenarios) y diagrama conceptual ("Filtros por segmento / por tiempo") | Se promete un "proceso interactivo" y una "consulta ad hoc" con ajuste de variables, pero el sistema solo produce reportes batch y no tiene interfaz. | Decidir (ADR-0010). Opción realista: escenario ad hoc = ejecución manual del DAG con parámetros (`--periodo`, archivo de escenario), y los filtros como hojas del Excel. Si no, eliminarlo del documento y del diagrama. |
| I-04 | Objetivo funcional (3.3) y 3.4.1.1 | Cinco segmentos (doméstico, industrial, agroindustrial, granel, domicilio), pero el dataset **no tiene campo de segmento**. Hay que derivarlo de `canal_venta`, `cliente_tipo`, `producto` y `categoria`, y esa regla no está definida. | Definir `referencias/mapa_segmentos.csv` con Lojagas. Documentar la regla en 3.4.3 (preparación de datos). Mientras no exista, no hay target. |
| I-05 | 3.4.4, Vista de Desarrollo | Cita DVC. El Lakehouse ya versiona con Delta Lake. | Retirar DVC y citar ADR-0006. |
| I-06 | 3.4.4, Vista Lógica | Cuatro componentes que no coinciden con el diagrama conceptual: faltan el Data Lakehouse (con sus tres zonas), la separación entrenamiento/evaluación/predictor y el registro de modelos. | Alinear con DiseñoArquitectónico_v2 y `docs/arquitectura/trazabilidad.md`. |
| I-07 | Vista de Desarrollo y Tabla 1 | No se mencionan Airflow, Docker, PostgreSQL ni Delta Lake. Se menciona TensorFlow (no se usará). La Tabla 1 dice "ERP Odoo (PostgreSQL)" como sistema origen. | Actualizar el stack; la Tabla 1 pasa a "ERP Odoo (API)". |
| I-08 | 1.6 frente a 3.1 | El cap. 1 presenta la metodología como "CRISP-DM + ágil". El cap. 3 usa DSR como marco estructurante. El tribunal lo nota de inmediato. | Reescribir 1.6: DSR como marco; CRISP-DM y 4+1 como subprocesos en paralelo. |
| I-09 | 3.7 (Fase 6) y repo público | El repo es público por decisión del equipo; la sección 3.3 promete confidencialidad a Lojagas. | Pedir autorización escrita a Lojagas para publicar el **código** y declararlo en 3.7: el repo no contiene datos, credenciales ni el diccionario interno (garantizado por `.gitignore`, pre-commit y CI). |
| I-30 | Despliegue_v3, Contenedor Airflow | Dibuja "Webserver". En Airflow 3 no existe: lo reemplaza el *API Server*, y el *DAG Processor* es un proceso obligatorio que no aparece. | Cambiar a API Server + Scheduler + DAG Processor. Volver a Airflow 2 no es opción: su soporte terminó. |
| I-31 | Despliegue_v3 frente a DiseñoArquitectónico_v2 y el Word | El despliegue tiene cuatro zonas en el Lakehouse (Raw, Curated, Feature, **Predicciones**). El conceptual y el Word hablan de tres. | Agregar Predicciones al conceptual y a la sección del Lakehouse, y justificarla: las predicciones quedan versionadas y se comparan con el real para el monitoreo (I-11). |
| I-32 | README del repo | "Horizonte de 7 a 30 días" (el sistema es mensual), "por segmento y cantón" (ver I-14), Romería "agosto–octubre" (el Word dice agosto; el documento de fuentes dice 17-ago a 1-nov) y "© 2025". | Ya corregido en el README fusionado. Falta unificar la Romería en el Word (I-18). |

## P1 — Técnicas o conceptuales

| ID | Dónde | Problema | Corrección |
|---|---|---|---|
| I-10 | DiseñoArquitectónico_v2 | No tiene registro de modelos ni flecha de reentrenamiento o retroalimentación (pendientes desde septiembre). | Agregar "Registro de modelos" en el Motor ML y un bucle Evaluación → Entrenamiento. |
| I-11 | 2.5.2 y 3.4.5 (R3) | Se promete monitoreo de drift, pero ningún componente ni contenedor lo ejecuta. | Tarea en el DAG mensual: comparar el WAPE del mes cerrado con un umbral (ADR-0008). |
| I-12 | DiseñoArquitectónico_v2 | SIG y Eventos aparecen como "No estructurados". Una capa vial vectorial y un calendario son datos estructurados o semiestructurados. "Históricos transaccionales" está separado del ERP Odoo, cuando es la misma fuente. | Reclasificar las fuentes ("internas / externas" es más preciso) y fusionar ERP con el histórico. |
| I-13 | 2.9, 3.6.4 | Criterio de éxito MAPE < 10 % sin baseline. MAPE se indefine con ceros. | Añadir baselines ingenuos y WAPE. El criterio pasa a ser: MAPE/WAPE < 10 % **y** superar al estacional ingenuo. |
| I-14 | 3.4.3 | "Granularidad mensual por segmento **y zona**": 5 segmentos × N zonas × 46 meses deja series casi vacías. Además, la geografía solo está completa en menos del 30 % de los consumidores finales. | Modelar por segmento. La zona entra como feature agregada, o se justifica con el EDA. |
| I-15 | 3.5, Demostración | Se reservan "los últimos doce meses" para la demostración. Con aproximadamente 46 meses, si eso es aparte del walk-forward, quedan 34 meses para entrenar y validar. | Aclarar que la demostración usa los folds del walk-forward, o justificar el *hold-out*. |
| I-16 | 1.4 y 2.6.2 | "Ventas mensuales y anuales" y "unidades o toneladas". El target ya está decidido: toneladas. Con 3 o 4 años no se entrena un modelo anual. | Unificar: toneladas; anual = agregación de las predicciones mensuales. |
| I-17 | 3.4.3 | Ajuste de hiperparámetros "mediante búsqueda y validación cruzada" sin precisar que se hace **dentro** de cada fold. | Especificar validación anidada. Si no, las métricas quedan optimistas. |
| I-18 | Intro (1.1) | La Romería se ubica "cada año en agosto". El documento de fuentes la sitúa entre el 17 de agosto y el 1 de noviembre (traslado y retorno de la imagen). | Corregir y citar la fuente (GAD o Arquidiócesis de Loja). |
| I-19 | Variables externas | El documento no dice **cuándo** se publica cada variable. Si INAMHI publica con dos meses de rezago, la variable no existe al momento de predecir. | Añadir a la tabla de fuentes una columna "disponible al predecir". En código: `Fuente.disponible_desde_dias`. |
| I-20 | Ingesta | Odoo 19 depreca XML-RPC y JSON-RPC (se retiran en Online 21.1 y en self-hosted 22). | Confirmar la versión con Lojagas (ADR-0005). |

## P2 — Redacción y formato

| ID | Dónde | Problema |
|---|---|---|
| I-21 | Tabla 1 y 42010 (stakeholders) en 3.4.5 | "ARCERNNR" sigue apareciendo dos veces; debe ser **ARCH**. |
| I-22 | 2.5.2 | "Transformaciones descritas en la sección 2.4": la 2.4 es CRISP-DM; la ingeniería de características es la 2.7. |
| I-23 | 2.8.4, 2.8.5, 2.9.1 | ISO 23053 y 42001 aparecen dentro de "Modelos predictivos", e ISO 23894 dentro de "Métricas". Deben ir en una sección normativa propia. |
| I-24 | Cap. 3 (introducción) | "Peffers et al. (2020)": el modelo canónico de seis fases es Peffers et al. (2007), JMIS. Verificar la cita. |
| I-25 | Varios | Erratas: "múaltiples" (×6), "lígeres", "dministrador", "comportamiento,y", "ARCERNNR". |
| I-26 | Índices | Restos de la plantilla: "Figura 1 Cultivos editados genéticamente", "Tabla 1 Ficha informativa", Apéndice A con tabla del BCE. |
| I-27 | 3.8, Tabla 3 | La arquitectura 4+1 figura como "Planificado" en los meses 4-5, pero ya está hecha. Actualizar los estados. |
| I-28 | 3.4 | "Las primeras dos subfases ya han sido completadas", pero el instrumento de madurez aún no se aplica. |
| I-29 | 2.5.1 | Se dice que la Vista de Despliegue define la "capa de presentación de resultados para los usuarios". En batch no hay capa de presentación, solo archivos. |
