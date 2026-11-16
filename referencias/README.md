# referencias/

Datos **públicos o de definición propia** que sí se versionan en git. Nada con PII.

| Archivo | Qué es | Estado |
|---|---|---|
| `calendario_eventos.csv` | Feriados, Romería, fiestas cantonales | Solo Romería cargada. Las fechas 17-ago → 1-nov vienen del documento de fuentes; **citar la fuente** (GAD Loja o Arquidiócesis) en la tesis. Faltan feriados nacionales y fiestas cantonales. |
| `mapa_segmentos.csv` | Regla que asigna cada línea de factura a un segmento. Sus columnas (salvo `segmento`) son las claves; `*` es comodín y `excluir` saca líneas que no son demanda de gas | **Provisional, por `categoria` de producto** (doméstico, industrial, agroindustrial; los envases se excluyen), según el EDA. Falta que Lojagas confirme el campo del cupo (I-04): si es `tipo_distribuidor`, se cambian las columnas del CSV, no el código. Toda clave del mapa debe estar en la lista blanca de `procesamiento/anonimizacion.py`. |

Cualquier cambio a `mapa_segmentos.csv` cambia el target del modelo: requiere PR revisado por ambos y una nota en la model card.
