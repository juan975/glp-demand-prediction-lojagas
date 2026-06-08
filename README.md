# Modelo-predictivo-ventas-Lojagas

---

## Descripción

Este repositorio contiene el código fuente, los artefactos de arquitectura y la documentación técnica del **Trabajo de Integración Curricular (TIC)** desarrollado para la carrera de Computación de la **Universidad Técnica Particular de Loja (UTPL)**.

El proyecto consiste en el diseño, entrenamiento y evaluación de un **modelo predictivo de aprendizaje automático** para estimar las ventas mensuales de gas licuado de petróleo (GLP) en toneladas métricas para la empresa **Lojagas C.E.M.**, considerando variables históricas, territoriales, demográficas y coyunturales de las provincias de Loja y Zamora Chinchipe.

---

## Problema que resuelve

Lojagas opera su planificación de demanda con métodos empíricos basados únicamente en registros históricos de ventas, sin incorporar variables externas de alto impacto como el estado vial en la ruta de abastecimiento, el crecimiento poblacional por cantón, la estacionalidad agrícola o eventos masivos como la **Romería de la Virgen del Cisne** (agosto–octubre). Esto genera incertidumbre operativa que se traduce en sobrestock o desabastecimiento.

Este proyecto propone un sistema de predicción que integra múltiples fuentes de datos para generar estimaciones de alta precisión con un horizonte de 7 a 30 días, habilitando una planificación proactiva y basada en datos.

---

## Equipo

<table align="center">
  <tr>
    <th align="center">Autora / UX·Data</th>
    <th align="center">Autor / Data Architect</th>
    <th align="center">Director</th>
  </tr>
  <tr>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/your-dara-photo" width="130" height="160" alt="Dara Van Gijsel"><br>
      <a href="https://github.com/daravan1">Dara Van Gijsel Guarnizo</a>
    </td>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/your-juan-photo" width="130" height="160" alt="Juan Espinosa"><br>
      <a href="https://github.com/juan975">Juan Cristóbal Espinosa Rodas</a>
    </td>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/your-director-photo" width="130" height="160" alt="Armando Cabrera"><br>
      Armando Augusto Cabrera Silva, Mg.
    </td>
  </tr>
</table>

---

## Arquitectura del sistema

El sistema sigue el **Modelo de Vistas 4+1 de Kruchten** y está documentado bajo la norma **ISO/IEC/IEEE 42010:2022**. Los cuatro componentes principales son:

```
┌─────────────────────────────────────────────────────────────────┐
│                     SISTEMA DE PREDICCIÓN GLP                   │
├──────────────────┬──────────────────┬───────────────┬───────────┤
│  Fuentes de      │  Pipeline de     │  Motor de     │  Capa de  │
│  datos e         │  preprocesamiento│  predicción   │  reportes │
│  ingestión       │  e ingeniería    │  (inferencia) │  y SHAP   │
│                  │  de características               │           │
│  · Odoo (ERP)   │  · Imputación    │  · Random     │  · Output │
│  · INEC          │  · Encoding      │    Forest     │    tabular │
│  · ARCERNNR      │  · Feature eng.  │  · XGBoost    │  · Feature│
│  · SIG vial      │  · Leakage ctrl  │  · LSTM       │    import.│
│  · Eventos       │  · Versioning    │               │  · SHAP   │
└──────────────────┴──────────────────┴───────────────┴───────────┘
```

---

## Metodología

El desarrollo sigue el proceso **CRISP-DM** combinado con prácticas ágiles iterativas, estructurado en seis fases:

```
Comprensión      Comprensión     Preparación      Modelado      Evaluación     Despliegue
del negocio  →   de los datos → de los datos  →  (ML)       →  (métricas)  →  (docs + API)
     ↑                                                                              │
     └──────────────────────── iteración continua ◄──────────────────────────────┘
```

**Métricas de evaluación:** MAE · RMSE · MAPE · R²  
**Esquema de validación:** Walk-forward validation (validación cruzada temporal)

---

## Marcos normativos

El sistema se documenta y gobierna bajo los siguientes estándares internacionales:

| Norma | Aplicación en el proyecto |
|---|---|
| **ISO/IEC 23053:2022** | Marco conceptual del ciclo de vida del sistema ML |
| **ISO/IEC 42001:2023** | Sistema de gestión de IA (gobernanza y ética) |
| **ISO/IEC 23894:2023** | Gestión de riesgos específicos de IA |
| **ISO/IEC/IEEE 42010:2022** | Descripción arquitectónica (Modelo 4+1) |

---

<p align="center">
  <sub>© 2025 Dara Van Gijsel Guarnizo · Juan Cristóbal Espinosa Rodas — UTPL, Loja, Ecuador</sub>
</p>
