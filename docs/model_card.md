# Model card — Predicción de demanda de GLP (Lojagas)

Formato de *model card* (Mitchell et al., 2019), organizado según los componentes de un sistema de ML que define ISO/IEC 23053:2022. La norma es un marco conceptual: no exige una model card, pero da el vocabulario para describir el modelo (sección 3.4.6 del TIC). Se completa a medida que avanza CRISP-DM. **Cada cambio de target, features o métricas actualiza este archivo en el mismo PR.**

## 1. Uso previsto
- **Usuarios:** planificación comercial de Lojagas.
- **Decisión que apoya:** volumen mensual a solicitar a Petroecuador por segmento.
- **Fuera de alcance:** predicción por cliente individual, horizontes mayores a _[definir]_ meses y zonas fuera de Loja y Zamora Chinchipe.

## 2. Target
- Volumen físico de GLP en **toneladas** por mes y segmento (no USD).
- Fuente: `kg_glp` de las líneas de factura publicadas; las notas de crédito restan.
- Regla de segmentos: `referencias/mapa_segmentos.csv` (versión: _[commit]_). Provisional, por categoría de producto: doméstico, industrial y agroindustrial; la venta de envases de cilindro (≈ 0,75 % de los kg) se excluye porque no es gas. Pendiente de I-04.
- Solo meses cerrados: la curación descarta lo posterior al último mes cerrado, para que un mes en curso o una exportación cortada no parezcan una caída de la demanda.
- Anual = suma de las predicciones mensuales. No es un modelo aparte.

## 3. Datos
| Fuente | Periodo | Granularidad | `delta_version` | Disponible al predecir |
|---|---|---|---|---|
| Odoo (facturas) | 2023-01 → | línea de factura | | t−1 |
| Calendario de eventos | | día | git | t (se conoce de antemano) |
| INAMHI | | mes | | _[verificar latencia]_ |

## 4. Candidatos y protocolo
- **Horizonte provisional de 2**, sujeto al ADR-0014: el sistema corre el día 2 del mes M con datos cerrados hasta M−1 y predice M+1 (el 2 de noviembre predice diciembre). Ninguna feature usa un mes posterior a M−1: los rezagos empiezan en t−2 y las medias móviles se desplazan dos meses.
- Baselines: ingenuo (t−2, el último mes cerrado) y estacional ingenuo (t−12, el método actual de Lojagas).
- Candidatos: Lasso, Ridge, Elastic Net, Random Forest, XGBoost, LightGBM y LSTM (condicionado).
- Walk-forward con ventana expansiva, mínimo _[24]_ meses de entrenamiento y un mes de separación entre entrenamiento y prueba: para evaluar diciembre se entrena hasta octubre.
- **Criterio de éxito:** menor WAPE medio que el estacional ingenuo; se reporta la mejora relativa. El MAPE < 10 % del documento se informa pero no decide (issue I-13): en el EDA, el estacional ingenuo ya da ≈ 3,6 % sobre la serie total.
- Dos configuraciones con las mismas particiones, algoritmos y presupuesto de búsqueda: **A**, solo variables derivadas del histórico de ventas, y **B**, A más las fuentes contextuales. La comparación pareada por fold y por segmento responde la pregunta de investigación.
- Hiperparámetros con Optuna **dentro** de cada fold (validación anidada).

## 5. Resultados
| Modelo | Config. | WAPE | Mejora sobre el estacional ingenuo (%) | MAPE | MAE (t) | RMSE (t) | R² |
|---|---|---|---|---|---|---|---|

## 6. Supuestos y limitaciones
- Aproximadamente 46 meses de historia: la varianza de las métricas entre folds es alta. Se reporta media ± desviación.
- El MAPE se indefine con meses en cero y explota en segmentos de bajo volumen. Se reporta WAPE como métrica principal y MAPE porque lo usa el documento.

## 7. Explicabilidad
SHAP sobre el último fold.

## 8. Versionado
`git_sha`, `imagen_tag` y `delta_version.*` quedan etiquetados en cada corrida de MLflow.
