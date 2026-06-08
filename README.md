# Modelo-predictivo-ventas-Lojagas

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
      <img src="https://github.com/user-attachments/assets/your-dara-photo" width="130" height="160" alt="Dara Van Gijsel"><br>
      <a href="https://github.com/daravan1">Dara Van Gijsel Guarnizo</a>
    </td>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/your-juan-photo" width="130" height="160" alt="Juan Espinosa"><br>
      <a href="https://github.com/juan975">Juan Cristóbal Espinosa Rodas</a>
    </td>
  </tr>
</table>

---

## Descripción

Este repositorio contiene el código fuente, los artefactos de arquitectura y la documentación técnica del **Trabajo de Integración Curricular (TIC)** desarrollado para la carrera de Computación de la **Universidad Técnica Particular de Loja (UTPL)**.

El proyecto consiste en el diseño, entrenamiento y evaluación de un **modelo predictivo de aprendizaje automático** para estimar las ventas mensuales de gas licuado de petróleo (GLP) en toneladas métricas para la empresa **Lojagas C.E.M.**, considerando variables históricas, territoriales, demográficas y coyunturales de las provincias de Loja y Zamora Chinchipe.

---

## Problema que resuelve

Lojagas opera su planificación de demanda con métodos empíricos basados únicamente en registros históricos de ventas, sin incorporar variables externas de alto impacto como el estado vial en la ruta de abastecimiento, el crecimiento poblacional por cantón, la estacionalidad agrícola o eventos masivos como la **Romería de la Virgen del Cisne** (agosto–octubre). Esto genera incertidumbre operativa que se traduce en sobrestock o desabastecimiento.

Este proyecto propone un sistema de predicción que integra múltiples fuentes de datos para generar estimaciones de alta precisión con un horizonte de 7 a 30 días, habilitando una planificación proactiva y basada en datos.

---

## Solución propuesta

Se desarrolla un **modelo predictivo de ventas de GLP** que aprende de los datos
históricos de Lojagas y los combina con información externa — estado de las vías,
crecimiento poblacional por cantón, eventos regionales y ciclos agrícolas — para
generar estimaciones de demanda precisas con anticipación suficiente para que la
empresa pueda planificar sus compras, su logística y su inventario sin depender
del criterio empírico.

El proyecto se estructura en cuatro entregables principales:

- **Base de datos analítica:** integración y limpieza de todas las fuentes de
  información relevantes para el negocio de Lojagas en una sola base estructurada
  y lista para ser consultada.

- **Modelo predictivo:** entrenamiento y comparación de múltiples algoritmos de
  aprendizaje automático para identificar el que mejor estima las ventas mensuales
  de GLP por segmento y cantón.

- **Sistema explicable:** el modelo no solo predice, también indica qué variables
  están impulsando la demanda en cada período, de forma que la gerencia pueda
  entender y confiar en las estimaciones.

- **Documentación de arquitectura:** descripción completa del sistema bajo
  estándares internacionales ISO, incluyendo el mapa de capacidades del negocio,
  las vistas arquitectónicas 4+1 y la gestión de riesgos del modelo de IA.

---

## Objetivos del proyecto

### Objetivo general
Desarrollar un modelo predictivo de aprendizaje automático para estimar las ventas
mensuales y anuales de gas licuado de petróleo de la empresa Lojagas C.E.M.,
considerando variables históricas, territoriales y coyunturales, mediante datos
recopilados de la empresa y fuentes de información geográfica y contextual de las
provincias de Loja y Zamora Chinchipe.

### Objetivos específicos

- **Identificar** las variables históricas y contextuales que influyen en el
  comportamiento de las ventas de GLP en Lojagas, mediante análisis del negocio,
  revisión bibliográfica y entrevistas con expertos de la empresa.

- **Construir** una base de datos analítica que integre información comercial,
  temporal, geográfica y contextual relevante para el entrenamiento del modelo
  predictivo.

- **Diseñar y entrenar** modelos de aprendizaje automático orientados a la
  predicción de ventas mensuales y anuales, aplicando las mejores prácticas de
  ingeniería de características y selección de modelos.

- **Comparar** el desempeño de distintos modelos predictivos mediante métricas
  de precisión y error (MAE, RMSE, MAPE, R²), seleccionando el modelo de mejor
  rendimiento para su documentación e implementación bajo el marco ISO/IEC 23053:2022.

<p align="center">
  <sub>© 2025 Dara Van Gijsel Guarnizo · Juan Cristóbal Espinosa Rodas — UTPL, Loja, Ecuador</sub>
</p>
