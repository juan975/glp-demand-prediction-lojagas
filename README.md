# Modelo predictivo de ventas de GLP — Lojagas

---

## Equipo

<table align="center">
  <tr>
    <th align="center">Autora</th>
    <th align="center">Autor</th>
    <th align="center">Director</th>
  </tr>
  <tr>
    <td align="center">
      <a href="https://github.com/daravan1">Dara Van Gijsel Guarnizo</a>
    </td>
    <td align="center">
      <a href="https://github.com/juan975">Juan Cristóbal Espinosa Rodas</a>
    </td>
    <td align="center">
      Armando Augusto Cabrera Silva
    </td>
  </tr>
</table>

---

## Descripción

Este repositorio contiene el código fuente, los artefactos de arquitectura y la documentación técnica del **Trabajo de Integración Curricular (TIC)** de la carrera de Computación de la **Universidad Técnica Particular de Loja (UTPL)**.

El sistema predice, cada mes y por segmento de negocio, las **toneladas de GLP** que venderá **C.E.M. Lojagas** en el mes siguiente. Combina el histórico de facturación del ERP Odoo con variables territoriales, demográficas y coyunturales de Loja y Zamora Chinchipe: estado vial, población, clima, ciclos agrícolas y eventos como la Romería de la Virgen del Cisne. La predicción anual se obtiene sumando las mensuales.

Se desarrolla bajo **Design Science Research**, con **CRISP-DM** como subproceso de construcción del modelo y el **Modelo de Vistas 4+1** (ISO/IEC/IEEE 42010:2022) para la descripción arquitectónica. Por indicación del director, solo la vista lógica y la de despliegue llevan diagrama ([ADR-0013](docs/adr/0013-vistas-documentadas-con-diagrama.md)). La Vista de Desarrollo es este repositorio: cada paquete de `src/lojagas/` corresponde a un contenedor del diagrama de despliegue (`docs/arquitectura/03-vista-despliegue/`).

---

## Estructura

```
├── src/lojagas/
│   ├── comun/            config, acceso al Lakehouse (Delta Lake), trazabilidad
│   ├── ingesta/          «Contenedor Ingesta»: ingesta.py, odoo_api.py, externas/
│   ├── procesamiento/    «Contenedor Procesamiento»: curacion.py, ingenieria_caracteristicas.py
│   ├── ml/               «Contenedor ML»: pipeline_entrenamiento.py, evaluacion.py,
│   │                      predictor.py, generar_reportes.py, modelos/
│   ├── interfaz/         «Contenedor Interfaz»: tablero de consulta de solo lectura
│   └── cli.py            `lojagas <subcomando>`: lo que lanza Airflow en cada contenedor
├── dags/                 DAGs de Airflow (prediccion_mensual, reentrenamiento, prueba_humo)
├── docker/               un Dockerfile por contenedor + init de PostgreSQL
├── referencias/          datos públicos o de definición propia (calendario, mapa de segmentos)
├── tests/                solo datos sintéticos
├── notebooks/            EDA; nunca código de producción
└── docs/
    ├── arquitectura/     01-mapa-capacidades, 02-vista-logica, 03-vista-despliegue,
    │                      04 a 07 (datos, protección, seguridad, pruebas), trazabilidad.md
    ├── adr/              decisiones de arquitectura
    ├── entorno.md        instalación del entorno de desarrollo
    ├── inconsistencias.md   cómo se usa el backlog (issues con la etiqueta `tesis`)
    ├── model_card.md     ISO/IEC 23053
    └── registro_riesgos.md  ISO/IEC 23894
```

Los datos **no viven en el repositorio**. El Lakehouse, `mlruns/`, `pg_data/` y `reportes/` se montan desde `${LOJAGAS_DATA_ROOT}` en el servidor on-premise de Lojagas.

---

## Empezar

La instalación completa, paso a paso, está en [`docs/entorno.md`](docs/entorno.md). En resumen:

```bash
uv sync --extra ingesta --extra procesamiento --extra ml --extra interfaz   # no usar --all-extras
uv run pre-commit install
uv run pytest
```

La plataforma (Docker) necesita antes un `.env` con los secretos generados: el compose no arranca sin ellos. En desarrollo se usa además `compose.dev.yml` para abrir MLflow y Airflow en el navegador; en el servidor se entra por túnel SSH ([ADR-0015](docs/adr/0015-segmentacion-red.md)). Para comprobar que todo funciona, el DAG `prueba_humo` tiene que terminar en `success`.

Las reglas de trabajo están en [`CONTRIBUTING.md`](CONTRIBUTING.md) y el backlog, en los issues con la etiqueta `tesis`.

---

## Objetivos

**General:** desarrollar un modelo predictivo de aprendizaje automático para estimar las ventas mensuales y anuales de GLP de Lojagas C.E.M., considerando variables históricas, territoriales y coyunturales de las provincias de Loja y Zamora Chinchipe.

**Específicos:**
- **Identificar** las variables históricas y contextuales que influyen en las ventas de GLP.
- **Construir** una base de datos analítica que integre información comercial, temporal, geográfica y contextual.
- **Diseñar y entrenar** modelos de aprendizaje automático para la predicción mensual y anual.
- **Comparar** su desempeño (MAE, RMSE, MAPE, WAPE, R²) frente a baselines ingenuos y documentar el seleccionado bajo ISO/IEC 23053:2022.

<p align="center">
  <sub>© 2026 Dara Van Gijsel Guarnizo · Juan Cristóbal Espinosa Rodas — UTPL, Loja, Ecuador. Uso restringido: los datos pertenecen a C.E.M. Lojagas.</sub>
</p>
