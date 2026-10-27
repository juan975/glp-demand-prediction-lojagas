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

Se desarrolla bajo **Design Science Research**, con **CRISP-DM** como subproceso de construcción del modelo y el **Modelo de Vistas 4+1** (ISO/IEC/IEEE 42010:2022) para la descripción arquitectónica. Este repositorio es la **Vista de Desarrollo**: cada paquete de `src/lojagas/` corresponde a un contenedor del diagrama de despliegue (`docs/arquitectura/06-vista-despliegue/`).

---

## Estructura

```
├── src/lojagas/
│   ├── comun/            config, acceso al Lakehouse (Delta Lake), trazabilidad
│   ├── ingesta/          «Contenedor Ingesta»: ingesta.py, odoo_api.py, externas/
│   ├── procesamiento/    «Contenedor Procesamiento»: curacion.py, ingenieria_caracteristicas.py
│   ├── ml/               «Contenedor ML»: pipeline_entrenamiento.py, evaluacion.py,
│   │                      predictor.py, generar_reportes.py, modelos/
│   └── cli.py            `lojagas <subcomando>`: lo que lanza Airflow en cada contenedor
├── dags/                 DAGs de Airflow (prediccion_mensual, reentrenamiento)
├── docker/               un Dockerfile por contenedor + init de PostgreSQL
├── referencias/          datos públicos o de definición propia (calendario, mapa de segmentos)
├── tests/                solo datos sintéticos
├── notebooks/            EDA; nunca código de producción
└── docs/
    ├── arquitectura/     01-mapa-capacidades … 10-testing, trazabilidad.md
    ├── adr/              decisiones de arquitectura
    ├── inconsistencias.md   backlog de correcciones del Word y los diagramas
    ├── model_card.md     ISO/IEC 23053
    └── registro_riesgos.md  ISO/IEC 23894
```

Los datos **no viven en el repositorio**. El Lakehouse, `mlruns/`, `pg_data/` y `reportes/` se montan desde `${LOJAGAS_DATA_ROOT}` en el servidor on-premise de Lojagas.

---

## Empezar

```bash
uv sync --all-extras          # entorno completo (Python 3.11)
uv run pre-commit install     # bloquea datos y secretos antes de cada commit
uv run pytest                 # tests con datos sintéticos
```

Plataforma completa (requiere Docker):

```bash
cp .env.example .env && make dirs && make build && docker compose up -d
```

La configuración del equipo de cada integrante está en [`docs/entorno.md`](docs/entorno.md). Las reglas de trabajo están en [`CONTRIBUTING.md`](CONTRIBUTING.md).

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
