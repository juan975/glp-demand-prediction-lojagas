# referencias/

Datos **públicos o de definición propia** que sí se versionan en git. Nada con PII.

| Archivo | Qué es | Estado |
|---|---|---|
| `calendario_eventos.csv` | Feriados, Romería, fiestas cantonales | Solo Romería cargada. Las fechas 17-ago → 1-nov vienen del documento de fuentes; **citar la fuente** (GAD Loja o Arquidiócesis) en la tesis. Faltan feriados nacionales y fiestas cantonales. |
| `mapa_segmentos.csv` | Regla que asigna cada línea de factura a uno de los 5 segmentos de negocio | **Por definir con Lojagas.** El dataset no trae un campo "segmento". |

Cualquier cambio a `mapa_segmentos.csv` cambia el target del modelo: requiere PR revisado por ambos y una nota en la model card.
