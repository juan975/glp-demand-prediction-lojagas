# Model card — Predicción de demanda de GLP (Lojagas)

Estructura alineada con los componentes que exige ISO/IEC 23053:2022 (sección 3.4.5 del TIC). Se completa a medida que avanza CRISP-DM. **Cada cambio de target, features o métricas actualiza este archivo en el mismo PR.**

## 1. Uso previsto
- **Usuarios:** planificación comercial de Lojagas.
- **Decisión que apoya:** volumen mensual a solicitar a Petroecuador por segmento.
- **Fuera de alcance:** predicción por cliente individual, horizontes mayores a _[definir]_ meses y zonas fuera de Loja y Zamora Chinchipe.

## 2. Target
- Volumen físico de GLP en **toneladas** por mes y segmento (no USD).
- Fuente: `kg_glp` de las líneas de factura publicadas; las notas de crédito restan.
- Regla de segmentos: `referencias/mapa_segmentos.csv` (versión: _[commit]_).
- Anual = suma de las predicciones mensuales. No es un modelo aparte.

## 3. Datos
| Fuente | Periodo | Granularidad | `delta_version` | Disponible al predecir |
|---|---|---|---|---|
| Odoo (facturas) | 2023-01 → | línea de factura | | t−1 |
| Calendario de eventos | | día | git | t (se conoce de antemano) |
| INAMHI | | mes | | _[verificar latencia]_ |

## 4. Candidatos y protocolo
- Baselines: ingenuo (t−1) y estacional ingenuo (t−12).
- Candidatos: Lasso, Ridge, Elastic Net, Random Forest, XGBoost, LightGBM y LSTM (condicionado).
- Walk-forward con ventana expansiva, mínimo _[24]_ meses de entrenamiento y horizonte de 1.
- Hiperparámetros con Optuna **dentro** de cada fold (validación anidada).

## 5. Resultados
| Modelo | WAPE | MAPE | MAE (t) | RMSE (t) | R² | Gana al estacional ingenuo |
|---|---|---|---|---|---|---|

## 6. Supuestos y limitaciones
- Aproximadamente 46 meses de historia: la varianza de las métricas entre folds es alta. Se reporta media ± desviación.
- El MAPE se indefine con meses en cero. Se reporta WAPE como métrica principal y MAPE como criterio del documento.

## 7. Explicabilidad
SHAP sobre el último fold.

## 8. Versionado
`git_sha`, `imagen_tag` y `delta_version.*` quedan etiquetados en cada corrida de MLflow.
