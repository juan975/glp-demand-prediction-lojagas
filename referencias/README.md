# referencias/

Datos **públicos o de definición propia** que sí se versionan en git. Nada con PII.

| Archivo | Qué es | Estado |
|---|---|---|
| `calendario_eventos.csv` | Feriados, Romería, fiestas cantonales | Romería 2023–2026: las fechas 17-ago → 1-nov vienen del documento de fuentes; **citar la fuente** (GAD Loja o Arquidiócesis) en la tesis. Feriados nacionales 2023–2026 (`feriado_nacional`): una fila por día de descanso efectivo, ya trasladado según la Ley de Feriados (RO-S 906, 2016), tomado del calendario oficial del Ministerio/Viceministerio de Turismo; `provincia` y `canton` vacíos porque rigen en todo el país. No incluye los días de descanso adicionales por decreto ejecutivo (p. ej., 2 y 3 de enero de 2025, 17 de abril de 2025, 2 de enero de 2026). Faltan fiestas cantonales y 2027. |
| `mapa_segmentos.csv` | Regla que asigna cada línea de factura a un segmento. Sus columnas (salvo `segmento`) son las claves; `*` es comodín y `excluir` saca líneas que no son demanda de gas | **Provisional, por `categoria` de producto** (doméstico, industrial, agroindustrial; los envases se excluyen), según el EDA. Falta que Lojagas confirme el campo del cupo (I-04): si es `tipo_distribuidor`, se cambian las columnas del CSV, no el código. Toda clave del mapa debe estar en la lista blanca de `procesamiento/anonimizacion.py`. |
| `provincias.geojson` | Contorno de Loja y Zamora Chinchipe. `procesamiento/clima.py` asigna cada píxel de ERA5-Land a su provincia con él | Fuente: INEC, límites provinciales 2018, publicados en HDX (COD-AB Ecuador, `data.humdata.org/dataset/cod-ab-ecu`), versión simplificada de geoBoundaries gbHumanitarian (commit `9469f09`). Licencia CC BY 3.0 IGO: **citar al INEC** en la tesis. Con la malla de 0,1° quedan 86 píxeles en Loja y 88 en Zamora; los rectángulos de descarga de ERA5-Land los cubren todos. |

Cualquier cambio a `mapa_segmentos.csv` cambia el target del modelo: requiere PR revisado por ambos y una nota en la model card.
