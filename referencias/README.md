# referencias/

Datos **públicos o de definición propia** que sí se versionan en git. Nada con PII.

| Archivo | Qué es | Estado |
|---|---|---|
| `calendario_eventos.csv` | Feriados, Romería, fiestas cantonales | Romería 2023–2026: las fechas 17-ago → 1-nov vienen del documento de fuentes; **citar la fuente** (GAD Loja o Arquidiócesis) en la tesis. Feriados nacionales 2023–2026 (`feriado_nacional`): una fila por día de descanso efectivo, ya trasladado según la Ley de Feriados (RO-S 906, 2016), tomado del calendario oficial del Ministerio/Viceministerio de Turismo; `provincia` y `canton` vacíos porque rigen en todo el país. No incluye los días de descanso adicionales por decreto ejecutivo (p. ej., 2 y 3 de enero de 2025, 17 de abril de 2025, 2 de enero de 2026). Faltan fiestas cantonales y 2027. |
| `mapa_segmentos.csv` | Regla que asigna cada línea de factura a uno de los 5 segmentos de negocio | **Por definir con Lojagas.** El dataset no trae un campo "segmento". |

Cualquier cambio a `mapa_segmentos.csv` cambia el target del modelo: requiere PR revisado por ambos y una nota en la model card.
